#!/usr/bin/env python
"""
Script to add missing columns to existing database tables
"""
import os
import sys
from pathlib import Path
import sqlite3

# Add the backend directory to the path so we can import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

def add_missing_columns():
    """Add missing columns to the users table"""
    print("Adding missing columns to the database...")

    # Connect to the database
    db_path = "humanoid_ai_book.db"  # Default path
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print(f"Connected to database: {db_path}")

    try:
        # Check current users table structure
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        print(f"Current users table columns: {column_names}")

        # Add language_preference column if it doesn't exist
        if 'language_preference' not in column_names:
            print("Adding 'language_preference' column...")
            cursor.execute("ALTER TABLE users ADD COLUMN language_preference VARCHAR DEFAULT 'en'")
            print("+ Added 'language_preference' column")
        else:
            print("'language_preference' column already exists")

        # Add personalization_enabled column if it doesn't exist
        if 'personalization_enabled' not in column_names:
            print("Adding 'personalization_enabled' column...")
            cursor.execute("ALTER TABLE users ADD COLUMN personalization_enabled BOOLEAN DEFAULT 1")
            print("+ Added 'personalization_enabled' column")
        else:
            print("'personalization_enabled' column already exists")

        # Commit changes
        conn.commit()
        print("\n+ Missing columns added successfully!")

        # Verify the changes
        cursor.execute("PRAGMA table_info(users)")
        updated_columns = cursor.fetchall()
        print(f"\nUpdated users table columns: {[col[1] for col in updated_columns]}")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.rollback()
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_missing_columns()