import os
import time

from blockfrost import ApiError, BlockFrostIPFS
from dotenv import load_dotenv

from Utility import *


class IpfsManager:
    def __init__(self):
        load_dotenv()
        self.apiKey = "***REMOVED***" #os.getenv('IPFS')
        if self.apiKey == None:
            raise Exception("No 'IPFS' key Update .env")
        # init api

        self.ipfs = BlockFrostIPFS(
            project_id=self.apiKey
        )


    def pin_from_file(self):
        with open("./ipfs.txt", "r") as file:
            ipfsHashes = file.readlines();



        for hash in ipfsHashes:
            hash;

    
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
            print("remove result:", res)
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
            page = 1
            pinned = self.ipfs.pined_list(page=page)
            all = []
            while len(pinned) > 0:
                print("page:", page)
                pinned = self.ipfs.pined_list(page=page)
                page += 1
                for x in pinned:
                    all.append(x)

            print("total:")
            print(len(all))

            return all

        except ApiError as e:
            log_error(str(e))
        return []

    def removed_not_minted(self):
        storedInIPFS = self.get_all_pinned();

        hashesToKeep = []
        with open('ipfs.txt', 'r') as file:
            # Read the file as a list of strings
            hashesToKeep = [line.rstrip('\n') for line in file]

        print("lenStored", len(storedInIPFS))
        print("lenHashes", len(hashesToKeep))

        count = 0
        for x in storedInIPFS:
            if x.ipfs_hash not in hashesToKeep:
                print("removing", x.ipfs_hash)
                self.remove(file_hash=x.ipfs_hash)
                count +=1

        print("removed", count)


    def remove_all_pinned_TEST_ONLY(self):
        pinned = self.get_all_pinned()
        for i in pinned:
            time.sleep(0.02)
            self.remove(i.ipfs_hash)


