import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MONGO_URI = os.getenv("MONGODB_URI")
    DB_NAME = os.getenv("DB_NAME")
    RABBITMQ_URI = os.getenv("RABBITMQ_URI")
    MODEL_NEIGHBORS = int(os.getenv("MODEL_NEIGHBORS", 10))
    MODEL_METRIC = os.getenv("MODEL_METRIC", "cosine")
    API_KEYS = os.getenv("API_KEYS", "").split(",")