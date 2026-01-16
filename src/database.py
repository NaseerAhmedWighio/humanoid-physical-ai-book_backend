from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError
import os
import time
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment variables
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./humanoid_ai_book.db")

# Create engine with connection pooling
if DATABASE_URL.startswith("sqlite"):
    # SQLite doesn't support pool_pre_ping and other advanced features
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},  # Required for SQLite
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=10,
    )
else:
    # PostgreSQL settings
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_timeout=30,
        echo=False  # Set to True for debugging
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative models
Base = declarative_base()

logger = logging.getLogger(__name__)

def get_db():
    """
    Dependency function to get database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_with_retry(max_retries=3, backoff_factor=0.3):
    """
    Get database session with retry mechanism
    """
    for attempt in range(max_retries):
        try:
            db = SessionLocal()
            # Test the connection by executing a simple query
            db.execute(text("SELECT 1"))
            logger.info(f"Database connection established on attempt {attempt + 1}")
            return db
        except SQLAlchemyError as e:
            db.close()
            logger.error(f"Database connection attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                logger.critical(f"Database connection failed after {max_retries} attempts: {e}")
                raise e
            time.sleep(backoff_factor * (2 ** attempt))  # Exponential backoff
        except Exception as e:
            logger.error(f"Unexpected error during database connection attempt {attempt + 1}: {e}")
            if attempt == max_retries - 1:
                logger.critical(f"Database connection failed after {max_retries} attempts due to unexpected error: {e}")
                raise e
            time.sleep(backoff_factor * (2 ** attempt))  # Exponential backoff

def check_database_health():
    """
    Check database health by executing a simple query
    """
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return True, "Database is healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False, f"Database health check failed: {str(e)}"