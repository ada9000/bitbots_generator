import colorsys

import sys
sys.path.append('../src')

from Utility import *


l = 80;
s = 80;

colours = []

for h in range(0, 360, 20):
    print(h)
    rgb = colorsys.hls_to_rgb(h/360, l/100, s/100)
    rgb_res = '#%02x%02x%02x'%(round(rgb[0]*255),round(rgb[1]*255), round(rgb[2]*255))
    colours.append(rgb_res)

write_json("colours2.json", {"colours":colours})


