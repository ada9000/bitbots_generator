import os
import json
import random
import base64

from numpy.random import choice

INPUT_DIR = "input"
OUTPUT_DIR = "output/"
JSON_OUT = "meta.json"

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

PROPERTY_ORDER = ["neck", "head", "hats", "ears", "mouths", "eyes", "special"]

REFRESH_META = True

MAX_PAYLOAD_SIZE_BYTES = 12000


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
        for file in os.listdir(sub_dir_path):
            filepath = sub_dir_path + '/' + file
            skip_svg = False
            # open the svg file
            with open(filepath, 'r') as f:
                #data = f.read().replace('\n','')
                data = f.read()
                # remove all double or more whitespace substrings strings
                new_str = ""
                data_segments = []
                segment_count = 0
                # remove the XML tag the SVG endtag and all newlines
                data = data.replace(XML_tag,'')
                data = data.replace(SVG_end,'')
                data = data.replace('\n', '')
                # replace svg base colours with dynamic method
                data = data.replace(BASE_COLOUR, BASE_COLOUR_REPLACE)
                # loop though the string 
                for i in range(len(data)):
                    # remove svg tag
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
                    
                    # segregate data into payloads due to 16kb limit. Also add data to payload
                    # if we are at the last element
                    if len(new_str.encode('utf-8')) > MAX_PAYLOAD_SIZE_BYTES:
                        data_segments.append(new_str)
                        segment_count += 1
                        new_str = ""
                    elif i == len(data) - 1:
                        data_segments.append(new_str)
                        segment_count += 1
                
                # set data to the new refactored data
                data = new_str
            
            # name the json entry
            data = {"weight":10, "max":9000,"current":0,"segments":segment_count, "data":data_segments}
            sub_items.append(file.replace('.svg',''))
            sub_nft_data[file.replace('.svg','')] = data
        
        # add dir and 
        meta[dir_name] = {"count":len(sub_items)}
        nft_data[dir_name] = sub_nft_data
        
    return meta, nft_data


def make_svg(inner_svg:str, style:str, filename:str):
    """ create a svg file from given paramaters """
    svg_str = XML_tag + " " + SVG_start + "\n" 
    svg_str += style + "\n"
    svg_str += inner_svg + " " + SVG_end
    with open(filename, "w") as f:
        f.write(svg_str)
    return

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

    total = 0
    
    # calc total
    for _ in range(meta['hats']):
        for _ in range(meta['eyes']):
            for _ in range(meta['mouths']):
                for _ in range(meta['ears']):
                    total += 1

    print("Total in set = " + str(total))


def weighted_rand(meta, svg_meta):
    pass

def clean():
    # remove all files 
    for file in os.listdir(OUTPUT_DIR):
        file = OUTPUT_DIR + file
        os.remove(file)



if __name__ == "__main__":
    meta, svg_meta = generate_meta()

    # size of string calcs for rough checks
    json_str = json.dumps(svg_meta, ensure_ascii=False, indent=4)
    utf_size = len(json_str.encode('utf-8'))
    print("UTF size = " + str(utf_size / 1000.0 ) + "kB")

    # write json to file
    if REFRESH_META == True:
        with open(JSON_OUT, 'w', encoding='utf-8') as f:
            json.dump(svg_meta, f, ensure_ascii=False, indent=4)

    clean()
    print(meta)

    #test_a(meta, svg_meta)

    #[x] segregate files over 12kb into multiple files
    #[ ] weighted_rand(meta, svg_meta)
    #[ ] add weighted randomness to generation
    #[ ] put nfts in output folder
    #[ ] view all nfts