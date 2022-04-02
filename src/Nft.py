from Utility import NEW_CIP

class Nft:
    def __init__(self, policyid:str="todo"):

        self.policyid = policyid
        self.nft_CIP = '721'
        self.new_CIP = NEW_CIP
        # mime: data:image/svg+xml;utf8

    def generate_nft(self, nft_name:str, payload_ref:int, nft_payload:list, nft_references:list, properties):
        # TODO note nft_references might be ints but json only allows string keys
        meta = {}
        # 721 
        # notice the new CIP line
        # TODO convert this to variables passed into method
        nft_details = {
            'project':'Copyright Bitbots.art 2022',
            'traits':properties,
            'description':'nft showcasing new CIP',
            self.new_CIP: {
                'mediaType':'image/svg+xml;utf8,','ref':nft_references
                }
            }
        #meta[self.nft_CIP] = {self.policyid:{nft_name:nft_details}}

        if nft_payload != None:
            # TODO add multiple payloads i.e
            # '1':data,
            # '2':data,
            # 'n':data

            # include new CIP payload
            meta = {
                self.nft_CIP:{
                    self.policyid:{
                        nft_name:nft_details
                        }
                    }, 
                self.new_CIP:{
                    self.policyid:{
                        "NOTE":"COPYRIGHT Bitbots.art 2022",
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
                    }
                }
        
        return meta