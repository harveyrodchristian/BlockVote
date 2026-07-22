import os
from flask import Flask, render_template, request, redirect, url_for, flash
from blockfrost import BlockFrostApi, ApiUrls
from pycardano import (
    BlockFrostChainContext, Network, PaymentSigningKey,
    PaymentVerificationKey, Address, TransactionBuilder,
    TransactionOutput, AuxiliaryData, Metadata
)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "blockvote-secret-key-1999")

# Configuration Constants
NETWORK = Network.TESTNET
BLOCKFROST_API_KEY = os.environ.get("BLOCKFROST_API_KEY", "preprodIjlbf4FjmgjyIdeOQ6oz1LIT3jAWpgG9")
METADATA_LABEL = 1999

# Cryptographic Keys Loading / Generation
KEY_FILE = "payment.skey"
VKEY_FILE = "payment.vkey"

# Production configuration: load signing key from environment variables if present
env_skey_json = os.environ.get("PAYMENT_SKEY_JSON")
env_skey_cbor = os.environ.get("PAYMENT_SKEY_CBOR_HEX")

if env_skey_json:
    print("Loading admin signing key from environment variable (JSON)...")
    payment_skey = PaymentSigningKey.from_json(env_skey_json)
    payment_vkey = PaymentVerificationKey.from_signing_key(payment_skey)
elif env_skey_cbor:
    print("Loading admin signing key from environment variable (CBOR HEX)...")
    payment_skey = PaymentSigningKey.from_cbor(bytes.fromhex(env_skey_cbor))
    payment_vkey = PaymentVerificationKey.from_signing_key(payment_skey)
elif not os.path.exists(KEY_FILE):
    print("Generating new admin cryptographic keys...")
    payment_skey = PaymentSigningKey.generate()
    payment_skey.save(KEY_FILE)
    payment_vkey = PaymentVerificationKey.from_signing_key(payment_skey)
    payment_vkey.save(VKEY_FILE)
    print(f"Keys successfully generated: {KEY_FILE}, {VKEY_FILE}")
else:
    payment_skey = PaymentSigningKey.load(KEY_FILE)
    payment_vkey = PaymentVerificationKey.from_signing_key(payment_skey)

my_address = Address(payment_vkey.hash(), network=NETWORK)

print("=" * 60)
print(f"BlockVote Cardano Admin Wallet Address: {my_address}")
print("Funding Link: https://docs.cardano.org/cardano-testnet/faucet")
print("=" * 60)

# API and Context Initialization (gracefully handle missing API key)
has_api_key = BLOCKFROST_API_KEY and BLOCKFROST_API_KEY != "YOUR_BLOCKFROST_PREPROD_KEY"

if has_api_key:
    api = BlockFrostApi(project_id=BLOCKFROST_API_KEY, base_url=ApiUrls.preprod.value)
    context = BlockFrostChainContext(BLOCKFROST_API_KEY, base_url=ApiUrls.preprod.value)
else:
    api = None
    context = None
    print("WARNING: BLOCKFROST_API_KEY is not configured. Running in Read-Only Demo mode.")

def to_dict(obj):
    if isinstance(obj, list):
        return [to_dict(x) for x in obj]
    elif hasattr(obj, '__dict__') or type(obj).__name__ == 'Namespace':
        try:
            d = vars(obj)
        except TypeError:
            try:
                d = obj.__dict__
            except AttributeError:
                return str(obj)
        return {k: to_dict(v) for k, v in d.items()}
    elif isinstance(obj, dict):
        return {k: to_dict(v) for k, v in obj.items()}
    else:
        return obj

@app.route('/health')
def health():
    return {"status": "healthy"}, 200

@app.route('/')
def home():
    tally = {"Candidate A": 0, "Candidate B": 0}
    transactions = []
    ledger_error = None

    if has_api_key:
        try:
            # Fetch live records directly from Cardano's public ledger state
            on_chain_records = api.metadata_label_json(label=str(METADATA_LABEL))
            for record in on_chain_records:
                vote_data = to_dict(record.json_metadata)
                if isinstance(vote_data, dict):
                    candidate = vote_data.get("candidate")
                    if candidate in tally:
                        tally[candidate] += 1
                    transactions.append({
                        "tx_hash": record.tx_hash,
                        "data": vote_data
                    })
        except Exception as e:
            ledger_error = f"Ledger Query Error: {e}"
            print(ledger_error)
    else:
        ledger_error = "Blockfrost API key is missing. Please set BLOCKFROST_API_KEY to fetch/cast votes."

    return render_template(
        'index.html',
        tally=tally,
        transactions=transactions,
        address=str(my_address),
        has_api_key=has_api_key,
        ledger_error=ledger_error
    )

@app.route('/vote', methods=['POST'])
def vote():
    if not has_api_key:
        flash("Cannot cast vote: Blockfrost API key is not configured.", "error")
        return redirect(url_for('home'))

    candidate = request.form.get('candidate')
    if candidate:
        try:
            # Construct and sign on-chain transaction
            builder = TransactionBuilder(context)
            builder.add_input_address(my_address)
            builder.add_output(TransactionOutput(my_address, 1500000)) # 1.5 ADA self-transfer
            
            # Attach vote payload as Cardano Transaction Metadata
            metadata = Metadata({METADATA_LABEL: {"candidate": candidate, "app": "BlockVote"}})
            builder.auxiliary_data = AuxiliaryData(data=metadata)
            
            # Sign and build transaction
            signed_tx = builder.build_and_sign([payment_skey], change_address=my_address)
            
            # Submit transaction
            context.submit_tx(signed_tx)
            flash(f"Vote cast successfully! Transaction submitted: {signed_tx.id}", "success")
            print(f"Transaction Submitted: {signed_tx.id}")
        except Exception as e:
            error_msg = str(e)
            print(f"Transaction Execution Error: {error_msg}")
            if "ValueNotConservedUTxO" in error_msg or "Insufficient UTxO" in error_msg or "UTxO" in error_msg:
                flash("Transaction failed: Insufficient UTxO balance. Please fund your wallet using the Preprod testnet faucet.", "error")
            else:
                flash(f"Transaction Execution Error: {error_msg}", "error")
                
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)