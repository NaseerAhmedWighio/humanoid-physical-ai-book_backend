#!/usr/bin/env python3
"""
Test script to verify that the database connection issue is fixed.
"""
import sys
import os

# Add the backend src directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_database_connection():
    """Test the database connection with the fixed text() wrapping."""
    print("Testing database connection with fixed text() wrapping...")

    try:
        # Import the database module
        from src.database import get_db_with_retry, check_database_health

        print("SUCCESS: Successfully imported database functions")

        # Test the get_db_with_retry function
        print("Testing get_db_with_retry()...")
        try:
            db = get_db_with_retry(max_retries=2, backoff_factor=0.1)
            print("SUCCESS: Database connection successful with get_db_with_retry()")
            db.close()
        except Exception as e:
            print(f"FAILURE: Database connection failed: {e}")
            return False

        # Test the check_database_health function
        print("Testing check_database_health()...")
        try:
            is_healthy, message = check_database_health()
            print(f"SUCCESS: Database health check: {message}")
        except Exception as e:
            print(f"FAILURE: Database health check failed: {e}")
            return False

        print("\nSUCCESS: All database connection tests passed!")
        return True

    except ImportError as e:
        print(f"FAILURE: Import error: {e}")
        return False
    except Exception as e:
        print(f"FAILURE: Unexpected error: {e}")
        return False

def main():
    """Main test function."""
    print("="*60)
    print("Humanoid AI Book - Database Fix Verification Test")
    print("="*60)

    print("\nThis test verifies that the SQLAlchemy 'text()' wrapping issue is fixed.")
    print("Expected: No 'Textual SQL expression' errors during database operations.\n")

    success = test_database_connection()

    print("\n" + "="*60)
    if success:
        print("SUCCESS: Database connection issue has been fixed!")
        print("\nChanges made:")
        print("- Wrapped raw SQL strings with text() function in database.py")
        print("- Fixed get_db_with_retry() to use text('SELECT 1')")
        print("- Fixed check_database_health() to use text('SELECT 1')")
        print("- Maintained retry logic with exponential backoff")
        return 0
    else:
        print("FAILURE: Database connection issue persists.")
        return 1

if __name__ == "__main__":
    exit(main())