from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date
from app.models.employee import Gender, MaritalStatus

# Base schema for common attributes
class EmployeeProfileBase(BaseModel):
    first_name: str
    last_name: str
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    marital_status: Optional[MaritalStatus] = None
    nationality: Optional[str] = None
    address: Optional[str] = None
    personal_email: Optional[EmailStr] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    joining_date: Optional[date] = None
    profile_picture: Optional[str] = None
    resume_url: Optional[str] = None

# Schema for creating a new employee profile
class EmployeeProfileCreate(EmployeeProfileBase):
    user_id: int
    company_id: int
    employee_id: str
    manager_id: Optional[int] = None

# Schema for updating an employee profile
class EmployeeProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    marital_status: Optional[MaritalStatus] = None
    nationality: Optional[str] = None
    address: Optional[str] = None
    personal_email: Optional[EmailStr] = None
    department: Optional[str] = None
    manager_id: Optional[int] = None
    designation: Optional[str] = None
    joining_date: Optional[date] = None
    profile_picture: Optional[str] = None
    resume_url: Optional[str] = None

# Schema for employee profile data returned from the API
class EmployeeProfile(EmployeeProfileBase):
    id: int
    user_id: int
    company_id: int
    employee_id: str
    manager_id: Optional[int] = None

    class Config:
        from_attributes = True

class EmployeeCreateBasic(BaseModel):
    first_name: str
    last_name: str
    work_email: EmailStr
    job_position: str
    department: str
    mobile: str
    joining_date: date

class EmployeeBasicResponse(BaseModel):
    employee_id: str
    password: str
    work_email: str
    message: str

class EmployeeListResponse(EmployeeProfile):
    email: str
    status: str = "pending"

class EmployeeProfileMeResponse(EmployeeProfile):
    email: str
    company_name: Optional[str] = None
    company_logo: Optional[str] = None