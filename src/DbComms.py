from dotenv import load_dotenv
import os
from Utility import log_debug, log_error
import mysql.connector

HOST='localhost'
USER='jack'

class DbComms:
    def __init__(self, dbName:str=''):
        # check for dbName
        if dbName == '':
            raise Exception("Missing db name parameter")
        self.dbName = dbName
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
    

    def create_table(self, tableName, other):
        try:
            self.db_cursor.execute("CREATE TABLE " + tableName + "(" + other +")")
        except mysql.connector.Error as err:
            if err.errno == 1050:
                log_debug(str("table \'" + tableName + "\' exists"))
            else:
                raise err

    def show_tables(self):
        self.db_cursor.execute("SHOW TABLES")
        for x in self.db_cursor:
            print(x)

    def select_all(self, tableName):
        self.db_cursor.execute("SELECT * FROM " + tableName)
        for x in self.db_cursor:
            print(x)
            




if __name__ == "__main__":
    d = DbComms(dbName="hello")
    d.create_table("cake","name VARCHAR(255), address VARCHAR(255)")
    d.create_table("cake2","name VARCHAR(255), address VARCHAR(255)")
    d.create_table("cake3","name VARCHAR(255), address VARCHAR(255)")
    d.show_tables()
    d.select_all("cake")