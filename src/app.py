import os
import random

from flask import Flask, jsonify, request
from Bitbots import Bitbots

b = Bitbots()
nfts = b.shuffle()
app = Flask(__name__)
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
    # add post method 


# get specific
@app.route("/nft")
def nft():
    n = random.randint(0, 8192)
    return nfts[str(n)]


# TODO show svg image of nft

# TODO request purchase