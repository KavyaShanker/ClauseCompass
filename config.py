import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    # MongoDB Settings
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
    DB_NAME = 'contract_analyzer'

    # Collections
    USERS_COLLECTION = 'users'
    DOCUMENTS_COLLECTION = 'documents'

    # App Settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key')
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

    @staticmethod
    def is_development():
        return Config.ENVIRONMENT == 'development'