import sys
sys.path.append('../src')

import shutil
from dotenv import load_dotenv
import mysql.connector
import os

from Utility import PROJECT_DIR
HOST='localhost'
USER='jack'

def reset_test_dbs():
    START = "test_"
    load_dotenv()
    password = os.getenv('DB_PASSWORD')
    if password == None:
        raise Exception("Missing db password in .env")
    # connect as user and create db
    conn = mysql.connector.connect(
        host=HOST,
        user=USER,
        password=password
    )
    # show all db
    cursor = conn.cursor()
    cursor.execute("SHOW DATABASES")
    dbs = []
    for x in cursor:
        if "test_" in x[0]:
            dbs.append(x[0])
    print(dbs)
    input("press any key to drop tables...\n")
    for x in dbs:
        cursor.execute("DROP DATABASE " + x)

def clear_project_files():
    shutil.rmtree(PROJECT_DIR)



if __name__ == "__main__":
    reset_test_dbs()
    clear_project_files()


