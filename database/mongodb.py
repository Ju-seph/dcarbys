import pymongo
from dotenv import load_dotenv
import os

load_dotenv()

class Mongodb():

    db_name = os.getenv("DB_NAME")
    db_URI = os.getenv("DB_URI")


    def __init__(self):
        self.client = pymongo.MongoClient(self.db_URI)
        self.mbd = self.client[self.db_name]

    
    def db(self):
        return self.mbd