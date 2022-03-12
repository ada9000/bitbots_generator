# Bitbots.py
__author__ = 'pixel_pool'

# imports --------------------------------------------------------------------
import os
import json
import random
import base64
import random
import re
import sys

# consts ---------------------------------------------------------------------
INPUT_DIR = "../input"
OUTPUT_DIR = "../output/"
NFT_TRAIT_META_FILE = "nft-trait-meta.json"
NFT_ATTRIBUTES_META_FILE = "nft-attributes-meta.json"
NFT_WEIGHTS_FILE = "nft-weights.json"
NFT_PAYLOAD_FILE = "nft-payload.json"

NFT_MINT_DATA_FILE = "nft-mint-data.json"
NFT_MINT_STATS_FILE = OUTPUT_DIR + "_nft-mint-stats.json"

# XML and SVG consts
XML_tag = '<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?>\n<!DOCTYPE svg PUBLIC \"-//W3C//DTD SVG 1.1//EN\" \"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd\">'
SVG_start = '<svg width=\"100%\" height=\"100%\" viewBox=\"0 0 5906 5906\" version=\"1.1\" xmlns=\"http://www.w3.org/2000/svg\" xmlns:xlink=\"http://www.w3.org/1999/xlink\" xml:space=\"preserve\" xmlns:serif=\"http://www.serif.com/\" style=\"fill-rule:evenodd;clip-rule:evenodd;stroke-linejoin:round;stroke-miterlimit:2;\">'
SVG_end = '</svg>'
# colour consts used to replace SVG colours with variables
BASE_COLOUR = 'style="fill:rgb(219,212,255);"'
BASE_COLOUR_REPLACE = 'class="base_colour"'
COLOUR_STYLE_START = '<style> .base_colour {fill:'
COLOR_STYLE_DEFAULT = '{fill: #DBD4FF}' # TODO deprecated?
COLOUR_STYLE_END = '} </style>'

# attribute order
ATTRIBUTE_ORDER = ["neck", "special", "head", "hats", "ears", "mouths", "eyes"]
ATTRIBUTES_WITH_WEIGHTS = ["hats", "ears", "mouths", "eyes"]

DEFAULT_WEIGHT = 1.0

# Notes TODO REMOVE
    #[x] weighted_rand(meta, svg_meta)
    #[x] add weighted randomness to generation
    #[x] segregate files over 12kb into multiple files
    #[x] put nfts in output folder
    #[ ] view all nfts
    #[ ] TODO add webclient
    #[ ] TODO convert to Cardano 721 metadata
    #[ ] TODO webclient can read Cardano 721 metadata
    #[ ] TODO implement tally and other special mint options
    #[ ] TODO ignore lobster, lobster is special mint parameter for airdrop to lobster contact 
    #[ ] TODO issue with normal ears
    #[ ] in 721 no_<item> is renamed to none
    #[ ] todo NFT n that holds the colour payload will be PURE nft of said colour

    # Turn this file into business logic and server
    # Add API
    # Create react page for front-end
    # TODO where is special?
    # TODO turn the whole codebase into a class
    # TODO methods
    #       generate # does everything

    # base64? figure out data types
    #

# functions-------------------------------------------------------------------
def load_json(filepath):
    data = {}
    with open(filepath) as f:
        data = json.load(f)
    return data
 
def write_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    return

# Nft ------------------------------------------------------------------------
class Nft:
    def __init__(self, policyid:str="TEST5ba13e49e3877ef371be591eb1482bd8261d66a4c489a9b522bc"):

        self.policyid = policyid
        self.nft_CIP = '721'
        self.new_CIP = '696'

    def generate_nft(self, nft_name:str, payload_ref:int, nft_payload:[], nft_references:[]):
        meta = {self.nft_CIP:'', self.new_CIP:''}
        # TODO note nft_references might be ints but json only allows string keys
        # 721 
        # notice the new CIP line
        # TODO convert this to variables passed into method
        nft_details = {
            'project':'test',
            'traits':{'eye':'ada_eye','hat':'brain'},
            'description':'nft showcasing new CIP',
            self.new_CIP: {'mediaType':'image/svg+xml','ref':nft_references}
            }
        meta[self.nft_CIP] = {self.policyid:{nft_name:nft_details}}

        # new cip stuff
        meta[self.new_CIP] = {self.policyid:{payload_ref:nft_payload}}
        
        print(json.dumps(meta, indent=4))
        return meta


# Bitbots --------------------------------------------------------------------
class Bitbots:
    def __init__(self, max_mint:int=8192, max_payload_bytes:int=12000, reset:bool=True):
        # vars
        self.variable_attributes = ["colour", "special", "hats", "ears", "mouths", "eyes"]
        self.colour_lst = ["#dbd4ff", "#ffe0e0", "#ebffe0", "#e0fcff", "#ebda46", "#696969"]
        self.ref_order = ['startcolour','colour','endcolour','neck','special','head','hats','ears','mouths','eyes']
        # parameters
        self.max_mint = max_mint
        self.max_payload_bytes = max_payload_bytes
        # meta data       
        self.nft_traits = {}        # json defining each trait
        self.nft_attributes = {}    # json defining all attributes
        # mint data
        self.nft_set_data = {}
        self.nft_mint_data = {} #metadata for mint
        # payload vars
        self.payload_meta = {} # about payload indices
        self.payload_data = {} # payload data
        self.payload_index = 0

        # generate nft
        self.generate(reset)

    def generate(self, reset:bool=True):
        if not reset:
            return
        # clean and get data from files
        self.clean()
        self.nft_meta_from_files()
        # update and apply weights
        self.update_weights()

        # add payload refs
        self.gen_payload_meta()

        # create a random nft set!
        self.generate_random_set()
        
        # 
        self.make_svgs_from_nft_data()

        self.gen_721()
        # 
        self.make_svg_from_payloads()

    def clean(self):
        """ clean files """
        #remove all files in OUTPUT_DIR
        for file in os.listdir(OUTPUT_DIR):
            file = OUTPUT_DIR + file
            os.remove(file)

    def shuffle(self):
        nfts = {}
        nums = list(range(0, self.max_mint))
        random.shuffle(nums)
        print("shuffle...")
        i = 0
        for tmp in os.listdir("../output/"):
            if ".svg" in tmp:
                filename = "../output/" + tmp
                text = open(filename, 'r')
                nft = text.read()
                text.close()
                nfts[str(nums[i])] = nft
                i += 1
        print("shuffle done!")
        write_json("filepath.json", nfts)
        return nfts


    def clean_svg(self, data):
        # remove all double or more whitespace substrings strings
        skip_svg = False
        svg_str = ""
        for i in range(len(data)):
            # if we see the svg tag begin the skip
            if data[i:i+4] == "<svg":
                skip_svg = True
            # if the last char was the end of the svg disable the skip process
            if data[i-1] == ">":
                skip_svg = False
            # skip if we are still on the svg tag
            if skip_svg:
                continue
            # remove all instaces of two or more continues whitespace, 
            # by only appending character that are not whitespace followed
            # by whitespace
            if (i + 1) < len(data):
                if data[i] == ' ' and data[i+1] == ' ':
                    pass
                else:
                    svg_str += data[i]
        # remove the XML tag the SVG endtag and all newlines
        svg_str = svg_str.replace(XML_tag,'')
        svg_str = svg_str.replace(SVG_end,'')
        svg_str = svg_str.replace('\n', '')
        # replace svg base colours with dynamic method
        svg_str = svg_str.replace(BASE_COLOUR, BASE_COLOUR_REPLACE)
        # set data to the new refactored data
        return svg_str 

    def get_traits(self, attribbute:str):
        return self.nft_attributes[attribbute]

    def get_trait_refs(self, attribbute:str):
        return None # TODO

    def nft_meta_inner(self, attribute:str, id_num:int, data:str):
        return {'attribute':attribute, 'id':id_num, 'weight':1.0, 'max':self.max_mint, 'data':data}


    def nft_meta_from_files(self):
        """ generate metadata based of directory structure and filenames """
        # for each file in our INPUT_DIR, create a nft data entry (key)
        # then for each file in that dir get extract the metadata and svg payload
        self.nft_attributes = {}
        for attribute in os.listdir(INPUT_DIR):
            sub_dir_path = INPUT_DIR + '/' + attribute
            details = {}
            data = ""
            id_num = 0
            traits = []
            # for each svg file inside a sub directory
            # if the dirname is variable add none type 
            if attribute in self.variable_attributes:
                # TODO add none type
                trait = "no_" + attribute
                self.nft_traits[trait] = self.nft_meta_inner(attribute, id_num, data)
                id_num += 1
                traits.append(trait)
            # geneate metadata for each trait
            for trait in os.listdir(sub_dir_path):
                filepath = sub_dir_path + '/' + trait
                trait = trait.replace('.svg','')
                skip_svg = False
                # open the svg file
                with open(filepath, 'r') as f:
                    data = f.read()
                # clean / format svg
                data = self.clean_svg(data)
                # add new trait to nft_meta, including it's attribbute, id and svg data
                self.nft_traits[trait] = self.nft_meta_inner(attribute, id_num, data)
                id_num += 1
                # add traits for meta-meta data
                traits.append(trait)
            # meta meta data 
            self.nft_attributes[attribute] = traits
        # add colours to the set
        id_num = 0
        for trait in self.colour_lst:
            self.nft_traits[trait] = self.nft_meta_inner('colour', id_num, trait)
            id_num += 1
        # add colours to the nft attributes
        self.nft_attributes['colour'] = self.colour_lst
        # save to file 
        write_json(NFT_TRAIT_META_FILE, self.nft_traits)
        write_json(NFT_ATTRIBUTES_META_FILE, self.nft_attributes)


    def make_svg(self, inner_svg:str, style:str, filename:str):
        """ create a svg file from given paramaters """
        #svg_str = XML_tag + "\n" + SVG_start + "\n" 
        svg_str = SVG_start + "\n" 
        svg_str += style + "\n"
        svg_str += inner_svg + "\n" + SVG_end
        
        with open(filename, "w") as f:
            f.write(svg_str)
    

    def payload_to_str(self, payload):
        # TODO should be deprecated...
        data = ""
        for x in payload:
            data += x
        return data

    def get_payload_refs(self, nft_ref_arr:[], trait:str):
        # add the payload references to an array the nft will use this to
        # find the correct order of data that makes the final image
        for i in self.payload_meta[trait]:
            nft_ref_arr.append(i)
        return nft_ref_arr

    def make_svg_from_payloads(self):
        # we use the nft_data
        for n in self.nft_set_data:
            nft_ref_arr = []
            # add color
            nft_ref_arr = self.get_payload_refs(nft_ref_arr, "colour")
            col = self.nft_set_data[n]['colour']
            nft_ref_arr = self.get_payload_refs(nft_ref_arr, col)
            nft_ref_arr = self.get_payload_refs(nft_ref_arr, "endcolour")

            # neck
            nft_ref_arr = self.get_payload_refs(nft_ref_arr, "neck")
            # special
            print(self.nft_set_data[n])
            trait = self.nft_set_data[n]["special"]
            nft_ref_arr = self.get_payload_refs(nft_ref_arr, trait)
            # head
            nft_ref_arr = self.get_payload_refs(nft_ref_arr, "head")

            # others
            for attrubute in ATTRIBUTES_WITH_WEIGHTS:
                trait = self.nft_set_data[n][attrubute]
                nft_ref_arr = self.get_payload_refs(nft_ref_arr, trait)
                

            nft_ref_arr = self.get_payload_refs(nft_ref_arr, "end")
            # write the file
            filename = OUTPUT_DIR + str(n) + ".svg"

            breakpoint()
            svg_str = "todo"

            with open(filename, "w") as f:
                f.write(svg_str)


        pass

    def make_svgs_from_nft_data(self): # TODO deprecate
        for n in self.nft_set_data:
            filename = OUTPUT_DIR + str(n) + ".svg"

            svg_str = ""
            for i in self.nft_set_data[n]["refs"]:
                for line in self.payload_data[i]:
                    svg_str += line

    
            with open(filename, "w") as f:
                f.write(svg_str)

    def update_weights(self):
        # init weights load them if they exists
        weights = {}
        if os.path.isfile(NFT_WEIGHTS_FILE):
            weights = load_json(NFT_WEIGHTS_FILE)
        
        # update weights for all traits
        for trait in self.nft_traits.keys():
            # if the item is not in weights add it to weights json (populate the file)
            if trait not in weights.keys():
                weights[trait] = {"weight":DEFAULT_WEIGHT, "max":self.max_mint}

            # if weights or max need updating, update them
            if self.nft_traits[trait]["weight"] != weights[trait]["weight"]:
                self.nft_traits[trait]["weight"] = weights[trait]["weight"]
            if self.nft_traits[trait]["max"] != weights[trait]["max"]:
                self.nft_traits[trait]["max"] = weights[trait]["max"]
        
        # save weights in a json file (user can edit them)
        write_json(NFT_WEIGHTS_FILE, weights)

    def apply_refs_inner(self, payload_trait):
        res = []
        for i in self.payload_meta[payload_trait]:
            res += [i]
        return res

    def apply_refs(self, properties):
        refs = []
        order = ['neck','special','head','hats','ears','mouths','eyes']
        #self.payload_meta[trait] = used_indices
        refs += self.apply_refs_inner('startcolour')
        refs += self.apply_refs_inner(properties['colour'])
        refs += self.apply_refs_inner('endcolour')
        refs += self.apply_refs_inner('neck')
        refs += self.apply_refs_inner(properties['special'])
        refs += self.apply_refs_inner('head')
        refs += self.apply_refs_inner(properties['special'])
        refs += self.apply_refs_inner(properties['hats'])
        refs += self.apply_refs_inner(properties['ears'])
        refs += self.apply_refs_inner(properties['mouths'])
        refs += self.apply_refs_inner(properties['eyes'])
        refs += self.apply_refs_inner('end')
        return refs


    def generate_random_set(self):
        nfts = {}
        stats = {}
        nft_mint_number = 0
        used_hashes = []

        while len(nfts) != self.max_mint:
            refs = []
            # run inner loop that picks properties and creates a unique id based on props (hex_hash)
            hex_hash, properties = self.weight_inner()  
            # check for duplicates, and rerun until our new hex has is unique
            for h in used_hashes:
                while hex_hash not in used_hashes:
                    hex_hash, properties = self.weight_inner()  
            
            # apply refs
            refs = self.apply_refs(properties)
            # gen nft
            nfts[nft_mint_number] = {"meta":properties, "hex":hex_hash, "refs":refs}
            nft_mint_number += 1

        print("Created " + str(self.max_mint) + " nfts")
        stats = {"stats":stats, "nfts":nfts}
        write_json(NFT_MINT_STATS_FILE, stats)
        write_json(NFT_MINT_DATA_FILE, nfts)
        self.nft_set_stats = stats
        self.nft_set_data = nfts


    def weight_inner(self):
        hex_hash = "0x"

        properties = {}
        # this loop generates nfts based of weight values for traits within each attribute
        for attribute in self.variable_attributes:
            traits = [] 
            weights = []
            for trait in self.nft_attributes[attribute]:
                traits.append(trait)
                weights.append(self.nft_traits[trait]["weight"])
            
            # select a weighted random trait
            trait = random.choices(traits, weights)[0]
            properties[attribute] = trait

            # convert the trait id to hexadecimal and append it to the hex_hash identifier, also add some padding
            hex_hash += str(hex(self.nft_traits[trait]["id"])[2:]).zfill(2)
            
        return hex_hash, properties

    def str_to_64_char_arr(self, payload_str:str):
        payload_arr = []
        index = 0
        current_str = ""

        for c in payload_str:

            if len(current_str) == 64:
                payload_arr.append(current_str)
                print()
                current_str = ""
                index = 0
            
            current_str += c
            index += 1
        
        # add remaining (trailing i.e less than 64 chars) data
        if current_str != "":
            payload_arr.append(current_str)

        return payload_arr

    
    def append_payload(self, payload_str:str , trait:str):
        payload_arr = self.str_to_64_char_arr(payload_str)
        print(len(payload_arr))
        used_indices = []
        #self.payload_meta

        # TODO segregate payload arr
        tmp_payload = []
        payload_bytes = 0
        print("len payload = ")
        print(len(payload_arr))

        RESET_VALUE = 128
        payload_idx = 0

        for row in payload_arr:
            if payload_idx == RESET_VALUE:
                self.payload_data[self.payload_index] = payload_arr
                used_indices.append(self.payload_index)
                self.payload_index += 1
                tmp_payload = []
                payload_idx = 0
            
            tmp_payload.append(row)
            payload_idx += 1
        
        if tmp_payload != []:
            self.payload_data[self.payload_index] = payload_arr
            used_indices.append(self.payload_index)
            self.payload_index += 1

        self.payload_meta[trait] = used_indices
        return

    def nft_data_to_cardano(self):
        for i in self.nft_set_data:
            pass


    def gen_payload_meta(self):
        payload_str = ""
        self.payload_data = {}
        

        # SVG start until color
        payload_str = ""
        payload_str += SVG_start
        payload_str += COLOUR_STYLE_START 

        # add start
        self.append_payload(payload_str, 'startcolour')

        # add color
        for c in self.nft_attributes["colour"]:
            payload_str = c
            self.append_payload(payload_str, c)

        # end color
        self.append_payload(COLOUR_STYLE_END, 'endcolour')

        # add neck
        #payload_str = self.nft_traits["neck"]["data"]
        #self.append_payload(payload_str, "neck")
        
        # add the rest
        order = ["neck","special","head","hats", "ears", "mouths", "eyes"]
        known_traits = []
        for o in order:
            for x in self.nft_attributes[o]:
                # check for duplicates
                if x in known_traits:
                    raise Exception("Duplicate trait \'"+x+"\'! found in \'" + o + "\'")
                known_traits.append(x)
                # append payload
                self.append_payload(self.nft_traits[x]["data"], x)

        # apppend end
        self.append_payload(SVG_end, 'end')

        data = {"meta":self.payload_meta, "payload":self.payload_data}
        write_json(NFT_PAYLOAD_FILE, data)
        

    def gen_721_policy(self):
        # check if we need new one
        # get policy id

        # policy 721
        #   nft 1 <- note nft tag
        #       tags: {ada_eyes, brain, etc}
        #       src = {payloads [0,1,3,4,20,21,99,100]}
        #   payload tag <- note payload tag
        #       data = ["asdasdfds",asdfdsfasdfd,"asfdsdafdsa"]

        pass

    def gen_721(self):
        self.gen_721_policy()
        # using nft data
        # using payload meta
        # populate a 721 meta
        # 0: policyid nft721 .... etc
        pass 

    def nft_random_order(self):
        # for each hashtag in the set give it a random id
        # update nft json to be such as 1: nft_hash: ...
        #                               2: nft_hash: ...
        #                               3: nft_hash: ...
        # etc
        return

    def nft_stats(self):
        # iterate through json
        # generate stats
        return

    def max_combinations(self):
        return

    def size_test(self):
        # not accurate representation but just to get a feeling
        json_str = json.dumps(self.nft_traits, ensure_ascii=False, indent=4)
        utf_size = len(json_str.encode('utf-8'))
        print("UTF size of meta file ~" + str(utf_size / 1000.0 ) + "kB")