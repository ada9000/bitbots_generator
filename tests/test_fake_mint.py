import sys
sys.path.append('../src')
from ApiManager import *

PRICE=5
NEW_POLICY=False
PROJECT = "FULL_DATA"
MAX_MINT=1000

mint_wallet = Wallet()
m = ApiManager(mint_wallet=mint_wallet, nft_price_ada=PRICE, project=PROJECT, max_mint=MAX_MINT)

m.fake_mint()