from dotenv import load_dotenv
from blockfrost import BlockFrostIPFS, ApiError
import os, time
from Utility import *

class IpfsManager:
    def __init__(self):
        load_dotenv()
        self.apiKey = os.getenv('IPFS')
        if self.apiKey == None:
            raise Exception("No 'IPFS' key Update .env")
        # init api

        self.ipfs = BlockFrostIPFS(
            project_id=self.apiKey
        )

    
    def add(self, file_path: str):
        file_hash = None
        error = False
        try:
            # get hash
            ipfs_object = self.ipfs.add(file_path)
            file_hash = ipfs_object.ipfs_hash
            print(file_hash)
        except ApiError as e:
            error = True
            log_error(str(e))

        try:
            # pin
            res = self.ipfs.pin_object(file_hash)
            file_hash = res.ipfs_hash
            status = res.state
        except ApiError as e:
            error = True
            log_error(str(e))
        
        if error:
            log_debug(f"IPFS: Issue adding and pinning '{file_hash}' generated from '{file_path}'")
            breakpoint() # remove or leave?
            time.sleep(1)
            self.add(file_path)

        return file_hash

    
    def remove(self, file_hash: str):
        # REMOVE TODO delete after testing
        try:
            res = self.ipfs.pined_object_remove(file_hash)
            file_hash = res.ipfs_hash
            status = res.state
            breakpoint()
        except ApiError as e:
            log_error(str(e))
            breakpoint()
        return


    def get(self, file_hash):
        try:
            file_data = self.ipfs.gateway(IPFS_path=file_hash).text
        except ApiError as e:
            log_error(str(e))
            breakpoint()
        return file_data


    def get_all_pinned(self):
        try:
            pinned = self.ipfs.pined_list()
        except ApiError as e:
            log_error(str(e))
        return pinned


    def remove_all_pinned_TEST_ONLY(self):
        pinned = self.get_all_pinned()
        for i in pinned:
            time.sleep(0.02)
            self.remove(i.ipfs_hash)


