from sqlalchemy import Column, Integer, Boolean, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class UserSettings(Base):
    """
    Represents user-specific settings and preferences.
    """
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Example settings
    receive_notifications = Column(Boolean, default=True)
    theme = Column(String, default="light")
    language = Column(String, default="en")

    # Relationship
    user = relationship("User", back_populates="settings")
