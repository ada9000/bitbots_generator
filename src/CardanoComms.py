
MAINNET = "--mainnet"
TESTNET = "--testnet-magic 1097911063"
NETWORKS = [MAINNET, TESTNET]

class CardanoComms:
    def __init__(self, network:str, payment_addr:str):
        # check valid network
        if network not in NETWORKS:
            raise Exception("Invalid network please use one of the following \'" + str(NETWORKS) + "\'")
        
        # 
        self.network = network