import sys
sys.path.append('../src')
from CardanoComms import *
import time
from multiprocessing import Process

PRICE = 5
NFT_LEN = 60


def sub_wallet_buy(i):
    sent = False
    while not sent:
        log_debug("test wallet " + str(i) + " attempting buy")
        sent = c.simple_tx(lace=ada_to_lace(PRICE), 
            recv_addr="addr_test1qz9t6ykv3sl2dgulxv4efer4kue4k7jx8w2qrnldd694fzvjcfp434vp7hl82exe6nul2vf5d342wldhss4svegh03qs6eursz",
            sender_wallet=test_wallets[i])


if __name__ == "__main__":
    c = CardanoComms(TESTNET)
    master_wallet = Wallet("test_master")

    test_wallets = []
    for i in range(NFT_LEN):
        name = "test_" + str(i).zfill(2)
        test_wallets.append(Wallet(name))

    master_wallet.update_utxos()

    funds_required = PRICE * NFT_LEN + 2
    while master_wallet.lace < ada_to_lace(funds_required):
        master_wallet.update_utxos()
        log_info("Send \'" + str(funds_required) + "\' ada to \'" + master_wallet.addr + "\'")
        time.sleep(20)

    log_info("Funding test wallets")
    for i in range(NFT_LEN):
        test_wallets[i].update_utxos()
        if test_wallets[i].lace < ada_to_lace(PRICE + 2):
            sent = False
            while not sent:
                log_debug(str(i))
                log_debug("sending funds to test wallet " + str(i))
                sent = c.simple_tx(ada_to_lace(PRICE + 2), test_wallets[i].addr, master_wallet)
                time.sleep(5)

    # TODO all wallets send 1 tx to mint addr
    log_info("Buying nft")
    for i in range(NFT_LEN):
        p = Process(target=sub_wallet_buy, args=(i,))
        p.start()
        time.sleep(0.2)
        log_info("Buy thread for wallet " + str(i) + " started")
