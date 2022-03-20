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
# local files
from Nft import *
from Utility import *

# consts ---------------------------------------------------------------------
# files
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
# Variable
DEFAULT_WEIGHT = 1.0
MINT_MAX = 8192
MAX_PAYLOAD_BYTES = 14000
#-----------------------------------------------------------------------------
# TODO
# [ ] implent id special tag
# [ ] implent tally
# [ ] fix artifacts in svg's
# [ ] rename meta items (remove underscore etc)
# [ ] no_<attribute> is renamed to none in metadata
# [ ] ensure only 503 are lobsters (and these are giveaways) https://cardanoscan.io/tokenPolicy/cc7888851f0f5aa64c136e0c8fb251e9702f3f6c9efcf3a60a54f419
# [ ] NFT n that holds the colour payload will be PURE nft of said colour
# [ ] Add secretes into svg?
# [ ] Remove COPY_RIGHT comments
# [ ] change input dir before realise


# Bitbots --------------------------------------------------------------------
class Bitbots:
    def __init__(self, max_mint:int=MINT_MAX, max_payload_bytes:int=MAX_PAYLOAD_BYTES, reset:bool=True):
        # vars
        self.variable_attributes = ["colour", "special", "hats", "ears", "mouths", "eyes"]
        self.colours = ["#dbd4ff", "#ffe0e0", "#ebffe0", "#e0fcff","#8395a1","#90d7d5","#62bb9c","#90d797","#ff8b8b", "#ffc44b","#ffd700","#696969","#ffffff"]
        self.wire_colours = [("#009bff","#fff800"), ("#ff0093","#009bff"),("#62bb7f","#bb6862")]
        self.ref_order = ['startcolour','colour','endcolour','neck','head_shadow','special','head','hats','ears','mouths','eyes']
        # parameters
        self.max_mint = max_mint
        self.max_payload_bytes = max_payload_bytes
        # meta data       
        self.nft_traits = {}        # json defining each trait
        self.nft_attributes = {}    # json defining all attributes
        # mint/set data
        self.nft_set_data = {}
        # payload vars
        self.payload_meta = {} # about payload indices
        self.payload_data = {} # payload data
        self.payload_index = 0
        # Cardano nft meta
        self.cardano_nft_meta = {}

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
        log_info("Payload count is " + str(self.payload_index))
        if self.max_mint < self.payload_index:
            raise Exception(str(self.payload_index) + " nfts required but max mint is " + str(self.payload_index))
        # create a random nft set!
        self.generate_random_set()
        # populate output with svgs
        self.svg_from_nft_data()
        # create nft that conforms to CIP's
        self.create_cardano_nft()


    def clean(self):
        """ clean files """
        #remove all files in OUTPUT_DIR
        for file in os.listdir(OUTPUT_DIR):
            file = OUTPUT_DIR + file
            os.remove(file)


    def clean_svg(self, data):
        """ 
        alters a string containign svg data, 
        removes svg tags,
        replaces colours with a variable
        removes unnecessary whitespace
        """
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
            try:
                if (i) < len(data):
                    if data[i] == ' ' and data[i+1] == ' ':
                        pass
                    else:
                        svg_str += data[i]
            except IndexError as e:
                pass
        # remove the XML tag the SVG endtag and all newlines
        svg_str = svg_str.replace(XML_tag,'')
        svg_str = svg_str.replace(SVG_end,'')
        svg_str = svg_str.replace('\n', '')
        # replace svg base colours with dynamic method
        svg_str = svg_str.replace(BASE_COLOUR, BASE_COLOUR_REPLACE)
        # set data to the new refactored data
        return svg_str 


    def nft_meta_inner(self, attribute:str, id_num:int, data:str):
        """ defines the inner metadata for each trait """
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
                log_debug("Metadata for " + str( attribute ) + " adding \'" + trait + "\'")
            # meta meta data 
            self.nft_attributes[attribute] = traits
        # add colours to the set
        id_num = 0
        for trait in self.colours:
            self.nft_traits[trait] = self.nft_meta_inner('colour', id_num, trait)
            id_num += 1
        # add colours to the nft attributes
        self.nft_attributes['colour'] = self.colours
        # save to file 
        write_json(NFT_TRAIT_META_FILE, self.nft_traits)
        write_json(NFT_ATTRIBUTES_META_FILE, self.nft_attributes)


    def svg_from_nft_data(self):
        """ populate OUTPUT_DIR with svg files of each nft in our set """
        for n in self.nft_set_data:
            filename = OUTPUT_DIR + str(n) + ".svg"

            svg_str = ""
            for i in self.nft_set_data[n]["refs"]:
                for line in self.payload_data[i]:
                    svg_str += line

    
            with open(filename, "w") as f:
                f.write(svg_str)


    def update_weights(self):
        """ 
        creates NFT_WEIGHTS_FILE if it doesn't exists,
        updates metadata values to reflect those in the weights file

        useful for assigning rarity to a nft
        """
        # init weights load them if they exists
        weights = {}
        if os.path.isfile(NFT_WEIGHTS_FILE):
            weights = read_file_return_data(NFT_WEIGHTS_FILE)
        
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

    def find_payload_refs(self, payload_trait):
        """ helper function to find and return payload references to a trait """
        res = []
        for i in self.payload_meta[payload_trait]:
            res += [i]
        return res

    def find_refs_for_props(self, properties, nft_id):
        """ helper function to generate refs for a give set of nft properties """
        refs = []
        #self.payload_meta[trait] = used_indices
        refs += self.find_payload_refs('startcolour')
        refs += self.find_payload_refs(properties['colour'])
        refs += self.find_payload_refs('endcolour')
        refs += self.find_payload_refs('neck')
        # add id
        
        # id start
        refs += self.find_payload_refs('id_start')
        log_debug(nft_id)
        for i, x in enumerate(nft_id[2:]):
        # for ids

            # id transform start
            refs += self.find_payload_refs('id_transform_start')
            # id number ere
            pos_ref = "id_transform_pos" + str(i)
            refs += self.find_payload_refs(pos_ref)
            # id transform end end
            refs += self.find_payload_refs('id_transform_end')
            # add number here
            number_ref = "id_" + x.upper()
            refs += self.find_payload_refs(number_ref)
            # id end
        refs += self.find_payload_refs('id_end')

        refs += self.find_payload_refs('head_shadow')
        refs += self.find_payload_refs(properties['special'])
        refs += self.find_payload_refs('head')
        refs += self.find_payload_refs(properties['hats'])
        refs += self.find_payload_refs(properties['ears'])
        refs += self.find_payload_refs(properties['mouths'])
        refs += self.find_payload_refs(properties['eyes'])
        refs += self.find_payload_refs('end')
        return refs


    def generate_random_set(self):
        """ 
        generate a random set of nfts
        save the set to self.nft_set_data
        """
        nfts = {}
        nft_mint_number = 0
        used_hashes = []

        while len(nfts) != self.max_mint:
            refs = []
            # run inner loop that picks properties and creates a unique id based on props (hex_hash)
            hex_hash, properties = self.gen_random_props()  
            # check for duplicates, and rerun until our new hex has is unique
            for h in used_hashes:
                while hex_hash not in used_hashes:
                    hex_hash, properties = self.gen_random_props()  
            # apply refs
            nft_name = '0x' + hex(nft_mint_number)[2:].zfill(4)
            ##nft_mint_number_str = str(nft_mint_number).zfill(4)
            refs = self.find_refs_for_props(properties, nft_name)
            # save nft with padded number i.e 0001,...,1111,...,n
            nfts[nft_name] = {"meta":properties, "hex":hex_hash, "refs":refs}
            nft_mint_number += 1
        # update set data with new nfts and save to file
        self.nft_set_data = nfts
        write_json(NFT_MINT_DATA_FILE, nfts)
        log_info("Created " + str(self.max_mint) + " nfts")


    def gen_random_props(self):
        """
        generate random properties for each vairable attribute using
        the known weights

        returns a unique hex_hash identifier and random properties
        """
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
        """ separate a string into an array element for every 64 characters """
        payload_arr = []
        index = 0
        current_str = ""
        for c in payload_str:
            if len(current_str) == 64:
                payload_arr.append(current_str)
                current_str = ""
                index = 0
            current_str += c
            index += 1
        # add remaining (trailing i.e less than 64 chars) data
        if current_str != "":
            payload_arr.append(current_str)
        return payload_arr

    
    def append_to_payload(self, payload_str:str , trait:str):
        """ 
        given a payload string and a trait string,
        convert the payload string to blocks of data
        use the trait string to point to said blocks of data

        i.e payload_meta['start'] = [0,1]
            payload_data[0] = "aaaa"
            payload_data[1] = "bbbb"
            payload_data[2] = "cccc"

        update the self.payload_meta
        update the self.payload_data
        """
        # TODO remove later this just adds copy rights for initial tests
        #COPY_RIGHT = "<!-- COPYRIGHT bitbots.art pixelpool.io 2022 -->"
        #payload_str = COPY_RIGHT + payload_str
        # TODO deprecate above before release

        # convert string to array 
        payload_arr = self.str_to_64_char_arr(payload_str)
        # define vars
        used_indices = []
        tmp_payload = []
        payload_bytes = 0
        RESET_VALUE = 128# 128 rows
        line_count = 0
        # for each row of 64 in the payload array TODO fix
        for row in payload_arr:
            if line_count >= RESET_VALUE:
                log_debug("Payload for \'" + trait +"\' stored in idx " + str(self.payload_index))
                self.payload_data[self.payload_index] = tmp_payload
                used_indices.append(self.payload_index)
                self.payload_index += 1 # global index for payloads
                tmp_payload = []
                line_count = 0
                # remove used from payload_arr


            tmp_payload.append(row)
            line_count += 1

        # append any data left if we didn't finish on a RESET_VALUE
        if tmp_payload != []:
            log_debug("Payload for \'" + trait +"\' stored in idx " + str(self.payload_index))
            self.payload_data[self.payload_index] = tmp_payload
            used_indices.append(self.payload_index)
            self.payload_index += 1
        # allow the trait value to point to the 'block# indices
        self.payload_meta[trait] = used_indices
        return


    def gen_payload_meta(self):
        """
        add all svg data to payloads that can be searched up via trait keys
        """
        payload_str = ""
        self.payload_data = {}
        
        # SVG start until color
        payload_str = ""
        payload_str += SVG_start
        payload_str += COLOUR_STYLE_START 
        # add start
        self.append_to_payload(payload_str, 'startcolour')
        # add color
        for c in self.nft_attributes["colour"]:
            payload_str = c
            self.append_to_payload(payload_str, c)
        # end color
        self.append_to_payload(COLOUR_STYLE_END, 'endcolour')
        # add the rest
        order = ["neck","id","special","head_shadow","head","hats", "ears", "mouths", "eyes"]
        known_traits = []
        for o in order:
            # Add each trait to payload, you can reference it with payload_meta
            for x in self.nft_attributes[o]:
                # check for duplicates
                if x in known_traits:
                    raise Exception("Duplicate trait \'"+x+"\'! found in \'" + o + "\'")
                known_traits.append(x)
                # append payload
                self.append_to_payload(self.nft_traits[x]["data"], x)
        # apppend end
        self.append_to_payload(SVG_end, 'end')
        # save data
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
        return "TEST5ba13e49e3877ef371be591eb1482bd8261d66a4c489a9b522bc"

    def create_cardano_nft(self):
        policyid = self.gen_721_policy()
        n = Nft(policyid)

        for i in self.nft_set_data:
            log_error(i)
            nft_name = i
            i = int(i, 16)
            
            payload_refs = self.nft_set_data[nft_name]["refs"]
            
            nft_payload = None
            if i < len(self.payload_data):
                nft_payload = self.payload_data[i]

            props = self.nft_set_data[nft_name]["meta"]
            cardano_meta = n.generate_nft(nft_name=nft_name, payload_ref=i, nft_payload=nft_payload, nft_references=payload_refs, properties=props)
            self.cardano_nft_meta[nft_name] = cardano_meta
            #
            f = OUTPUT_DIR + nft_name + ".json"
            write_json(f, cardano_meta)
            # check file size
            s = os.path.getsize(f)
            if s > MAX_PAYLOAD_BYTES:
                raise Exception("File \'" + f + "\' has a size of " + str(s) + " larger than defined max \'" + str(MAX_PAYLOAD_BYTES) + "\'")