import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
from src.database import Base
from src.models import *

# Load environment variables
load_dotenv()

def init_db():
    """
    Initialize the database by creating all tables
    """
    # Get database URL from environment variables
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./humanoid_ai_book.db")

    # Create engine with appropriate settings based on database type
    if DATABASE_URL.startswith("sqlite"):
        # SQLite doesn't support pool_pre_ping and other advanced features
        engine = create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False},  # Required for SQLite
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

    print(f"Creating database tables with URL: {DATABASE_URL}...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_db()