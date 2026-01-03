from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from decimal import Decimal
from app.models.leave import LeaveType, LeaveStatus

# --- LeaveRequest Schemas ---

# Base schema for common attributes
class LeaveRequestBase(BaseModel):
    leave_type: LeaveType
    start_date: date
    end_date: date
    reason: Optional[str] = None

# Schema for creating a new leave request
class LeaveRequestCreate(LeaveRequestBase):
    employee_profile_id: int
    total_days: Decimal

# Schema for updating a leave request (by admin/approver)
class LeaveRequestUpdate(BaseModel):
    status: Optional[LeaveStatus] = None
    comments: Optional[str] = None

# Schema for leave request data returned from the API
class LeaveRequest(LeaveRequestBase):
    id: int
    employee_profile_id: int
    total_days: Decimal
    status: LeaveStatus
    approver_id: Optional[int] = None
    approved_at: Optional[datetime] = None
    comments: Optional[str] = None

    class Config:
        from_attributes = True


# --- LeaveBalance Schemas ---

# Base schema for common attributes
class LeaveBalanceBase(BaseModel):
    leave_type: LeaveType
    year: int
    total_days: Decimal

# Schema for creating a new leave balance
class LeaveBalanceCreate(LeaveBalanceBase):
    employee_profile_id: int

# Schema for updating a leave balance
class LeaveBalanceUpdate(BaseModel):
    total_days: Optional[Decimal] = None
    used_days: Optional[Decimal] = None

# Schema for leave balance data returned from the API
class LeaveBalance(LeaveBalanceBase):
    id: int
    employee_profile_id: int
    used_days: Decimal
    remaining_days: Decimal

    class Config:
        from_attributes = True
