from ApiManager import ApiManager
from Utility import TESTNET, MAINNET
from Wallet import Wallet

from dotenv import load_dotenv
import os



if __name__ == "__main__":
    mintWallet = Wallet()

    load_dotenv()
    price       = os.getenv('PRICE')
    project     = str(os.getenv('PROJECT'))
    maxMint     = os.getenv('MAX_MINT')
    newPolicy   = False
    network     = TESTNET

    for x in [project, price, maxMint]:
        if x == None:
            raise Exception("Missing .env value")

    a = ApiManager(network=network, mint_wallet=mintWallet, nft_price_ada=price, project=project, max_mint=maxMint)
    a.run()
