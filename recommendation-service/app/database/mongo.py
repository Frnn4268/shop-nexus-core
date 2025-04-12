from pymongo import MongoClient
import os

def get_mongo_client():
    return MongoClient(os.getenv("MONGODB_URI"))

def get_purchase_history_collection():
    client = get_mongo_client()
    return client[os.getenv("DB_NAME")]["user_purchases"]