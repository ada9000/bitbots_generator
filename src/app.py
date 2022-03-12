import os
import base64
import random

from flask import Flask, jsonify, request
from Bitbots import Bitbots

from flask_cors import CORS

import urllib.parse

b = Bitbots()
nfts = b.shuffle()
app = Flask(__name__)
CORS(app)
app.config["SERVER_NAME"] = "127.0.0.1:5000"


# load json

# test mint


# get all?
@app.route("/")
def home():
    return "Home"


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

# get specific
@app.route("/nfts")
def nft():
    # warning can be a 300 mb call
    return jsonify(nfts)

# TODO show svg image of nft
# TODO request purchase
