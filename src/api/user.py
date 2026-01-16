from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..services.auth_service import auth_service, UserResponse
from ..database import get_db

router = APIRouter(
    prefix="/v1/user",
    tags=["user"],
    responses={404: {"description": "Not found"}},
)

@router.get("/preferences", response_model=UserResponse)
async def get_user_preferences(user = Depends(auth_service.get_current_user)):
    """
    Get current user preferences
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

@router.put("/preferences", response_model=UserResponse)
async def update_user_preferences(
    user_data: dict,
    user = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user preferences
    """
    # Update user preferences based on provided data
    if 'has_mobile' in user_data:
        user.has_mobile = user_data['has_mobile']
    if 'has_laptop' in user_data:
        user.has_laptop = user_data['has_laptop']
    if 'has_physical_robot' in user_data:
        user.has_physical_robot = user_data['has_physical_robot']
    if 'has_other_hardware' in user_data:
        user.has_other_hardware = user_data['has_other_hardware']
    if 'web_dev_experience' in user_data:
        user.web_dev_experience = user_data['web_dev_experience']
    if 'language_preference' in user_data:
        user.language_preference = user_data['language_preference']
    if 'personalization_enabled' in user_data:
        user.personalization_enabled = user_data['personalization_enabled']

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