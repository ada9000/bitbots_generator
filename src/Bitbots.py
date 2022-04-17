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
import shutil
from DbComms import NFT_STATUS_TABLE, DbComms
# local files
from Nft import *
from Utility import *
# consts ---------------------------------------------------------------------
# files
INPUT_DIR = "../input-mainnet/"
#------------------------------------------------------------------------------
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
# animated background consts
# anim_start, bg_colour, anim_mid, bg_array, anim_grade_1, grade1_colour, anim_grade_mid, grade2_colour, anim_end
ANIM_START = '<g id="bg"><g id="solid" transform="matrix(0.901267,0,0,0.970583,437.114,88.3231)"><path d="M6068,2951.5C6068,1272.3 4599.85,-91 2791.5,-91C983.15,-91 -485,1272.3 -485,2951.5C-485,4630.7 983.15,5994 2791.5,5994C4599.85,5994 6068,4630.7 6068,2951.5Z" style="fill:'
ANIM_DARK  = '#393939;"/></g></g>'
ANIM_MID = '"><animate id="bgAnimation" attributeName="fill" values="'
ANIM_GRADE_1 = '" dur="10s" repeatCount="indefinite" /></path></g><g id="colour45" transform="matrix(0.637292,0.637292,-0.686306,0.686306,3199.63,-851.632)"><path d="M6068,2951.5C6068,1272.3 4599.85,-91 2791.5,-91C983.15,-91 -485,1272.3 -485,2951.5C-485,4630.7 983.15,5994 2791.5,5994C4599.85,5994 6068,4630.7 6068,2951.5Z" style="fill:url(#_Linear1);"/></g><g id="colour451" serif:id="colour45" transform="matrix(0.637292,-0.637292,0.686306,0.686306,-851.632,2706.37)"><path d="M6068,2951.5C6068,1272.3 4599.85,-91 2791.5,-91C983.15,-91 -485,1272.3 -485,2951.5C-485,4630.7 983.15,5994 2791.5,5994C4599.85,5994 6068,4630.7 6068,2951.5Z" style="fill:url(#_Linear2);"/></g><g id="shadow" transform="matrix(-0.901267,2.22045e-16,-1.66533e-16,-0.970583,5468.89,5817.68)"><path d="M6068,2951.5C6068,1272.3 4599.85,-91 2791.5,-91C983.15,-91 -485,1272.3 -485,2951.5C-485,4630.7 983.15,5994 2791.5,5994C4599.85,5994 6068,4630.7 6068,2951.5Z" style="fill:url(#_Linear3);"/></g></g><defs><linearGradient id="_Linear1" x1="0" y1="0" x2="1" y2="0" gradientUnits="userSpaceOnUse" gradientTransform="matrix(6553,0,0,6085,-485,2951.5)"><stop offset="0" style="stop-color:white;stop-opacity:0"/><stop offset="1" style="stop-color:'
ANIM_GRADE_MID = 'stop-opacity:0.2"/></linearGradient><linearGradient id="_Linear2" x1="0" y1="0" x2="1" y2="0" gradientUnits="userSpaceOnUse" gradientTransform="matrix(6553,0,0,6085,-485,2951.5)"><stop offset="0" style="stop-color:white;stop-opacity:0"/><stop offset="1" style="stop-color:'
ANIM_END = 'stop-opacity:0.2"/></linearGradient><linearGradient id="_Linear3" x1="0" y1="0" x2="1" y2="0" gradientUnits="userSpaceOnUse" gradientTransform="matrix(6553,0,0,6085,-485,2951.5)"><stop offset="0" style="stop-color:white;stop-opacity:0"/><stop offset="1" style="stop-color:black;stop-opacity:0.31"/></linearGradient></defs>'

#-----------------------------------------------------------------------------
DEFAULT_WEIGHT = 1.0
MINT_MAX = 8192
MAX_PAYLOAD_BYTES = 14000
#-----------------------------------------------------------------------------
# TODO remove
INPUT_DIR = "../input-mainnet/" # TODO
#MINT_MAX = 60
#-----------------------------------------------------------------------------
# TODO
# [ ] rename meta items (remove underscore etc)
# [ ] no_<attribute> is renamed to none in metadata
# [ ] ensure only 503 are lobsters (and these are giveaways) https://cardanoscan.io/tokenPolicy/cc7888851f0f5aa64c136e0c8fb251e9702f3f6c9efcf3a60a54f419
# [ ] NFT n that holds the colour payload will be PURE nft of said colour
# [ ] Add secretes into svg?
# [ ] Remove COPY_RIGHT comments
# [ ] change input dir before realise

# Bitbots --------------------------------------------------------------------
class Bitbots:
    def __init__(self, max_mint:int=MINT_MAX, max_payload_bytes:int=MAX_PAYLOAD_BYTES, project:str=None, policy:str=None, adaPrice:str=None):
        # check args
        if project == None:
            raise Exception("No project defined")
        if policy == None:
            raise Exception("No policy defined")
        
        # parameters
        self.max_mint = max_mint
        self.max_payload_bytes = max_payload_bytes
        self.policy = policy
        # vars
        self.variable_attributes = ["bg_effects", "colour", "bg_colour", "special", "hats", "ears", "mouths", "eyes"] #

        self.colours = [
            "#dbd4ff",
            "#767ECA", 
            "#90d7d5",
            "#62bb9c",
            "#90d797",
            "#ff8b8b", 
            "#ffd700",
            "#696969",
            "#ffffff"]
        self.wire_colours = [
            ("#009bff","#fff800"),
            ("#ff0093","#009bff"),
            ("#62bb7f","#bb6862")
            ]

        self.bg_colours = [
            "#393939;",
            "#FF0063;",
            "#3E51FF;",
            "#d19494;",
            "#d1a894;",
            "#d1bd94;",
            "#d1d194;",
            "#bdd194;",
            "#a8d194;",
            "#94d194;",
            "#94d1a8;",
            "#94d1bd;",
            "#94d1d1;",
            "#94bdd1;",
            "#94a8d1;",
            "#9494d1;",
            "#a894d1;",
            "#bd94d1;",
            "#d194d1;",
            "#d194bd;",
            "#d194a8;"
        ]

        # anim_start, bg_colour, anim_mid, bg_array, anim_grade_1, grade1_colour, anim_grade_mid, grade2_colour, anim_end
        self.ref_order = ['startcolour','colour','endcolour', 'bg_colour', 'anim_mid', 'bg_array', 'anim_grade_1', 'grade1_colour', 'anim_grade_mid', 'grade2_colour', 'anim_end','anim_dark','neck','head_shadow','special','head','hats','ears','mouths','eyes'] # 
        # meta data       
        self.nft_traits = {}        # json defining each trait #TODO note this also includes count
        self.nft_attributes = {}    # json defining all attributes
        # mint/set data
        self.nft_set_data = {}
        # payload vars
        self.payload_meta = {} # about payload indices
        self.payload_data = {} # payload data
        self.payload_index = 0
        self.last_payload_size = 0
        # Cardano nft meta
        self.cardano_nft_meta = {}

        # define project dir 
        self.project_dir = PROJECT_DIR + project + "/"
        if not os.path.isdir(self.project_dir):
            os.mkdir(self.project_dir)

        # db
        self.db = DbComms(dbName=project, maxMint=self.max_mint, adaPrice=adaPrice) # TODO PASS IN PRICE
        # define files
        self.traits_meta_file       = self.project_dir + "_nft-trait-meta.json"
        self.attributes_meta_file   = self.project_dir + "_nft-attributes-meta.json"
        self.nft_weights_file       = self.project_dir + "_nft-weights.json"
        self.nft_payload_file       = self.project_dir + "_nft-payload.json"
       
        # save all meta and svg to disk
        self.nft_meta_dir         = self.project_dir + "meta/"
        self.nft_svg_dir          = self.project_dir + "svgs/"
        if not os.path.isdir(self.nft_meta_dir):
            os.mkdir(self.nft_meta_dir)
        if not os.path.isdir(self.nft_svg_dir):
            os.mkdir(self.nft_svg_dir)
        
        #self.generate()

        #print("about to clean type continue ")
        #breakpoint() # TODO testing only
        #self.clean() # TODO testing only

    def generate(self):
        # check to see if project exists
        if self.db.getAllGenerated():
            # exists return do not generate new set
            log_info("All generated, not creating new set")
            return

        # clean and get data from files
        self.nft_meta_from_files()
        # update and apply weights
        # TODO wait for user imput after weghts?
        self.update_weights()
        input("Edit the weights file now, press any key to continue...\n")
        self.update_weights()

        # add payload refs
        self.gen_payload_meta()
        #
        self.create_new_set() # TODO maybe move this to handler

    def clean(self):
        """ clean files """
        shutil.rmtree(self.nft_meta_dir)
        os.mkdir(self.nft_meta_dir)
        shutil.rmtree(self.nft_svg_dir)
        os.mkdir(self.nft_svg_dir)
        self.db.delete_db() # TODO

    # Input to metadata ------------------------------------------------------
    def nft_meta_inner(self, attribute:str, id_num:int, data:str):
        """ defines the inner metadata for each trait """
        return {'attribute':attribute, 'id':id_num, 'weight':1.0, 'max':self.max_mint, 'data':data, 'current':0}


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

        # add bg colours
        id_num = 0
        for trait in self.bg_colours: #
            self.nft_traits[trait] = self.nft_meta_inner('bg_colour', id_num, trait) #
            id_num += 1
        # add colours to the nft attributes
        self.nft_attributes['bg_colour'] = self.bg_colours #



        # save to file 
        write_json(self.traits_meta_file, self.nft_traits)
        write_json(self.attributes_meta_file, self.nft_attributes)


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


    # convert nft meta to svg ------------------------------------------------
    def nft_to_svg(self, path, refs):
        svg_str = ""
        for i in refs:
            try:
                for line in self.payload_data[i]:
                    svg_str += line
            except KeyError:
                for line in self.payload_data[str(i)]:
                    svg_str += line

        with open(path, "w") as f:
            f.write(svg_str)
        
        return svg_str
            
    
    # weights ----------------------------------------------------------------
    def update_weights(self):
        """ 
        creates NFT_WEIGHTS_FILE if it doesn't exists,
        updates metadata values to reflect those in the weights file

        useful for assigning rarity to a nft
        """
        # init weights load them if they exists
        weights = {}
        if os.path.isfile(self.nft_weights_file):
            weights = read_file_return_data(self.nft_weights_file)
        
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
        write_json(self.nft_weights_file, weights)

    # payloads ---------------------------------------------------------------
    def find_payload_refs(self, payload_trait):
        """ helper function to find and return payload references to a trait """
        res = []
        for i in self.payload_meta[payload_trait]:
            res += [i]
        return res

    def find_refs_for_props(self, properties, nft_id):
        """ helper function to generate refs for a give set of nft properties """
        refs = []
        # bitbot colour ------------------------------------------------------
        refs += self.find_payload_refs('startcolour') # TODO
        refs += self.find_payload_refs(properties['colour']) # TODO HERE
        refs += self.find_payload_refs('endcolour')
        
        # animated background ------------------------------------------------
        # anim_start, bg_colour, anim_mid, bg_array, anim_grade_1, grade1_colour, anim_grade_mid, grade2_colour, anim_end
        refs += self.find_payload_refs('anim_start')

        if properties['bg_colour'] == "#393939;":
            refs += self.find_payload_refs("anim_dark")
            # end as dark is not animated

        else:
            # animate
            refs += self.find_payload_refs(properties['bg_colour']) 

            refs += self.find_payload_refs('anim_mid')

            # define and use the correct bg array
            if properties['bg_colour'] == "#FF0063;":
                refs += self.find_payload_refs('#FF0063;')
                refs += self.find_payload_refs('#3E51FF;')
                refs += self.find_payload_refs('#FF0063;')
            if properties['bg_colour'] == "#3E51FF;":
                refs += self.find_payload_refs('#3E51FF;')
                refs += self.find_payload_refs('#FF0063;')
                refs += self.find_payload_refs('#3E51FF;')
            else:
                # for pastel colours
                test = ["#d19494;","#d1a894;","#d1bd94;","#d1d194;","#bdd194;","#a8d194;","#94d194;","#94d1a8;","#94d1bd;","#94d1d1;","#94bdd1;","#94a8d1;","#9494d1;","#a894d1;","#bd94d1;","#d194d1;","#d194bd;","#d194a8;"]
                index = 0
                start = ""
                for i, x in enumerate(test):
                    if x == properties['bg_colour']:
                        index = i
                        start = x
                for x in test[index:]:
                    refs += self.find_payload_refs(x)
                for x in test[:index]:
                    refs += self.find_payload_refs(x)
                refs += self.find_payload_refs(start)

            # add anim grades TODO COULD ALL BE ONE REF if needed
            refs += self.find_payload_refs('anim_grade_1')
            refs += self.find_payload_refs('yellow_grade')
            refs += self.find_payload_refs('anim_grade_mid')
            refs += self.find_payload_refs('blue_grade') 
            refs += self.find_payload_refs('anim_end')
        # end animated background --------------------------------------------

        # backgrounds effects
        refs += self.find_payload_refs(properties['bg_effects']) 

        # neck
        refs += self.find_payload_refs('neck')
        # add id
        
        # id tag -------------------------------------------------------------
        refs += self.find_payload_refs('id_start')
        for i, x in enumerate(nft_id):
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

        # head shadow and other traits ---------------------------------------
        refs += self.find_payload_refs('head_shadow')
        refs += self.find_payload_refs(properties['special'])
        refs += self.find_payload_refs('head')
        refs += self.find_payload_refs(properties['hats'])
        refs += self.find_payload_refs(properties['ears'])
        refs += self.find_payload_refs(properties['mouths'])
        refs += self.find_payload_refs(properties['eyes'])
        refs += self.find_payload_refs('end')
        return refs

    # random nft gen ---------------------------------------------------------
    def gen_random_props(self):
        """
        generate random properties for each vairable attribute using
        the known weights

        returns a unique hex_hash identifier and random properties
        """
        uuidHexHash = "0x"

        properties = {}
        # this loop generates nfts based of weight values for traits within each attribute
        for attribute in self.variable_attributes:
            traits = [] 
            weights = []
            for trait in self.nft_attributes[attribute]:
                
                # check trait can be added without violating max
                current = self.nft_traits[trait]['current']
                max = self.nft_traits[trait]['max']
                if current < max:
                    traits.append(trait)
                    weights.append(self.nft_traits[trait]["weight"])
                else:
                    log_debug("Could not use \'" + trait + "\' as current count is " + str(current) + " and max defined is " + str(max))
        
            # select a weighted random trait
            trait = random.choices(traits, weights)[0]
            properties[attribute] = trait
            # convert the trait id to hexadecimal and append it to the uuidHexHash identifier, also add some padding
            # ignore some attributes such as colour which in this case don't create a 'unique' nft
            attributesToIgnoreInHexHash = ['colour','bg_colour'] #
            if attribute not in attributesToIgnoreInHexHash:
                uuidHexHash += str(hex(self.nft_traits[trait]["id"])[2:]).zfill(2)

        #breakpoint()
        return uuidHexHash, properties


    # payloads ---------------------------------------------------------------
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
        # store payload TODO describe this
        for row in payload_arr:
            if line_count >= RESET_VALUE:
                log_debug("Payload for \'" + trait +"\' stored in idx " + str(self.payload_index))
                self.payload_data[self.payload_index] = tmp_payload # TODO string? THIS NEEDS TO BE STORTED IN CIP
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
            self.payload_data[self.payload_index] = tmp_payload # TODO string? for Json, but looks alright
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
        self.payload_index = 0
        self.last_payload_size = 0
        
        # SVG start until color
        payload_str = ""
        payload_str += SVG_start
        
        # COLOURS
        payload_str += '<style> .base_colour {fill:'
        # add start
        self.append_to_payload(payload_str, 'startcolour')
        # add base colour
        for c in self.nft_attributes["colour"]:
            payload_str = c
            self.append_to_payload(payload_str, c)
        
        # end base colour
        #self.append_to_payload('} .bg_colour {fill:',"colour_seperator") #



        # anim_start, bg_colour, anim_mid, bg_array, anim_grade_1, grade1_colour, anim_grade_mid, grade2_colour, anim_end
        self.append_to_payload(ANIM_START, 'anim_start')
        self.append_to_payload(ANIM_MID, 'anim_mid')
        self.append_to_payload(ANIM_GRADE_1, 'anim_grade_1')
        self.append_to_payload(ANIM_GRADE_MID, 'anim_grade_mid')
        self.append_to_payload(ANIM_END, 'anim_end')
        self.append_to_payload(ANIM_DARK, 'anim_dark')

        self.append_to_payload('#f2ff00;', 'yellow_grade')
        self.append_to_payload('#0006ff;', 'blue_grade')



        # bg colours
        for c in self.nft_attributes["bg_colour"]: #
            payload_str = c
            self.append_to_payload(payload_str, c)
 


        self.append_to_payload(COLOUR_STYLE_END, 'endcolour')
        # add the rest


        order = ["bg_effects","neck","id","special","head_shadow","head","hats", "ears", "mouths", "eyes"]
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
        write_json(self.nft_payload_file, data)
        

    # ALL THIS MIGRATE TO API MANAGER ----------------------------------------------------------------------------------------------------
    def check_hash_exists(self, hash):
        # TODO REPLACE WITH DB
        status = read_file_return_data(self.nft_status_file)
        for idx in status:
            if status[idx]['tx_hash'] == hash:
                return idx
        return None


    def check_customer(self, customer_addr):
        # TODO REPLACE WITH DB
        pass

    def set_status(self, idx, new_status=None, customer_addr=None, tx_hash=None):
        # TODO REPLACE WITH DB
        idx = str(idx)
        status = read_file_return_data(self.nft_status_file)
        try:
            status[idx]
        except KeyError:
            status[idx] = {"status":"", "tx_hash":"", "customer_addr":"", "nft_name":"extra", "meta_path":""}

        if new_status != None:
            status[idx]['status'] = new_status
        if customer_addr != None:
            status[idx]['customer_addr'] = customer_addr
        if tx_hash != None:
            status[idx]['tx_hash'] = tx_hash
        
        write_json(self.nft_status_file, status)
    
    def find_status(self, status_to_find):
        # TODO REPLACE WITH DB
        status = read_file_return_data(self.nft_status_file)
        for idx in status:
            if status[idx]['status'] == status_to_find:
                return status[idx]['tx_hash']
        return None



    def get_status(self, idx):
        # TODO REPLACE WITH DB
        idx = str(idx)
        status = read_file_return_data(self.nft_status_file)
        return status[idx]['status']

    def get_customer(self, idx):
        # TODO REPLACE WITH DB
        idx = str(idx)
        status = read_file_return_data(self.nft_status_file)
        return status[idx]['customer_addr']

    def get_meta_path(self, idx):
        # TODO REPLACE WITH DB
        idx = str(idx)
        status = read_file_return_data(self.nft_status_file)
        return status[idx]['meta_path']

    def get_meta(self, idx):
        # TODO REPLACE WITH DB
        idx = str(idx).upper()
        status = read_file_return_data(self.nft_status_file)
        try:
            _ = status[idx]
        except:
            log_error("idx error when getting meta")
            return None
        data = read_file_return_data(status[idx]['meta_path'])
        return data

    def get_svg(self, idx):
        # TODO REPLACE WITH DB

        idx = str(idx).upper()
        status = read_file_return_data(self.nft_status_file)
        try:
            _ = status[idx]
        except:
            log_error("idx error when getting svg")
            return None
        # read full file to str
        #open text file in read mode
        text_file = open(status[idx]['svg_path'], "r")
        #read whole file to a string
        data = text_file.read()
        #close file
        text_file.close()
        return data

    def get_all_names(self):
        # TODO REPLACE WITH DB

        status = read_file_return_data(self.nft_status_file)
        names = []
        for i in status:
            names.append(i)
        return names
    # ALL THIS MIGRATE TO API MANAGER ----------------------------------------------------------------------------------------------------


    def create_new_set(self):
        # minting vars TODO put inside local function
        mint_idx = 0
        current_payload_idx = 0
        last_nft_with_payload = None

        payloadsNeedAdding = True
        nftsLeftToMint = True

        used_hashes = []

        # loop while there are still payloads to be added or nfts left to mint
        while payloadsNeedAdding or nftsLeftToMint:
            # check current idx
            n = Nft(self.policy)
            
            # set index
            nft_idx = int_to_hex_id(mint_idx)

            # generate random nft
            refs = []
            # run inner loop that picks properties and creates a unique id based on props (hex_hash)
            uuidHexHash, properties = self.gen_random_props()  

            # TODO also check to ensure we don't mint more than allowed of any given trait
            # write a test but I think the hex hash does this

            # check for duplicates, and rerun until our new hex has is unique

            while uuidHexHash in used_hashes:
                log_debug("duplicate nft regenerating")
                uuidHexHash, properties = self.gen_random_props()  
            
            used_hashes.append(uuidHexHash)

            # update TRAIT meta to increase count TODO
            # properties [ attribute ] = trait
            for attribute in properties:
                trait = properties[attribute]
                self.nft_traits[trait]['current'] += 1


            # apply refs
            nft_name = 'Bitbot 0x' + nft_idx

            refs = self.find_refs_for_props(properties, nft_idx)

            # payload
            nft_payload = None
            # TODO check if NFT should have property for holding data here?
            # get the next payload found using the payload index,
            if current_payload_idx < len(self.payload_data):
                try:
                    nft_payload = self.payload_data[current_payload_idx]
                except KeyError as e:
                    nft_payload = self.payload_data[str(current_payload_idx)]
                last_nft_with_payload = mint_idx

            # create the nft meta with the payload index
            nft_meta = n.generate_nft(nft_name=nft_name, payload_ref=current_payload_idx, nft_payload=nft_payload, nft_references=refs, properties=properties)
            current_payload_idx += 1 #TODO fit more payload into one nft

            # append payloads ------------------------------------------------------------------
            if current_payload_idx < len(self.payload_data):
                valid_size = True
                while valid_size:
                    # get payload data
                    try:
                        nft_payload = self.payload_data[current_payload_idx]
                    except KeyError as e:
                        try:
                            nft_payload = self.payload_data[str(current_payload_idx)]
                        except KeyError as e:
                            valid_size = False
                    # TODO this is due to index missing fix with leading if statement before while loop
                    if valid_size == False:
                        break
                    # append more data, NFT function
                    nft_meta_tmp = n.append_more_data(meta=nft_meta, payload_ref=current_payload_idx, nft_payload=nft_payload)
                    # check if we are still under size by creating a tmp file (most accurate but slow)
                    f = self.nft_meta_dir + nft_idx + "_temp.json"
                    write_json(f, nft_meta_tmp)
                    s = os.path.getsize(f)

                    # if under size update current payload idx
                    if s < (MAX_PAYLOAD_BYTES):
                        current_payload_idx += 1
                        last_nft_with_payload = mint_idx
                        nft_meta = nft_meta_tmp
                    else:
                        # too large exit without saving new changes
                        valid_size = False
                    # remove tmp file
                    os.remove(f)

            # write meta json ----------------------------------------------------
            meta_file_path = self.nft_meta_dir + nft_idx + ".json"
            write_json(meta_file_path ,nft_meta)

            # write svg ----------------------------------------------------------
            svg_file_path = self.nft_svg_dir + nft_idx + ".svg"
            self.nft_to_svg(path=svg_file_path, refs=refs)

            # check file size
            s = os.path.getsize(meta_file_path)
            MAX_CARDANO_META = 15000
            if s > MAX_CARDANO_META:
                raise Exception("File \'" + meta_file_path + "\' has a size of " + str(s) + " larger than defined max \'" + str(MAX_CARDANO_META) + "\'")

            # update the database to include the nft details (could be more efficient, not required though)
            self.db.nft_update(hexId=nft_idx, nftName=nft_name, metaFilePath=meta_file_path, svgFilePath=svg_file_path, hasPayload=nft_payload)
            
            # nft created
            self.db.select("*", NFT_STATUS_TABLE ,"hexId='"+nft_idx+"'")
            log_info("Created " + nft_name)
            mint_idx += 1

            # if there are still nfts to be minted keep looping
            if mint_idx > self.max_mint:
                nftsLeftToMint = False
            # if there are still payloads to be added keep looping
            if current_payload_idx > len(self.payload_data) - 1:
                payloadsNeedAdding = False

        log_debug("Last payload is int\'" + str(last_nft_with_payload) + "\' or hex\'" + int_to_hex_id(last_nft_with_payload)+ "\'")

        # return the nft idx of the last nft with a payload
        self.db.setAllGenerated()
        return last_nft_with_payload 