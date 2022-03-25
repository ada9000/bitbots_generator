from CardanoComms import *

PRICE=5
NEW_POLICY=False

mint_wallet = Wallet()
m = MintProcess(mint_wallet=mint_wallet, nft_price_ada=PRICE, new_policy=NEW_POLICY)

done = False

while not done:
    done = m.run()
