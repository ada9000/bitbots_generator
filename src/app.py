import os
import base64
import random

from flask import Flask, jsonify, request
from Bitbots import Bitbots
from CardanoComms import *

from flask_cors import CORS

import urllib.parse

app = Flask(__name__)
CORS(app)
app.config["SERVER_NAME"] = "127.0.0.1:5225"

mint_wallet = Wallet()
#m = MintProcess(mint_wallet=mint_wallet, nft_price_ada=69)
t = BlockFrostTools()
#m.run()

POLICY = "f681ff0a98086b3862f341c704b29faee8dbaafa2ea6279acf05d4a8"

# get all?
@app.route("/")
def home():
    return "Home"

@app.route("/policy", methods=['GET','POST'])
def policy():
    return t.return_all_meta()

@app.route("/nft_count")
def get_count():
    return jsonify({"count":t.policy_nft_count(POLICY)})

# you can now type nft/0001 to and the image will be returned
# svg data is sourced from the Cardano blockchain!
@app.route("/nft/<id>")
def get_nft(id):
    svg = t.onchain_nft_to_svg(POLICY, id)
    return svg

@app.route("/nfts")
def nfts():
    return jsonify(t.get_nfts(POLICY))


@app.route("/addr")
def addr():
    return m.get_payment_addr()

@app.route("/price")
def price():
    return m.get_nft_price()


#@app.route("/svg")
#def svg():
#    with open(filename_svg, 'r') as f:
#        data = f.read()



@app.route("/generate")
def generate():
    b.generate()
    return "Done"
    # add post method 


@app.route("/rand")
def random_nft():
    n = random.randint(0, 8192)
    print("sending...")
    return jsonify(nfts[str(n)])

@app.route("/test")
def test():
    n = random.randint(0, 8192)
    print("sending...")
    test = nfts[str(n)]
    test = urllib.parse.quote(test)
    return test

@app.route("/showme")
def showme():
    n = random.randint(0, 8192)
    test = nfts[str(n)]
    return test

# TODO show svg image of nft
# TODO request purchase
