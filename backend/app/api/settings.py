from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, UserSettings
from app.schemas import UserSettings as UserSettingsSchema, UserSettingsUpdate
from app.auth.dependencies import get_current_active_user

router = APIRouter()

@router.get("/me", response_model=UserSettingsSchema)
def get_my_settings(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve the current user's settings.
    """
    user_settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    if not user_settings:
        # Create default settings if none exist
        user_settings = UserSettings(user_id=current_user.id)
        db.add(user_settings)
        db.commit()
        db.refresh(user_settings)
    return user_settings

@router.put("/me", response_model=UserSettingsSchema)
def update_my_settings(
    settings_update: UserSettingsUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update the current user's settings.
    """
    user_settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    if not user_settings:
        raise HTTPException(status_code=404, detail="User settings not found")

    update_data = settings_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user_settings, field, value)
    
    db.add(user_settings)
    db.commit()
    db.refresh(user_settings)
    return user_settings
