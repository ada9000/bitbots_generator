from Utility import *
import time
import os
from datetime import datetime

class Wallet:
    def __init__(self, name:str='', network:str=TESTNET):
        self.network    = network
        self.name       = name
        # add
        self.sub_dir = '' 
        if name != '':
            self.sub_dir = name + '/'
            if not os.path.isdir(WALLET_DIR + self.sub_dir):
                os.mkdir(WALLET_DIR + self.sub_dir)

        self.addr = None
        self.addr_path  = WALLET_DIR + self.sub_dir + 'base.addr'
        self.skey       = WALLET_DIR + self.sub_dir + 'payment.skey'
        self.vkey       = WALLET_DIR + self.sub_dir + 'payment.vkey'
        # tx files are stored in a wallet
        self.tx_dir     = WALLET_DIR + self.sub_dir + "transactions/"

        if not os.path.isdir(self.tx_dir):
            os.mkdir(self.tx_dir)
        self.tx_raw     = WALLET_DIR + self.sub_dir + "tx.raw"
        self.tx_signed  = WALLET_DIR + self.sub_dir + "tx.signed"
        # check all required files exist
        self.create_wallet()
                #raise Exception("Missing " + f)
        # set addr
        if self.addr is None:
            cmd = "cat " + self.addr_path
            self.addr = replace_b_str(cmd_out(cmd))
        # lace, nfts and transactions
        self.lace = 0
        self.nfts = []
        self.txs  = []
        log_debug("Wallet: " + self.name + " has addr " + self.addr)

    def gen_new_tx_raw(self, tx_hash:str=''):
        if tx_hash == '':
            now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            self.tx_raw = WALLET_DIR + self.sub_dir + now + "_tx.raw"
        else:
            self.tx_raw = WALLET_DIR + self.sub_dir + tx_hash + "_tx.raw"

        self.tx_raw = str(self.tx_raw)
        return self.tx_raw
    
    def gen_new_tx_signed(self, tx_hash:str=''):
        if tx_hash == '':
            now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            self.tx_signed = WALLET_DIR + self.sub_dir + now + "_tx.signed"
        else:
            self.tx_raw = WALLET_DIR + self.sub_dir + tx_hash + "_tx.raw"
        self.tx_signed = str(self.tx_signed)
        return self.tx_signed

    def create_wallet(self):
        # check for wallet 
        wallet_dir = WALLET_DIR + self.name + "/"
        if not os.path.isdir(WALLET_DIR):
            os.mkdir(WALLET_DIR)
        # create wallet dir 
        if not os.path.isdir(wallet_dir):
            os.mkdir(wallet_dir)
        # return if ANY files are found
        files = [self.addr_path, self.skey, self.vkey]
        for f in files:
            if os.path.isfile(f):
                return
        # create wallet keys
        payment_keys = "cardano-cli address key-gen"+\
            " --verification-key-file "+ self.vkey +\
            " --signing-key-file " + self.skey
        build_base = "cardano-cli address build"+\
            " --payment-verification-key-file " + self.vkey +\
            " --out-file " + self.addr_path + " " + self.network
        res = cmd_out(payment_keys)
        res = cmd_out(build_base)
        log_debug("created new wallet \'" + self.name + "\'")
        return


    def update_utxos(self, msg:str=''):
        # query utxo
        cmd = "cardano-cli query utxo --address " + self.addr + " " + self.network
        res = cmd_out(cmd)

        if "Network.Socket.connect" in str(res):
            log_error(f"Network socket lost waiting a minute... {msg}")
            time.sleep(60)
            return self.update_utxos(msg)
        # remove header from utxo cmd output, convert to array of lines
        utxos = res.strip().splitlines()
        utxos = utxos[2:]
        # init vars
        lace_available = 0
        lace_total = 0
        nfts = []
        txs = []
        # get transaction index
        for tx_idx in range(len(utxos)):
            # tx lace tracks lace in current tx
            tx_lace = 0
            # get utxo from utxos
            utxo = utxos[tx_idx].split()
            # remove unwanted characters, cardano-cli is strict on whitespace
            # convert back into an array
            utxo = str(utxo)
            utxo = replace_b_str(utxo)
            utxo = utxo.split(',')
            # check for utxos that contain nfts by looking for
            # multiple tokens past the '+' token
            # (note TxOutDatumNone is the terminating token, but is not needed)
            utxo_has_nft = False
            for i, token in enumerate(utxo):
                if '+' in token:
                    if i+2 < len(utxo):
                        utxo_has_nft = True
                        nfts.append( (utxo[i+1], utxo[i+2]) )
            # ignore transactions with nfts in available lace
            if utxo_has_nft == False:
                try:
                    lace_available += int(utxo[2])
                except ValueError:
                    log_debug("ValueError likely a socket issue")
                    time.sleep(5)
                    self.update_utxos()
            tx_lace = int(utxo[2])
            # calc total lace by adding lace attached to each uxto
            lace_total += int(utxo[2])
            # append all transactions with a boolean to announce nft present
            txs.append( (utxo[0], utxo[1], tx_lace, utxo_has_nft) )
        # log and assign
        #log_debug("addr  : " + COLOR_CYAN +self.addr)
        #log_debug("lace  : " + str(lace_available))
        #log_debug("total : " + str(lace_total))
        self.lace   = lace_available
        self.txs    = txs
        # return type is [(tx_hash:str, tx_id:str, tx_lace, contains_nft:bool),...]
        return self.txs

    def get_txhashes(self):
        utxos = self.update_utxos()
        tx_hashes = []
        for utxo in utxos:
            tx_hash, _, _, _ = utxo
            tx_hashes.append(tx_hash)
        return tx_hashes


    def look_for_lace(self, lace):
        lace = int(lace)
        log_debug("Waiting for tx with \'" + str(lace_to_ada(lace)) + "\' ada in \'" + self.addr + "\'")
        while True:
            utxos = self.update_utxos()
            for utxo in utxos:
                tx_hash, tx_id, tx_lace, _ = utxo
                if tx_lace == lace:
                    # TODO this one is important \/
                    # mutex tx_hash check here to ensure we don't mint twice
                    # for a single utxo/tx_hash
                    return tx_hash, tx_id
            time.sleep(5)

    def find_txs_containing_lace_amount(self, lace):
        lace = int(lace)
        txHashIdList = []
        utxos = self.update_utxos(f"while looking for lace {lace}")
        for utxo in utxos:
            tx_hash, tx_id, tx_lace, _ = utxo
            if tx_lace == lace:
                # TODO this one is important \/
                # mutex tx_hash check here to ensure we don't mint twice
                # for a single utxo/tx_hash
                txHashIdList.append( (tx_hash, tx_id) )
        return txHashIdList

    def find_txs_ignoring_lace(self, lace):
        lace = int(lace)
        txHashIdList = []
        utxos = self.update_utxos(f"while looking for lace {lace}")
        for utxo in utxos:
            tx_hash, tx_id, tx_lace, _ = utxo
            if tx_lace != lace:
                txHashIdList.append( (tx_hash, tx_id) )
        return txHashIdList


    def socket_healthy(self):
        cmd = "cardano-cli query utxo --address " + self.addr + " " + self.network
        res = cmd_out(cmd)
        if "Network.Socket.connect" in str(res):
            return False
        return True
    
    def refund(self, txsToIgnore):
        # get all txs

        # return filteded tx#s

        pass