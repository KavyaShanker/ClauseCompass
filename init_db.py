from pymongo import MongoClient
from config import Config

def init_database():
    client = MongoClient(Config.MONGODB_URI)
    db = client[Config.DB_NAME]

    # Creating 'users' collection with indexes
    if Config.USERS_COLLECTION not in db.list_collection_names():
        users = db[Config.USERS_COLLECTION]
        users.create_index("username", unique=True)
        print(f"Created {Config.USERS_COLLECTION} collection with indexes")

    # Creating 'documents' collection with indexes
    if Config.DOCUMENTS_COLLECTION not in db.list_collection_names():
        documents = db[Config.DOCUMENTS_COLLECTION]
        documents.create_index([("user_id", 1), ("uploaded_at", -1)])
        print(f"Created {Config.DOCUMENTS_COLLECTION} collection with indexes")

    print("Database initialization completed")

if __name__ == "__main__":
    init_database()