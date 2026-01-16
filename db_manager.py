#!/usr/bin/env python3
"""
Database management script for the Humanoid AI Textbook project.

This script provides commands to:
- Initialize the database
- Run migrations
- Check database health
"""

import os
import sys
import argparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def init_database():
    """Initialize the database with all required tables."""
    from src.database import engine, Base
    from src.models import *  # Import all models

    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

def check_db_connection():
    """Check if the database connection is working."""
    from src.database import check_database_health
    is_healthy, message = check_database_health()
    print(f"Database health check: {message}")
    return is_healthy

def run_migrations():
    """Run alembic migrations to update the database schema."""
    import subprocess
    import os

    # Change to the backend directory
    original_dir = os.getcwd()
    os.chdir('..')  # Go to the project root

    try:
        # Run alembic upgrade to head
        result = subprocess.run([
            sys.executable, '-m', 'alembic', 'upgrade', 'head'
        ], env=os.environ, capture_output=True, text=True)

        if result.returncode == 0:
            print("Migrations applied successfully!")
            print(result.stdout)
        else:
            print("Error applying migrations:")
            print(result.stderr)
            return False

    except Exception as e:
        print(f"Error running migrations: {e}")
        return False
    finally:
        os.chdir(original_dir)  # Return to original directory

    return True

def create_migration(message):
    """Create a new migration with the given message."""
    import subprocess
    import os

    # Change to the backend directory
    original_dir = os.getcwd()
    os.chdir('..')  # Go to the project root

    try:
        # Run alembic revision to create a new migration
        result = subprocess.run([
            sys.executable, '-m', 'alembic', 'revision', '--autogenerate', '-m', message
        ], env=os.environ, capture_output=True, text=True)

        if result.returncode == 0:
            print("Migration created successfully!")
            print(result.stdout)
        else:
            print("Error creating migration:")
            print(result.stderr)
            return False

    except Exception as e:
        print(f"Error creating migration: {e}")
        return False
    finally:
        os.chdir(original_dir)  # Return to original directory

    return True

def main():
    parser = argparse.ArgumentParser(description='Database management for Humanoid AI Textbook')
    parser.add_argument('command', choices=['init', 'check', 'migrate', 'create-migration'],
                       help='Command to execute')
    parser.add_argument('--message', '-m', help='Message for migration (used with create-migration)')

    args = parser.parse_args()

    if args.command == 'init':
        init_database()
    elif args.command == 'check':
        check_db_connection()
    elif args.command == 'migrate':
        run_migrations()
    elif args.command == 'create-migration':
        if not args.message:
            print("Error: --message is required for create-migration command")
            sys.exit(1)
        create_migration(args.message)

if __name__ == "__main__":
    main()