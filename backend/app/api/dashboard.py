from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel # Added this import
from app.database import get_db
from app.models import User, EmployeeProfile, Attendance, LeaveBalance, UserRole, LeaveRequest, LeaveStatus
from app.schemas import EmployeeProfile as EmployeeProfileSchema, Attendance as AttendanceSchema, LeaveBalance as LeaveBalanceSchema
from app.auth.dependencies import get_current_active_user, get_current_active_user_with_roles
from datetime import date
from typing import List, Optional

router = APIRouter()

class EmployeeDashboardSummary(BaseModel):
    profile: EmployeeProfileSchema
    today_attendance: Optional[AttendanceSchema] = None
    leave_balances: List[LeaveBalanceSchema]
    # recent_activity: List[ActivitySchema] # Assuming ActivitySchema would be defined later

class AdminDashboardSummary(BaseModel):
    employee_count: int
    active_employee_count: int
    pending_leave_requests_count: int
    # attendance_summary: Optional[dict] = None # To be implemented
    # recent_activities: List[ActivitySchema] # To be implemented

@router.get("/me", response_model=EmployeeDashboardSummary)
def get_employee_dashboard_summary(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve dashboard data for the current employee.
    """
    employee_profile = db.query(EmployeeProfile).filter(EmployeeProfile.user_id == current_user.id).first()
    if not employee_profile:
        raise HTTPException(status_code=404, detail="Employee profile not found for this user")

    today_attendance = db.query(Attendance).filter(
        Attendance.employee_profile_id == employee_profile.id,
        Attendance.date == date.today()
    ).first()

    leave_balances = db.query(LeaveBalance).filter(
        LeaveBalance.employee_profile_id == employee_profile.id,
        LeaveBalance.year == date.today().year
    ).all()

    return EmployeeDashboardSummary(
        profile=employee_profile,
        today_attendance=today_attendance,
        leave_balances=leave_balances,
        # recent_activity=[] # Placeholder
    )

@router.get("/admin", response_model=AdminDashboardSummary)
def get_admin_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_with_roles([UserRole.ADMIN, UserRole.HR_OFFICER])),
):
    """
    Retrieve dashboard data for administrators and HR officers.
    """
    employee_count = db.query(EmployeeProfile).count()
    active_employee_count = db.query(User).filter(User.is_active == True).count()
    pending_leave_requests_count = db.query(LeaveRequest).filter(LeaveRequest.status == LeaveStatus.PENDING).count()
    
    return AdminDashboardSummary(
        employee_count=employee_count,
        active_employee_count=active_employee_count,
        pending_leave_requests_count=pending_leave_requests_count,
    )
