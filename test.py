import os
import json
import random

INPUT_DIR = "input"
OUTPUT_DIR = "output/"
JSON_OUT = "meta.json"

XML_tag = '<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?>\n<!DOCTYPE svg PUBLIC \"-//W3C//DTD SVG 1.1//EN\" \"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd\">'
SVG_start = '\n<svg width=\"100%\" height=\"100%\" viewBox=\"0 0 5906 5906\" version=\"1.1\" xmlns=\"http://www.w3.org/2000/svg\" xmlns:xlink=\"http://www.w3.org/1999/xlink\" xml:space=\"preserve\" xmlns:serif=\"http://www.serif.com/\" style=\"fill-rule:evenodd;clip-rule:evenodd;stroke-linejoin:round;stroke-miterlimit:2;\">'
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



def get_meta():
    metadata = {}
    meta = {}

    for dir_name in os.listdir(INPUT_DIR):
        sub_dir_path = INPUT_DIR + '/' + dir_name
        sub_metadata = {}
        total_items = 0
        for file in os.listdir(sub_dir_path):
            total_items += 1        
            filepath = sub_dir_path + '/' + file
            # extract svg as data

            skip_svg = False

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

            # name the json entry
            sub_metadata[file.replace('.svg','')] = data
        
        meta[dir_name] = total_items
        metadata[dir_name] = sub_metadata
    
    print(meta)
    return meta, metadata

def make_svg(inner_svg:str, style:str, filename:str):
    svg_str = XML_tag + " " + SVG_start + "\n" 
    svg_str += style + "\n"
    svg_str += inner_svg + " " + SVG_end
    with open(filename, "w") as f:
        f.write(svg_str)
    return

if __name__ == "__main__":
    meta, svg_meta = get_meta()

    with open(JSON_OUT, 'w', encoding='utf-8') as f:
        json.dump(svg_meta, f, ensure_ascii=False, indent=4)

    # test
    neck = svg_meta["neck"]["neck"]
    head = svg_meta["head"]["head"]
    eyes = svg_meta["eyes"]["void"]
    hat = svg_meta["hats"]["swiss_cheese_plant"]
    hat = svg_meta["hats"]["yellow_cake"]
    ears = svg_meta["ears"]["ram"]
    mouth = svg_meta["mouths"]["simple"]
    mouth = svg_meta["mouths"]["warning_patch_fluid"]
    
    inner_svg = neck + head + hat + mouth + ears + eyes
    #style = COLOUR_STYLE_START + COLOR_STYLE_DEFAULT + COLOUR_STYLE_END
    #make_svg(inner_svg, style, "test_basic.svg")

    # remove all files 
    for file in os.listdir(OUTPUT_DIR):
        file = OUTPUT_DIR + file
        os.remove(file)

    for i, col in enumerate(BASE_COLOUR_LIST):
        #r = lambda: random.randint(0,255)
        #color = "%06x" % random.randint(0, 0xFFFFFF)
        #print(color)
        style = COLOUR_STYLE_START + "{fill: " + col + "}"+ COLOUR_STYLE_END
        filename = OUTPUT_DIR + "test_" + str(i) + ".svg"
        make_svg(inner_svg, style, filename)


    total = 0
    
    # calc total
    for _ in range(meta['hats']):
        for _ in range(meta['eyes']):
            for _ in range(meta['mouths']):
                for _ in range(meta['ears']):
                    total += 1

    print("Total in set = " + str(total))


    # segregate files over 10kb into multiple files

    # add weighted randomness to generation

    # put nfts in output folder

    # view all nfts