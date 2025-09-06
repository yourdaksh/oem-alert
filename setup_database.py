"""
Database setup and initialization script
"""
import os
import sys
from database import init_database, engine
from database.models import Base
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_database():
    """Initialize the database with all tables"""
    try:
        logger.info("Initializing database...")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        logger.info("Database initialized successfully!")
        
        # Verify tables were created
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        logger.info(f"Created tables: {tables}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False

def reset_database():
    """Reset the database (drop and recreate all tables)"""
    try:
        logger.info("Resetting database...")
        
        # Drop all tables
        Base.metadata.drop_all(bind=engine)
        logger.info("Dropped all tables")
        
        # Recreate all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Recreated all tables")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to reset database: {e}")
        return False

def check_database_status():
    """Check database status and table information"""
    try:
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        logger.info("Database Status:")
        logger.info(f"  Tables: {tables}")
        
        # Check if database file exists
        db_file = "vulnerability_alerts.db"
        if os.path.exists(db_file):
            size = os.path.getsize(db_file)
            logger.info(f"  Database file: {db_file} ({size} bytes)")
        else:
            logger.info(f"  Database file: {db_file} (not found)")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to check database status: {e}")
        return False

def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "setup":
            success = setup_database()
        elif command == "reset":
            success = reset_database()
        elif command == "status":
            success = check_database_status()
        else:
            print("Usage: python setup_database.py [setup|reset|status]")
            sys.exit(1)
    else:
        # Default to setup
        success = setup_database()
    
    if success:
        print("Database operation completed successfully!")
    else:
        print("Database operation failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
