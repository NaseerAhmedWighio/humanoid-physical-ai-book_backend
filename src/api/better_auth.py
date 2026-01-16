from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from ..services.auth_service import auth_service, UserCreate, UserLogin, Token, UserResponse, UserRegistration
from ..database import get_db
from datetime import timedelta
from pydantic import BaseModel
from typing import Optional

router = APIRouter(
    prefix="/v1/better-auth",
    tags=["better-auth"],
    responses={404: {"description": "Not found"}},
)

class BetterAuthRegisterRequest(BaseModel):
    email: str
    password: str
    has_mobile: bool = False
    has_laptop: bool = False
    has_physical_robot: bool = False
    has_other_hardware: Optional[str] = None
    web_dev_experience: Optional[str] = None
    language_preference: str = 'en'
    personalization_enabled: bool = True

class BetterAuthLoginRequest(BaseModel):
    email: str
    password: str

class BetterAuthPreferencesRequest(BaseModel):
    has_mobile: bool = False
    has_laptop: bool = False
    has_physical_robot: bool = False
    has_other_hardware: Optional[str] = None
    web_dev_experience: Optional[str] = None
    language_preference: str = 'en'
    personalization_enabled: bool = True

@router.post("/register")
async def better_auth_register(user_data: BetterAuthRegisterRequest, db: Session = Depends(get_db)):
    """
    Register endpoint compatible with better-auth client
    """
    try:
        # Create user with minimal validation - allow registration with default hardware preferences
        # The validation that requires hardware preferences should only apply to the UserRegistration model
        # For registration, we'll use UserCreate which doesn't have the strict hardware validation

        # Validate the basic user data without the strict hardware validation
        user_create = UserCreate(
            email=user_data.email,
            password=user_data.password,
            has_mobile=user_data.has_mobile,
            has_laptop=user_data.has_laptop,
            has_physical_robot=user_data.has_physical_robot,
            has_other_hardware=user_data.has_other_hardware,
            web_dev_experience=user_data.web_dev_experience,
            language_preference=user_data.language_preference,
            personalization_enabled=user_data.personalization_enabled
        )

        # Use existing auth service to create user
        user = auth_service.create_user(db, user_create)

        # Return a response that's compatible with better-auth client expectations
        return {
            "user": {
                "id": str(user.id),
                "email": user.email,
                "has_mobile": user.has_mobile,
                "has_laptop": user.has_laptop,
                "has_physical_robot": user.has_physical_robot,
                "has_other_hardware": user.has_other_hardware,
                "web_dev_experience": user.web_dev_experience,
                "language_preference": user.language_preference,
                "personalization_enabled": user.personalization_enabled,
                "created_at": user.created_at
            },
            "session": {
                "access_token": auth_service.create_access_token(
                    data={"sub": user.email},
                    expires_delta=timedelta(minutes=30)
                ),
                "token_type": "bearer"
            }
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during registration: {str(e)}"
        )

@router.post("/login")
async def better_auth_login(user_data: BetterAuthLoginRequest, db: Session = Depends(get_db)):
    """
    Login endpoint compatible with better-auth client
    """
    user = auth_service.authenticate_user(db, user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=30)
    access_token = auth_service.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "has_mobile": user.has_mobile,
            "has_laptop": user.has_laptop,
            "has_physical_robot": user.has_physical_robot,
            "has_other_hardware": user.has_other_hardware,
            "web_dev_experience": user.web_dev_experience,
            "language_preference": user.language_preference,
            "personalization_enabled": user.personalization_enabled,
            "created_at": user.created_at
        },
        "session": {
            "access_token": access_token,
            "token_type": "bearer"
        }
    }

@router.post("/update-preferences")
async def better_auth_update_preferences(
    preferences: BetterAuthPreferencesRequest,
    user = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user preferences endpoint compatible with better-auth client
    """
    # Update user preferences
    user.has_mobile = preferences.has_mobile
    user.has_laptop = preferences.has_laptop
    user.has_physical_robot = preferences.has_physical_robot
    user.has_other_hardware = preferences.has_other_hardware
    user.web_dev_experience = preferences.web_dev_experience
    user.language_preference = preferences.language_preference
    user.personalization_enabled = preferences.personalization_enabled

    db.commit()
    db.refresh(user)

    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "has_mobile": user.has_mobile,
            "has_laptop": user.has_laptop,
            "has_physical_robot": user.has_physical_robot,
            "has_other_hardware": user.has_other_hardware,
            "web_dev_experience": user.web_dev_experience,
            "language_preference": user.language_preference,
            "personalization_enabled": user.personalization_enabled,
            "created_at": user.created_at
        }
    }

@router.get("/session")
async def better_auth_session(user = Depends(auth_service.get_current_user)):
    """
    Get current user session - compatible with better-auth client
    """
    if not user:
        return {"user": None, "session": None}

    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "has_mobile": user.has_mobile,
            "has_laptop": user.has_laptop,
            "has_physical_robot": user.has_physical_robot,
            "has_other_hardware": user.has_other_hardware,
            "web_dev_experience": user.web_dev_experience,
            "language_preference": user.language_preference,
            "personalization_enabled": user.personalization_enabled,
            "created_at": user.created_at
        },
        "session": {
            "access_token": "valid_token",  # This would be the actual token if needed
            "token_type": "bearer"
        }
    }

@router.post("/sign-out")
async def better_auth_sign_out():
    """
    Sign out endpoint - compatible with better-auth client
    """
    return {"success": True}