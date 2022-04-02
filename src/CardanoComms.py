from cmath import log
from distutils.file_util import write_file
from distutils.log import debug
from mimetypes import init
import os
from re import M
import time
from Bitbots import *
from threading import Thread, Lock
import time
import base64
from Wallet import *
from datetime import datetime
#-----------------------------------------------------------------------------
# TODO make concurrent
# [ ] ensure matx.raw and matx.signed are made conccurent i.e not read at the same time by diff processes
# [ ] ensure mutex is placed over each nft



# ----------------------------------------------------------------------------
class CardanoComms:
    def __init__(self, network:str=TESTNET, new_policy:bool=False, project:str=''):
        
        # if the project is not-defined set it to the current date
        if project == '':
            new_policy = True
            project = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        # define policy directory       
        self.project_dir = PROJECT_DIR + project

        # create project dir if missing
        if not os.path.isdir(PROJECT_DIR):
            os.mkdir(PROJECT_DIR)
        # check for the project, if it doesn't exists create a new policy for it
        if not os.path.isdir(self.project_dir):
            os.mkdir(self.project_dir)
            new_policy = True

        # check for valid network
        if network not in NETWORKS:
            raise Exception("Invalid network please use one of the following \'" + str(NETWORKS) + "\'")
        
        # required file defintions
        self.network = network
        self.project_json   = self.project_dir + "/project.json" # TODO sort out multiple json files
        self.policy_script  = self.project_dir + "/policy.script"
        self.policy_vkey    = self.project_dir + "/policy.vkey"
        self.policy_skey    = self.project_dir + "/policy.skey"
        self.slot_path      = self.project_dir + "/slot.json"
        self.policy_id_path = self.project_dir + "/policy_id.json"
        self.protocol_path  = self.project_dir + "/protocol.json"
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
            raise Exception("No policy-id json at " + str(self.policy_id_path))
        self.policy_id = read_file_return_data(self.policy_id_path)["id"]
        self.target_slot = read_file_return_data(self.slot_path)["slot"] 

    def gen_policy(self): # TODO 
        log_info("generating policy files...")
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
        self.key_hash = self.key_hash.replace('\\n','')
        # check key hash is correct
        if len(self.key_hash) != 56:
            raise Exception("Generate Key Hash Error", self.keyhash)
        # get current slot
        log_debug("querying tip")
        cmd = "cardano-cli query tip " + self.network + " | jq .slot?"
        current_slot = int(cmd_out(cmd))
        # multiple expire time by 3600 seconds and add to amend inputted hours to the target slot
        self.target_slot = current_slot + 8760 * 3600 # TODO allow user to pass this in
        write_json(self.slot_path, {"slot":self.target_slot})
        log_debug("slot current : " + str(current_slot))
        log_debug("slot target  : " + str(self.target_slot))
        log_debug("slot diff    : " + str((self.target_slot - current_slot)))
        # populate the policy script template and write as json
        policy_script = {
            "type": "all",
            "scripts": [
                {
                    "type": "before",
                    "slot": self.target_slot
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
        # for 721 and new CIP aka for cip iteration
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
    
    
    # simple tx --------------------------------------------------------------
    def simple_tx(self, lace, recv_addr:str, sender_wallet:Wallet):
        sender_wallet.update_utxos()
        fee = "0"
        change = "0"
        lace = str(lace)
        # build 1 
        self.build_tx(fee=fee, change=change,
            lace=lace,
            recv_addr=recv_addr,
            mint_wallet=sender_wallet,)
        # calc fee
        witness = "1"
        cmd = "cardano-cli transaction calculate-min-fee"+\
            " --tx-body-file " + sender_wallet.tx_raw+\
            " --tx-in-count 1 --tx-out-count 1"+\
            " --witness-count " + witness +\
            " " + self.network +\
            " --protocol-params-file " + self.protocol_path+\
            " | cut -d \" \" -f1"
        fee = cmd_out(cmd)
        fee = str(fee).replace('b\'','').replace('\\n\'','')
        # get funds
        sender_wallet.update_utxos() # TODO what happens if it keeps updating due to incoming payments
        funds = sender_wallet.lace
        # calculate change


        change = int(funds) - int(fee) - int(lace)
        log_error("funds = " + str(funds))
        log_error("fee = " + str(fee))
        log_error("lace = " + str(lace))
        log_error("change = " + str(change))

        
        # build 2
        self.build_tx(fee=fee, change=change,
            lace=lace,
            recv_addr=recv_addr,
            mint_wallet=sender_wallet,)

        # sign
        sign_tx = "cardano-cli transaction sign" + \
            " --signing-key-file " + sender_wallet.skey + \
            " "+ self.network +\
            " --tx-body-file " + sender_wallet.tx_raw+\
            " --out-file " + sender_wallet.tx_signed
        
        res = cmd_out(sign_tx)
        if str(res) != EMPTY_BYTE_STRING:
            log_error("signing failed! " + str(res))
            return False
        log_info("signing success")

        cmd = "cardano-cli transaction submit"+\
            " --tx-file " + sender_wallet.tx_signed + " " + self.network
        res = cmd_out(cmd)
        res = replace_b_str(res)
        res = res.replace('\n','')
        log_info(res)
        if 'BadImputsUTxO' in res:
            log_error("BadImputsUTxO")
            return False
        if 'ValueNotConservedUTxO' in res:
            log_error("ValueNotConservedUTxO")
            log_error("Maybe try funding " + sender_wallet.addr + " it contains " + str(lace_to_ada(sender_wallet.lace)))
            return False
        if 'Error' in res:
            log_error("Error" + res)
            return False


        # TODO check if payment was sent?
        return True

        
    def build_tx(self, fee, lace, change, recv_addr:str, mint_wallet:Wallet):
        # get usable transactions
        tx_in = ""
        for tx_id, tx_hash, _, contains_nft in mint_wallet.txs:
            if contains_nft == False:
                tx_in += " --tx-in " + tx_id + "#" + tx_hash
        # set the mint wallet as our change address
        tx_out = " --tx-out " + mint_wallet.addr + "+" + str(change)
        # template transaction for cmd string # TODO self target slot in build_raw should be altered
        build_raw = "cardano-cli transaction build-raw "+\
            " --fee "+ fee +\
            " --tx-out " + recv_addr + "+" + lace+\
            tx_out +\
            tx_in +\
            " --invalid-hereafter " + str(self.target_slot)+\
            " --out-file " + mint_wallet.tx_raw
        # remove any double whitespace
        build_raw = build_raw.replace("  "," ")
        #log_debug(build_raw)
        # run build tx cmd
        res = cmd_out(build_raw)
        if str(res) == EMPTY_BYTE_STRING:
            log_info("build tx success")
        else:
            res = replace_b_str(res)
            log_error(str(res))
        return


    def mint_nft_using_txhash(self, metadata_path:str, recv_addr:str, mint_wallet:Wallet, tx_hash, tx_id, price):
        # read meta and 'fix' (insert policy id into it)
        metadata = read_file_return_data(metadata_path)
        nft_id, metadata = self.add_policy_id_to_meta(metadata)
        # set min mint costs and arbitrary change value
        #log_debug("nft-id: " + nft_id)
        change = 0 # 1.5 ada
        min_mint_cost = 1500000
        # template build TODO note this doesn't return anything as it saves it in
        #                TODO   tx raw which is not so good as needs a mutex at the least and a diff name or unique name for tx
        self.build_mint_tx(fee="0", change=change,
            recv_addr=recv_addr,
            mint_wallet=mint_wallet,
            nft_id=nft_id,
            min_mint_cost=min_mint_cost,
            metadata_path=metadata_path,
            txhash=tx_hash,
            txid=tx_id)
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
        #funds = mint_wallet.lace
        funds = price # TODO funds are the price of tx
        # calculate change
        change = int(funds) - int(fee) - int(min_mint_cost)
        if change < 1:
            log_error("Invalid change \'" + str(lace_to_ada(change)) + "\' ada")
        #log_debug("fee      : " +str(fee))
        #log_debug("min-mint : " + str(min_mint_cost))
        #log_debug("funds    : " +str(funds))
        #log_debug("change   : " + str(change))
        #log_debug("diff lace: " + str(int(funds) - int(change)))
        #log_debug("diff ada : " + str(lace_to_ada((int(funds) - int(change)))))
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
            metadata_path=metadata_path,
            txhash=tx_hash,
            txid=tx_id)
        #sign
        if self.sign_mint_tx(wallet=mint_wallet) is False:
            return False
        # send
        return self.submit_mint_tx(recv_addr=recv_addr, wallet=mint_wallet, nft_id=nft_id)


    # TODO DEPRECATE OR IGNORE
    # nft mint ---------------------------------------------------------------
    def mint_nft(self, metadata_path:str, recv_addr:str, mint_wallet:Wallet):
        # read meta and 'fix' (insert policy id into it)
        metadata = read_file_return_data(metadata_path)
        nft_id, metadata = self.add_policy_id_to_meta(metadata)
        # set min mint costs and arbitrary change value
        #log_debug("nft-id: " + nft_id)
        change = 0 # 1.5 ada
        min_mint_cost = 1500000
        # template build TODO note this doesn't return anything as it saves it in
        #                TODO   tx raw which is not so good as needs a mutex at the least and a diff name or unique name for tx
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
        #log_debug("fee      : " +str(fee))
        #log_debug("min-mint : " + str(min_mint_cost))
        #log_debug("funds    : " +str(funds))
        #log_debug("change   : " + str(change))
        #log_debug("diff lace: " + str(int(funds) - int(change)))
        #log_debug("diff ada : " + str(lace_to_ada((int(funds) - int(change)))))
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
        return self.submit_mint_tx(recv_addr=recv_addr, wallet=mint_wallet, nft_id=nft_id)


    def build_mint_tx(self, fee, change, recv_addr, mint_wallet, nft_id, min_mint_cost, metadata_path, txhash=None, txid=None):
        """ builds a nft transaction """
        # set 
        nft_id = nft_id.encode("utf-8")
        nft_id = base64.b16encode(nft_id)
        nft_id = replace_b_str(nft_id)

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
                # TODO DO NOT USE ALL TXS, ONLY CONSUME SENDERS TX
        if tx_hash != None:
            log_debug("spending tx from sender")
            tx_in = " --tx-in " + str(txhash) + '#' + str(txid) # TODO somewhere txid is mixed up is it in for loop above
            log_error(tx_in)

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
        #log_debug(build_raw)
        # run build tx cmd
        res = cmd_out(build_raw)
        if str(res) == EMPTY_BYTE_STRING:
            log_info("build tx success for \'" + nft_mint_str + "\'")
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


    def submit_mint_tx(self, recv_addr:str, wallet:Wallet, nft_id:str):
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
        if 'Error' in res:
            log_error("something went wrong (socket?)")
            return False

        return True
