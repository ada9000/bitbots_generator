class Nft:
    def __init__(self, policyid:str="todo"):

        self.policyid = policyid
        self.nft_CIP = '721'
        self.new_CIP = '696'

    def generate_nft(self, nft_name:str, payload_ref:int, nft_payload:[], nft_references:[], properties):
        # TODO note nft_references might be ints but json only allows string keys
        meta = {}
        # 721 
        # notice the new CIP line
        # TODO convert this to variables passed into method
        nft_details = {
            'project':'Copyright Bitbots.art 2022',
            'traits':properties,
            'description':'nft showcasing new CIP',
            self.new_CIP: {'mediaType':'image/svg+xml','ref':nft_references}
            }
        #meta[self.nft_CIP] = {self.policyid:{nft_name:nft_details}}

        if nft_payload != None:
            # include new CIP payload
            meta = {
                self.nft_CIP:{
                    self.policyid:{
                        nft_name:nft_details
                        }
                    }, 
                self.new_CIP:{
                    self.policyid:{
                        payload_ref:nft_payload
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