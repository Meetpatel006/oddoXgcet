from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import relationship
from app.database import Base

class ActivityLog(Base):
    """
    Records significant actions performed by users within the system.
    """
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String, nullable=False) # e.g., "User logged in", "Employee profile updated"
    details = Column(Text, nullable=True) # JSON string or detailed text description
    timestamp = Column(DateTime, server_default=func.now())

    # Relationship
    user = relationship("User")
