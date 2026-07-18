from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from geoalchemy2 import Geometry
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://cleanloop:cleanloop_dev@localhost:5432/cleanloop_db")

# Create database engine
engine = create_engine(
    DATABASE_URL,
    echo=os.getenv("DEBUG", "False").lower() in ("true", "1"),
    pool_pre_ping=True  # Verify connection before using
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency for FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
