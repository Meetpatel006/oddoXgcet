from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from app.models.attendance import AttendanceStatus

# Base schema for common attributes
class AttendanceBase(BaseModel):
    date: date
    status: AttendanceStatus
    notes: Optional[str] = None

# Schema for creating a new attendance record
class AttendanceCreate(AttendanceBase):
    employee_profile_id: int
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None

# Schema for manual attendance entry
class AttendanceManualCreate(BaseModel):
    employee_profile_id: int
    date: date
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    status: AttendanceStatus
    notes: Optional[str] = None

# Schema for updating an attendance record
class AttendanceUpdate(BaseModel):
    date: Optional[date] = None
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    status: Optional[AttendanceStatus] = None
    notes: Optional[str] = None

# Schema for attendance data returned from the API
class Attendance(AttendanceBase):
    id: int
    employee_profile_id: int
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None

    class Config:
        from_attributes = True
