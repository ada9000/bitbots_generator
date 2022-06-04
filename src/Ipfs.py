from dotenv import load_dotenv
from blockfrost import BlockFrostIPFS, ApiError
import os
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
        file_data = None
        ipfs_object = None

        error = False

        try:
            ipfs_object = self.ipfs.add(file_path)
            file_hash = ipfs_object.ipfs_hash
            #print(file_hash)
        except ApiError as e:
            error = True
            log_error(str(e))

        try:
            file_data = self.ipfs.gateway(IPFS_path=file_hash).text
            #print(file_data)
        except ApiError as e:
            error = True
            log_error(str(e))

        # TODO PIN!


        if error:
            log_error("IPFS error hit")
            breakpoint()
            self.add()
        else:
            # set success in db 
            # add parameters
            pass

        return file_hash
