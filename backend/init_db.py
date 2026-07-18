"""
Database initialization script for CleanLoop.

Creates all tables in the database using SQLAlchemy ORM models.

Usage:
    python backend/init_db.py
"""

import sys
import logging
from backend_database import engine, Base

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import all models to register them with Base
from backend_models import User, Ward, Complaint, Assignment, Hotspot, WardMetric


def init_db():
    """
    Initialize database by creating all tables.
    
    Uses SQLAlchemy Base.metadata.create_all() to create tables for all
    registered models (User, Ward, Complaint, Assignment, Hotspot, WardMetric).
    """
    try:
        logger.info("🚀 Starting database initialization...")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        logger.info("✅ Database initialization completed successfully!")
        logger.info("Tables created:")
        logger.info("  - users")
        logger.info("  - wards")
        logger.info("  - complaints")
        logger.info("  - assignments")
        logger.info("  - hotspots")
        logger.info("  - ward_metrics")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {str(e)}")
        return False


if __name__ == "__main__":
    success = init_db()
    sys.exit(0 if success else 1)
