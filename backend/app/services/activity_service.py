from sqlalchemy.orm import Session
from app.models import ActivityLog
from app.schemas import ActivityLogCreate
from typing import Optional # Added this import

def log_activity(
    db: Session, 
    user_id: int, 
    action: str, 
    details: Optional[str] = None
):
    """
    Logs an activity performed by a user.
    """
    activity = ActivityLog(user_id=user_id, action=action, details=details)
    db.add(activity)
    db.commit()
    db.refresh(activity)
