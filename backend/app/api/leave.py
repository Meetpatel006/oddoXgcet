from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from app.database import get_db
from app.models import User, EmployeeProfile, LeaveRequest, LeaveBalance, UserRole, LeaveStatus
from app.schemas import LeaveRequest as LeaveRequestSchema, LeaveRequestCreate, LeaveRequestUpdate, LeaveBalance as LeaveBalanceSchema
from app.auth.dependencies import get_current_active_user, get_current_active_user_with_roles

router = APIRouter()

@router.post("/apply", response_model=LeaveRequestSchema, status_code=status.HTTP_201_CREATED)
def apply_for_leave(
    leave_request_in: LeaveRequestCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Submit a new leave request.
    """
    employee_profile = db.query(EmployeeProfile).filter(EmployeeProfile.user_id == current_user.id).first()
    if not employee_profile:
        raise HTTPException(status_code=404, detail="Employee profile not found for this user")

    # Check if the leave request is for the current employee's profile
    if leave_request_in.employee_profile_id != employee_profile.id:
        raise HTTPException(status_code=403, detail="Not authorized to submit leave for this employee profile")

    # Basic validation for dates
    if leave_request_in.start_date > leave_request_in.end_date:
        raise HTTPException(status_code=400, detail="Start date cannot be after end date")

    # Calculate total days (simple calculation, can be made more complex to exclude weekends/holidays)
    delta = leave_request_in.end_date - leave_request_in.start_date
    total_days = Decimal(delta.days + 1) # +1 to include both start and end dates

    if total_days != leave_request_in.total_days:
        raise HTTPException(status_code=400, detail="Total days calculated do not match provided total days.")

    # Check leave balance (simplified for now, actual logic will be in leave_service)
    leave_balance = db.query(LeaveBalance).filter(
        LeaveBalance.employee_profile_id == employee_profile.id,
        LeaveBalance.leave_type == leave_request_in.leave_type,
        LeaveBalance.year == leave_request_in.start_date.year
    ).first()

    if not leave_balance or leave_balance.remaining_days < total_days:
        raise HTTPException(status_code=400, detail="Insufficient leave balance for this leave type.")

    db_leave_request = LeaveRequest(
        employee_profile_id=employee_profile.id,
        leave_type=leave_request_in.leave_type,
        start_date=leave_request_in.start_date,
        end_date=leave_request_in.end_date,
        total_days=total_days,
        reason=leave_request_in.reason
    )
    db.add(db_leave_request)
    db.commit()
    db.refresh(db_leave_request)
    return db_leave_request

@router.get("/my-requests", response_model=List[LeaveRequestSchema])
def get_my_leave_requests(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve the current employee's leave requests.
    """
    employee_profile = db.query(EmployeeProfile).filter(EmployeeProfile.user_id == current_user.id).first()
    if not employee_profile:
        raise HTTPException(status_code=404, detail="Employee profile not found for this user")

    leave_requests = db.query(LeaveRequest).filter(LeaveRequest.employee_profile_id == employee_profile.id).all()
    return leave_requests

@router.get("/pending", response_model=List[LeaveRequestSchema])
def get_pending_leave_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_with_roles([UserRole.ADMIN, UserRole.HR_OFFICER])),
):
    """
    Get all pending leave requests. (Admin or HR Officer only)
    """
    pending_requests = db.query(LeaveRequest).filter(LeaveRequest.status == LeaveStatus.PENDING).all()
    return pending_requests

@router.put("/{leave_id}/approve", response_model=LeaveRequestSchema)
def approve_leave_request(
    leave_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_with_roles([UserRole.ADMIN, UserRole.HR_OFFICER])),
):
    """
    Approve a pending leave request. (Admin or HR Officer only)
    """
    leave_request = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
    if not leave_request:
        raise HTTPException(status_code=404, detail="Leave request not found")

    if leave_request.status != LeaveStatus.PENDING:
        raise HTTPException(status_code=400, detail="Only pending leave requests can be approved")

    # Update leave balance
    leave_balance = db.query(LeaveBalance).filter(
        LeaveBalance.employee_profile_id == leave_request.employee_profile_id,
        LeaveBalance.leave_type == leave_request.leave_type,
        LeaveBalance.year == leave_request.start_date.year
    ).first()

    if not leave_balance or leave_balance.remaining_days < leave_request.total_days:
        raise HTTPException(status_code=400, detail="Insufficient leave balance to approve this request")

    leave_balance.used_days += leave_request.total_days
    leave_balance.remaining_days -= leave_request.total_days
    db.add(leave_balance)

    # Update leave request status
    leave_request.status = LeaveStatus.APPROVED
    leave_request.approver_id = current_user.id
    leave_request.approved_at = datetime.now()
    db.add(leave_request)
    db.commit()
    db.refresh(leave_request)
    db.refresh(leave_balance) # Refresh balance to reflect changes

    return leave_request

@router.put("/{leave_id}/reject", response_model=LeaveRequestSchema)
def reject_leave_request(
    leave_id: int,
    rejection_in: Optional[LeaveRequestUpdate] = None, # Optional to allow just rejection without comments
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_with_roles([UserRole.ADMIN, UserRole.HR_OFFICER])),
):
    """
    Reject a pending leave request. (Admin or HR Officer only)
    """
    leave_request = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
    if not leave_request:
        raise HTTPException(status_code=404, detail="Leave request not found")

    if leave_request.status != LeaveStatus.PENDING:
        raise HTTPException(status_code=400, detail="Only pending leave requests can be rejected")

    leave_request.status = LeaveStatus.REJECTED
    leave_request.approver_id = current_user.id
    leave_request.approved_at = datetime.now()
    if rejection_in and rejection_in.comments:
        leave_request.comments = rejection_in.comments
    db.add(leave_request)
    db.commit()
    db.refresh(leave_request)
    return leave_request

@router.put("/{leave_id}/cancel", response_model=LeaveRequestSchema)
def cancel_leave_request(
    leave_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Cancel a pending leave request. (Employee can cancel their own pending request)
    """
    leave_request = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
    if not leave_request:
        raise HTTPException(status_code=404, detail="Leave request not found")

    employee_profile = db.query(EmployeeProfile).filter(EmployeeProfile.id == leave_request.employee_profile_id).first()
    if not employee_profile or employee_profile.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to cancel this leave request")

    if leave_request.status != LeaveStatus.PENDING:
        raise HTTPException(status_code=400, detail="Only pending leave requests can be cancelled")

    leave_request.status = LeaveStatus.CANCELLED
    db.add(leave_request)
    db.commit()
    db.refresh(leave_request)
    return leave_request

@router.get("/balance", response_model=List[LeaveBalanceSchema])
def get_leave_balance(
    employee_profile_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieve leave balance for the current employee or a specific employee (Admin/HR).
    """
    if employee_profile_id is None: # Employee viewing their own balance
        employee_profile = db.query(EmployeeProfile).filter(EmployeeProfile.user_id == current_user.id).first()
        if not employee_profile:
            raise HTTPException(status_code=404, detail="Employee profile not found for this user")
        target_employee_profile_id = employee_profile.id
    else: # Admin/HR viewing another employee's balance
        if current_user.role not in [UserRole.ADMIN, UserRole.HR_OFFICER]:
            raise HTTPException(status_code=403, detail="Not authorized to view other employee's leave balance")
        target_employee_profile_id = employee_profile_id
        
        # Verify target employee profile exists
        if not db.query(EmployeeProfile).filter(EmployeeProfile.id == target_employee_profile_id).first():
            raise HTTPException(status_code=404, detail="Employee profile not found")

    leave_balances = db.query(LeaveBalance).filter(
        LeaveBalance.employee_profile_id == target_employee_profile_id,
        LeaveBalance.year == date.today().year # Only get balances for the current year
    ).all()
    return leave_balances
