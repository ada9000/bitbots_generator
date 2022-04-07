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
INPUT_DIR = "../input"
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
#-----------------------------------------------------------------------------
DEFAULT_WEIGHT = 1.0
MINT_MAX = 8192
MAX_PAYLOAD_BYTES = 14000
#-----------------------------------------------------------------------------
# TODO remove
#INPUT_DIR = "../input-testnet/"
#MINT_MAX = 60
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
    def __init__(self, max_mint:int=MINT_MAX, max_payload_bytes:int=MAX_PAYLOAD_BYTES, project:str=None, policy:str=None):
        # check args
        if project == None:
            raise Exception("No project defined")
        if project == None:
            raise Exception("No policy defined")
        
        # parameters
        self.max_mint = max_mint
        self.max_payload_bytes = max_payload_bytes
        self.policy = policy
        # vars
        self.variable_attributes = ["colour", "special", "hats", "ears", "mouths", "eyes"]
        self.colours = ["#dbd4ff", "#ffe0e0", "#ebffe0", "#e0fcff","#8395a1","#90d7d5","#62bb9c","#90d797","#ff8b8b","#ebda46", "#ffc44b","#ffd700","#696969","#ffffff"]
        self.wire_colours = [("#009bff","#fff800"), ("#ff0093","#009bff"),("#62bb7f","#bb6862")]
        self.ref_order = ['startcolour','colour','endcolour','neck','head_shadow','special','head','hats','ears','mouths','eyes']
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
        self.db = DbComms(dbName=project, maxMint=self.max_mint) # TODO PASS IN PRICE
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
        
        self.generate()

        print("about to clean type continue ")
        breakpoint() # TODO testing only
        self.clean() # TODO testing only

    def generate(self):
        # check to see if project exists TODO
        # clean and get data from files
        self.nft_meta_from_files()
        # update and apply weights
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
        #self.payload_meta[trait] = used_indices
        refs += self.find_payload_refs('startcolour')
        refs += self.find_payload_refs(properties['colour'])
        refs += self.find_payload_refs('endcolour')
        refs += self.find_payload_refs('neck')
        # add id
        
        # id start
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
        self.payload_index = 0
        self.last_payload_size = 0
        
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
        for mint_idx in range(self.max_mint): 

            # check correct
            if mint_idx >= self.max_mint:
                if current_payload_idx > len(self.payload_data):
                    return None
                else:
                    self.max_mint += 1
                    log_error("Max mint increased due to missing data that needs deploying to blockchain")

            # check current idx
            n = Nft(self.policy)
            
            # use current index
            self.payload_index
            
            # set index
            nft_idx = int_to_hex_id(mint_idx)

            # generate random nft
            nft = {}
            used_hashes = []
            refs = []
            # run inner loop that picks properties and creates a unique id based on props (hex_hash)
            hex_hash, properties = self.gen_random_props()  

            # TODO also check to ensure we don't mint more than allowed of any given trait

            # check for duplicates, and rerun until our new hex has is unique
            for h in used_hashes:
                while hex_hash not in used_hashes:
                    hex_hash, properties = self.gen_random_props()  
            # apply refs
            nft_name = 'Bitbot 0x' + nft_idx

            refs = self.find_refs_for_props(properties, nft_idx)
            # save nft with padded number i.e 0001,...,1111,...,n
            nft = {"meta":properties, "hex":hex_hash, "refs":refs}


            # payload
            nft_payload = None

            # TODO check if NFT should have property for holding data here?
            if current_payload_idx < len(self.payload_data):
                try:
                    nft_payload = self.payload_data[current_payload_idx]
                except KeyError as e:
                    nft_payload = self.payload_data[str(current_payload_idx)]
                last_nft_with_payload = mint_idx

            # nft meta
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
                    if s < MAX_PAYLOAD_BYTES:
                        current_payload_idx += 1
                        last_nft_with_payload = mint_idx
                        nft_meta = nft_meta_tmp
                    # too large exit without saving new changes
                    else:
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
            if s > MAX_PAYLOAD_BYTES:
                raise Exception("File \'" + meta_file_path + "\' has a size of " + str(s) + " larger than defined max \'" + str(MAX_PAYLOAD_BYTES) + "\'")
            # update the database to include the nft details (could be more efficient, not required though)
            self.db.nft_update(hexId=nft_idx, nftName=nft_name, metaFilePath=meta_file_path, svgFilePath=svg_file_path)
            # nft created
            self.db.select("*", NFT_STATUS_TABLE ,"hexId='"+nft_idx+"'")
            log_info("Created " + nft_name)
            mint_idx += 1
        log_debug("Last payload is int\'" + str(last_nft_with_payload) + "\' or hex\'" + int_to_hex_id(last_nft_with_payload)+ "\'")
        log_error("don't forget to generate policy first") # TODO REMOVE this comment