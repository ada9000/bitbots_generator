import sys
sys.path.append('../src')

from ApiManager import ApiManager
from Utility import TESTNET, MAINNET
from Wallet import Wallet

mintWallet = Wallet()
a = ApiManager(network=TESTNET, mint_wallet=mintWallet, nft_price_ada=10, project='a', max_mint=4)
a.run()