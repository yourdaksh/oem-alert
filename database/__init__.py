import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def get_database_url():
    url = os.getenv('SUPABASE_DB_URL')
    if not url:
        raise ValueError("SUPABASE_DB_URL environment variable is required")
    return url


engine = create_engine(
    get_database_url(),
    echo=False,
    poolclass=NullPool,
    pool_pre_ping=True,
    connect_args={"sslmode": "require"}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_database():
    try:
        from .models import Base
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized")
        return True
    except Exception as e:
        logger.error(f"Database init error: {e}")
        return False


def test_connection():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False