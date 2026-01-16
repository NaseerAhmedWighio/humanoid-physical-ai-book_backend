from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from ..services.auth_service import auth_service, UserCreate, UserLogin, Token, UserResponse, UserRegistration
from ..database import get_db
from datetime import timedelta

router = APIRouter(
    prefix="/v1/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user
    """
    try:
        user = auth_service.create_user(db, user_data)
        return UserResponse(
            id=str(user.id),
            email=user.email,
            has_mobile=user.has_mobile,
            has_laptop=user.has_laptop,
            has_physical_robot=user.has_physical_robot,
            has_other_hardware=user.has_other_hardware,
            web_dev_experience=user.web_dev_experience,
            language_preference=user.language_preference,
            personalization_enabled=user.personalization_enabled,
            created_at=user.created_at
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during registration: {str(e)}"
        )

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """
    Login with email and password
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
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def get_current_user(user = Depends(auth_service.get_current_user)):
    """
    Get current user info
    """
    return UserResponse(
        id=str(user.id),
        email=user.email,
        has_mobile=user.has_mobile,
        has_laptop=user.has_laptop,
        has_physical_robot=user.has_physical_robot,
        has_other_hardware=user.has_other_hardware,
        web_dev_experience=user.web_dev_experience,
        language_preference=user.language_preference,
        personalization_enabled=user.personalization_enabled,
        created_at=user.created_at
    )

@router.post("/update-preferences", response_model=UserResponse)
async def update_user_preferences(
    user_data: UserCreate,
    user = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user preferences (hardware availability)
    """
    user.has_mobile = user_data.has_mobile
    user.has_laptop = user_data.has_laptop
    user.has_physical_robot = user_data.has_physical_robot
    user.has_other_hardware = user_data.has_other_hardware
    user.web_dev_experience = user_data.web_dev_experience

    db.commit()
    db.refresh(user)

    return UserResponse(
        id=str(user.id),
        email=user.email,
        has_mobile=user.has_mobile,
        has_laptop=user.has_laptop,
        has_physical_robot=user.has_physical_robot,
        has_other_hardware=user.has_other_hardware,
        web_dev_experience=user.web_dev_experience,
        language_preference=user.language_preference,
        personalization_enabled=user.personalization_enabled,
        created_at=user.created_at
    )