import sys
sys.path.append('../src')
from CardanoComms import *
import time
from multiprocessing import Process


PRICE = 5 # PRICE OF SINGLE NFT
NFT_LEN = 30 # AMOUNT OF NFTS TO MINT
MULTIMINT_FUNDS = (PRICE * 5) + 2 # MULTIPLE TO AVOID THE LONG DISTRIBUTION PROCESS
PRIME = False # IF TRUE WALLETS ARE FUNDED IF FALSE WALLETS START MINTING
NFT_ADDR = "addr_test1qz9t6ykv3sl2dgulxv4efer4kue4k7jx8w2qrnldd694fzvjcfp434vp7hl82exe6nul2vf5d342wldhss4svegh03qs6eursz"

def sub_wallet_buy(i):
    sent = False
    while not sent:
        log_debug("test wallet " + str(i) + " attempting buy")
        sent = c.simple_tx(lace=ada_to_lace(PRICE), 
            recv_addr=NFT_ADDR,
            sender_wallet=test_wallets[i])


if __name__ == "__main__":
    c = CardanoComms(TESTNET)
    master_wallet = Wallet("test_master")

    test_wallets = []
    for i in range(NFT_LEN):
        name = "test_" + str(i).zfill(2)
        test_wallets.append(Wallet(name))

        master_wallet.update_utxos()


        funds_required = MULTIMINT_FUNDS * NFT_LEN
        while master_wallet.lace < ada_to_lace(funds_required):
            master_wallet.update_utxos()
            logging.info("Send \'" + str(funds_required) + "\' ada to \'" + master_wallet.addr + "\'")
            time.sleep(20)

        logging.info("Funding test wallets")
        for i in range(NFT_LEN):
            test_wallets[i].update_utxos()
            if test_wallets[i].lace < ada_to_lace(PRICE + 2):
                sent = False
                while not sent:
                    logging.debug(str(i))
                    logging.debug("sending funds to test wallet " + str(i))
                    sent = c.simple_tx(ada_to_lace(MULTIMINT_FUNDS), test_wallets[i].addr, master_wallet)
                    time.sleep(5)
    else:
        # TODO all wallets send 1 tx to mint addr
        logging.debug("SEND MODE")
        time.sleep(3)
        for i in range(NFT_LEN):
            p = Process(target=sub_wallet_buy, args=(i,))
            p.start()
            time.sleep(0.2)
            logging.info("Buy thread for wallet " + str(i) + " started")
