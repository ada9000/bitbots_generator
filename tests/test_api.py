import sys
sys.path.append('../src')
from Utility import *

from multiprocessing import Process

PRICE = 5
NFT_LEN = 60


def test_api(i):
    res = cmd_out("curl 192.168.1.95:5000/mint_price")


if __name__ == "__main__":
    for i in range(1000):
        print(i)
        p = Process(target=test_api, args=(i,))
        p.start()
        #time.sleep(0.2)
