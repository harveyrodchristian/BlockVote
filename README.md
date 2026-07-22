# BlockVote: Decentralized & Tamper-Proof Student Voting System

BlockVote is a decentralized, tamper-proof student voting system that eliminates database manipulation risks by storing vote transactions directly on the **Cardano Preprod Testnet**. 

Traditional voting applications persist data in centralized SQL or NoSQL databases. A rogue administrator or external attacker with system access can update database tables to modify election results. BlockVote solves this by using the Cardano blockchain as its ledger. Votes are signed locally by the admin's private key, structured as a 1.5 ADA self-transfer transaction, and published on-chain with JSON metadata identifying the candidate.

---

## 1. System Architecture

```
[ Client Browser (Tailwind UI) ]
      │ ▲
      │ │ (HTTP GET/POST Render)
      ▼ │
[ Flask Web Server (app.py) ]
      │ ▲
      │ │ (Queries Metadata Label 1999 / Submits Signed TX)
      ▼ │
[ Blockfrost API Gateway ]
      │ ▲
      │ │ (Relays Transactions to Network Nodes)
      ▼ │
[ Cardano Preprod Testnet Ledger ]
```

---

## 2. 4-Step Technical Workflow

1. **User Interaction**: The voter selects a candidate (Candidate A or Candidate B) on the web dashboard and submits the voting form.
2. **Transaction Building & Local Signing**: The Flask backend receives the POST request. Using `pycardano`, it builds a 1.5 ADA self-transfer transaction, attaches JSON metadata `{"candidate": "Candidate Name", "app": "BlockVote"}` under label `1999`, and signs it locally using the private signing key (`payment.skey`).
3. **Blockchain Broadcasting**: The signed transaction is transmitted to the Blockfrost API gateway, which broadcasts it to the active Cardano Preprod validator nodes.
4. **Consensus & Permanent Seal**: Cardano's Ouroboros Proof-of-Stake consensus validates the digital signature and UTxOs, committing the transaction into a new block. The frontend queries Blockfrost in real-time to list on-chain transactions and calculate the current tally.

---

## 3. Directory Structure

```
blockvote/
│
├── app.py              # Flask app & Cardano blockchain controller
├── payment.skey        # Admin Wallet Signing Key (Generated on first run)
├── payment.vkey        # Admin Wallet Verification Key (Generated on first run)
│
├── templates/
│   └── index.html      # Responsive Web Dashboard (Tailwind CSS)
│
└── README.md           # System deployment & evaluation guide (this file)
```

---

## 4. Quickstart Guide

### Step 1: Clone and Set Up Environment
Create a Python virtual environment and install dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install flask pycardano
```

### Step 2: Set Up Blockfrost API Key
1. Go to [blockfrost.io](https://blockfrost.io/) and create a free account.
2. Create a new project targeting the **Cardano Preprod** network.
3. Copy your project ID (API key).
4. Set it as an environment variable:
   ```bash
   export BLOCKFROST_API_KEY="your_blockfrost_project_id"
   ```
   *Alternatively, replace the `BLOCKFROST_API_KEY` string placeholder directly inside [app.py](file:///Users/angelaolorbida/Desktop/BlockVote/BlockVote/app.py).*

### Step 3: Initialize Keys & Fund Wallet
1. Run the Flask application once to automatically generate your cryptographic keys:
   ```bash
   python3 app.py
   ```
   *This will create `payment.skey` and `payment.vkey` in your project root, and print your new wallet address.*
2. Copy your wallet address from the console output or the web interface.
3. Fund your wallet using the official [Cardano Testnet Faucet](https://docs.cardano.org/cardano-testnet/faucet):
   * Select **Preprod Testnet** as the network.
   * Paste your wallet address.
   * Complete the recaptcha and click **Request funds**.
   * Wait 1–2 minutes for the transaction to clear. You can verify your balance on the dashboard.

### Step 4: Launch and Vote
Start the server and visit `http://127.0.0.1:5000` to cast votes and view live on-chain ledger records!
```bash
python3 app.py
```
