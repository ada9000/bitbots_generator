from DbComms import STATUS_IN_PROGRESS, STATUS_AWAITING_MINT, STATUS_AIRDROP, STATUS_SOLD, STATUS_ISSUE
from Utility import *
from Wallet import *
from CardanoComms import *
from BlockFrostTools import *
from Bitbots import *
from threading import Thread, Lock

class MintManager:
    # TODO pass in reference to object of tx_ids
    # with mutex when a process is processing a tx it adds it to list
    def __init__(self, network:str=TESTNET, mint_wallet:Wallet=None, nft_price_ada:int=100, project:str=None, max_mint:int=8192, new_policy:bool=False):
        if mint_wallet == None:
            raise Exception('Wallet not valid')
            #wallet = Wallet(name='', network=network)
        
        # CardanoComms will generate the project directory
        self.cc = CardanoComms(network=network, new_policy=new_policy, project=project,)
        # set project dir 
        self.project = project
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
        self.lace_mint_price  = ada_to_lace(nft_price_ada)
        self.search_mutex = Lock()
        self.mint_mutex = Lock()

        # TODO note we might want to check bb first???
        if self.cc.policy_id == None:
            raise Exception("Policy issue")# TODO maybe add policy to db?
        self.bb = Bitbots(max_mint=max_mint, project=project, adaPrice=nft_price_ada, policy=self.cc.policy_id)

        self.bb.generate() # TODO protect this to avoid overrighting
        # queue TODO
        self.db = DbComms(dbName=project, maxMint=max_mint, adaPrice=nft_price_ada)


    def run(self):
        # handle airdrops
        self.airdrops()

        # check for issues
        if self.db.issueFound():
            raise Exception(f"Issue found please resolve in DB for '{self.project}'")

        # handle minting
        customer_job_t = Thread(target=self.customer_job, args=())
        mint_job_t = Thread(target=self.mint_job, args=())
        log_info("Starting customer job thread")
        customer_job_t.start()
        log_info("Starting mint job thread")
        mint_job_t.start()


    def airdrops(self):
        # first complete airdrops
        airdropList = self.db.getAllWithStatus(STATUS_AIRDROP)
        if airdropList:
            log_debug("In airdrop list!")

            airdropCount = len(airdropList)

            # send simple tx of 2?
            airdropAda = ada_to_lace(5)

            addresses = []
            for i in range(len(airdropList)):
                addresses.append(self.wallet.addr)

            log_debug("Airdrop simple tx")
            success = self.cc.simple_tx(airdropAda, addresses, self.wallet)
            if not success:
                success = self.cc.simple_tx(airdropAda, addresses, self.wallet)
                log_debug("airdrop simple tx failed, waiting...")
                time.sleep(20)

            # get all those tx's
            txHashIdList = self.wallet.find_txs_containing_lace_amount(lace=airdropAda)
            while len(txHashIdList) < 1:
                txHashIdList = self.wallet.find_txs_containing_lace_amount(lace=airdropAda)
                log_debug("airdrop waiting on txs...")
                time.sleep(20)



            # mint all airdrops and set to sold
            index = 0
            for hexId, _, nftName, _, _, metaDataPath in airdropList:
                outputTx = False
                
                txHash, txId = txHashIdList[index]
                print(f"{txHash} #{txId} hit" )
                customerAddr = self.wallet.addr
                try:
                    while not outputTx:
                        log_info(f"Starting '{nftName}' mint for tx '{txHash}'")
                        outputTx = self.cc.mint_nft_using_txhash(
                            metadata_path=metaDataPath, 
                            recv_addr=customerAddr, 
                            mint_wallet=self.wallet,
                            nft_name=nftName,
                            tx_hash=txHash, 
                            tx_id=txId, 
                            price=airdropAda
                        )
                        if not outputTx:
                            log_error(f"Mint job waiting 25 seconds due to minting error. OutputTx={str(outputTx)}")
                            time.sleep(25)
                    # update status to sold
                    self.db.setStatus(hexId, STATUS_SOLD)
                    self.db.setOutputTx(hexId, outputTx)
                except Exception as e:
                    self.db.setStatus(hexId, STATUS_ISSUE)
                    log_error(f"Exception hit '{nftName}' with tx '{txHash}'...")
                    log_error(f"'{nftName}' Error '{e}'")
                    self.db.setOutputTx(hexId, outputTx)

                index += 1
                log_debug("Minted NFT with id \'"+ hexId +"\' to address \'" + customerAddr + "\'")

        log_info("Airdrop minting complete")






    def customer_job(self):
        """ 
        while not sold out, 
            keep checking tx hashes for the correct price, 
            and if txhash found with the correct price
            get the customer address and add it to the db with the awaiting mint status
            (the mint job thread will then look for the awaiting mint status and attempt to mint).
        """
        # while not all sold
        sold_out = self.db.sold_out()
        while not sold_out:
            log_debug("Customer job looping start")
            log_debug("Curstomer job waiting for \'" + str(lace_to_ada(self.lace_mint_price)) + "\' ada in \'" + self.wallet.addr + "\'")
            txHashIdList = self.wallet.find_txs_containing_lace_amount(lace=self.lace_mint_price)
            while not txHashIdList:
                log_debug("Checking for customer...")
                time.sleep(20)
                txHashIdList = self.wallet.find_txs_containing_lace_amount(lace=self.lace_mint_price)

            # subtract txs that are already in use (conncurrent)
            txsToIgnore = self.db.txHashesToIgnore()

            for txHash, txId in txHashIdList:
                # ignore any txs that do not have the available status
                if txsToIgnore:
                    if txHash in txsToIgnore:
                        break
                # get customer address using BLOCK FROST
                customer_addr = self.bf_api.find_sender(
                    txhash=txHash, 
                    recv_addr=self.wallet.addr, 
                    lace=self.lace_mint_price)
                    # wait and retry
                if customer_addr is None:
                    log_error("Issue finding customer with txHash \'" + txHash + "\' in customer_job()")
                else:
                    # update customers in database to include new customer, set status to awaiting mint
                    self.db.add_customer(address=customer_addr, txId=txId, txHash=txHash)
                    log_info("Customer added with address \'" + customer_addr + "\'")
            sold_out = self.db.sold_out()
        
        log_info(f"Customer job finished for project '{self.project}'")


    # TODO
    def mint_job(self):
        """
        While not sold out,
            get the nfts with the awaiting mint status
            for each nft awaiting mint
                set status to 'minting' (in case a failure / conccurent / force quit) TODO is this right?
                mint nft
                set status to sold
        """
        log_info("Mint Job")
        sold_out = self.db.sold_out()
        while not sold_out:
            log_debug("Mint job looping start")
            time.sleep(20) # add a timeout
            mintList = self.db.getAllWithStatus(STATUS_AWAITING_MINT)
            if mintList:
                for hexId, customerAddr, nftName, txHash, txId, metaDataPath in mintList:
                    # set status to in progress and keep attempting mint
                    #self.db.setStatus(hexId, STATUS_IN_PROGRESS)
                    outputTx = False
                    log_info(f"Starting '{nftName}' mint for tx '{txHash}'")
                    try:
                        while not outputTx:
                            log_debug(f"mint loop for '{nftName}' with tx '{txHash}'")
                            outputTx = self.cc.mint_nft_using_txhash(
                                metadata_path=metaDataPath, 
                                recv_addr=customerAddr, 
                                mint_wallet=self.wallet,
                                nft_name=nftName,
                                tx_hash=txHash, 
                                tx_id=txId, 
                                price=self.lace_mint_price
                            )
                            if not outputTx:
                                log_error(f"Mint job waiting 25 seconds due to minting error. OutputTx={str(outputTx)}")
                                time.sleep(25)
                        # update status to sold
                        self.db.setOutputTx(hexId, outputTx)
                        self.db.setStatus(hexId, STATUS_SOLD)
                    except Exception as e:
                        self.db.setStatus(hexId, STATUS_ISSUE)
                        log_error(f"Exception hit '{nftName}' with tx '{txHash}'...")
                        log_error(f"'{nftName}' Error '{e}'")
                        self.db.setOutputTx(hexId, outputTx)


                    log_info("Minted NFT with id \'"+ hexId +"\' to address \'" + customerAddr + "\'")
            # break loop if sold out
            sold_out = self.db.sold_out()

        log_info(f"Mint job finished for project '{self.project}'")

    # TODO
    def refund_job(self):
        # TODO must ensure we don't drain fees by loop refunding the 
        # mint wallet!!!!!!!!!!

        # send all confirmed ada to self

        # whitelist the tx for future ignoring to avoid drain via fee's?

        # return all other ada

        pass

    # API --------------------------------------------------------------------
    
    # TODO
    def check_purchase_status(self, user):
        # get user or something to id customer
        # keep checking db for status, wait js-react side will await a change and show loading or something
        return None

    # TODO
    def request_buy(self, user):
        # get user or something to id customer
        # check if that user has a active buy request if so return that

        # else 
            # look for available
            # generate a new and unique price
            # set to reserved

            # return buy addr and the price  
        return None

    # in use
    def nftPagination(self, index):
        return self.db.getNftPagination(index=index)

    def getNft(self, nft_id):
        return self.db.getNft(nft_id)

    def get_names(self):
        return self.bb.get_all_names()

    def get_nft_svg(self, nft_id):
        return self.db.getSvg(nft_id)

    def get_nft_meta(self, nft_id):
        return self.db.getMeta(nft_id)
    
    def get_all_meta(self):
        return self.db.getAllMeta()

    def get_all_svg(self):
        return self.db.getAllSvg()

    def getNftStatus(self):
        return self.db.getNftStatus()

    def get_policy(self):
        return self.cc.policy_id

    def get_payment_addr(self):
        return self.wallet.addr

    def get_nft_price(self):
        return lace_to_ada(self.lace_mint_price)

    def meets_addr_rules(self, addr):
        return True