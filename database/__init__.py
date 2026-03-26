"""
Database initialization and configuration
Supports both SQLite and Supabase PostgreSQL
"""
import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool, NullPool
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

def get_database_type():
    """Get database type from environment"""
    return os.getenv('DATABASE_TYPE', 'sqlite').lower()

def get_database_url():
    """Get database URL based on configured type"""
    db_type = get_database_type()
    
    if db_type == 'supabase':
        supabase_db_url = os.getenv('SUPABASE_DB_URL')
        if not supabase_db_url:
            raise ValueError("SUPABASE_DB_URL environment variable is required when DATABASE_TYPE=supabase")
        logger.info("Using Supabase PostgreSQL database")
        return supabase_db_url
    else:
        sqlite_url = os.getenv('SQLITE_DATABASE_URL', 'sqlite:///vulnerability_alerts.db')
        logger.info(f"Using SQLite database: {sqlite_url}")
        return sqlite_url

def create_engine_instance():
    """Create SQLAlchemy engine based on database type"""
    database_url = get_database_url()
    db_type = get_database_type()
    
    if db_type == 'supabase':
        engine = create_engine(
            database_url,
            echo=False,
            poolclass=NullPool,
            pool_pre_ping=True,
            connect_args={
                "sslmode": "require"  # Supabase requires SSL
            }
        )
    else:
        engine = create_engine(
            database_url,
            echo=False,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False}
        )
    
    return engine

engine = create_engine_instance()

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
        db_type = get_database_type()
        
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully!")
        logger.info(f"Database type: {db_type}")
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return False

def test_connection():
    """Test database connection"""
    try:
        with engine.connect() as connection:
            if get_database_type() == 'supabase':
                result = connection.execute(text("SELECT 1"))
            else:
                result = connection.execute(text("SELECT 1"))
            logger.info("Database connection test successful")
            return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False