from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.attendance_correction import CorrectionRequestStatus

class AttendanceCorrectionRequestBase(BaseModel):
    reason: str
    requested_check_in_time: Optional[datetime] = None
    requested_check_out_time: Optional[datetime] = None

class AttendanceCorrectionRequestCreate(AttendanceCorrectionRequestBase):
    attendance_id: int

class AttendanceCorrectionRequestUpdate(BaseModel):
    status: CorrectionRequestStatus
    reviewer_comments: Optional[str] = None

class AttendanceCorrectionRequest(AttendanceCorrectionRequestBase):
    id: int
    attendance_id: int
    requested_by_id: int
    status: CorrectionRequestStatus
    reviewed_by_id: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    reviewer_comments: Optional[str] = None

    class Config:
        from_attributes = True
