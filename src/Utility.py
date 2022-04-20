import json
import logging
import re
import os
from subprocess import Popen, PIPE, STDOUT
logging.basicConfig(level=logging.DEBUG)

# consts ---------------------------------------------------------------------
NEW_CIP = "payload"
MAINNET = "--mainnet"
TESTNET = "--testnet-magic 1097911063"
NETWORKS = [MAINNET, TESTNET]
FILES_DIR = "../files/"
PROJECT_DIR = FILES_DIR + "projects/"
WALLET_DIR = FILES_DIR + "wallets/"
CARDANO_CLI_PATH = "cardano-cli"
EMPTY_BYTE_STRING = "b\'\'"

# consts ---------------------------------------------------------------------
# logging colours
COLOR_RESET = '\033[0m'
COLOR_CYAN = '\033[0;36m'
COLOR_YELLOW = '\033[1;33m'
COLOR_RED = '\033[1;31m'

# make missing dirs -----------------------------------------------------------
if not os.path.isdir(FILES_DIR):
    os.mkdir(FILES_DIR)
if not os.path.isdir(PROJECT_DIR):
    os.mkdir(PROJECT_DIR)
if not os.path.isdir(WALLET_DIR):
    os.mkdir(WALLET_DIR)

# setup logggin ---------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(PROJECT_DIR + "debug.log"),
        logging.StreamHandler()
    ]
)

# logging --------------------------------------------------------------------
def log_debug(msg:str):
    msg = " " + COLOR_YELLOW + msg + COLOR_RESET
    logging.debug(msg)
    pass

def log_info(msg:str):
    msg = " " + COLOR_CYAN + msg + COLOR_RESET
    logging.info(msg)

def log_error(msg:str):
    msg = " " + COLOR_RED + msg + COLOR_RESET
    logging.info(msg)

# files ----------------------------------------------------------------------
def read_file_return_data(filepath):
    data = {}
    with open(filepath) as f:
        data = json.load(f)
    return data
 
def write_json(filepath, data):
    #TODO put mutex here?
    with open(filepath, 'w', encoding='utf-8') as f:
        #json.dump(data, f, ensure_ascii=False, indent=4)
        json.dump(data, f, ensure_ascii=False, indent=None)
    return

def check_files_exist(files:list):
    """
    Check a list of files and return True if they all exist,
    return False if one or more don't exist
    """
    for f in files:
        if os.path.isfile(f) == False:
            return False
    return True

# bash commands --------------------------------------------------------------
def cmd_out(cmd):
    """ get the result of a shell command """
    p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True)
    res =  p.stdout.read()
    # if error raise exception
    error_str = "Error"
    if error_str in str(res):
        log_error("Error" + str(res))
    return res

# formating ------------------------------------------------------------------
def replace_b_str(msg):
    """ remove 'b' token and single quote from a str """
    msg = str(msg)
    # use regex to match all text between b'<target>'
    re_res = re.findall(r'b\'(.*?)\'', msg)
    for i, s in enumerate(re_res):
        if i == 0:
            msg = s
        else:
            msg += ','
            msg += s
    # replace any of the following symbols
    msg = msg.replace('\'','')
    msg = msg.replace('[','')
    msg = msg.replace(']','')
    return msg

# Cardano conversions --------------------------------------------------------
def ada_to_lace(x:float):
    return x * 1000000

def lace_to_ada(x:float):
    return x / 1000000

# MISC -----------------------------------------------------------------------
def int_to_hex_id(x:int):
    return hex(x)[2:].zfill(4).upper()
