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
NFT_META_JSON = "nft-meta.json"
NFT_DATA_JSON = "nft-data.json"
NFT_WEIGHTS_JSON = "nft-weights.json"
NFT_MINT_STATS_JSON = OUTPUT_DIR + "_nft-mint-stats.json"

# XML and SVG consts
XML_tag = '<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?>\n<!DOCTYPE svg PUBLIC \"-//W3C//DTD SVG 1.1//EN\" \"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd\">'
SVG_start = '\n<svg width=\"100%\" height=\"100%\" viewBox=\"0 0 5906 5906\" version=\"1.1\" xmlns=\"http://www.w3.org/2000/svg\" xmlns:xlink=\"http://www.w3.org/1999/xlink\" xml:space=\"preserve\" xmlns:serif=\"http://www.serif.com/\" style=\"fill-rule:evenodd;clip-rule:evenodd;stroke-linejoin:round;stroke-miterlimit:2;\">'
SVG_end = '</svg>'

# colour consts used to replace SVG colours with variables
BASE_COLOUR = 'style="fill:rgb(219,212,255);"'
BASE_COLOUR_REPLACE = 'class="base_colour"'
COLOUR_STYLE_START = '<style> .base_colour '
COLOR_STYLE_DEFAULT = '{fill: #DBD4FF}'
COLOUR_STYLE_END = ' </style>'

# dynamic colours
BASE_COLOUR_LIST = ["#dbd4ff", "#ffe0e0", "#ebffe0", "#e0fcff", "#ebda46", "#696969"] # TODO find better colours

WIRE_1_COLOUR_LIST = []
WIRE_1_DARK_COLOUR_LIST = [] # just wire 1 but with 20% transparent black overlay 
WIRE_2_COLOUR_LIST = []
WIRE_2_DARK_COLOUR_LIST = []

# attribute order
ATTRIBUTE_ORDER = ["neck", "head", "hats", "ears", "mouths", "eyes", "special"]
ATTRIBUTES_WITH_WEIGHTS = ["hats", "ears", "mouths", "eyes", "special"]

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

    # Turn this file into business logic and server
    # Add API
    # Create react page for front-end
    # TODO where is special?
    # TODO turn the whole codebase into a class
    # TODO methods
    #       generate # does everything

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

# classes---------------------------------------------------------------------
class Bitbots:
    def __init__(self, max_mint:int=8192, max_payload_bytes:int=12000, reset:bool=True):
        self.max_mint = max_mint
        self.max_payload_bytes = max_payload_bytes
        self.nft_meta = {}
        self.nft_stats = {}
        self.nft_weights = {}
        self.nft_attributes = {}
        self.nft_data = {}
        self.nft_mint_data = {} #metadata for mint
        # generate nft
        self.generate(reset)

    def generate(self, reset:bool=True):
        if not reset:
            return

        self.clean()
        self.populate_nft_from_input()
        self.update_weights()
        self.weighted_rand()
        
        self.make_svgs_from_nft_data()
        self.size_test()

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

    def populate_nft_from_input(self):
        """ generate metadata based of directory structure and filenames """
        # for each file in our INPUT_DIR, create a nft data entry (key)
        # then for each file in that dir get extract the metadata and svg payload
        for dir_name in os.listdir(INPUT_DIR):
            sub_dir_path = INPUT_DIR + '/' + dir_name
            sub_nft_data = {}
            sub_items = []
            # for each svg file inside a sub directory
            item_number = 0
            for file in os.listdir(sub_dir_path):
                # Append 'none' traits type once to each attribute
                if item_number == 0:
                    if dir_name in ATTRIBUTES_WITH_WEIGHTS:
                        # add none type
                        none_type_name = "no_" + dir_name + ".svg"
                        data = {"weight":DEFAULT_WEIGHT, "max":self.max_mint,"current":"","id":item_number,"type":dir_name, "data":""}
                        sub_items.append(none_type_name)
                        sub_nft_data[none_type_name] = data
                        
                item_number += 1
                filepath = sub_dir_path + '/' + file
                skip_svg = False
                # open the svg file
                with open(filepath, 'r') as f:
                    data = f.read()
                    # remove all double or more whitespace substrings strings
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
                    data = svg_str

                    # segregate data into segments
                    segments = []
                    segment_count = 0
                    current_segment = ""
                    for x in data:
                        current_segment += x
                        if sys.getsizeof(current_segment) >= self.max_payload_bytes:
                            segment_count += 1
                            segments.append(current_segment)
                            current_segment = ""
                    
                    if current_segment != "":
                        segment_count += 1
                        segments.append(current_segment)

                # name the json entry
                data = {"weight":DEFAULT_WEIGHT, "max":"","current":"","segments":segment_count,"id":item_number,"type":dir_name, "data":segments}
                sub_items.append(file.replace('.svg',''))
                sub_nft_data[file.replace('.svg','')] = data
            
            # add dir and 
            self.nft_attributes[dir_name] = len(sub_items)
            self.nft_meta[dir_name] = sub_nft_data

            # add colours
            data = {}
            for i, col in enumerate(BASE_COLOUR_LIST):
                data[col] = {"weight":"", "max":"","current":"","id":i,"type":"colour"}
                self.nft_meta["colour"] = data    

    def make_svg(self, inner_svg:str, style:str, filename:str):
        """ create a svg file from given paramaters """
        svg_str = XML_tag + "\n" + SVG_start + "\n" 
        svg_str += style + "\n"
        svg_str += inner_svg + "\n" + SVG_end

        with open(filename, "w") as f:
            f.write(svg_str)
    

    def payload_to_str(self, payload):
        data = ""
        for x in payload:
            data += x
        return data


    def make_svgs_from_nft_data(self):
        for n in self.nft_data:

            # make inner svg
            neck = self.payload_to_str( self.nft_meta["neck"]["neck"]["data"] )
            head = self.payload_to_str( self.nft_meta["head"]["head"]["data"] )

            # TODO testing special
            special_attribute = self.nft_data[n]["props"][4]
            special = self.payload_to_str( self.nft_meta["special"]["lobster"]["data"])
            inner_svg = neck + special + head
            #inner_svg = neck + head
            
            for i, attribute in enumerate(ATTRIBUTES_WITH_WEIGHTS):
                # TODO ignoring special
                if attribute == "special":
                    break

                trait = self.nft_data[n]["props"][i]
                inner_svg += self.payload_to_str( self.nft_meta[attribute][trait]["data"] )


            # make style
            col = self.nft_data[n]["colour"]
            style = COLOUR_STYLE_START + "{fill: " + col + "}"+ COLOUR_STYLE_END

            # name and create file
            filename = OUTPUT_DIR + str(n) + ".svg"
            self.make_svg(inner_svg, style, filename)
    

    def update_weights(self):
        # init weights load them if they exists
        weights = {}
        if os.path.isfile(NFT_WEIGHTS_JSON):
            weights = load_json(NFT_WEIGHTS_JSON)
        

        # for each item in the jsonfile
        for trait in self.nft_meta.keys():
            for item in self.nft_meta[trait].keys():
                # if the item is not in weights add it to weights json
                if item not in weights.keys():
                    weights[item] = {"weight":DEFAULT_WEIGHT, "max":self.max_mint}
                # if weights or max need updating, update them
                if self.nft_meta[trait][item]["weight"] != weights[item]["weight"]:
                    self.nft_meta[trait][item]["weight"] = weights[item]["weight"]
                if self.nft_meta[trait][item]["max"] != weights[item]["max"]:
                    self.nft_meta[trait][item]["max"] = weights[item]["max"]
        
        # save weights in a json file (user can edit them)
        self.nft_weights = weights
        write_json(NFT_WEIGHTS_JSON, weights)


    def weighted_rand(self):
        nfts = {}
        stats = {}

        while len(nfts) != self.max_mint:
            # run inner loop that picks properties and creates a unique id based on props (hex_hash)
            hex_hash, properties, colour = self.weight_inner()  
            # check for duplicates, and rerun until our new hex has is unique
            if hex_hash in nfts.keys():
                while hex_hash not in nfts.keys():
                    hex_hash, properties, colour = self.weight_inner()  
            
            # collect stats
            for x in properties:
                if x not in stats.keys():
                    stats[x] = 1
                else:
                    stats[x] += 1
            
            if colour not in stats.keys():
                stats[colour] = 1
            else:
                stats[colour] += 1

            # gen nft
            nfts[hex_hash] = {"props":properties, "colour":colour}

        print("Created " + str(self.max_mint) + " nfts")
        stats = {"stats":stats, "nfts":nfts}
        write_json(NFT_MINT_STATS_JSON, stats)
        self.nft_stats = stats
        self.nft_data = nfts


    def weight_inner(self):
        hex_hash = "0x"

        properties = []
        # this loop generates nfts based of weight values for traits within each attribute
        for attribute in ATTRIBUTES_WITH_WEIGHTS:
            traits = [] 
            weights = []
            for trait in self.nft_meta[attribute]:
                traits.append(trait)
                weights.append(self.nft_meta[attribute][trait]["weight"])
            
            # select a weighted random trait
            selection = random.choices(traits, weights)[0]
            properties.append(selection)
            
            # find the traits attribute type
            attribute_type = ""
            for tmp in ATTRIBUTES_WITH_WEIGHTS:
                if selection in self.nft_meta[tmp].keys():
                    attribute_type = tmp

            # convert the trait id to hexadecimal and append it to the hex_hash identifier, also add some padding
            hex_hash += str(hex(self.nft_meta[attribute_type][selection]["id"])[2:]).zfill(2)
            
            # add random weighted colour here
            traits = []
            weights = []
            for col in BASE_COLOUR_LIST:
                traits.append(col)
                weights.append(self.nft_meta["colour"][col]["weight"])
            colour = random.choices(traits, weights)[0]
            # add colour to hex hash
            hex_hash += str(hex(self.nft_meta["colour"][colour]["id"])[2:]).zfill(2)

        return hex_hash, properties, colour

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
        json_str = json.dumps(self.nft_meta, ensure_ascii=False, indent=4)
        utf_size = len(json_str.encode('utf-8'))
        print("UTF size of meta file ~" + str(utf_size / 1000.0 ) + "kB")