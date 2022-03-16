from distutils.log import debug
import os
from re import M
import sys
import json
from subprocess import Popen, PIPE, STDOUT
import subprocess
import time
from Bitbots import *
import re
from dotenv import load_dotenv
from blockfrost import BlockFrostApi, ApiError, ApiUrls
from threading import Thread, Lock
import time

# consts ---------------------------------------------------------------------
MAINNET = "--mainnet"
TESTNET = "--testnet-magic 1097911063"
NETWORKS = [MAINNET, TESTNET]
FILES_DIR = "../files/"
POLICY_DIR = FILES_DIR + "policy/"
WALLET_DIR = FILES_DIR + "wallet/"
CARDANO_CLI_PATH = "cardano-cli"
EMPTY_BYTE_STRING = "b\'\'"

# global ---------------------------------------------------------------------
purchase_mutex = Lock()

# functions ------------------------------------------------------------------
def cmd_out(cmd):
    """ get the result of a shell command """
    p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True)
    res =  p.stdout.read()
    # if error raise exception
    error_str = "Error"
    if error_str in str(res):
        log_error("Error" + str(res))
    return res

def replace_b_str(msg):
    """ remove 'b' token and single quote from a str """
    msg = str(msg)
    # use regex to match all text between b'<target>'
    re_res = re.findall(r'b\'(.*?)\'', msg)
    for i, s in enumerate(re_res):
        if i == 0:
            msg = s
        else:
            msg += ','
            msg += s
    # replace any of the following symbols
    msg = msg.replace('\'','')
    msg = msg.replace('[','')
    msg = msg.replace(']','')
    return msg

def ada_to_lace(x:float):
    return x * 1000000

def lace_to_ada(x:float):
    return x / 1000000

def check_files_exist(self, files:list):
    """
    Check a list of files and return True if they all exist,
    return False if one or more don't exist
    """
    for f in files:
        if os.path.isfile(f) == False:
            return False
    return True


#-----------------------------------------------------------------------------
# TODO make concurrent
# [ ] ensure matx.raw and matx.signed are made conccurent i.e not read at the same time by diff processes
# [ ] ensure mutex is placed over each nft

#-----------------------------------------------------------------------------
class Wallet:
    def __init__(self, name:str='', network:str=TESTNET):
        self.network    = network
        self.name       = name
        # add
        sub_dir = '' 
        if name != '':
            sub_dir = name + '/'
        self.addr_path  = WALLET_DIR + sub_dir + 'base.addr'
        self.skey       = WALLET_DIR + sub_dir + 'payment.skey'
        self.vkey       = WALLET_DIR + sub_dir + 'payment.vkey'
        # tx files are stored in a wallet
        self.tx_raw     = WALLET_DIR + sub_dir + 'tx.raw'
        self.tx_signed  = WALLET_DIR + sub_dir + 'tx.signed'
        # check all required files exist
        files = [self.addr_path, self.skey, self.vkey]
        for f in files:
            if not os.path.isfile(f):
                raise Exception("Missing " + f)
        # set addr
        cmd = "cat " + self.addr_path
        self.addr = replace_b_str(cmd_out(cmd))
        # lace, nfts and transactions
        self.lace = 0
        self.nfts = []
        self.txs  = []
    
    def update_utxos(self):
        # query utxo
        cmd = "cardano-cli query utxo --address " + self.addr + " " + self.network
        res = cmd_out(cmd)
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
                lace_available += int(utxo[2])
            tx_lace = int(utxo[2])
            # calc total lace by adding lace attached to each uxto
            lace_total += int(utxo[2])
            # append all transactions with a boolean to announce nft present
            txs.append( (utxo[0], utxo[1], tx_lace, utxo_has_nft) )
        # log and assign
        log_debug("addr  : " + self.addr)
        log_debug("lace  : " + str(lace_available))
        log_debug("total : " + str(lace_total))
        self.lace   = lace_available
        self.txs    = txs
        # return type is [(tx_hash:str, tx_id:str, tx_lace, contains_nft:bool),...]
        return self.txs

    def look_for_lace(self, lace):
        while True:
            logging.info("Waiting for " + str(lace) + " lace tx in \'" + self.addr + "\'...")
            utxos = self.update_utxos()
            for utxo in utxos:
                tx_hash, _, tx_lace, _ = utxo
                if tx_lace == lace:
                    # TODO this one is important \/
                    # mutex tx_hash check here to ensure we don't mint twice
                    # for a single utxo/tx_hash
                    return tx_hash
            time.sleep(5)

class CardanoComms:
    def __init__(self, network:str, new_policy:bool=False):
        # check valid network
        if network not in NETWORKS:
            raise Exception("Invalid network please use one of the following \'" + str(NETWORKS) + "\'")
        self.network = network
        self.policy_script  = POLICY_DIR + "policy.script"
        self.policy_vkey    = POLICY_DIR + "policy.vkey"
        self.policy_skey    = POLICY_DIR + "policy.skey"
        self.policy_slot    = POLICY_DIR + "slot.json"
        self.policy_id_path = POLICY_DIR + "policy_id.json"
        self.protocol_path  = POLICY_DIR + "protocol.json"
        self.target_slot    = None
        self.key_hash       = None
        self.policy_id      = None
        # generate a new policy or use existing
        if new_policy:
            self.gen_policy()
        else:
            self.use_existing_policy()
    
    def use_existing_policy(self):
        log_info("using existing policy")
        if not os.path.isfile(self.policy_id_path):
            raise Exception("Not policy-id json at " + str(self.policy_id_path))
        self.policy_id = read_file_return_data(self.policy_id_path)["id"]
        self.target_slot = read_file_return_data(self.policy_slot)["slot"] 

    def clean(self):
        # first backup
        # then remove files
        pass

    def gen_policy(self): # TODO 
        log_info("generating policy files...")
        if not os.path.isdir(POLICY_DIR):
            os.mkdir(POLICY_DIR)
        else:
            self.clean()
        # generate policy keys, check for err
        log_debug("creating policy keys")
        cmd = "cardano-cli address key-gen"+\
            " --verification-key-file " + self.policy_vkey+\
            " --signing-key-file " + self.policy_skey
        res = cmd_out(cmd)
        if str(res) != EMPTY_BYTE_STRING:
            raise Exception("Policy Key creation error", res)
        # get protocol json, check for err
        log_debug("fetching procol json")
        cmd ="cardano-cli query protocol-parameters " + self.network +\
            " --out-file " + self.protocol_path 
        res = cmd_out(cmd)
        if str(res) != EMPTY_BYTE_STRING:
            raise Exception("Protocol json creation error", res)
        # generate key hash, check for errors
        log_debug("generating key hash")
        cmd = "cardano-cli address key-hash"+\
            " --payment-verification-key-file " + self.policy_vkey
        res = cmd_out(cmd)
        # stip unwanted chars from key_hash   
        self.key_hash = replace_b_str(res)#str(res).replace('b\'','').replace('\\n\'','')
        print(self.key_hash)
        breakpoint()
        # check key hash is correct
        if len(self.key_hash) != 56:
            raise Exception("Generate Key Hash Error", self.keyhash)
        # get current slot
        log_debug("querying tip")
        cmd = "cardano-cli query tip " + self.network + " | jq .slot?"
        current_slot = int(cmd_out(cmd))
        # multiple expire time by 3600 seconds and add to amend inputed hours to the target slot
        self.target_slot = current_slot + 8760 * 3600
        self.write_json(self.slot_path, {"slot":self.target_slot})
        log_debug("slot current : " + str(current_slot))
        log_debug("slot target  : " + str(self.target_slot))
        log_debug("slot diff    : " + str((self.target_slot - current_slot)))
        # populate the policy script template and write as json
        policy_script = {
            "type": "all",
            "scripts": [
                {
                    "type": "before",
                    "slot": self.policy_slot
                }, {
                    "type": "sig",
                    "keyHash": self.key_hash
                }
            ]
        }
        write_json(self.policy_script, policy_script)
        # gen policy id and clean result
        log_debug("generating policy id")
        cmd = "cardano-cli transaction policyid"+\
            " --script-file " + self.policy_script
        res = cmd_out(cmd)
        self.policy_id = str(res).replace('b\'','').replace('\\n\'','')
        write_json(self.policy_id_path, {"id":self.policy_id})
        log_info("policy files generated")

    def add_policy_id_to_meta(self, metadata):
        fixed_meta = {}
        # for 721 and 722 aka for cip iteration
        for cip in metadata.keys():
            inner_keys = metadata[cip].keys()
            inner_data = {}
            for i in inner_keys:
                inner_data = metadata[cip][i]
            # replace old policy-id with new
            fixed_meta[cip] = {self.policy_id:inner_data}
        
        metadata = fixed_meta
        # get nft id from keys
        k = metadata["721"][self.policy_id].keys()
        nft_id = None
        for i in k:
            nft_id = i
        # return meta
        return nft_id, metadata
    
    
    # nft mint ---------------------------------------------------------------
    def mint_nft(self, metadata_path:str, recv_addr:str, mint_wallet:Wallet):
        # read meta and 'fix' (insert policy id into it)
        metadata = read_file_return_data(metadata_path)
        nft_id, metadata = self.add_policy_id_to_meta(metadata)
        # set min mint costs and arbitrary change value
        log_debug("nft-id: " + nft_id)
        change = 0 # 1.5 ada
        min_mint_cost = 1500000
        # template build
        self.build_mint_tx(fee="0", change=change,
            recv_addr=recv_addr,
            mint_wallet=mint_wallet,
            nft_id=nft_id,
            min_mint_cost=min_mint_cost,
            metadata_path=metadata_path)
        witness = "1"
        cmd = "cardano-cli transaction calculate-min-fee"+\
            " --tx-body-file " + mint_wallet.tx_raw+\
            " --tx-in-count 1 --tx-out-count 1"+\
            " --witness-count " + witness +\
            " " + self.network +\
            " --protocol-params-file " + self.protocol_path+\
            " | cut -d \" \" -f1"
        fee = cmd_out(cmd)
        fee = str(fee).replace('b\'','').replace('\\n\'','')
        # get funds
        mint_wallet.update_utxos() # TODO what happens if it keeps updating due to incomiing payments
        funds = mint_wallet.lace
        # calculate change
        change = int(funds) - int(fee) - int(min_mint_cost)
        log_debug("fee      : " +str(fee))
        log_debug("min-mint : " + str(min_mint_cost))
        log_debug("funds    : " +str(funds))
        log_debug("change   : " + str(change))
        log_debug("diff lace: " + str(int(funds) - int(change)))
        log_debug("diff ada : " + str(lace_to_ada((int(funds) - int(change)))))
        # check if we have enough funding
        min_funds_required = int(min_mint_cost) + int(fee) + 10
        if funds < min_funds_required:
            log_error("Aborting mint."+\
                " Low funds " + str(funds)+\
                " expected " + str(min_funds_required))
            return False
        #build
        self.build_mint_tx(fee=fee,
            change=change,
            recv_addr=recv_addr,
            mint_wallet=mint_wallet,
            nft_id=nft_id,
            min_mint_cost=min_mint_cost,
            metadata_path=metadata_path)
        #sign
        if self.sign_mint_tx(wallet=mint_wallet) is False:
            return False
        # send
        return self.submit_tx(recv_addr=recv_addr, wallet=mint_wallet, nft_id=nft_id)


    def build_mint_tx(self, fee, change, recv_addr, mint_wallet, nft_id, min_mint_cost, metadata_path):
        """ builds a nft transaction """
        # build nft mint str (assume amount to be 1)
        nft_mint_str = "\""
        nft_mint_str = nft_mint_str + "1" + " " + self.policy_id + "." + nft_id
        nft_mint_str = nft_mint_str + " \""
        # convert ints to strings
        fee = str(fee)
        change = str(change)
        min_mint_cost = str(min_mint_cost)
        # get usable transactions
        tx_in = ""
        for tx_id, tx_hash, _, contains_nft in mint_wallet.txs:
            if contains_nft == False:
                # replace any 
                #tx_id = tx_id.replace(' ','')
                #tx_hash = tx_hash.replace(' ','')
                tx_in += " --tx-in " + tx_id + "#" + tx_hash
        # set the mint wallet as our change address
        tx_out = " --tx-out " + mint_wallet.addr + "+" + change
        # template transaction for cmd string
        build_raw = "cardano-cli transaction build-raw "+\
            " --fee "+ fee +\
            " --tx-out " + recv_addr + "+" + min_mint_cost + "+" + nft_mint_str+\
            tx_out +\
            tx_in +\
            " --mint=" + nft_mint_str +\
            " --minting-script-file " + self.policy_script+\
            " --metadata-json-file " + metadata_path +\
            " --invalid-hereafter " + str(self.target_slot)+\
            " --out-file " + mint_wallet.tx_raw
        # remove any double whitespace
        build_raw = build_raw.replace("  "," ")
        log_debug(build_raw)
        # run build tx cmd
        res = cmd_out(build_raw)
        if str(res) == EMPTY_BYTE_STRING:
            log_info("build tx success")
        else:
            res = replace_b_str(res)
            log_error(str(res))
        return


    def sign_mint_tx(self, wallet:Wallet):
        sign_tx = "cardano-cli transaction sign" + \
            " --signing-key-file " + wallet.skey + \
            " --signing-key-file " + self.policy_skey +\
            " "+ self.network +\
            " --tx-body-file " + wallet.tx_raw+\
            " --out-file " + wallet.tx_signed
        # 
        res = cmd_out(sign_tx)
        if str(res) != EMPTY_BYTE_STRING:
            log_error("signing failed! " + str(res))
            return False
        log_info("signing success")
        return True


    def submit_tx(self, recv_addr:str, wallet:Wallet, nft_id:str):
        cmd = "cardano-cli transaction submit"+\
            " --tx-file " + wallet.tx_signed + " " + self.network
        res = cmd_out(cmd)
        res = replace_b_str(res)
        res = res.replace('\n','')
        log_info(res)
        if 'BadImputsUTxO' in res:
            log_error("BadImputsUTxO")
            return False
        if 'ValueNotConservedUTxO' in res:
            log_error("ValueNotConservedUTxO")
            return False
        transaction_sent = False
        idx = 0
        while not transaction_sent:
            cmd = "cardano-cli query utxo --address "+ recv_addr + " " + self.network
            #print(cmd)
            res = cmd_out(cmd)
            target = self.policy_id + "." + nft_id
            target.strip() # remove any whitespace
            if target in str(res):
                transaction_sent = True
                log_info("found tx, mint success \'" + target + "\'") #TODO do I need to check for policyid.nftnumber
            else:
                log_debug("tx not found waiting waiting..." + str(idx))
                time.sleep(5)
                idx += 1
        return True

# Refund manger class
# Mint manger class
class BlockFrostTools:
    def __init__(self, network:str=TESTNET):
        # set network url
        self.b_url = ApiUrls.testnet.value
        if network == MAINNET:
            self.b_url = ApiUrls.mainnet.value
        # get api key from .env
        load_dotenv()
        self.api_key = os.getenv('BLOCK_FROST_API_KEY')
        if self.api_key is None:
            raise Exception("No blockfrost api key. Update .env")
        # init api
        self.api = BlockFrostApi(
            project_id=self.api_key,
            base_url=self.b_url
        )
        self.health = self.health_query()

    def health_query(self):
        return self.api.health()

    def find_sender(self, txhash:str, recv_addr:str, lace):
        lace = str(lace)
        res = self.api.transaction_utxos(hash=txhash)

        found_recv = False
        target_addr = False
        # TODO add check for lace?

        for x in res.inputs:
            if x.address == recv_addr:
                found_recv = True
        
        # TODO what if multiple outputs i.e more than 2?
        for x in res.outputs:
            log_debug(x.address)
            if x.address != recv_addr:
                return x.address
        time.sleep(20)
        return False

        #print("outputs")
        #print(res.inputs)


    def utxo_query(self, txhash:str):
        res = self.api.transaction_utxos(hash=txhash)
        print(res)

    def addr_query(self, addr:str):
        address = self.api.address(address=addr)
        print(address)
        print(address.type)  # prints 'shelley'


if __name__ == "__main__":
    cmd = "cat ../files/wallet/base.addr" 
    addr = replace_b_str(cmd_out(cmd))

    b = BlockFrostTools(TESTNET)
    #b.addr_query(addr)

    #tx = "95a8b663563c111c19900da01157cc893113ad6c9e6130157c8dc0043390467d"
    #tx = "cd2e514f926671d514c427bc8a0205b0e7506b443665d0121cf919b47fd1b683"

    # TODO start x listeners
    nft_purchase_costs = ada_to_lace(6.9)
    wallet = Wallet()
    txhash = wallet.look_for_lace(nft_purchase_costs)
    # TODO create a customer list and mutex, to ensure we don't send two nfts
    # in the list put consumed utxos to ensure we don't use the same one twice

    # TODO check for 300 or something loop until txhash is found
    customer_addr = False

    while not customer_addr:
        customer_addr = b.find_sender(txhash=txhash, recv_addr=wallet.addr, lace=nft_purchase_costs)

    log_debug("customer is " + customer_addr)

    # 

    """
    breakpoint()
    print("Running tests")


    wallet = Wallet()
    wallet.update_utxos()
    cc = CardanoComms(TESTNET, False)

    # check the blockchain to see if nft exists if so don't mint
    # might have to use blockfrost
    # NOT smart blockchain or query could be off resulting in duplicates, best to do that backend here

    idx = "0018"
    meta_path = "../output/"+idx+".json"
    res = cc.mint_nft(metadata_path=meta_path, recv_addr=wallet.addr, mint_wallet=wallet)
    while res == False:
        input("Bad mint try again\nPress any key...")
        res = cc.mint_nft(metadata_path=meta_path, recv_addr=wallet.addr, mint_wallet=wallet)
    """