from typing import Optional
from datetime import datetime
from ..models.user_preferences import UserPreference, UserPreferenceCreate, UserPreferenceUpdate


class UserPreferencesService:
    def __init__(self):
        # In a real implementation, this would connect to a database
        # For now, using in-memory storage for demonstration
        self.preferences_db = {}

    async def get_user_preference(self, user_id: str) -> Optional[UserPreference]:
        """Get user preferences by user ID"""
        pref_data = self.preferences_db.get(user_id)
        if pref_data:
            return UserPreference(**pref_data)
        return None

    async def create_user_preference(self, user_preference: UserPreferenceCreate) -> UserPreference:
        """Create new user preferences"""
        pref_id = f"pref_{user_preference.user_id}"
        now = datetime.now()
        pref_data = {
            "id": pref_id,
            "user_id": user_preference.user_id,
            "hardware_preference": user_preference.hardware_preference,
            "personalization_enabled": user_preference.personalization_enabled,
            "created_at": now,
            "updated_at": now
        }
        self.preferences_db[user_preference.user_id] = pref_data
        return UserPreference(**pref_data)

    async def update_user_preference(self, user_id: str, update_data: UserPreferenceUpdate) -> Optional[UserPreference]:
        """Update user preferences"""
        existing = await self.get_user_preference(user_id)
        if not existing:
            return None

        pref_data = self.preferences_db[user_id]
        if update_data.hardware_preference is not None:
            pref_data["hardware_preference"] = update_data.hardware_preference
        if update_data.personalization_enabled is not None:
            pref_data["personalization_enabled"] = update_data.personalization_enabled
        pref_data["updated_at"] = datetime.now()

        self.preferences_db[user_id] = pref_data
        return UserPreference(**pref_data)

    async def toggle_personalization(self, user_id: str, enabled: bool) -> Optional[UserPreference]:
        """Toggle personalization for a user"""
        update_data = UserPreferenceUpdate(personalization_enabled=enabled)
        return await self.update_user_preference(user_id, update_data)