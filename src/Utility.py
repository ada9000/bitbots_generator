import json
import logging
logging.basicConfig(level=logging.DEBUG)

# consts ---------------------------------------------------------------------
# logging colours
COLOR_RESET = '\033[0m'
COLOR_CYAN = '\033[0;36m'
COLOR_YELLOW = '\033[1;33m'
COLOR_RED = '\033[1;31m'

# functions ------------------------------------------------------------------
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

def read_file_return_data(filepath):
    data = {}
    with open(filepath) as f:
        data = json.load(f)
    return data
 
def write_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    return

