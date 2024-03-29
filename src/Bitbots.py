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
from DbComms import NFT_STATUS_TABLE, STATUS_AIRDROP, DbComms
from Ipfs import IpfsManager
# local files
from Nft import *
from Utility import *
from dotenv import load_dotenv
# consts ---------------------------------------------------------------------
# files
INPUT_DIR = "../input-mainnet/"

#------------------------------------------------------------------------------
# XML and SVG consts
XML_tag = '<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?>\n<!DOCTYPE svg PUBLIC \"-//W3C//DTD SVG 1.1//EN\" \"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd\">'
SVG_start = '<svg width=\"973\" height=\"973\" viewBox=\"0 0 5906 5906\" version=\"1.1\" xmlns=\"http://www.w3.org/2000/svg\" xmlns:xlink=\"http://www.w3.org/1999/xlink\" xml:space=\"preserve\" xmlns:serif=\"http://www.serif.com/\" style=\"fill-rule:evenodd;clip-rule:evenodd;stroke-linejoin:round;stroke-miterlimit:2;\">'
SVG_end = '</svg>'
# colour consts used to replace SVG colours with variables
BASE_COLOUR = 'style="fill:rgb(219,212,255);"'
BASE_COLOUR_REPLACE = 'class="base_colour"'
COLOUR_STYLE_START = '<style> .base_colour {fill:'
COLOR_STYLE_DEFAULT = '{fill: #DBD4FF}' # TODO deprecated?
COLOUR_STYLE_END = '} </style>'
DARK_BG_COLOUR = "#141414;"

ANIM_START = '<g id="bg"><path id="solid" d="M5906,295.3C5906,132.319 5773.68,-0 5610.7,-0L295.3,-0C132.319,-0 0,132.319 0,295.3L0,5610.7C0,5773.68 132.319,5906 295.3,5906L5610.7,5906C5773.68,5906 5906,5773.68 5906,5610.7L5906,295.3Z" style="fill:'
ANIM_DARK  = DARK_BG_COLOUR + '"/></g>'
ANIM_MID = '"><animate id="bgAnimation" attributeName="fill" values="'
ANIM_GRADE_1 = '" dur="10s" repeatCount="indefinite" /></path> <path id="hue_b" d="M5906,295.3C5906,132.319 5773.68,-0 5610.7,-0L295.3,-0C132.319,-0 0,132.319 0,295.3L0,5610.7C0,5773.68 132.319,5906 295.3,5906L5610.7,5906C5773.68,5906 5906,5773.68 5906,5610.7L5906,295.3Z" style="fill:url(#_Linear1);"/><path id="hue_a" d="M5906,295.3C5906,132.319 5773.68,-0 5610.7,-0L295.3,-0C132.319,-0 0,132.319 0,295.3L0,5610.7C0,5773.68 132.319,5906 295.3,5906L5610.7,5906C5773.68,5906 5906,5773.68 5906,5610.7L5906,295.3Z" style="fill:url(#_Linear2);"/></g><defs><linearGradient id="_Linear1" x1="0" y1="0" x2="1" y2="0" gradientUnits="userSpaceOnUse" gradientTransform="matrix(-5906,5906,-5906,-5906,5906,0)"><stop offset="0" style="stop-color:'
# colour here
ANIM_GRADE_MID = 'stop-opacity:0.3"/><stop offset="1" style="stop-color:white;stop-opacity:0.2"/></linearGradient><linearGradient id="_Linear2" x1="0" y1="0" x2="1" y2="0" gradientUnits="userSpaceOnUse" gradientTransform="matrix(-5906,-5906,5906,-5906,5906,5906)"><stop offset="0" style="stop-color:'
# colour here
ANIM_END = 'stop-opacity:0.3"/><stop offset="1" style="stop-color:white;stop-opacity:0.2"/></linearGradient></defs>'
MINT_MAX = 8192

# unique
MISSING_404_ID = ['0404','0000', '1404']

DEFAULT_WEIGHT = 100
MAX_PAYLOAD_BYTES = 14000
#-----------------------------------------------------------------------------

# Bitbots --------------------------------------------------------------------
class Bitbots:
    def __init__(self, max_mint:int=MINT_MAX, max_payload_bytes:int=MAX_PAYLOAD_BYTES, project:str=None, policy:str=None, adaPrice:str=None):
        log_info(f"🥳 Started Bitbot generation for project '{project}'")

        # check args
        if project == None:
            raise Exception("No project defined")
        if policy == None:
            raise Exception("No policy defined")
        
        load_dotenv()
        self.airdrop = os.getenv('AIRDROP')
        if self.airdrop == None:
            raise Exception("Missing airdrop in .env")


        # parameters
        self.max_mint = max_mint
        self.max_payload_bytes = max_payload_bytes
        self.policy = policy
        # vars
        self.variable_attributes = ["bg_effects", "colour", "bg_colour", "special", "hats", "ears", "mouths", "eyes"] #

        self.requiresDarkAndStarsBg = ['moon', 'red_planet', 'gas_giant']
        self.requiresStars = ['Mount_Matter', 'two_suns', 'stars']

        self.colours = [
            "#dbd4ff",
            "#767ECA", 
            "#90d7d5",
            "#62bb9c",
            "#90d797",
            "#ff8b8b",
            "#f2b5ff",
            "#e59a54",
            "#e55454",
            "#ffd700",
            "#696969",
            "#ffffff",
            "#5498e5",
            ]
        self.wire_colours = [
            ("#009bff","#fff800"),
            ("#ff0093","#009bff"),
            ("#62bb7f","#bb6862")
            ]

        self.bg_colours = [
            DARK_BG_COLOUR,
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
        # ipfs
        self.ipfs = IpfsManager()

        # define files
        self.traits_meta_file       = self.project_dir + "_nft-trait-meta.json"
        self.attributes_meta_file   = self.project_dir + "_nft-attributes-meta.json"
        self.nft_weights_file       = self.project_dir + "_nft-weights.json"
        self.nft_payload_file       = self.project_dir + "_nft-payload.json"
        self.nft_rarity_file        = self.project_dir + "_nft-rarity.json"
        self.nft_grammar_file       = self.project_dir + "_grammar.json"
       
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
        return {'attribute':attribute, 'id':id_num, 'weight':DEFAULT_WEIGHT, 'max':self.max_mint, 'data':data, 'current':0, 'percentage':0}


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
                #if attribute == "hats":
                #    trait = "Default"
                #else:
                trait = "no_" + attribute
                self.nft_traits[trait] = self.nft_meta_inner(attribute, id_num, data)
                id_num += 1
                traits.append(trait)

                # add custom traits ---------------------------------------------------
                if attribute == 'special':
                    trait = "headless"
                    self.nft_traits[trait] = self.nft_meta_inner(attribute, id_num, "")
                    self.nft_traits[trait]['weight'] = 0
                    id_num += 1
                    traits.append(trait)

                if attribute == 'special':
                    trait = "unlimited_power"
                    self.nft_traits[trait] = self.nft_meta_inner(attribute, id_num, "")
                    self.nft_traits[trait]['weight'] = 0
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
        pretty_write_json(self.traits_meta_file, self.nft_traits)
        pretty_write_json(self.attributes_meta_file, self.nft_attributes)


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
        pretty_write_json(self.nft_weights_file, weights)

    # payloads ---------------------------------------------------------------
    def find_payload_refs(self, payload_trait):
        """ helper function to find and return payload references to a trait """
        res = []
        for i in self.payload_meta[payload_trait]:
            res += [i]
        return res

    def find_refs_for_props(self, properties, nft_id):
        """ 
        helper function to generate refs for a give set of nft properties 
        This is the best place to modify the nft
        """
        refs = []
        # bitbot colour ------------------------------------------------------
        refs += self.find_payload_refs('startcolour') # TODO
        refs += self.find_payload_refs(properties['colour']) # TODO HERE
        refs += self.find_payload_refs('endcolour')
        
        refs += self.find_payload_refs('about')
        # animated background ------------------------------------------------
        # anim_start, bg_colour, anim_mid, bg_array, anim_grade_1, grade1_colour, anim_grade_mid, grade2_colour, anim_end


        refs += self.find_payload_refs('anim_start')

        if properties['bg_colour'] == DARK_BG_COLOUR or properties['bg_effects'] in self.requiresDarkAndStarsBg:
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
            elif properties['bg_colour'] == "#3E51FF;":
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
                    if x != '':
                        refs += self.find_payload_refs(x)
                for x in test[:index]:
                    if x != '':
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
        if properties['bg_effects'] in self.requiresStars:
            refs += self.find_payload_refs('shooting_stars_extra')
            refs += self.find_payload_refs(properties['bg_effects'])
        elif properties['bg_effects'] in self.requiresDarkAndStarsBg:
            refs += self.find_payload_refs('shooting_stars')
            refs += self.find_payload_refs(properties['bg_effects']) 
        else:
            refs += self.find_payload_refs(properties['bg_effects']) 

        # neck
        refs += self.find_payload_refs('neck')

        # silent traits ------------------------------------------------------
        if random.random() < 0.01:
            log_info("Mark of Pixel added")
            refs += self.find_payload_refs('mark_of_pixel')
        if random.random() < 0.02:
            log_info("Not a bot!")
            refs += self.find_payload_refs('not_a_bot')
        if random.random() < 0.008:
            log_info("Bugs added")
            refs += self.find_payload_refs('bug')

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

        
        # unique nfts here
        if nft_id in MISSING_404_ID or properties['special'] == 'headless': # TODO implement or remove headless?
            refs += self.find_payload_refs('end')
            return refs

        # head shadow and other traits ---------------------------------------
        refs += self.find_payload_refs('head_shadow')

        # if special is special frog!
        if properties['special'] == 'unlimited_power':
            refs += self.find_payload_refs('freg')
            refs += self.find_payload_refs('froggo')
        else:
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
        fullUUID = "0x"

        properties = {}
        # this loop generates nfts based of weight values for traits within each attribute
        for attribute in self.variable_attributes:
            traits = [] 
            weights = []
            for trait in self.nft_attributes[attribute]:
                
                # check trait can be added without violating max
                current = self.nft_traits[trait]['current']
                max = self.nft_traits[trait]['max']
                if current < int(max):
                    traits.append(trait)
                    weights.append(self.nft_traits[trait]["weight"])
                else:
                    log_debug("Could not use \'" + trait + "\' as current count is " + str(current) + " and max defined is " + str(max))
        
            # select a weighted random trait
            trait = random.choices(traits, weights)[0]
            properties[attribute] = trait
            # convert the trait id to hexadecimal and append it to the uuidHexHash identifier, also add some padding
            # ignore some attributes such as colour which in this case don't create a 'unique' nft
            if properties['bg_effects'] in self.requiresDarkAndStarsBg:
                properties['bg_colour'] = DARK_BG_COLOUR

            attributesToIgnoreInHexHash = ['colour','bg_colour']
            if attribute not in attributesToIgnoreInHexHash:
                uuidHexHash += str(hex(self.nft_traits[trait]["id"])[2:]).zfill(2)

            fullUUID += str(hex(self.nft_traits[trait]["id"])[2:]).zfill(2).upper()

        properties['uid'] = fullUUID # save unquie id for metadata
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
        
        # start message
        about = f"""<!--
        bit_bots
        
        Created by Cardano stake pool:
            4f3410f074e7363091a1cc1c21b128ae423d1cce897bd19478e534bb

        Build specification:
            Inside each 721 metadatum there is a 'references' tag.
            Inside some 721 metadatum a 'payload' tag can be found.
            Given all transactions for this policy ({self.policy}) you can find all payloads.
            Given all payloads you can rebuild any NFT by concatenating the related payloads in sequential order.
        -->"""
        self.append_to_payload(about, "about")

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


        order = ["bg_effects","neck","id","special","silent","head_shadow","head","hats", "ears", "mouths", "eyes"] # TODO? order matters here? I don't think so
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

        truth = f"<!-- The cake is a lie -->"
        self.append_to_payload(truth, "0SumTruth")

        # save data
        data = {"meta":self.payload_meta, "payload":self.payload_data}
        pretty_write_json(self.nft_payload_file, data)
        

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
        
        pretty_write_json(self.nft_status_file, status)
    
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

    def clean_props(self, properties):
        cleanPropNames = {}
        for x in properties:
            newAttribute = x.replace('_',' ')
            newTrait = properties[x].replace('_',' ')
            # replace no <trait> with none
            if "no " in newTrait:
                newTrait = "none"
            cleanPropNames[newAttribute] = newTrait
        return cleanPropNames
            


    def create_new_set(self):
        # minting vars TODO put inside local function
        mint_idx = 0
        current_payload_idx = 0
        last_nft_with_payload = None

        payloadsNeedAdding = True

        used_hashes = []

        nftRarityTest = {}

        traitsGrammar = []
        attributesGrammar = []

        # loop while there are still payloads to be added or nfts left to mint
        for i in range(int(self.max_mint)):
            # check current idx
            n = Nft(policyid=self.policy)
            
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
            uid = properties['uid']

            for attribute in properties:
                trait = properties[attribute]
                if attribute == 'uid':
                    continue
                self.nft_traits[trait]['current'] += 1
                self.nft_traits[trait]['percentage'] = int(self.nft_traits[trait]['current']) / int(self.max_mint)



            # apply refs
            nft_name = 'bit_bot 0x' + nft_idx # TODO note name

            refs = self.find_refs_for_props(properties, nft_idx)
            

            # weird nfts here
            # 404 ------------------------------------------------------------
            if nft_idx in MISSING_404_ID or properties['special'] == 'headless':
                # reset UUID
                used_hashes.remove(uuidHexHash)
                fullUUID = "0x"
                uuidHexHash = "0x"
                
                # 404 requires props to be none 
                ignoreKeys = ['bg_effects', 'colour', 'bg_colour', 'uid', 'special']
                properties['special'] = 'headless'
                for key, value in properties.items():
                    if key not in ignoreKeys:
                        properties[key] = 'no_' + key
                
                # build new uuid
                for key, value in properties.items():
                    # fix uid
                    if key != 'uid':
                        fullUUID += str(hex(self.nft_traits[value]["id"])[2:]).zfill(2).upper()

                    attributesToIgnoreInHexHash = ['colour','bg_colour', 'uid']
                    if key not in attributesToIgnoreInHexHash:
                        uuidHexHash += str(hex(self.nft_traits[value]["id"])[2:]).zfill(2)

                properties['uid'] = fullUUID # save unquie id for metadata
                # add updated hash
                used_hashes.append(uuidHexHash)
            #-----------------------------------------------------------------


            # clean property names for payload metadata
            properties = self.clean_props(properties)

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

            # trait rarity
            nftRarityTest[nft_idx] = properties

            # write svg ----------------------------------------------------------
            svg_file_path = self.nft_svg_dir + nft_idx + ".svg"
            self.nft_to_svg(path=svg_file_path, refs=refs)

            # get ipfs hash from block frost
            # TODO
            #ipfs_hash = self.ipfs.add(svg_file_path) # TODO TODO TODO TODO
            ipfs_hash = "TODO turn on and pin"

            # create the nft meta with the payload index
            nft_meta = n.generate_nft(
                nft_name=nft_name,
                payload_ref=current_payload_idx,
                nft_payload=nft_payload, 
                nft_references=refs, 
                properties=properties,
                ipfs_hash=ipfs_hash
            )
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


            # check file size
            s = os.path.getsize(meta_file_path)
            MAX_CARDANO_META = 15000
            if s > MAX_CARDANO_META:
                raise Exception("File \'" + meta_file_path + "\' has a size of " + str(s) + " larger than defined max \'" + str(MAX_CARDANO_META) + "\'")

            # ADD THEST TO DB TOOOOO
            # clean nft meta TODO?
            minimalMeta = n.nft_minimal_details(
                nft_name=nft_name,
                nft_references=refs, 
                properties=properties,
                uid=uid,
                )

            # update the database to include the nft details (could be more efficient, not required though)
            self.db.nft_update(
                hexId=nft_idx, 
                nftName=nft_name, 
                metaFilePath=meta_file_path, 
                svgFilePath=svg_file_path, 
                hasPayload=nft_payload, 
                ipfsHash=ipfs_hash,
                uid=uid,
                minimalMeta=minimalMeta,
                )

            if int(nft_idx, 16) < int(self.airdrop): # TODO
                self.db.setStatus(nft_idx, STATUS_AIRDROP)
            
            # nft created
            self.db.select("*", NFT_STATUS_TABLE ,"hexId='"+nft_idx+"'")
            log_info("Created " + nft_name)
            mint_idx += 1

            # if there are still payloads to be added keep looping
            if current_payload_idx > len(self.payload_data) - 1:
                payloadsNeedAdding = False

            # finaly append to grammar lists for checks later
            propertiesGrammar = n.fixProperties(properties)
            for attribute, trait in propertiesGrammar.items():
                if trait not in traitsGrammar:
                    traitsGrammar.append(trait)
                if attribute not in attributesGrammar:
                    attributesGrammar.append(attribute)

        if payloadsNeedAdding:
            log_error("Not all payloads have been added!")
            input("Press any key to continue\n> ")

        log_debug("UID -------")
        for attribute in self.variable_attributes:
            log_debug(attribute)
        log_debug("END UID ----")

        self.db.setAllGenerated()

        self.rarity(nftRarityTest)

        propertyNames = {"attributes":attributesGrammar, "traits":traitsGrammar}
        pretty_write_json(self.nft_grammar_file, propertyNames)

        log_info("Last payload is int\'" + str(last_nft_with_payload) + "\' or hex\'" + int_to_hex_id(last_nft_with_payload)+ "\'")
        return last_nft_with_payload 
    
    def rarity(self, nfts):
        rarity = {}
        log_debug("Calculating trait rarity")
        for x in self.nft_traits:
            if self.nft_traits[x]['percentage'] != 0:
                a = self.nft_traits[x]['attribute']
                p = self.nft_traits[x]['percentage']
                c = self.nft_traits[x]['current']
                rarity[x] = {"a":a, "%":p, "c":c}
        pretty_write_json(self.nft_rarity_file, rarity)