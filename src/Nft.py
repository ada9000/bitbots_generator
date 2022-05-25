from numpy import fix
from Utility import NEW_CIP
import copy

ATTRIBUTE_FIXES = {
    "bg effects":"Effects",
    "colour":"Base colour",
    "bg colour":"Background colour",
    "bg effects":"Effects",
    "hats":"Hat",
    "mouths":"Mouth",
    }

TRAIT_FIXES = {
    "jkr":"JKR",
    "rj45":"RJ45",
    "#ffd700":"Gold",
    "#2897e0":"Diamond",
    "#FF0063;":"Hot Pink",  # cool bg colour
    "#3E51FF;":"Deep Blue", # cool bg colour
    }


class Nft:
    def __init__(self, policyid:str="todo"):

        self.policyid = policyid
        self.nft_name = ''
        self.nft_CIP = '721'
        self.payload = 'payload'#NEW_CIP TODO
        self.references = 'references'#NEW_CIP TODO
        self.version = '2'
        # mime: data:image/svg+xml;utf8

    def fixProperties(self, properties):
        fixedProperties = {}
        for attribute, trait in properties.items():
            fixedAttribute = attribute.capitalize()
            fixedTrait = trait.capitalize()
            
            # make any colours uppercase
            if "colour" in attribute:
                fixedTrait = trait.upper()
                fixedTrait = fixedTrait.replace(';','')
            
            # fix values
            if attribute in ATTRIBUTE_FIXES.keys():
                fixedAttribute = ATTRIBUTE_FIXES[attribute]
            if trait in TRAIT_FIXES.keys():
                fixedTrait = TRAIT_FIXES[trait]

            fixedProperties[fixedAttribute] = fixedTrait

        return fixedProperties

    def generate_nft(self, nft_name:str, payload_ref:int, nft_payload:list, nft_references:list, properties):
        # TODO note nft_references might be ints but json only allows string keys
        meta = {}
        self.nft_name = nft_name
        properties = self.fixProperties(properties)
        # 721 
        # notice the new CIP line
        # TODO convert this to variables passed into method
        nft_details = {
            'project':'Bitbots',
            'name':nft_name,
            'traits':properties,
            #'type':'NPC', TODO
            self.references: {
                'mediaType':'image/svg+xml;utf8,','src':nft_references
                }
            }

        if nft_payload != None:
            # include new CIP payload
            meta = {
                self.nft_CIP:{
                    self.policyid:{
                        nft_name:nft_details
                    },
                    'version':self.version,
                    self.payload:{
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
                    },
                    'version':self.version,
                    },
                }
        return meta


    def append_more_data(self, meta, payload_ref:int, nft_payload:list):
        new_meta = copy.deepcopy(meta)
        #new_meta[self.new_CIP][self.policyid][payload_ref] = nft_payload
        new_meta['721'][self.payload][payload_ref] = nft_payload
        return new_meta


    def change_type(self, meta, type):
        if self.nft_name == '':
            raise Exception("Invalid nft name")
        new_meta = copy.deepcopy(meta)
        new_meta[self.nft_CIP][self.policyid][self.nft_name]['type'] = type
        return new_meta