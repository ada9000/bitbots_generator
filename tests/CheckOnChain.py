
import sys
sys.path.append('../src')

from BlockFrostTools import BlockFrostTools
from Utility import int_to_hex_id, write_json

import os
import urllib.parse

max = 7
policy = "6cb2a0b7a8c3fd5760a5aeb223cc3f24b6c7c1719f43c01901b34265"

b = BlockFrostTools();

dirLoc = "_chainSVGTEST" + policy
os.mkdir(dirLoc)

for i in range(max):
    id = int_to_hex_id(i)
    searchFor = "Bitbot 0x" + id
    svg =  b.onchain_nft_to_svg(policy, searchFor)
    filepath = dirLoc + "/" + id + ".svg"
    with open(filepath, 'w') as f:
        f.write(svg)