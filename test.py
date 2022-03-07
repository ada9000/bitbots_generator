import os
import json
import random
import base64
import random
import re
import sys

INPUT_DIR = "input"
OUTPUT_DIR = "output/"
JSON_OUT = "meta.json"
WEIGHTS_OUT = "weights.json"

XML_tag = '<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?>\n<!DOCTYPE svg PUBLIC \"-//W3C//DTD SVG 1.1//EN\" \"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd\">'
SVG_start = '\n<svg width=\"100%\" height=\"100%\" viewBox=\"0 0 5906 5906\" version=\"1.1\" xmlns=\"http://www.w3.org/2000/svg\" xmlns:xlink=\"http://www.w3.org/1999/xlink\" xml:space=\"preserve\" xmlns:serif=\"http://www.serif.com/\" style=\"fill-rule:evenodd;clip-rule:evenodd;stroke-linejoin:round;stroke-miterlimit:2;\">'
#SVG_start = '<svg width="100%" height="100%" viewBox="0 0 5906 5906" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" xml:space="preserve" xmlns:serif="http://www.serif.com/" style="fill-rule:evenodd;clip-rule:evenodd;stroke-linecap:round;stroke-linejoin:round;stroke-miterlimit:1.5;">'
SVG_end = '</svg>'

# to replace base use
BASE_COLOUR = 'style="fill:rgb(219,212,255);"'
BASE_COLOUR_REPLACE = 'class="base_colour"'

# to set colour for base use
COLOUR_STYLE_START = '<style> .base_colour '
COLOR_STYLE_DEFAULT = '{fill: #DBD4FF}'
COLOUR_STYLE_END = ' </style>'

# dynamic colours
BASE_COLOUR_LIST = ["#dbd4ff", "#ffe0e0", "#ebffe0", "#e0fcff", "#ebda46", "#696969"] # TODO find better colours

WIRE_1_COLOUR_LIST = []
WIRE_1_DARK_COLOUR_LIST = [] # just wire 1 but with 20% transparent black overlay 
WIRE_2_COLOUR_LIST = []
WIRE_2_DARK_COLOUR_LIST = []

ATTRIBUTE_ORDER = ["neck", "head", "hats", "ears", "mouths", "eyes", "special"]
ATTRIBUTES_WITH_WEIGHTS = ["hats", "ears", "mouths", "eyes", "special"]


MAX_MINT = 8192
MAX_PAYLOAD_SIZE_BYTES = 12000

DEFAULT_WEIGHT = 1.0

REFRESH_META = True
UPDATE_WEIGHTS = True

def generate_meta():
    """ generate metadata based of directory structure and filenames """
    nft_data = {}   # actual data
    meta = {}       # meta describing nft_data

    # for each file in our INPUT_DIR, create a nft data entry (key)
    # then for each file in that dir get extract the metadata and svg payload
    for dir_name in os.listdir(INPUT_DIR):
        sub_dir_path = INPUT_DIR + '/' + dir_name
        sub_nft_data = {}
        sub_items = []
        # for each svg file inside a sub directory
        item_number = 0
        
        for file in os.listdir(sub_dir_path):
            
            if item_number == 0:
                if dir_name in ATTRIBUTES_WITH_WEIGHTS:
                    # add none type
                    none_type_name = "no_" + dir_name + ".svg"
                    data = {"weight":"", "max":"","current":"","id":item_number,"type":dir_name, "data":""}
                    sub_items.append(none_type_name)
                    sub_nft_data[none_type_name] = data
                    
   
            item_number += 1


            filepath = sub_dir_path + '/' + file
            skip_svg = False
            # open the svg file
            with open(filepath, 'r') as f:
                #data = f.read().replace('\n','')
                data = f.read()

                # remove all double or more whitespace substrings strings
                new_str = ""

                
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
                            new_str += data[i]
                
                # remove the XML tag the SVG endtag and all newlines
                new_str = new_str.replace(XML_tag,'')
                new_str = new_str.replace(SVG_end,'')
                new_str = new_str.replace('\n', '')

                # replace svg base colours with dynamic method
                new_str = new_str.replace(BASE_COLOUR, BASE_COLOUR_REPLACE)

                # set data to the new refactored data
                data = new_str

                # segregate data into segments
                segments = []
                segment_count = 0
                current_segment = ""
                for x in data:
                    current_segment += x
                    if sys.getsizeof(current_segment) >= MAX_PAYLOAD_SIZE_BYTES:
                        segment_count += 1
                        segments.append(current_segment)
                        current_segment = ""
                
                if current_segment != "":
                    segment_count += 1
                    segments.append(current_segment)


            
            # name the json entry
            data = {"weight":"", "max":"","current":"","segments":segment_count,"id":item_number,"type":dir_name, "data":segments}
            sub_items.append(file.replace('.svg',''))
            sub_nft_data[file.replace('.svg','')] = data
        
        # add dir and 
        meta[dir_name] = len(sub_items)
        nft_data[dir_name] = sub_nft_data

        # add colours
        data = {}
        for i, col in enumerate(BASE_COLOUR_LIST):
            data[col] = {"weight":"", "max":"","current":"","id":i,"type":"colour"}
            nft_data["colour"] = data
        
    return meta, nft_data


def make_svg(inner_svg:str, style:str, filename:str):
    """ create a svg file from given paramaters """
    svg_str = XML_tag + "\n" + SVG_start + "\n" 
    svg_str += style + "\n"
    svg_str += inner_svg + "\n" + SVG_end

    with open(filename, "w") as f:
        f.write(svg_str)
    


def test_a(meta, svg_meta):
    # test a
    neck = svg_meta["neck"]["neck"]
    head = svg_meta["head"]["head"]
    eyes = svg_meta["eyes"]["void"]
    hat = svg_meta["hats"]["extended"]
    #hat = svg_meta["hats"]["yellow_cake"]
    ears = svg_meta["ears"]["ram"]
    mouth = svg_meta["mouths"]["simple"]
    mouth = svg_meta["mouths"]["warning_patch_fluid"]
    
    inner_svg = neck + head + hat + mouth + ears + eyes
    #style = COLOUR_STYLE_START + COLOR_STYLE_DEFAULT + COLOUR_STYLE_END
    #make_svg(inner_svg, style, "test_basic.svg")
    
    for i, col in enumerate(BASE_COLOUR_LIST):
        #r = lambda: random.randint(0,255)
        #color = "%06x" % random.randint(0, 0xFFFFFF)
        #print(color)
        style = COLOUR_STYLE_START + "{fill: " + col + "}"+ COLOUR_STYLE_END
        filename = OUTPUT_DIR + "test_" + str(i) + ".svg"
        make_svg(inner_svg, style, filename)

    for x in svg_meta["hats"]:
        inner_svg = neck + head +svg_meta["hats"][x] + mouth + ears + eyes
        for i, col in enumerate(BASE_COLOUR_LIST):
            style = COLOUR_STYLE_START + "{fill: " + col + "}"+ COLOUR_STYLE_END
            filename = OUTPUT_DIR + "test_" + str(x) + "-" + str(col) + ".svg"
            make_svg(inner_svg, style, filename)
    # 100 randos
    #for i in range(100)

def payload_to_str(payload):
    data = ""
    for x in payload:
        data += x
    return data


def nfts_to_svgs(meta, nfts):
    #nfts[hex_hash] = {"props":properties, "colour":colour}
    #print(nfts)
    for n in nfts:

        # make inner svg
        neck = payload_to_str( meta["neck"]["neck"]["data"] )
        head = payload_to_str( meta["head"]["head"]["data"] )
        inner_svg = neck + head
        for i, attribute in enumerate(ATTRIBUTES_WITH_WEIGHTS):
            # TODO ignoring special
            if attribute == "special":
                break

            trait = nfts[n]["props"][i]
            inner_svg += payload_to_str( meta[attribute][trait]["data"] )
        # make style
        col = nfts[n]["colour"]
        style = COLOUR_STYLE_START + "{fill: " + col + "}"+ COLOUR_STYLE_END

        # name and create file
        filename = OUTPUT_DIR + str(n) + ".svg"
        make_svg(inner_svg, style, filename)
    

def load_json(filepath):
    data = {}
    with open(filepath) as f:
        data = json.load(f)
    return data
 
    pass

def write_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    return


def update_weights(meta, total):
    weights = {}

    if os.path.isfile(WEIGHTS_OUT):
        weights = load_json(WEIGHTS_OUT)
    
    # for each item in the jsonfile
    for trait in meta.keys():
        for item in meta[trait].keys():

            # if the item is not in weights add it to weights json
            if item not in weights.keys():
                weights[item] = {"weight":DEFAULT_WEIGHT, "max":total}
            # if weights or max need updating, update them
            if meta[trait][item]["weight"] != weights[item]["weight"]:
                meta[trait][item]["weight"] = weights[item]["weight"]
            if meta[trait][item]["max"] != weights[item]["max"]:
                meta[trait][item]["max"] = weights[item]["max"]
    
    #update meta to reflect weights, return new meta
    write_json(WEIGHTS_OUT, weights)
    return meta


def weighted_rand(data):
    nfts = {}
    meta = {}

    stats = {}

    while len(nfts) != MAX_MINT:
        # run inner loop that picks properties and creates a unique id based on props (hex_hash)
        hex_hash, properties, colour = weight_inner(data)  
        # check for duplicates, and rerun until our new hex has is unique
        if hex_hash in nfts.keys():
            while hex_hash not in nfts.keys():
                hex_hash, properties, colour = weight_inner(data)  
        
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

    print("stats:")
    print(stats)
    print("Created " + str(MAX_MINT) + " nfts")
    write_json(OUTPUT_DIR + "000_nftdata.json", nfts)
    write_json(OUTPUT_DIR + "000_stats.json", stats)
    return nfts


def weight_inner(data):
    hex_hash = "0x"

    properties = []
    # this loop generates nfts based of weight values for traits within each attribute
    for attribute in ATTRIBUTES_WITH_WEIGHTS:
        traits = [] 
        weights = []

        for trait in data[attribute]:
            traits.append(trait)
            weights.append(data[attribute][trait]["weight"])
        
        # select a weighted random trait
        selection = random.choices(traits, weights)[0]
        properties.append(selection)
        
        # find the traits attribute type
        attribute_type = ""
        for tmp in ATTRIBUTES_WITH_WEIGHTS:
            if selection in data[tmp].keys():
                attribute_type = tmp

        # convert the trait id to hexadecimal and append it to the hex_hash identifier
        hex_hash += str(hex(data[attribute_type][selection]["id"])[2:]).zfill(2) # TODO pad so it's always got a leading 0 ie: 7 = 07 or E = 0E
        
        # add random weighted colour here
        traits = []
        weights = []
        for col in BASE_COLOUR_LIST:
            traits.append(col)
            weights.append(data["colour"][col]["weight"])
        colour = random.choices(traits, weights)[0]
        # add colour to hex hash
        hex_hash += str(hex(data["colour"][colour]["id"])[2:]).zfill(2)

    return hex_hash, properties, colour


def clean():
    """ clean files """
    #remove all files in OUTPUT_DIR
    for file in os.listdir(OUTPUT_DIR):
        file = OUTPUT_DIR + file
        os.remove(file)


if __name__ == "__main__":
    # gen meta and 
    meta, data = generate_meta()
    # size of string calcs for rough checks
    json_str = json.dumps(data, ensure_ascii=False, indent=4)
    utf_size = len(json_str.encode('utf-8'))
    print("UTF size = " + str(utf_size / 1000.0 ) + "kB")

    # find upper limit
    total = 0
    # calc total
    for _ in range(meta['hats']):
        for _ in range(meta['eyes']):
            for _ in range(meta['mouths']):
                for _ in range(meta['ears']):
                    total += 1
    print(meta)
    print("Total in set = " + str(total))


    # update weights
    data = update_weights(data, total)

    # write json to file
    if REFRESH_META == True:
        write_json(JSON_OUT, data)

    clean()
    nfts = weighted_rand(data)

    nfts_to_svgs(data, nfts)



    #test_a(meta, svg_meta)

    #[x] weighted_rand(meta, svg_meta)
    #[x] add weighted randomness to generation
    #[ ] segregate files over 12kb into multiple files
    #[ ] put nfts in output folder
    #[ ] view all nfts
    #[ ] TODO implement tally and other special mint options
    #[ ] TODO ignore lobster, lobster is special mint parameter for airdrop to lobster contact 
    #[ ] TODO issue with normal ears
    #[ ] in 721 no_<item> is renamed to none
    # TODO where is special?