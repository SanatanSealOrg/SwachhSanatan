import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration settings for CleanLoop API"""
    
    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://cleanloop:cleanloop_dev@localhost:5432/cleanloop_db")
    
    # App
    APP_NAME: str = os.getenv("APP_NAME", "CleanLoop")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"


config = Config()
