import os
import sys
import json
from subprocess import Popen, PIPE, STDOUT
import time


from Bitbots import *

#-----------------------------------------------------------------------------
MAINNET = "--mainnet"
TESTNET = "--testnet-magic 1097911063"
NETWORKS = [MAINNET, TESTNET]
EMPTY_BYTE_STRING = "b\'\'"

FILES_DIR = "../files/"
WALLET_DIR = FILES_DIR + "wallet/"

#-----------------------------------------------------------------------------
def cmd_out(cmd):
    # return the output of a command
    p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True)
    res =  p.stdout.read()

    error_str = "Error"
    if error_str in str(res):
        raise Exception("Error", str(res))

    return res


#-----------------------------------------------------------------------------
class CardanoComms:
    def __init__(self, network:str, payment_addr:str):
        # check valid network
        if network not in NETWORKS:
            raise Exception("Invalid network please use one of the following \'" + str(NETWORKS) + "\'")
        
        # 
        self.network = network


class CardanoCliMintWrapper:
    def __init__(self):
        self.network = TESTNET
        
        self.src_address = None
        self.src_skey = None
        self.src_vkey = None
        
        self.policy_path        = FILES_DIR + "policy/"
        self.policy_script_path = FILES_DIR + "policy/policy.script"
        self.policy_vkey_path   = FILES_DIR + "policy/policy.vkey"
        self.policy_skey_path   = FILES_DIR + "policy/policy.skey"
        self.policy_id_path   = FILES_DIR + "policy/policy_id.txt"
        self.meta_data_path     = FILES_DIR + "meta_data.json"
        self.protocol_path      = FILES_DIR + "protocol.json"
        self.recv_status_path   = FILES_DIR + "recv_status.json" # check recieved if crash or stop TODO

        self.payment_addr_path  = WALLET_DIR + "payment.addr"
        self.payment_skey_path  = WALLET_DIR + "payment.skey"
        self.payment_vkey_path  = WALLET_DIR + "payment.vkey"
        
        self.recv_status = []
        
        self.payment_addr = None

        self.recv_address = None

        self.target_slot = None
        self.key_hash = None
        self.meta_data = None
        self.policy_id = None

        self.nft_ids = []

        self.payment_utxos = None
        self.first_run = True


    def setup_checks(self):
        files = [self.payment_addr_path, self.payment_skey_path, self.payment_vkey_path]

        if self.check_files_exist(files) == False:
            raise Exception("missing " + str(files))
            return False # TODO ask user to generate new wallet?

        return True

    def setup(self):
        u_input = input("First run? y/n")

        if u_input is "y":
            print("Cleaning before run...")
            self.clean()

            print("Creating policy_keys and protocol json...")
            self.create_policy_keys_and_proto()

            print("Set slot...")
            self.set_target_slot()

            print("Gen key...")
            self.generate_key_hash()
        
            print("Gen policy...")
            self.generate_policy()
    
        else:
            self.first_run = False
            print("Not first run - not cleaning up")
            self.policy_id =  read_file_return_data(self.policy_id_path)
            pass


        print("Running setup checks...")
        if self.setup_checks() == False:
            print("some payment.* files are missing! please copy them into the local dir, then try again")
            return 
        
        
        #setup payment addr
        print("Get payment addr...")
        self.payment_addr =  str(cmd_out("cat " + self.payment_addr_path)).replace('b\'','').replace('\'','')
        print(self.payment_addr)


    def set_metadata(self, meta_data_path):
        self.meta_data_path = meta_data_path
        self.meta_data = read_file_return_data(self.meta_data_path)
        print("ready to mint()")



    def clean(self):
        files = [self.policy_vkey_path, self.policy_skey_path, self.policy_script_path, self.meta_data_path, self.protocol_path, "matx.raw", "matx.signed"]
        # for all files check if it exists and remove if true
        for f in files:
            if os.path.isfile(f):
                os.remove(f)
        return

    def write_json(self, path, data):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)


    def check_files_exist(self, files):
        """
        Check a list of files and return True if they all exist,
        return False if one or more don't exist
        """
        for f in files:
            if os.path.isfile(f) == False:
                return False
        return True
    

    def create_policy_keys_and_proto(self):
        # if the policy dir does not exist create it
        if os.path.isdir(self.policy_path) != True:
            os.mkdir(self.policy_path)
        # if the policy v or s keys are not found generate them
        files = [self.policy_vkey_path, self.policy_skey_path]
        if self.check_files_exist(files) == False:
            cmd = "cardano-cli address key-gen --verification-key-file " + self.policy_vkey_path + " --signing-key-file " + self.policy_skey_path
            res = cmd_out(cmd)
            if str(res) != EMPTY_BYTE_STRING:
                raise Exception("Create Policy Key Error", res)

        proto_cmd ="cardano-cli query protocol-parameters " + self.network + " --out-file " + self.protocol_path 
        res = cmd_out(proto_cmd)
        if str(res) != EMPTY_BYTE_STRING:
            raise Exception("Create Protocol json Error", res)
        # 
        return


    def set_target_slot(self):
        # create slot expiry

        expire_time = int(input("Enter an expiry time in hours, starting from this slot:\n> "))
        
        cmd = "cardano-cli query tip " + self.network + " | jq .slot?"
        current_slot = int(cmd_out(cmd))
        
        # multiple expire time by 3600 seconds and add to amend inputed hours to the target slot
        self.target_slot = current_slot + ((expire_time) * 3600)
        print("SLOT DEBUG: Currentslot = " + str(current_slot) + " Target slot = " + str(self.target_slot) + " Diff = "+str((self.target_slot - current_slot)))

        return


    def generate_key_hash(self):
        # get key hash
        cmd = "cardano-cli address key-hash --payment-verification-key-file " + self.policy_vkey_path
        res = cmd_out(cmd)
        # stip unwanted chars from key_hash   
        self.key_hash = str(res).replace('b\'','').replace('\\n\'','')

        print("KEY HASH DEBUG: " + self.key_hash)
        
        # check key hash is correct
        if len(self.key_hash) == 56:
            return
        raise Exception("Generate Key Hash Error", self.keyhash)


    def generate_policy(self):
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
        self.write_json(self.policy_script_path, policy_script)

        # gen policy id and clean result
        cmd = "cardano-cli transaction policyid --script-file " + self.policy_script_path

        print(cmd)
        res = cmd_out(cmd)
        self.policy_id = str(res).replace('b\'','').replace('\\n\'','')
        
        text_file = open(self.policy_id_path, "w")
        n = text_file.write(self.policy_id)
        text_file.close()
        #self.write_json(self.policy_id_path, {self.policy_id})
        #TODO CHECK POLICY ID HERE

        print("POLICY DEBUG: " + str(self.policy_id))

        return


    def query_addr(self):
        # query address
        cmd = "cardano-cli query utxo --address $(cat payment.addr) " + self.network
        print(cmd)
        res = str(cmd_out(cmd))
        print(res)

        # chars to remove
        to_remove = ['b\'','-','\n','\\n','\'','Amount','TxOutDatumHashNone','TxHash','TxIx','+']
        
        for item in to_remove:
            res = res.replace(item, '')

        return res.split()
    

    def find_payment_utxos(self):
        print("UTXO HASH DEBUG:")
        utxos = self.query_addr()

        # get all tx hashes
        hashes = {}
        for i, line in enumerate(utxos):
            if len(line) == 64: #64 chars in a hash
                inner = []
                j = i + 1
                while (j < len(utxos) and len(utxos[j]) != 64):
                    inner.append(utxos[j])
                    j = j + 1
                hashes[line] = inner

        self.payment_utxos = hashes
        return

    
    def build_tx(self, fee, output, recv_addr, nft_id, ada_to_send):
        
        #print("IN BUILD TX")
        #addr = cmd_out(
        
        #print("To mint in one transaction")
        amount = 1
        nft_mint_str = "\""
        nft_mint_str = nft_mint_str + "1" + " " + self.policy_id + "." + NFT_ID
        nft_mint_str = nft_mint_str + " \""

        addr = str(self.payment_addr)
        fee = str(fee)
        output = str(output)
        
        # get tx in #TODO
        tx_in = " --tx-in "
        for i, x in enumerate(self.payment_utxos):
            if i < 1: #temp we must figure out how to add all utxo! TODO
                tx_in = tx_in + " " + x + '#' + self.payment_utxos[x][0]


        ada_to_send = str(ada_to_send)
        # where output is change TODO

        # template transaction for cmd string
        build_raw = "cardano-cli transaction build-raw " +\
        " --fee "+ fee +\
        " --tx-out " + recv_addr + "+" + ada_to_send + "+" + nft_mint_str +\
        " --tx-out " + "$(cat payment.addr)" + "+" + output +\
        tx_in + \
        " --mint=" + nft_mint_str +\
        " --minting-script-file " + self.policy_script_path +\
        " --metadata-json-file " + self.meta_data_path +\
        " --invalid-hereafter " + str(self.target_slot) +\
        " --out-file matx.raw"
    
        #" --tx-out " + recv_addresses[1] + "0" + "+" + nft_mint_str + \
        #" --tx-out " + recv_addresses[2] + "0" + "+" + nft_mint_str + \
        build_raw = build_raw.replace("  "," ")
        #print(build_raw)
        
        print("Build raw:")
        print(build_raw)
        print()

        res = cmd_out(build_raw)
        #print(res)
        if str(res) == EMPTY_BYTE_STRING:
            print("matx.raw created success!")
        
        return
    

    def get_funds(self):
        funds = 0
        for x in self.payment_utxos:
            funds = funds + int(self.payment_utxos[x][1])
        print()
        return funds


    def sign_tx(self):
        sign_tx = "cardano-cli transaction sign" + \
        " --signing-key-file " + self.payment_skey_path + \
        " --signing-key-file " + self.policy_skey_path +\
        " "+ self.network +\
        " --tx-body-file matx.raw"+\
        " --out-file matx.signed"

        res = cmd_out(sign_tx)
        if str(res) != EMPTY_BYTE_STRING:
            print("Signing failed: " + str(res))
            return
        print("Signing success")
        return

    def submit_tx(self, recv_addr):
        # sumbit
        #input("Press any key to sumbit ...")
        print("About to sumbit...")
        time.sleep(2)
    
        cmd = "cardano-cli transaction submit --tx-file matx.signed " + self.network
        print(cmd)
        res = cmd_out(cmd)
        print(res)

        
        transaction_sent = False
        kek = 0
        while not transaction_sent:
            cmd = "cardano-cli query utxo --address "+ recv_addr + " " + self.network
            #print(cmd)
            res = cmd_out(cmd)
            if str(self.policy_id) in str(res):
                transaction_sent = True
                print("found tx")
                #print(res)
                self.recv_status.append(recv_addr)
                time.sleep(1)
            else:
                #print("looking for" + str(self.policy_id) + " in " + str(res))
                print("Tx not found waiting..." + str(kek))
                time.sleep(5)
                kek = kek + 1

        return


    def mint(self, meta_data_path, recv_addr):
        self.set_metadata(meta_data_path)

        _ = input("paused press any key")       

        os.system("clear")
        #output = "16000"
        output = "1500000" # 1.5 ada
        
        i = 0
        last_funds = 0

        #self.write_json(self.meta_data_path, self.nft_meta_json[i])

        print("Minting <<<<<<<<<<<<<<<<<")
        self.find_payment_utxos()
        x_costs = (int(output)+170000) /1000000
        print("Total cost will be ~" + str(x_costs)+ "ADA")
        
        asdf = input("continue?")

        # build 1
        ada_to_send = 1500000
        self.build_tx(fee=0, output=output, recv_addr=recv_addr, nft_id=NFT_ID, ada_to_send=ada_to_send)
        witness = "1"
        cmd = "cardano-cli transaction calculate-min-fee --tx-body-file matx.raw --tx-in-count 1 --tx-out-count 1 --witness-count " + witness + " --testnet-magic 1097911063 --protocol-params-file protocol.json | cut -d \" \" -f1"
        print(cmd)
        fee = cmd_out(cmd)

        fee = str(fee).replace('b\'','').replace('\\n\'','')
        funds = self.get_funds()
        
        if i != 0:
            while last_funds == funds:
                print("fund calc error... trying again")
                self.find_payment_utxos()
                funds = self.get_funds()
                time.sleep(5)

                
        last_funds = funds

        fund_i = int(funds)
        fee_i = int(fee)
        output = int(funds) - int(fee_i) - int(ada_to_send)
        output = str(output)
        print("Funds: " + str(funds))
        print("Fee: " + fee)
        print("Output: " + output)
        print("ADA attached: " + str(ada_to_send))

        # build 2
        self.build_tx(fee=fee, output=output, recv_addr=recv_addr, nft_id=NFT_ID, ada_to_send=ada_to_send)

        #sign
        self.sign_tx()

        # send
        self.submit_tx(recv_addr)

        i = i + 1

        print()
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        print()

        print("done")


if __name__ == "__main__":
    print("Running tests")
    cli_wrap = CardanoCliMintWrapper()
    #cli_wrap.clean()
    cli_wrap.setup()