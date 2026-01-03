from pydantic import BaseModel
from typing import Optional

# Base schema for common attributes
class UserSettingsBase(BaseModel):
    receive_notifications: bool = True
    theme: str = "light"
    language: str = "en"

# Schema for creating user settings (e.g., when a user registers)
class UserSettingsCreate(UserSettingsBase):
    user_id: int

# Schema for updating user settings
class UserSettingsUpdate(BaseModel):
    receive_notifications: Optional[bool] = None
    theme: Optional[str] = None
    language: Optional[str] = None

# Schema for user settings data returned from the API
class UserSettings(UserSettingsBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
