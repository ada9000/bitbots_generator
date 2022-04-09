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
project = "FULL_DATA"
apiManager = ApiManager(mint_wallet=mint_wallet, project=project, nft_price_ada=price, max_mint=max_mint)
t = BlockFrostTools()
# ----------------------------------------------------------------------------


# get all?
@app.route("/")
def home():
    return jsonify({"status":"alive"})

# TODO incorrect usage here
@app.route("/nft_count")
def get_count():
    return jsonify({ "count": t.policy_nft_count(apiManager.get_policy()) })

# Cardano NFT actions --------------------------------------------------------
# you can now type nft/0001 to and the image will be returned
# svg data is sourced from the Cardano blockchain!
@app.route("/nft/<id>")
def get_nft(id):
    svg = t.onchain_nft_to_svg(apiManager.get_policy(), id)
    return svg

@app.route("/nfts")
def nfts():
    return jsonify(t.get_nfts(apiManager.get_policy()))


#@app.route("/random_nfts")
#def nfts():
#    return jsonify(t.get_nfts(apiManager.get_policy()))

# local nft actions ----------------------------------------------------------
@app.route("/nft_id", methods=['GET'])
def get_nft_id():
    id = None
    svg = None
    meta = None
    try:
        id = request.args.get('id')
        svg = apiManager.get_nft_svg(id)
        meta = apiManager.get_nft_meta(id)
    except:
        return '', 300

    if svg == None or meta == None:
        return '', 300

    return jsonify({"svg":svg, "meta":meta})


@app.route("/nft_svg/<id>")
def get_nft_svg(id):
    svg = apiManager.get_nft_svg(id)
    return jsonify({"svg":svg})

@app.route("/nft_meta/<id>")
def get_nft_meta(id):
    meta = apiManager.get_nft_meta(id)
    return jsonify({"meta":meta})

@app.route("/nft_names")
def get_nft_names():
    names = apiManager.get_names()
    return jsonify({"names":names})


# Mint actions ---------------------------------------------------------------
@app.route("/policy")
def policy():
    return jsonify({"policy" : str(apiManager.get_policy()) })

@app.route("/mint_addr")
def addr():
    return jsonify({"addr" : str(apiManager.get_payment_addr()) })

@app.route("/mint_price")
def price():
    return jsonify({"price" : str(apiManager.get_nft_price()) })