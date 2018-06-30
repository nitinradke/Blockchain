# -*- coding: utf-8 -*-
"""
Created on Sat Jun 30 16:20:36 2018

@author: Nitin Radke
"""
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 28 10:36:07 2018

@author: Nitin Radke
"""

# 2. CreateCryptocurrency

import datetime
import json
from flask import jsonify, Flask, request
import hashlib
import requests
from uuid import uuid4
from urllib.parse import urlparse

# Cryptocurrency blockchain
class Blockchain:
   
        def create_block(self, proof, previous_hash):
            block = {
            'index' : len(self.chain)+1,
            'timestamp' : str(datetime.datetime.now()),
            'proof' : proof,
            'previous_hash' : previous_hash,
            'transactions': self.transactions
            }
            self.transactions = []
            self.chain.append(block)
            return block
        
        def __init__(self):
            self.chain = []
            self.transactions = []
            self.nodes = set()
            self.create_block(proof = 1, previous_hash = '0')

        def get_previous_block(self):
            return self.chain[-1]


        def proof_of_work(self, previous_proof):
            new_proof = 1
            isdetected = False
            while isdetected is False:
                hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
                if hash_operation[:4] == '0000':
                    isdetected = True
                else:
                    new_proof += 1
            return new_proof
        
        def hash(self, block):
            encoded_block = json.dumps(block, sort_keys=True).encode()
            return hashlib.sha256(encoded_block).hexdigest()
        
        
        def is_chain_valid(self, chain):
            previous_block = chain[0]
            block_index = 1
            while block_index < len(chain):
                block = chain[block_index]
                if block['previous_hash'] != self.hash(previous_block):
                    return False
                current_proof = block['proof']
                previous_proof = previous_block['proof']
                hash_operation = hashlib.sha256(str(current_proof**2 - previous_proof**2).encode()).hexdigest()
                if hash_operation[:4] != '0000':
                    return False
                previous_block = chain[block_index]
                block_index+=1
            return True
            
        def add_transactions(self, sender, reciever, amount):
            self.transactions.append({'sender':sender,
                                     'reciever':reciever,
                                     'amount':amount})
            return(self.get_previous_block()['index']+1)
            
        def add_node(self, address):
            parsed_url = urlparse(address)
            self.nodes.add(parsed_url.netloc)
            
        def update_chain(self):
            network = self.nodes
            length = len(self.chain)
            longestchain = None
            maxlength = 0
            for node in network:
                response = requests.get('http://'+node+'/get_chain')
                if response.status_code == 200:
                    length = response.json()['length']
                    chain = response.json()['chain']
                    if length > maxlength and self.is_chain_valid(chain):
                        maxlength = length
                        longestchain = chain
            if longestchain:
                self.chain = longestchain
                return True
            return False
              
            
#Part2 Mining our Blockchain
            
#Building app
app = Flask(__name__)
blockchain = Blockchain()


node_address = str(uuid4()).replace('-','')

#Mining a block
@app.route('/mine_block', methods = ['GET'])
def mine_block():
    blockchain.add_transactions(sender = node_address, reciever = 'Shubham', amount = 0.001)
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    block = blockchain.create_block(proof,previous_hash)
    response = {'message':'Congratulation you mined a block',
                'block_index':block['index'],
                'timestamp':block['timestamp'],
                'transactions':block['transactions'],
                'proof':block['proof'],
                'previous_hash':block['previous_hash']
                }
    return jsonify(response), 200 

#Fetching the blockchain      
@app.route('/get_chain', methods = ['GET'])           
def get_block():
    response = {'chain':blockchain.chain,
                'length':len(blockchain.chain)}
    return jsonify(response), 200
            
#Validating blockchain
@app.route('/is_valid', methods = ['GET'])
def isvalid():
    if blockchain.is_chain_valid(blockchain.chain):
        response = {'message':'Everything good going man'}
    else:
        response = {'message':'Hey, we got some problem here'}
    return jsonify(response), 200


@app.route('/add_transaction', methods = ['POST'])
def add_transaction():
    json = request.get_json()
    transaction_keys = ['sender','reciever','amount']
    if not all(key in json for key in transaction_keys):
        return 'There is some problem', 400
    index = blockchain.add_transactions(json['sender'], json['reciever'], json['amount'])
    return 'Your transaction will be added to the block no '+index, 201

@app.route('/add_nodes', methods = ['POST'])
def add_nodes():
    json = request.get_json()
    nodes = json.get('node')
    if nodes == []:
        return 'Something wrong', 400
    else:
        for node in nodes:
            blockchain.add_node(node)
        response = {'message':'hey, all the nodes are added',
                    'nodes': list(blockchain.nodes)}
        return jsonify(response), 201

@app.route('/repalce_chain', methods = ['GET'])
def replace_chain():
    is_valid_chain = blockchain.update_chain()
    if is_valid_chain:
        response = {'message':'Hey your chain was invalid now it is updated',
                'chain':blockchain.chain}
        return jsonify(response) , 200
    else:
        response = {'messsage':'Chain is up to date',
                'actual_chain':blockchain.chain}
        return jsonify(response), 200


#Running app
app.run(host = '0.0.0.0', port = 5002)



