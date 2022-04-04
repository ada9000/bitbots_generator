from dotenv import load_dotenv
import os
from Utility import log_debug, log_error
import mysql.connector

HOST='localhost'
USER='jack'

class DbComms:
    def __init__(self, dbName:str=''):
        if dbName == '':
            raise Exception("Missing db name parameter")
        load_dotenv()
        self.password = os.getenv('DB_PASSWORD')
        self.dbName = dbName
        if self.password == None:
            raise Exception("Missing db password in .env")
        
        # 
        self.conn = mysql.connector.connect(
            host=HOST,
            user=USER,
            password=self.password
        )
        self.create_db()

        self.conn = mysql.connector.connect(
            host=HOST,
            user=USER,
            password=self.password,
            database=self.dbName
        )


    def clean(self):
        pass

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
    
    def connect_db(self):
        self.cnx = mysql.connector.connect(
            host=HOST,
            user=USER,
            password=self.password,
            database=self.dbName
        )



if __name__ == "__main__":
    d = DbComms(dbName="hello")