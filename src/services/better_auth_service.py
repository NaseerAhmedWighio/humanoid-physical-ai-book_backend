from better_auth import auth, models, Base
from better_auth.types import User
from sqlalchemy.orm import sessionmaker
from ..database import engine
from ..models.user import User as CustomUser
from typing import Optional
import os

# Create database session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Initialize Better Auth
auth_app = auth.Auth(
    secret=os.getenv("BETTER_AUTH_SECRET", "your-super-secret-key-change-in-production"),
    database_url=os.getenv("DATABASE_URL", "sqlite:///./test.db"),  # This should match your actual database
    # Add custom fields for hardware preferences
    additional_user_data={
        "has_mobile": bool,
        "has_laptop": bool,
        "has_physical_robot": bool,
        "has_other_hardware": str,
        "web_dev_experience": str,
    }
)

# Function to sync custom user data with better-auth
def sync_user_data(user: User, db_user: CustomUser) -> User:
    """
    Synchronize custom user data from our custom User model to Better Auth user
    """
    user.has_mobile = getattr(db_user, 'has_mobile', False)
    user.has_laptop = getattr(db_user, 'has_laptop', False)
    user.has_physical_robot = getattr(db_user, 'has_physical_robot', False)
    user.has_other_hardware = getattr(db_user, 'has_other_hardware', '')
    user.web_dev_experience = getattr(db_user, 'web_dev_experience', '')
    return user

def create_better_auth_user(user_data: dict) -> Optional[User]:
    """
    Create a user using Better Auth with custom data
    """
    try:
        # Create user through Better Auth
        better_user = auth_app.create_user(
            email=user_data['email'],
            password=user_data['password'],
            # Pass custom data
            has_mobile=user_data.get('has_mobile', False),
            has_laptop=user_data.get('has_laptop', False),
            has_physical_robot=user_data.get('has_physical_robot', False),
            has_other_hardware=user_data.get('has_other_hardware', ''),
            web_dev_experience=user_data.get('web_dev_experience', '')
        )

        # Sync with our custom user model if needed
        # This would depend on your specific requirements

        return better_user
    except Exception as e:
        print(f"Error creating better auth user: {e}")
        return None

def update_user_hardware_preferences(user_id: str, preferences: dict) -> Optional[User]:
    """
    Update user's hardware preferences in Better Auth
    """
    try:
        # Update user data in Better Auth
        updated_user = auth_app.update_user(
            user_id=user_id,
            has_mobile=preferences.get('has_mobile'),
            has_laptop=preferences.get('has_laptop'),
            has_physical_robot=preferences.get('has_physical_robot'),
            has_other_hardware=preferences.get('has_other_hardware'),
            web_dev_experience=preferences.get('web_dev_experience')
        )

        return updated_user
    except Exception as e:
        print(f"Error updating user preferences: {e}")
        return None