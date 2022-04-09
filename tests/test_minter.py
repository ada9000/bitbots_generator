import sys
sys.path.append('../src')
from ApiManager import *


PRICE=5
NEW_POLICY=False
PROJECT = "TESTSS"
MAX_MINT=10

mint_wallet = Wallet()
m = ApiManager(mint_wallet=mint_wallet, nft_price_ada=PRICE, project=PROJECT, max_mint=MAX_MINT)

done = False

while not done:
    done = m.run()
