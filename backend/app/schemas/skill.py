from pydantic import BaseModel
from typing import Optional

# Base schema for common attributes
class SkillBase(BaseModel):
    name: str
    category: Optional[str] = None

# Schema for creating a new skill
class SkillCreate(SkillBase):
    pass

# Schema for updating a skill
class SkillUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None

# Schema for skill data returned from the API
class Skill(SkillBase):
    id: int

    class Config:
        from_attributes = True

# Schema for the association between Employee and Skill
class EmployeeSkillBase(BaseModel):
    employee_profile_id: int
    skill_id: int

class EmployeeSkillCreate(EmployeeSkillBase):
    pass

class EmployeeSkill(EmployeeSkillBase):
    class Config:
        from_attributes = True
