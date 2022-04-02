import os
import base64
import random
from flask import Flask, jsonify, request
from flask_cors import CORS
import urllib.parse
from ApiManager import *
from BlockFrostTools import BlockFrostTools
# flask config ---------------------------------------------------------------
app = Flask(__name__)
CORS(app)
#app.config["SERVER_NAME"] = "127.0.0.1:5225" # TODO set this to ip + port
# vars -----------------------------------------------------------------------
mint_wallet = Wallet()
price = 5
max_mint = 12
apiManager = ApiManager(mint_wallet=mint_wallet, project="TEST3", nft_price_ada=price, max_mint=max_mint)
t = BlockFrostTools()
# ----------------------------------------------------------------------------


# get all?
@app.route("/")
def home():
    return "Home"

#@app.route("/policy", methods=['GET','POST'])
#def policy():
#    return t.return_all_meta()


@app.route("/nft_count")
def get_count():
    POLICY = "264ffa1e5e783cb31b7aeceac530d2054b60d1ee48c0a701d12246dd" # TODO use this to test
    return jsonify({ "count": t.policy_nft_count(apiManager.get_policy()) })

# you can now type nft/0001 to and the image will be returned
# svg data is sourced from the Cardano blockchain!
@app.route("/nft/<id>")
def get_nft(id):
    svg = t.onchain_nft_to_svg(apiManager.get_policy(), id)
    return svg

@app.route("/nfts")
def nfts():
    log_error(apiManager.get_policy())
    return jsonify(t.get_nfts(apiManager.get_policy()))

@app.route("/policy")
def policy():
    return jsonify({"policy" : str(apiManager.get_policy()) })

@app.route("/mint_addr")
def addr():
    return jsonify({"addr" : str(apiManager.get_payment_addr()) })

@app.route("/mint_price")
def price():
    return jsonify({"price" : str(apiManager.get_nft_price()) })

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