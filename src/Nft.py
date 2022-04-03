from Utility import NEW_CIP
import copy

class Nft:
    def __init__(self, policyid:str="todo"):

        self.policyid = policyid
        self.nft_name = ''
        self.nft_CIP = '721'
        self.new_CIP = NEW_CIP
        self.version = '2.0'
        # mime: data:image/svg+xml;utf8

    def generate_nft(self, nft_name:str, payload_ref:int, nft_payload:list, nft_references:list, properties):
        # TODO note nft_references might be ints but json only allows string keys
        meta = {}
        self.nft_name = nft_name
        # 721 
        # notice the new CIP line
        # TODO convert this to variables passed into method
        nft_details = {
            'project':'Bitbots',
            'name':nft_name,
            'traits':properties,
            #'type':'NPC', TODO
            self.new_CIP: {
                'mediaType':'image/svg+xml;utf8,','ref':nft_references
                }
            }

        if nft_payload != None:
            # include new CIP payload
            meta = {
                self.nft_CIP:{
                    self.policyid:{
                        nft_name:nft_details
                        },
                    }, 
                    'version':self.version,
                self.new_CIP:{
                    self.policyid:{
                        str(payload_ref):nft_payload
                        }
                    }
                }
        else:
            # ignore new CIP payload
            meta = {
                self.nft_CIP:{
                    self.policyid:{
                        nft_name:nft_details
                        }
                    },
                    'version':self.version,
                }
        return meta


    def append_more_data(self, meta, payload_ref:int, nft_payload:list):
        new_meta = copy.deepcopy(meta)
        new_meta[self.new_CIP][self.policyid][payload_ref] = nft_payload
        return new_meta


    def change_type(self, meta, type):
        if self.nft_name == '':
            raise Exception("Invalid nft name")
        new_meta = copy.deepcopy(meta)
        new_meta[self.nft_CIP][self.policyid][self.nft_name]['type'] = type
        return new_meta