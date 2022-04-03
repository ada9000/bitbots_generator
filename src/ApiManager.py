from Utility import *
from Wallet import *
from CardanoComms import *
from BlockFrostTools import *
from Bitbots import *
from threading import Thread, Lock

STATUS_AVAILABLE    = "" # empty string
STATUS_IN_PROGRESS  = "in-progress"
STATUS_SOLD         = "sold"

class ApiManager:
    # TODO pass in reference to object of tx_ids
    # with mutex when a process is processing a tx it adds it to list
    def __init__(self, network:str=TESTNET, mint_wallet:Wallet=None, nft_price_ada:int=100, project:str='', max_mint:int=8192):
        if mint_wallet == None:
            raise Exception('Wallet not valid')
            #wallet = Wallet(name='', network=network)
        
        # CardanoComms will generate the project directory
        self.cc = CardanoComms(network=network, project=project)
        # set project dir 
        self.project_dir = PROJECT_DIR + project
        # set project json
        self.project_json = self.project_dir + "/project.json"
        # check for project json
        if not os.path.isfile(self.project_json):
            tmp_json = {""}
            pass

        self.network = network
        self.wallet = mint_wallet
        self.bf_api = BlockFrostTools(network)
        self.price  = ada_to_lace(nft_price_ada)
        self.search_mutex = Lock()
        self.mint_mutex = Lock()
        self.bb = Bitbots(max_mint=max_mint, project=project)

        # queue TODO

    def get_policy(self):
        return self.cc.policy_id

    def get_payment_addr(self):
        return self.wallet.addr

    def get_nft_price(self):
        return lace_to_ada(self.price)

    def meets_addr_rules(self, addr):
        return True

    def run(self):
        # first complete all pending

        txhash, tx_id = self.wallet.look_for_lace(lace=self.price)
        # if tx hash exists in meta ignore
        idx = self.bb.check_hash_exists(txhash) # TODO why is this correct behavior

        print("hash")
        log_error(txhash)
        print("id")
        log_error(tx_id)
        customer_addr = None
        while not customer_addr:
            customer_addr = self.bf_api.find_sender(
                txhash=txhash, 
                recv_addr=self.wallet.addr, 
                lace=self.price)

            if customer_addr is None:
                time.sleep(5)

        # TODO MINT MUTEX AND USE IT TO CHECK THE CURRENT TX HASH
        # BEFORE MINT LOOK AGAIN FOR TX HASH IN WALLET UTXOS

        log_debug("search mutex acquire")
        self.search_mutex.acquire()

        # check idx is none from check hash
        if idx == None:
            try:
                idx = self.bb.generate_next_nft(policy=self.get_policy(), customer_addr=customer_addr, tx_hash=txhash)
                # update status and attach customer addr
                if idx != None:
                    self.bb.set_status(idx, STATUS_IN_PROGRESS)
            finally:
                log_debug("search mutex relase")
                self.search_mutex.release()

        # TODO check for mints that failed due to restart here
        if idx == None:
            # get tx_id # TODO
            #idx, customer_addr, tx_hash = self.bb.find_status(STATUS_IN_PROGRESS)
            pass

        if idx == None:
            log_debug("All minted ensure app enters refund mode")
            # REFUND CODE HERE TODO
            return True
            #raise Exception("App must go into refund mode")

        meta_path = self.bb.get_meta_path(idx)
        # TODO 
        # meta_path = get_nft_id_db()
        log_debug("Nft \'" + str(idx) + "\' attempting mint to \'" + customer_addr + "\'")
        res = False
        # mint loop here
        while not res:
            self.mint_mutex.acquire()
            # generate new tx ids # might need to refer to these later
            #self.wallet.gen_new_tx_raw(tx_hash=txhash)
            #self.wallet.gen_new_tx_signed(tx_hash=txhash)
            log_error("attempting mint for " + customer_addr)
            res = self.cc.mint_nft_using_txhash(metadata_path=meta_path, recv_addr=customer_addr, mint_wallet=self.wallet, tx_hash=txhash, tx_id=tx_id, price=self.price)
            if not res:
                time.sleep(5)
            self.mint_mutex.release()

        tx_hashes = self.wallet.get_txhashes()
        while txhash in tx_hashes:
            log_debug("txhash still in txhashes " + str(len(tx_hashes)))
            time.sleep(5)
            tx_hashes = self.wallet.get_txhashes()

        log_error("TX success")
        if res != False:
            self.bb.set_status(idx, STATUS_SOLD)
            log_debug("Nft \'" + str(idx) + "\' status set to sold")
        
        return False

    def fake_mint(self):
        idx = ""
        while idx != None:
            log_error("idx " + idx)
            idx = self.bb.generate_next_nft(policy=self.get_policy(), customer_addr="false_addr", tx_hash="false_hash")

    def get_minted_nfts(self):
        pass

    def get_nft_svg(self, nft_id):
        return self.bb.get_svg(idx=nft_id)

    def get_nft_meta(self, nft_id):
        return self.bb.get_meta(idx=nft_id)