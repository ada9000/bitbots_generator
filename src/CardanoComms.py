from distutils.log import debug
import os
from re import M
import sys
import json
from subprocess import Popen, PIPE, STDOUT
import subprocess
import time


from Bitbots import *

#-----------------------------------------------------------------------------
MAINNET = "--mainnet"
TESTNET = "--testnet-magic 1097911063"
NETWORKS = [MAINNET, TESTNET]
EMPTY_BYTE_STRING = "b\'\'"

FILES_DIR = "../files/"
POLICY_DIR = FILES_DIR + "policy/"
WALLET_DIR = FILES_DIR + "wallet/"

CARDANO_CLI_PATH = "cardano-cli"

# functions ------------------------------------------------------------------
def cmd_out(cmd):
    """ get the result of a shell command """
    p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True)
    res =  p.stdout.read()
    # if error raise exception
    error_str = "Error"
    if error_str in str(res):
        raise Exception("Error", str(res))
    return res

def replace_b_str(msg):
    """ remove 'b' token and single quote from a str """
    msg = str(msg)
    msg = msg.replace('b\'','')
    msg = msg.replace('\'','')
    msg = msg.replace('[','')
    msg = msg.replace(']','')
    return msg

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
            # get utxo from utxos
            utxo = utxos[tx_idx].split()
            # remove unwanted characters, cardano-cli is strict on whitespace
            utxo = replace_b_str(utxo)
            utxo = utxo.replace(' ','')
            # convert back into an array
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
            # calc total lace by adding lace attached to each uxto
            lace_total += int(utxo[2])
            # append all transactions with a boolean to announce nft present
            txs.append( (utxo[0], utxo[1], utxo_has_nft) )
        # log and assign
        log_debug("addr  : " + self.addr)
        log_debug("lace  : " + str(lace_available))
        log_debug("total : " + str(lace_total))
        self.lace   = lace_available
        self.txs    = txs
        # return type is [(tx_hash:str, tx_id:str, contains_nft:bool),...]
        return self.txs


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
        cmd = "cardano-cli address key-gen --verification-key-file " + self.policy_vkey + " --signing-key-file " + self.policy_skey
        res = cmd_out(cmd)
        if str(res) != EMPTY_BYTE_STRING:
            raise Exception("Policy Key creation error", res)
        # get protocol json, check for err
        log_debug("fetching procol json")
        cmd ="cardano-cli query protocol-parameters " + self.network + " --out-file " + self.protocol_path 
        res = cmd_out(cmd)
        if str(res) != EMPTY_BYTE_STRING:
            raise Exception("Protocol json creation error", res)
        # generate key hash, check for errors
        log_debug("generating key hash")
        cmd = "cardano-cli address key-hash --payment-verification-key-file " + self.policy_vkey
        res = cmd_out(cmd)
        # stip unwanted chars from key_hash   
        self.key_hash = str(res).replace('b\'','').replace('\\n\'','')
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
        log_debug("slot: current=" + str(current_slot) + " target=" + str(self.target_slot) + " diff="+str((self.target_slot - current_slot)))
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
        cmd = "cardano-cli transaction policyid --script-file " + self.policy_script
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

    def mint(self, metadata_path:str, recv_addr:str, mint_wallet:Wallet):
        # read meta and 'fix' (insert policy id into it)
        metadata = read_file_return_data(metadata_path)
        nft_id, metadata = self.add_policy_id_to_meta(metadata)
        # set min mint costs and arbitrary change value
        log_debug("nft-id: " + nft_id)
        change = 0 # 1.5 ada
        min_mint_cost = 1500000
        # template build
        self.build_tx(fee="0", change=change, recv_addr=recv_addr, mint_wallet=mint_wallet, nft_id=nft_id, min_mint_cost=min_mint_cost, metadata_path=metadata_path)
        witness = "1"
        cmd = "cardano-cli transaction calculate-min-fee --tx-body-file matx.raw --tx-in-count 1 --tx-out-count 1 --witness-count " + witness + " " + self.network + " --protocol-params-file " + self.protocol_path + " | cut -d \" \" -f1"
        fee = cmd_out(cmd)
        fee = str(fee).replace('b\'','').replace('\\n\'','')
        # get funds
        mint_wallet.update_utxos() # TODO what happens if it keeps updating due to incomiing payments
        funds = mint_wallet.lace
        # calculate change
        change = int(funds) - int(fee) - int(min_mint_cost)
        log_debug("fee="+str(funds))
        log_debug("funds="+str(funds))
        log_debug("min-mint-cost=" + str(min_mint_cost))
        log_debug("funds  ="+str(funds))
        log_debug("change =" + str(change))
        #build
        self.build_tx(fee=fee, change=change, recv_addr=recv_addr, mint_wallet=mint_wallet, nft_id=nft_id, min_mint_cost=min_mint_cost, metadata_path=metadata_path)
        #sign
        self.sign_tx(mint_wallet=mint_wallet)
        # send
        self.submit_tx(recv_addr)


    def build_tx(self, fee, change, recv_addr, mint_wallet, nft_id, min_mint_cost, metadata_path):
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
        for tx_id, tx_hash, contains_nft in mint_wallet.txs:
            if contains_nft == False:
                # replace any 
                #tx_id = tx_id.replace(' ','')
                #tx_hash = tx_hash.replace(' ','')
                tx_in += " --tx-in " + tx_id + "#" + tx_hash
        # set the mint wallet as our change address
        tx_out = " --tx-out " + mint_wallet.addr + "+" + change
        # template transaction for cmd string
        build_raw = "cardano-cli transaction build-raw " +\
        " --fee "+ fee +\
        " --tx-out " + recv_addr + "+" + min_mint_cost + "+" + nft_mint_str +\
        tx_out +\
        tx_in + \
        " --mint=" + nft_mint_str +\
        " --minting-script-file " + self.policy_script +\
        " --metadata-json-file " + metadata_path +\
        " --invalid-hereafter " + str(self.target_slot) +\
        " --out-file matx.raw"
        # remove any double whitespace
        build_raw = build_raw.replace("  "," ")
        # run build tx cmd
        res = cmd_out(build_raw)
        if str(res) == EMPTY_BYTE_STRING:
            log_info("build tx success")
        return


    def sign_tx(self, mint_wallet:Wallet):
        sign_tx = "cardano-cli transaction sign" + \
        " --signing-key-file " + mint_wallet.skey + \
        " --signing-key-file " + self.policy_skey +\
        " "+ self.network +\
        " --tx-body-file matx.raw"+\
        " --out-file matx.signed"
        # 
        res = cmd_out(sign_tx)
        if str(res) != EMPTY_BYTE_STRING:
            log_debug("signing failed! " + str(res))
            return
        log_info("signing success")
        return


    def submit_tx(self, recv_addr):
        cmd = "cardano-cli transaction submit --tx-file matx.signed " + self.network
        res = cmd_out(cmd)
        res = replace_b_str(res)
        res.replace('\n','')
        log_info(res)
        transaction_sent = False
        idx = 0
        while not transaction_sent:
            cmd = "cardano-cli query utxo --address "+ recv_addr + " " + self.network
            #print(cmd)
            res = cmd_out(cmd)
            if str(self.policy_id) in str(res):
                transaction_sent = True
                log_info("found tx, mint success \'" + self.policy_id + "\'") #TODO do I need to check for policyid.nftnumber
            else:
                log_debug("tx not found waiting waiting..." + str(idx))
                time.sleep(5)
                idx += 1
        return


if __name__ == "__main__":
    print("Running tests")

    cmd = "cat ../files/wallet/base.addr" 
    addr = replace_b_str(cmd_out(cmd))
    print(addr)

    wallet = Wallet()
    wallet.update_utxos()
    cc = CardanoComms(TESTNET, False)
    cc.mint(metadata_path="../output/0009.json", recv_addr=wallet.addr, mint_wallet=wallet)
