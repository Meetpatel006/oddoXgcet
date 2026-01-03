from pydantic import BaseModel
from typing import Optional

# Base schema for common attributes
class BankDetailBase(BaseModel):
    account_number: str
    bank_name: str
    ifsc_code: str
    branch_name: str

# Schema for creating a new bank detail
class BankDetailCreate(BankDetailBase):
    employee_profile_id: int

# Schema for updating a bank detail
class BankDetailUpdate(BaseModel):
    account_number: Optional[str] = None
    bank_name: Optional[str] = None
    ifsc_code: Optional[str] = None
    branch_name: Optional[str] = None

# Schema for bank detail data returned from the API
class BankDetail(BankDetailBase):
    id: int
    employee_profile_id: int

    class Config:
        from_attributes = True
