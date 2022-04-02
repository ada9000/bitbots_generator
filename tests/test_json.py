import sys
sys.path.append('../src')
from Utility import *

FILE_NAME = "test.json"

write_json(FILE_NAME, {"hello":"world"} )
data = read_file_return_data(FILE_NAME)

breakpoint()

data['fizz'] = 'buzz'
write_json(FILE_NAME, data)