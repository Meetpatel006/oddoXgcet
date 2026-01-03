import enum
from sqlalchemy import Column, Integer, String, Date, Enum, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"

class MaritalStatus(str, enum.Enum):
    SINGLE = "single"
    MARRIED = "married"
    DIVORCED = "divorced"
    WIDOWED = "widowed"

class EmployeeProfile(Base):
    """
    Represents the detailed profile of an employee.
    This model stores personal and professional information about an employee.
    """
    __tablename__ = "employee_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    employee_id = Column(String, unique=True, index=True, nullable=False)
    
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(Enum(Gender), nullable=True)
    marital_status = Column(Enum(MaritalStatus), nullable=True)
    nationality = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    personal_email = Column(String, unique=True, nullable=True)
    
    department = Column(String, nullable=True)
    manager_id = Column(Integer, ForeignKey("employee_profiles.id"), nullable=True)
    designation = Column(String, nullable=True)
    joining_date = Column(Date, nullable=True)
    profile_picture = Column(String, nullable=True) # URL to the image

    # Relationships
    user = relationship("User", back_populates="employee_profile")
    company = relationship("Company", back_populates="employee_profiles")
    manager = relationship("EmployeeProfile", remote_side=[id])

    bank_details = relationship("BankDetail", back_populates="employee_profile", cascade="all, delete-orphan")
    certifications = relationship("Certification", back_populates="employee_profile", cascade="all, delete-orphan")
    salary_structure = relationship("SalaryStructure", back_populates="employee_profile", uselist=False, cascade="all, delete-orphan")
    attendances = relationship("Attendance", back_populates="employee_profile", cascade="all, delete-orphan")
    leave_requests = relationship("LeaveRequest", back_populates="employee_profile", cascade="all, delete-orphan")
    leave_balances = relationship("LeaveBalance", back_populates="employee_profile", cascade="all, delete-orphan")

    # Association with Skills
    employee_skills = relationship("EmployeeSkill", back_populates="employee_profile", cascade="all, delete-orphan")

class EmployeeSkill(Base):
    """Association table between EmployeeProfile and Skill."""
    __tablename__ = 'employee_skills'
    employee_profile_id = Column(Integer, ForeignKey('employee_profiles.id'), primary_key=True)
    skill_id = Column(Integer, ForeignKey('skills.id'), primary_key=True)

    employee_profile = relationship("EmployeeProfile", back_populates="employee_skills")
    skill = relationship("Skill", back_populates="employee_skills")
