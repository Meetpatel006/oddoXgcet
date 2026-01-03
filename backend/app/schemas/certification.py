from pydantic import BaseModel
from typing import Optional
from datetime import date

# Base schema for common attributes
class CertificationBase(BaseModel):
    name: str
    issuing_organization: str
    issue_date: date
    expiry_date: Optional[date] = None
    credential_id: Optional[str] = None

# Schema for creating a new certification
class CertificationCreate(CertificationBase):
    employee_profile_id: int

# Schema for updating a certification
class CertificationUpdate(BaseModel):
    name: Optional[str] = None
    issuing_organization: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    credential_id: Optional[str] = None

# Schema for certification data returned from the API
class Certification(CertificationBase):
    id: int
    employee_profile_id: int

    class Config:
        from_attributes = True
