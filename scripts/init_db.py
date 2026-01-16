#!/usr/bin/env python
"""
Script to initialize the database with proper schema
"""
import os
import sys
from pathlib import Path

# Add the backend directory to the path so we can import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import engine, Base
from src.models.user import User
from src.models.chat_session import ChatSession
from src.models.chat_message import ChatMessage
from src.models.student_progress import StudentProgress
from src.models.chat_conversation import ChatConversation
from src.models.personalized_content import PersonalizedContent
from src.models.translation_cache import TranslationCache
from src.models.translation_dictionary import TranslationDictionary
from src.models.content_chunk import ContentChunk
from src.models.course_module import CourseModule
from src.models.exercise import Exercise
from src.models.hardware_requirement import HardwareRequirement
from src.models.weekly_content import WeeklyContent
from src.models.assessment_project import AssessmentProject
from sqlalchemy import inspect

def init_db():
    """Initialize the database with all required tables"""
    print("Initializing database...")

    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")

    # Verify tables were created
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    print(f"\nCreated tables: {tables}")

    # Show column information for the users table
    if 'users' in tables:
        columns = inspector.get_columns('users')
        print(f"\nUsers table columns:")
        for col in columns:
            print(f"  - {col['name']} ({col['type']})")

    print("\nDatabase initialization complete!")

if __name__ == "__main__":
    init_db()