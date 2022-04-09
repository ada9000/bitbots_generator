from Utility import *
from Wallet import *
from blockfrost import BlockFrostApi, ApiError, ApiUrls
from dotenv import load_dotenv
import os

class BlockFrostTools:
    def __init__(self, network:str=TESTNET):
        # set network url
        self.b_url = ApiUrls.testnet.value
        if network == MAINNET:
            self.b_url = ApiUrls.mainnet.value
        # get api key from .env
        load_dotenv()
        self.api_key = os.getenv('BLOCK_FROST_API_KEY')
        if self.api_key == None:
            raise Exception("No blockfrost api key. Update .env")
        # init api
        self.api = BlockFrostApi(
            project_id=self.api_key,
            base_url=self.b_url
        )
        self.health = self.health_query()

        self.policy_meta = {}

    def health_query(self):
        return self.api.health()

    def find_sender(self, txhash:str, recv_addr:str, lace):
        lace = str(lace)
        res = self.api.transaction_utxos(hash=txhash)

        found_recv = False
        target_addr = False
        # TODO add check for lace?

        # TODO deprecate this logic
        for x in res.inputs:
            if x.address == recv_addr:
                found_recv = True
        #END TODO ------
        
        # TODO what if multiple outputs i.e more than 2?
        for x in res.outputs:
            #logging.info(x.address)
            if x.address != recv_addr:
                return x.address
        return None

        #print("outputs")
        #print(res.inputs)


    def utxo_query(self, txhash:str):
        res = self.api.transaction_utxos(hash=txhash)
        print(res)

    def addr_query(self, addr:str):
        address = self.api.address(address=addr)
        print(address)
        print(address.type)  # prints 'shelley'

    def policy_to_json(self, policy:str):
        assets = []
        txs = []
        meta721 = {}
        metaNEW_CIP = {}

        # get asset from policy
        res = self.api.assets_policy(policy)
        for x in res:
            assets.append(x.asset)

        # get txs from asset
        for x in assets:
            tx = self.api.asset_transactions(x)
            for y in tx:
                txs.append(y.tx_hash)

        # for each transaction related to an asset
        for x in txs:
            # obtain meta as json
            meta = self.api.transaction_metadata(x, return_type='json')
            log_debug("meta payload/s \'" + str(len(meta)) + " \'")
            # for each CIP 
            for i in range(len(meta)):
                # get json specific json/dict keys
                json_tag = 'json_metadata'
                label = meta[i]['label']
                
                # ignore version tag # TODO in the future we might need to check for policy id regex
                policy_id = None
                for loc, data in enumerate(meta[i][json_tag].keys()):
                    if data != 'version':
                        policy_id =  list(meta[i][json_tag])[loc]
                

                mint_id =  list(meta[i][json_tag][policy_id])[0]
                # each metadata type to it's own dict (optionally we could put it all in one json) 
                if label == "721":
                    log_debug("721")
                    # get the metadata using the 721 standard
                    meta721[mint_id] = meta[i][json_tag][policy_id][mint_id]
                elif label == NEW_CIP:
                    log_debug(NEW_CIP)
                    # for each datapackage in new CIP
                    for ref in list(meta[i][json_tag][policy_id]):
                        # add the payload to our json, store using the payload reference
                        # as key to the contained payload data
                        metaNEW_CIP[ref] = meta[i][json_tag][policy_id][ref]
                else:
                    log_error("Unknown label")
        # return dict of 721 and NEW_CIP
        self.policy_meta[policy] = {'721':meta721, NEW_CIP:metaNEW_CIP}
        return meta721, metaNEW_CIP


    def policy_nft_count(self, policy:str):
        # if this is the first run convert policy to json
        if policy not in self.policy_meta.keys():
            self.policy_to_json(policy)
        return len(self.policy_meta[policy]['721'])


    # populate and return nft data. i.e the svg image for a given nft
    def get_nfts(self, policy:str, force_update:bool=False):
        total = self.policy_nft_count(policy)
        # TODO update as minting happens?       
        if 'nfts' not in self.policy_meta[policy].keys():
            force_update = True 

        if force_update:
            svgs = {}
            for i in self.policy_meta[policy]['721'].keys():
                svg_str = self.onchain_nft_to_svg(policy, i)
                svgs[str(i)] = svg_str

            meta721 = self.policy_meta[policy]['721']
            metaNEW_CIP =  self.policy_meta[policy][NEW_CIP]       
            self.policy_meta[policy] = {'721':meta721, NEW_CIP:metaNEW_CIP, 'nfts':svgs}

        return self.policy_meta[policy]

    def onchain_nft_to_svg(self, policy:str, nft_id:str, force_update:bool=False):
        
        # if this is the first run convert policy to json
        if policy in self.policy_meta.keys() and force_update:
            self.policy_to_json(policy)
        elif policy not in self.policy_meta.keys():
            self.policy_to_json(policy)

        # get the refs for the current nft_id
        svg_str = ""
        #breakpoint()
        refs = self.policy_meta[policy]['721'][nft_id][NEW_CIP]['ref']

        # combine all payload strings into one svg string
        for i in refs:
            for data in self.policy_meta[policy][NEW_CIP][str(i)]:
                svg_str += data
        svg_str = svg_str.strip()

        # TODO if write is needed
        if False:
            f = open("test.svg", "w")
            f.write(svg_str)
            f.close()
        # return the svg string
        return svg_str
