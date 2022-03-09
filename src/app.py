from flask import Flask, jsonify, request
from Bitbots import Bitbots

app = Flask(__name__)
app.config["SERVER_NAME"] = "127.0.0.1:5000"

nft_test =  { 'something':'yes', 'id':1}

# load json

# test mint


# get all?
@app.route("/")
def home():
    return "Home"


@app.route("/generate")
def generate():
    b = Bitbots()
    return '', 200
    # add post method 


# get specific
@app.route("/nft")
def nft():
    return jsonify(nft_test)

# TODO show svg image of nft

# TODO request purchase