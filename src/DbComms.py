from dotenv import load_dotenv
import os

from mysqlx import Column
from Utility import int_to_hex_id, log_debug, log_error
import mysql.connector

HOST='localhost'
USER='jack'

class DbComms:
    def __init__(self, dbName:str='', maxMint:int=8192):
        # check for dbName
        if dbName == '':
            raise Exception("Missing db name parameter")
        self.dbName = "test_" + dbName # TODO note test
        self.maxMint = maxMint
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
        self.create_state_table()
        self.populate_state()
        self.create_status_table()
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
            else:
                raise err
        log_debug(str("table \'" + tableName + "\' created"))

    def show_tables(self):
        self.db_cursor.execute("SHOW TABLES")
        for x in self.db_cursor:
            print(x)

    def select_all(self, tableName):
        self.db_cursor.execute("SELECT * FROM " + tableName)
        for x in self.db_cursor:
            print(x)
    
    # EXAMPLE USAGE select("*","status","hexId='0001'")
    def select(self, x, table, where:str=None):
        sql = "SELECT " + x + " FROM " + table
        if where != None:
            sql += " WHERE " + where
        log_error(sql)
        self.db_cursor.execute(sql)
        res = self.db_cursor.fetchall()
        for x in res:
            log_debug(str(x))

    def update(self, table, values, where):
        sql = "UPDATE " + table + " SET " + values + " WHERE " + where
        log_error(sql)
        self.db_cursor.execute(sql)
        self.conn.commit()
        res = self.db_cursor.fetchall()
        for x in res:
            log_debug(str(x))


    # STATE ------------------------------------------------------------------
    def create_state_table(self):
        tableName = "state"
        other =  "project VARCHAR(255) PRIMARY KEY, "
        other += "nftIndex VARCHAR(10), "
        other += "price VARCHAR(10), "
        other += "maxNFTS INT, "
        other += "nftBearingLastPayload VARCHAR(10)"
        self.create_table(tableName=tableName, other=other)

    def populate_state(self):
        values = []
        sql = "INSERT INTO state (project, nftIndex) VALUES (%s, %s)"
        val = (self.dbName, int_to_hex_id(0))
        try:
            self.db_cursor.execute(sql, val)
            self.conn.commit()
        except mysql.connector.Error as err:
            if err.errno == 1062:
                log_debug("duplicate")
            else:
                raise err


    # STATUS -----------------------------------------------------------------
    def create_status_table(self):
        tableName = "status"
        other =  "hexId VARCHAR(4) PRIMARY KEY, "
        other += "status VARCHAR(255), "
        other += "txHash VARCHAR(255), "
        other += "customer VARCHAR(255), "
        other += "nftName VARCHAR(255), "
        other += "metaFilePath VARCHAR(255), "
        other += "svgFilePath VARCHAR(255), "
        other += "price VARCHAR(10)"
        self.create_table(tableName=tableName, other=other)

    #d.update("status", "status='cake'", "hexId='0000'")
    def nft_update(self, hexId, nftName, metaFilePath, svgFilePath):
        updates = "nftName='" + nftName + "', "
        updates += "metaFilePath='" + metaFilePath + "', "
        updates += "svgFilePath='" + svgFilePath + "'"
        where = "hexId='" + hexId + "'"
        self.update("status", updates, where)
    
    def customer_purchase_detected():
        # select next not taken
        pass

    def populate_status(self):
        values = []
        sql = "INSERT INTO status "
        sql +="(hexId, status) VALUES (%s, %s)" 
        for i in range(self.maxMint):
            values.append((
                int_to_hex_id(i),
                "available"
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