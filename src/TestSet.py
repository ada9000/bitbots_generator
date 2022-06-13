import os
from MintManager import *
from dotenv import load_dotenv
import sys

# vars -----------------------------------------------------------------------
mintWallet = Wallet()
load_dotenv()
price       = os.getenv('PRICE')
#project     = str(os.getenv('PROJECT'))
maxMint     = os.getenv('MAX_MINT')
newPolicy   = False
network     = TESTNET # NOTE CHANGE ON PRODUCTION


project = None
try:
    project = sys.argv[1]
    maxMint = sys.argv[2]
except:
    project = input("Please enter project name\n> ")
    maxMint = input("Enter how many to generate\n> ")

print(f"Project is {project}")

MintManager = MintManager(network=network, mint_wallet=mintWallet, project=project, nft_price_ada=price, max_mint=maxMint)