from flask import Flask, render_template, request, redirect, url_for, jsonify
import hashlib
import json
import time

app = Flask(__name__)

# --- BLOCKCHAIN CORE ---
class Block:
    def __init__(self, index, timestamp, data, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]

    def create_genesis_block(self):
        return Block(0, time.time(), "Genesis Block - Election Started", "0")

    def get_latest_block(self):
        return self.chain[-1]

    def add_block(self, data):
        latest_block = self.get_latest_block()
        new_block = Block(
            index=latest_block.index + 1,
            timestamp=time.time(),
            data=data,
            previous_hash=latest_block.hash
        )
        self.chain.append(new_block)

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i-1]
            if current.hash != current.calculate_hash():
                return False
            if current.previous_hash != previous.hash:
                return False
        return True

# Initialize our election blockchain
election = Blockchain()

# --- WEB ROUTES ---
@app.route('/')
def home():
    # Count the votes from the blockchain
    tally = {"Candidate A": 0, "Candidate B": 0}
    for block in election.chain[1:]:  # Skip genesis block
        candidate = block.data.get("candidate")
        if candidate in tally:
            tally[candidate] += 1
            
    is_valid = election.is_chain_valid()
    return render_template('index.html', chain=election.chain, tally=tally, is_valid=is_valid)

@app.route('/vote', methods=['POST'])
def vote():
    candidate = request.form.get('candidate')
    if candidate:
        # Cast vote by adding a new block to the chain
        election.add_block({"candidate": candidate, "voter_id": f"VOTER_{int(time.time())}"})
    return redirect(url_for('home'))

@app.route('/tamper', methods=['POST'])
def tamper():
    # Simulate a database hack by altering an existing block's data directly
    if len(election.chain) > 1:
        election.chain[1].data = {"candidate": "Candidate B", "voter_id": "HACKED_VOTE"}
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)