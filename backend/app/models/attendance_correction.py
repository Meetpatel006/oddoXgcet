import enum
from sqlalchemy import Column, Integer, DateTime, Enum, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class CorrectionRequestStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class AttendanceCorrectionRequest(Base):
    """
    Represents a request to correct an attendance record.
    """
    __tablename__ = "attendance_correction_requests"

    id = Column(Integer, primary_key=True, index=True)
    attendance_id = Column(Integer, ForeignKey("attendances.id"), nullable=False)
    requested_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reason = Column(Text, nullable=False)
    requested_check_in_time = Column(DateTime, nullable=True)
    requested_check_out_time = Column(DateTime, nullable=True)
    status = Column(Enum(CorrectionRequestStatus), nullable=False, default=CorrectionRequestStatus.PENDING)
    reviewed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    reviewer_comments = Column(Text, nullable=True)

    # Relationships
    attendance = relationship("Attendance")
    requested_by = relationship("User", foreign_keys=[requested_by_id])
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])
