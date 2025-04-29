from pymongo import MongoClient
import os

def get_db():
    client = MongoClient(os.getenv("MONGO_URI", "mongodb://mongo:27017"))
    return client[os.getenv("DB_NAME", "shop-nexus-core")]