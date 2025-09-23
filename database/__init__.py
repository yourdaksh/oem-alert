"""
Database initialization and configuration
SQLite database support
"""
import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

def get_database_url():
    """Get SQLite database URL"""
    sqlite_url = os.getenv('SQLITE_DATABASE_URL', 'sqlite:///vulnerability_alerts.db')
    logger.info(f"Using SQLite database: {sqlite_url}")
    return sqlite_url

def create_engine_instance():
    """Create SQLAlchemy engine for SQLite"""
    database_url = get_database_url()
    
    # SQLite engine
    engine = create_engine(
        database_url,
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False}
    )
    
    return engine

# Create engine
engine = create_engine_instance()

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_database():
    """Initialize database tables"""
    try:
        from .models import Base
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully!")
        logger.info("Database type: sqlite")
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return False

def test_connection():
    """Test database connection"""
    try:
        with engine.connect() as connection:
            result = connection.execute("SELECT 1")
            logger.info("Database connection test successful")
            return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False