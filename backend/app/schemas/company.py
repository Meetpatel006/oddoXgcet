from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Base schema for common attributes
class CompanyBase(BaseModel):
    name: str
    logo: Optional[str] = None

# Schema for creating a new company
class CompanyCreate(CompanyBase):
    pass

# Schema for updating a company
class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    logo: Optional[str] = None

# Schema for company data returned from the API
class Company(CompanyBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
