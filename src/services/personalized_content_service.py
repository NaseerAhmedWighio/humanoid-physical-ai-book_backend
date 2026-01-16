from typing import Optional
from datetime import datetime
from ..models.personalized_content import PersonalizedContent, PersonalizedContentCreate, PersonalizedContentUpdate
import logging

logger = logging.getLogger(__name__)


class PersonalizedContentService:
    def __init__(self):
        # In a real implementation, this would connect to a database
        # For now, using in-memory storage for demonstration
        self.content_db = {}

    async def get_personalized_content(self, content_id: str) -> Optional[PersonalizedContent]:
        """Get personalized content by ID"""
        try:
            content_data = self.content_db.get(content_id)
            if content_data:
                return PersonalizedContent(**content_data)
            return None
        except Exception as e:
            logger.error(f"Error getting personalized content by ID {content_id}: {str(e)}")
            return None

    async def create_personalized_content(self, content: PersonalizedContentCreate) -> PersonalizedContent:
        """Create new personalized content"""
        try:
            content_id = f"pc_{content.original_content_id}_{content.user_id}"
            now = datetime.now()
            content_data = {
                "id": content_id,
                "original_content_id": content.original_content_id,
                "user_id": content.user_id,
                "hardware_preference": content.hardware_preference,
                "personalized_content": content.personalized_content,
                "created_at": now
            }
            self.content_db[content_id] = content_data
            return PersonalizedContent(**content_data)
        except Exception as e:
            logger.error(f"Error creating personalized content: {str(e)}")
            # Return a fallback content object
            return PersonalizedContent(
                id=f"pc_{content.original_content_id}_{content.user_id}",
                original_content_id=content.original_content_id,
                user_id=content.user_id,
                hardware_preference=content.hardware_preference,
                personalized_content=content.personalized_content,
                created_at=now
            )

    async def update_personalized_content(self, content_id: str, update_data: PersonalizedContentUpdate) -> Optional[PersonalizedContent]:
        """Update personalized content"""
        try:
            existing = await self.get_personalized_content(content_id)
            if not existing:
                return None

            content_data = self.content_db[content_id]
            if update_data.personalized_content is not None:
                content_data["personalized_content"] = update_data.personalized_content
            if update_data.hardware_preference is not None:
                content_data["hardware_preference"] = update_data.hardware_preference

            self.content_db[content_id] = content_data
            return PersonalizedContent(**content_data)
        except Exception as e:
            logger.error(f"Error updating personalized content {content_id}: {str(e)}")
            return None

    async def get_personalized_content_by_user_and_original(self, user_id: str, original_content_id: str) -> Optional[PersonalizedContent]:
        """Get personalized content by user and original content ID"""
        try:
            content_id = f"pc_{original_content_id}_{user_id}"
            return await self.get_personalized_content(content_id)
        except Exception as e:
            logger.error(f"Error getting personalized content for user {user_id} and content {original_content_id}: {str(e)}")
            return None

    async def generate_personalized_content(self, original_content: str, hardware_preference: str) -> str:
        """Generate personalized content based on hardware preference"""
        try:
            # This is a simplified implementation
            # In a real system, this would use more sophisticated transformation logic
            if hardware_preference == "mobile":
                # Add mobile-specific formatting and optimizations
                return f"<!-- Mobile optimized -->\n{original_content}\n<!-- End mobile optimization -->"
            elif hardware_preference == "laptop":
                # Add laptop/desktop-specific formatting
                return f"<!-- Desktop optimized -->\n{original_content}\n<!-- End desktop optimization -->"
            elif hardware_preference == "physical_robot":
                # Add physical robot-specific content
                return f"<!-- Physical Robot Content -->\n{original_content}\n<!-- End Robot-specific content -->"
            else:
                # Return original content if preference is not recognized
                return original_content
        except Exception as e:
            logger.error(f"Error generating personalized content for hardware {hardware_preference}: {str(e)}")
            # Fallback to original content
            return original_content

    async def get_fallback_content(self, original_content: str) -> str:
        """Get fallback content when personalization service is unavailable"""
        try:
            # Provide a safe fallback that returns the original content with minimal processing
            return original_content
        except Exception as e:
            logger.error(f"Error generating fallback content: {str(e)}")
            # Ultimate fallback - return empty string if all else fails
            return original_content if original_content else ""