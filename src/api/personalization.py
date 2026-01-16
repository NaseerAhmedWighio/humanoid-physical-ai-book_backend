from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime
import logging
from ..models.user_preferences import UserPreference, UserPreferenceCreate, UserPreferenceUpdate
from ..models.personalized_content import PersonalizedContent
from ..services.user_preferences_service import UserPreferencesService
from ..services.personalized_content_service import PersonalizedContentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/personalization", tags=["personalization"])

# Initialize services
user_prefs_service = UserPreferencesService()
content_service = PersonalizedContentService()


@router.get("/content/{content_id}")
async def get_personalized_content(
    content_id: str,
    hardware_preference: Optional[str] = None,
    user_id: Optional[str] = None
):
    """
    Get personalized content based on user preferences
    """
    try:
        # If user_id is provided, get their preferences
        user_pref = None
        if user_id:
            user_pref = await user_prefs_service.get_user_preference(user_id)

        # Determine hardware preference to use
        target_hardware = hardware_preference
        if not target_hardware and user_pref:
            target_hardware = user_pref.hardware_preference

        # If still no hardware preference, default to 'laptop'
        if not target_hardware:
            target_hardware = "laptop"

        # For this endpoint, we'll return the original content with personalization applied
        # In a real implementation, this would fetch the actual content from the CMS
        # and apply personalization based on the hardware preference

        # For now, return a mock response
        # In a real implementation, we would fetch the original content by content_id
        # and then generate personalized content
        original_content = f"Original content for ID: {content_id}"

        # Attempt to generate personalized content
        try:
            personalized_content = await content_service.generate_personalized_content(
                original_content,
                target_hardware
            )
        except Exception as gen_error:
            logger.error(f"Error generating personalized content: {str(gen_error)}")
            # Fallback to original content
            personalized_content = original_content

        # Create or get existing personalized content
        try:
            existing_content = await content_service.get_personalized_content_by_user_and_original(
                user_id or "anonymous",
                content_id
            )

            if existing_content:
                # Update existing content
                updated_content = await content_service.update_personalized_content(
                    existing_content.id,
                    PersonalizedContentUpdate(
                        personalized_content=personalized_content,
                        hardware_preference=target_hardware
                    )
                )
            else:
                # Create new personalized content
                updated_content = await content_service.create_personalized_content(
                    content=PersonalizedContent(
                        original_content_id=content_id,
                        user_id=user_id or "anonymous",
                        hardware_preference=target_hardware,
                        personalized_content=personalized_content
                    )
                )
        except Exception as db_error:
            logger.error(f"Error managing personalized content in DB: {str(db_error)}")
            # Fallback: return content without DB persistence
            updated_content = PersonalizedContent(
                id=f"pc_{content_id}_{user_id or 'anonymous'}",
                original_content_id=content_id,
                user_id=user_id or "anonymous",
                hardware_preference=target_hardware,
                personalized_content=personalized_content,
                created_at=datetime.now()
            )

        return {
            "content": updated_content.personalized_content,
            "isPersonalized": True,
            "hardwarePreference": target_hardware
        }
    except Exception as e:
        logger.error(f"Error retrieving personalized content: {str(e)}")
        # Ultimate fallback: return original content with error flag
        return {
            "content": f"Original content for ID: {content_id}",
            "isPersonalized": False,
            "hardwarePreference": "laptop",
            "error": "Service temporarily unavailable, showing original content"
        }


@router.post("/toggle")
async def toggle_personalization(user_id: str, enabled: bool):
    """
    Toggle personalization on/off for the current user
    """
    try:
        # Update user preferences to enable/disable personalization
        user_pref = await user_prefs_service.get_user_preference(user_id)

        if not user_pref:
            # Create new preferences if they don't exist
            new_pref = UserPreferenceCreate(
                user_id=user_id,
                hardware_preference="laptop",  # Default preference
                personalization_enabled=enabled
            )
            updated_pref = await user_prefs_service.create_user_preference(new_pref)
        else:
            # Update existing preferences
            update_data = UserPreferenceUpdate(personalization_enabled=enabled)
            updated_pref = await user_prefs_service.update_user_preference(user_id, update_data)

        if not updated_pref:
            raise HTTPException(status_code=404, detail="User preferences not found")

        return {
            "success": True,
            "personalizationEnabled": updated_pref.personalization_enabled
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error toggling personalization: {str(e)}")


@router.get("/preferences/{user_id}")
async def get_user_preferences(user_id: str):
    """
    Get user preferences
    """
    try:
        user_pref = await user_prefs_service.get_user_preference(user_id)
        if not user_pref:
            raise HTTPException(status_code=404, detail="User preferences not found")

        return user_pref
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving user preferences: {str(e)}")


@router.put("/preferences/{user_id}")
async def update_user_preferences(user_id: str, preferences: UserPreferenceUpdate):
    """
    Update user preferences
    """
    try:
        updated_pref = await user_prefs_service.update_user_preference(user_id, preferences)
        if not updated_pref:
            raise HTTPException(status_code=404, detail="User preferences not found")

        return updated_pref
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating user preferences: {str(e)}")