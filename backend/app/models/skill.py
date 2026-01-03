from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base

class Skill(Base):
    """
    Represents a professional skill.
    Skills can be associated with multiple employees.
    """
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    category = Column(String, index=True, nullable=True)

    # Association with EmployeeProfile
    employee_skills = relationship("EmployeeSkill", back_populates="skill", cascade="all, delete-orphan")
