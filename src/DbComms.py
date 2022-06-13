from cmath import log
from dotenv import load_dotenv
import os
import datetime
import random
import json
import base64
from mysqlx import Column
from Utility import ada_to_lace, int_to_hex_id, lace_to_ada, log_debug, log_error, read_file_return_data
import mysql.connector
from threading import Lock

HOST='localhost'
USER='jack'

STATUS_AVAILABLE            = "available"
#STATUS_AWAITING_PAYMANET    = "awaiting-payment"
STATUS_AWAITING_MINT        = "awaiting-mint"
STATUS_IN_PROGRESS          = "minting" # this state is required in case of hard failure, in which something may or maynot have minted
STATUS_SOLD                 = "sold"
STATUS_AIRDROP              = "airdrop"
STATUS_ISSUE                = "issue"

# status list to validate correct status is being used
STATUS_LIST = [STATUS_AVAILABLE, STATUS_AWAITING_MINT, STATUS_IN_PROGRESS, STATUS_SOLD, STATUS_AIRDROP, STATUS_ISSUE]

NFT_STATUS_TABLE = "nft_status"
NFT_STATE_TABLE = "state"

DB_MUTEX = Lock() # TODO REMOVE THIS ONE?
DB_STATUS_MUTEX = Lock()
# TODO note we could remove mutex on any functions that just get nft data... LOOK AT THIS LATER


class DbComms:
    def __init__(self, dbName:str='', maxMint:int=8192, adaPrice:int=100):
        self.adaPrice = adaPrice
        # check for dbName
        if dbName == '':
            raise Exception("Missing db name parameter")
        self.dbName =  dbName
        self.maxMint = int(maxMint)
        # get password
        load_dotenv()
        self.password = os.getenv('DB_PASSWORD')
        if self.password == None:
            raise Exception("Missing db password in .env")
        # connect as user and create db
        self.conn = mysql.connector.connect(
            host=HOST,
            user=USER,
            password=self.password
        )
        self.create_db()
        # set cursor in db
        self.conn = mysql.connector.connect(
            host=HOST,
            user=USER,
            password=self.password,
            database=self.dbName
        )
        self.db_cursor = self.conn.cursor()
        # setup tables
        self.setupTables()


    def setupTables(self):
        if self.create_state_table():
            print("populate table!")
            self.populate_state()
        if self.create_status_table():
            self.populate_status()

    
    # FUNCTIONALITY ----------------------------------------------------------
    def delete_db(self):
        cursor = self.conn.cursor()
        cursor.execute("DROP DATABASE " + self.dbName)

    def create_db(self):
        """ creates a db if it doesn't exist """
        try:
            cursor = self.conn.cursor()
            cursor.execute("CREATE DATABASE " + self.dbName)
        except mysql.connector.Error as err:
            if err.errno == 1007:
                log_debug(str("DB \'" + self.dbName + "\' exists"))
            else:
                raise err
        log_debug("New DB \'" + self.dbName + "\' created" )

    def create_table(self, tableName, other):
        try:
            self.db_cursor.execute("CREATE TABLE " + tableName + "(" + other +")")
        except mysql.connector.Error as err:
            if err.errno == 1050:
                log_debug(str("table \'" + tableName + "\' exists"))
                return False
            else:
                raise err
        log_debug(str("table \'" + tableName + "\' created"))
        return True

    def show_tables(self):
        self.db_cursor.execute("SHOW TABLES")
        for x in self.db_cursor:
            print(x)

    def select_all(self, tableName):
        DB_MUTEX.acquire()
        try:
            self.db_cursor.execute("SELECT * FROM " + tableName)
        finally:
            DB_MUTEX.release()
        for x in self.db_cursor:
            print(x)
    
    # EXAMPLE USAGE select("*","status","hexId='0001'")
    def select(self, x, table, where:str=None):
        sql = "SELECT " + x + " FROM " + table
        if where != None:
            sql += " WHERE " + where
        res = None
        DB_MUTEX.acquire()
        try:
            self.db_cursor.execute(sql)
            res = self.db_cursor.fetchall()
        finally:
            DB_MUTEX.release()
        # // remove in prod?
        #for x in res:
        #    log_debug(str(x))
        # // remove ^
        return res

    def update(self, table, values, where):
        sql = "UPDATE " + table + " SET " + values + " WHERE " + where
        #log_error(sql)
        res = None
        DB_MUTEX.acquire()
        try:
            self.db_cursor.execute(sql)
            self.conn.commit()
            res = self.db_cursor.fetchall()
        finally:
            DB_MUTEX.release()

        #for x in res:
        #    log_debug(str(x))


    # STATE ------------------------------------------------------------------
    def create_state_table(self):
        other =  "project VARCHAR(255) PRIMARY KEY, "
        other += "nftIndex VARCHAR(10), "
        other += "price VARCHAR(10), "
        other += "maxNFTS INT, "
        other += "allGenerated VARCHAR(5), "
        other += "nftBearingLastPayload VARCHAR(10)"
        return self.create_table(tableName=NFT_STATE_TABLE, other=other)

    def populate_state(self):
        sql = "INSERT INTO "+ NFT_STATE_TABLE +" (project, nftIndex, allGenerated) VALUES (%s, %s, %s)"
        val = (self.dbName, int_to_hex_id(0), 'false')
        try:
            self.db_cursor.execute(sql, val)
            self.conn.commit()
        except mysql.connector.Error as err:
            if err.errno == 1062:
                log_debug("duplicate")
            else:
                raise err
        
    def setAllGenerated(self):
        updates = "allGenerated='true' "
        where = "project='" + self.dbName + "'"
        self.update(NFT_STATE_TABLE, updates, where)

    def getAllGenerated(self,):
        where = "project='" + self.dbName + "'"
        res = self.select("allGenerated", NFT_STATE_TABLE, where)
        if res[0][0] == 'true':
            return True
        return False
    
    # STATUS -----------------------------------------------------------------
    def create_status_table(self):
        # no need for mutex here as it's ran before any concurrent code
        tableName = NFT_STATUS_TABLE
        other =  "hexId VARCHAR(4) PRIMARY KEY, "
        other += "intId INT, "
        other += "status VARCHAR(255), "
        other += "txHash VARCHAR(255), "
        other += "txId VARCHAR(100), "
        other += "outputTx VARCHAR(255), "
        other += "spentOutputTx BIT, "
        other += "customerAddr VARCHAR(255), "
        other += "nftName VARCHAR(255), "
        other += "metaFilePath VARCHAR(255), "
        other += "svgFilePath VARCHAR(255), "
        other += "price VARCHAR(20), "
        other += "hasPayload VARCHAR(20), "
        other += "meta BLOB, "
        other += "svg MEDIUMBLOB, "
        other += "date VARCHAR(255), "
        other += "ipfsHash VARCHAR(255), "
        other += "uid VARCHAR(255), "
        other += "minimalMeta VARCHAR(10000) "
        return self.create_table(tableName=tableName, other=other)
    
    def populate_status(self):
        # no need for mutex here as it's ran before any concurrent code
        values = []
        sql = "INSERT INTO " + NFT_STATUS_TABLE
        sql += " (hexId, intId, status, price) VALUES (%s, %s, %s, %s)" 
        for i in range(self.maxMint):
            values.append((
                int_to_hex_id(i),
                int(i),
                STATUS_AVAILABLE,
                str(self.adaPrice)
            ))
        try:
            self.db_cursor.executemany(sql, values)
            self.conn.commit()
        except mysql.connector.Error as err:
            if err.errno == 1062:
                log_debug("duplicate")
            else:
                raise err

        log_debug(str(self.db_cursor.rowcount) + " inserted")
    
    def getNftPagination(self, index):
        where = "intId >= " + str(index) + " LIMIT 32"
        res = self.select("hexId, intId, nftName, status, hasPayload, minimalMeta, svg, ipfsHash", NFT_STATUS_TABLE, where)
        paginationJson = {}

        for hexId, intId, nftName, status, hasPayload, meta, svg, ipfsHash in res:
            meta = json.loads(meta) 
            svg = svg.decode('utf-8')
            paginationJson[intId] = {"hexId":hexId, "nftName":nftName, "status":status, "hasPayload":hasPayload, "meta":meta, "svg":svg}

        return paginationJson

    def getNft(self, nft_id):
        hexId, nftName, status, hasPayload, meta = self.select("hexId, nftName, status, hasPayload, meta", NFT_STATUS_TABLE)[0]
        intId = int(hexId, 16)
        meta = json.loads(meta)
        details = {"hexId":hexId, "nftName":nftName, "status":status, "hasPayload":hasPayload, "meta":meta}
        # TODO don't return meta if not avilable!!
        return {intId: details}
    
    """
    def getNft(self, nft_id):
        hexId, nftName, status, hasPayload, meta = self.select("hexId, nftName, status, hasPayload, meta", NFT_STATUS_TABLE)[0]
        intId = int(hexId, 16)
        meta = json.loads(meta)
        details = {"hexId":hexId, "nftName":nftName, "status":status, "hasPayload":hasPayload, "meta":meta}
        # TODO don't return meta if not avilable!!
        return {intId: details}
    """
    
    def getNftStatus(self,):
        res = self.select("hexId, status, hasPayload", NFT_STATUS_TABLE)
        nftStatusJson = {}
        for hexId, status, hasPayload in res:
            intId = int(hexId, 16)
            nftStatusJson[intId] = {"hexId":hexId, "status":status, "hasPayload":hasPayload}

        return nftStatusJson

    def getMinimalNftWithIpfs(self, hexId):
        # get all nfts 
        where = "hexId='" + hexId + "'"
        ipfs, meta = self.select("ipfsHash, minimalMeta", NFT_STATUS_TABLE, where)[0]
        meta = json.loads(meta)
        return ipfs, meta

    #d.update("status", "status='cake'", "hexId='0000'")
    def nft_update(self, hexId, nftName, metaFilePath, svgFilePath, hasPayload, ipfsHash, uid, minimalMeta):
        updates = "nftName='" + nftName + "', "
        if hasPayload != None:
            updates += "hasPayload='true', "
        else:
            updates += "hasPayload='false', "

        updates += "metaFilePath='" + metaFilePath + "', "
        updates += "ipfsHash='" + ipfsHash + "', "
        updates += "uid='" + uid + "', "
        updates += "minimalMeta='" + json.dumps(minimalMeta) + "', "
        updates += "svgFilePath='" + svgFilePath + "'"

        where = "hexId='" + hexId + "'"
        self.update(NFT_STATUS_TABLE, updates, where)

        # add files to db
        self.updateBlob(hexId, "meta", metaFilePath)
        self.updateBlob(hexId, "svg", svgFilePath)
    
    def updateBlob(self, hexId, target, filepath):
        data = None
        with open(filepath, 'rb') as f:
            data = f.read()

        sql = "UPDATE " + NFT_STATUS_TABLE + " SET " + target + " = %s WHERE hexId = %s "
        DB_MUTEX.acquire()
        try:
            self.db_cursor.execute(sql, (data, hexId) )
            self.conn.commit()
            res = self.db_cursor.fetchall()
        finally:
            DB_MUTEX.release()

    # query for svgs and meta ------------------------------------------------
    def getSvg(self, hexId):
        where = "hexId='" + hexId + "'"
        res = self.select("svg", NFT_STATUS_TABLE, where)
        return res[0][0].decode('utf-8')

    def getMeta(self, hexId):
        where = "hexId='" + hexId + "'"
        res = self.select("meta", NFT_STATUS_TABLE, where)
        return json.loads(res[0][0])

    def getAllMeta(self):
        """ return all metadata fro the database """
        res = self.select("hexId, meta", NFT_STATUS_TABLE)
        allMeta = {}
        for hexId, meta in res:
            allMeta[hexId] = json.loads(meta)
        return allMeta
    
    def getAllSvg(self):
        """ return all metadata fro the database """
        res = self.select("hexId, svg", NFT_STATUS_TABLE)
        allSvg = {}
        for hexId, svg in res:
            allSvg[hexId] = svg.decode('utf-8')
        return allSvg


    # customer depreacted maybe ----------------------------------------------
    def check_if_customer_session_expired(self): # TODO works with customer reserved
        # return true if expired
        # get date
        time_in_db = None # get this from db
        time_reserved = datetime.datetime.fromisoformat(time_in_db)
        pass

    def customer_reserved(self): # TODO might be deprecated?
        DB_STATUS_MUTEX.acquire()
        try:
            # returns price if available else None

            # get hexId of next available....
            hexId = None 
            # get hex id
            where = "status='" + STATUS_AVAILABLE + "'"
            allAvailable = self.select("hexId", NFT_STATUS_TABLE, where)
            if allAvailable :
                hexId = allAvailable[0][0] # first available, inside tuple
            if hexId == None:
                return None
            # get all prices
            allPrices = self.select("price", NFT_STATUS_TABLE, where)
            # convert all prices from str in tuple to integers as knownPrices
            knownPrices = []
            for i in allPrices:
                knownPrices.append(int(i[0]))
            # generate random price from the divisions of one ada
            max_lace_int = ada_to_lace(1)
            price = None
            lace_price = ada_to_lace(self.adaPrice)
            random_lace = None
            try:
                random_lace = random.choice([i for i in range(0, max_lace_int) if i not in knownPrices]) # TODO check if failed
            except IndexError:
                # failed to generate (this should be statitaly improbable, still checking though)
                log_error("Failed to generate a random price value")
                return None
            # convert to string for db
            price = lace_to_ada( lace_price + random_lace )
            price = str(price)
            # add time, status and price to status table, then update
            current_time = datetime.datetime.utcnow().isoformat()
            updates = "date='" + current_time + "', "
            updates += "status='" + STATUS_AWAITING_PAYMANET + "', "
            updates += "price='" + price + "' "
            where = "hexId='" + hexId + "'"
            self.update(NFT_STATUS_TABLE, updates, where)
        finally:
            DB_STATUS_MUTEX.release()
        # return something unique to customer so they can look at there reservation maybe price?
        # but if using price we might need a new db to store all use prices as we replace price on
        # session timeout. And we want the customer to be able to view a link to know current status
        return price # TODO note a customer could keep spaming this function and then no would be available TODO TODO


    def sold_out(self):
        # get all nfts that don't have the sold status
        where = "status!='" + STATUS_SOLD + "'"
        notSoldEntries = self.select("txHash", NFT_STATUS_TABLE, where)
        if notSoldEntries:
            return False
        return True
        


    def txHashesToIgnore(self):
        pass
        DB_STATUS_MUTEX.acquire()
        try:
            # get all nfts that don't have the available status
            where = "status!='" + STATUS_AVAILABLE + "'"
            txHashes = self.select("txHash", NFT_STATUS_TABLE, where)
            txHashes = [i[0] for i in txHashes]
            if txHashes:
                return txHashes
            return None
        finally:
            DB_STATUS_MUTEX.release()
    
    # get all nfts that have a customer assigned
    # TODO no checks to check if addr is valid
    def getAllWithStatus(self, status):
        pass
        DB_STATUS_MUTEX.acquire()
        try:
            # get all nfts 
            where = "status='" + status + "'"
            res = self.select("hexId, customerAddr, nftName, txHash, txId, metaFilePath", NFT_STATUS_TABLE, where)
            if res:
                return res
            return None
        finally:
            DB_STATUS_MUTEX.release()

    def sold_out(self):
        # get all nfts that don't have the sold status
        where = "status='" + STATUS_ISSUE + "'"
        issues = self.select("txHash", NFT_STATUS_TABLE, where)
        if issues:
            return True
        return False


    def setOutputTx(self, hexId, outputTx):
        DB_STATUS_MUTEX.acquire()
        if outputTx == False:
            raise Exception(f"Issues with setOutputTx '{str(outputTx)}'")
        try:
            update = "outputTx='" + outputTx + "' "
            where = "hexId='" + hexId + "'"
            self.update(NFT_STATUS_TABLE, update, where)
        finally:
            DB_STATUS_MUTEX.release()

    def getOutputTxList(self):
        # get all nfts that 
        where = "outputTx is NOT NULL'"
        outputTxs = self.select("outputTx", NFT_STATUS_TABLE, where)
        return outputTxs


    def setStatus(self, hexId, status):
        DB_STATUS_MUTEX.acquire()
        if status not in STATUS_LIST:
            raise Exception("invalid status \'" + status + "\'")
            
        try:
            update = "status='" + status + "' "
            where = "hexId='" + hexId + "'"
            self.update(NFT_STATUS_TABLE, update, where)
        finally:
            DB_STATUS_MUTEX.release()



    def add_customer(self, address:str=None, txId:str=None, txHash:str=None):
        if address == None or txId == None or txHash == None:
            raise Exception("customer found requires an address, txId and txHash")
        # mutex to protect against same nft being assigned to multiple customers
        DB_STATUS_MUTEX.acquire()
        try:
            # ensure txHash is not in db to avoid duplicate mints
            # get hexId of next available....
            hexId = None # TODO
            # get hex id
            where = "status='" + STATUS_AVAILABLE + "'"
            allAvailable = self.select("hexId", NFT_STATUS_TABLE, where)
            if allAvailable :
                hexId = allAvailable[0][0] # first available, inside tuple
            if hexId == None:
                return None
            # add time, status and price to status table, then update
            current_time = datetime.datetime.utcnow().isoformat()
            updates = "date='" + current_time + "', "
            updates += "status='" + STATUS_AWAITING_MINT + "', "
            updates += "customerAddr='" + address + "', "
            updates += "txId='" + txId + "', "
            updates += "txHash='" + txHash + "' "
            where = "hexId='" + hexId + "'"
            self.update(NFT_STATUS_TABLE, updates, where)
        finally:
            DB_STATUS_MUTEX.release()

        return hexId # TODO not needed as minting thread will handle this

"""
if __name__ == "__main__":
    d = DbComms(dbName="hello")
    d.show_tables()
    # note we delete here
    d.select("*","status","hexId='0000'")
    d.update("status", "status='cake'", "hexId='0000'")
    d.select("*","status","hexId='0000'")
    d.delete_db()
"""