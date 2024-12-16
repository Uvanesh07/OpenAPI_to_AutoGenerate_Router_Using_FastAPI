import os
from dotenv import load_dotenv

def load_env():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))    
    # Path to the .env file
    dotenv_path = os.path.join(project_root, '.env')
    load_dotenv(dotenv_path)

class Config:
    load_env()
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_NAME = os.getenv("DB_NAME")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")

    API_URL = os.getenv("API_URL")
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    LOG_TO_FILE = os.getenv("LOG_TO_FILE", "True").lower() == "true"
    LOG_TO_CONSOLE = os.getenv("LOG_TO_CONSOLE", "True").lower() == "true"

    # Debugging prints to ensure variables are loaded correctly
    print(f"Loaded DB_USER: {DB_USER}")
    print(f"Loaded DB_PASSWORD: {DB_PASSWORD}")
    print(f"Loaded DB_NAME: {DB_NAME}")
    print(f"Loaded DB_HOST: {DB_HOST}")
    print(f"Loaded DB_PORT: {DB_PORT}")
