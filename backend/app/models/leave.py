import enum
from sqlalchemy import Column, Integer, String, Date, Enum, ForeignKey, Text, Numeric, DateTime
from sqlalchemy.orm import relationship
from app.database import Base

class LeaveType(str, enum.Enum):
    PAID = "paid"
    SICK = "sick"
    UNPAID = "unpaid"

class LeaveStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class LeaveRequest(Base):
    """
    Represents a leave request submitted by an employee.
    """
    __tablename__ = "leave_requests"

    id = Column(Integer, primary_key=True, index=True)
    employee_profile_id = Column(Integer, ForeignKey("employee_profiles.id"), nullable=False)
    leave_type = Column(
        Enum(LeaveType, values_callable=lambda obj: [e.value for e in obj], validate_strings=True),
        nullable=False,
    )
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    total_days = Column(Numeric(4, 2), nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(Enum(LeaveStatus), nullable=False, default=LeaveStatus.PENDING)
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    comments = Column(Text, nullable=True)

    # Relationships
    employee_profile = relationship("EmployeeProfile", back_populates="leave_requests")
    approver = relationship("User")

class LeaveBalance(Base):
    """
    Represents the leave balance for an employee for a specific leave type and year.
    """
    __tablename__ = "leave_balances"

    id = Column(Integer, primary_key=True, index=True)
    employee_profile_id = Column(Integer, ForeignKey("employee_profiles.id"), nullable=False)
    leave_type = Column(
        Enum(LeaveType, values_callable=lambda obj: [e.value for e in obj], validate_strings=True),
        nullable=False,
    )
    total_days = Column(Numeric(4, 2), nullable=False)
    used_days = Column(Numeric(4, 2), default=0.0)
    remaining_days = Column(Numeric(4, 2), nullable=False)
    year = Column(Integer, nullable=False, index=True)

    # Relationship
    employee_profile = relationship("EmployeeProfile", back_populates="leave_balances")
