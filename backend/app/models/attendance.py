import enum
from sqlalchemy import Column, Integer, Date, DateTime, Enum, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class AttendanceStatus(str, enum.Enum):
    PRESENT = "present"
    ABSENT = "absent"
    HALF_DAY = "half_day"
    LEAVE = "leave"

class Attendance(Base):
    """
    Represents an employee's attendance record for a specific day.
    """
    __tablename__ = "attendances"

    id = Column(Integer, primary_key=True, index=True)
    employee_profile_id = Column(Integer, ForeignKey("employee_profiles.id"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    check_in_time = Column(DateTime, nullable=True)
    check_out_time = Column(DateTime, nullable=True)
    status = Column(Enum(AttendanceStatus), nullable=False)
    notes = Column(Text, nullable=True)

    # Relationship
    employee_profile = relationship("EmployeeProfile", back_populates="attendances")
