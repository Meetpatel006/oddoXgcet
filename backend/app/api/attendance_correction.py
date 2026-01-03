from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.database import get_db
from app.models import User, Attendance, AttendanceCorrectionRequest, UserRole, CorrectionRequestStatus
from app.schemas.attendance_correction import AttendanceCorrectionRequest as AttendanceCorrectionRequestSchema, AttendanceCorrectionRequestCreate, AttendanceCorrectionRequestUpdate
from app.auth.dependencies import get_current_active_user, get_current_active_user_with_roles

router = APIRouter()

@router.post("/", response_model=AttendanceCorrectionRequestSchema, status_code=status.HTTP_201_CREATED)
def create_attendance_correction_request(
    request_in: AttendanceCorrectionRequestCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new attendance correction request.
    """
    attendance = db.query(Attendance).filter(Attendance.id == request_in.attendance_id).first()
    if not attendance:
        raise HTTPException(status_code=404, detail="Attendance record not found")
        
    # Check if the user is requesting for their own attendance
    if attendance.employee_profile.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to request correction for this attendance record")

    db_request = AttendanceCorrectionRequest(
        **request_in.model_dump(),
        requested_by_id=current_user.id
    )
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request

@router.get("/pending", response_model=List[AttendanceCorrectionRequestSchema])
def get_pending_correction_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_with_roles([UserRole.ADMIN, UserRole.HR_OFFICER])),
):
    """
    Get all pending attendance correction requests. (Admin or HR Officer only)
    """
    requests = db.query(AttendanceCorrectionRequest).filter(AttendanceCorrectionRequest.status == CorrectionRequestStatus.PENDING).all()
    return requests

@router.put("/{request_id}/approve", response_model=AttendanceCorrectionRequestSchema)
def approve_correction_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_with_roles([UserRole.ADMIN, UserRole.HR_OFFICER])),
):
    """
    Approve an attendance correction request. (Admin or HR Officer only)
    """
    db_request = db.query(AttendanceCorrectionRequest).filter(AttendanceCorrectionRequest.id == request_id).first()
    if not db_request:
        raise HTTPException(status_code=404, detail="Correction request not found")

    if db_request.status != CorrectionRequestStatus.PENDING:
        raise HTTPException(status_code=400, detail="Request is not pending")

    db_request.status = CorrectionRequestStatus.APPROVED
    db_request.reviewed_by_id = current_user.id
    db_request.reviewed_at = datetime.now()
    
    # Update the attendance record
    attendance = db.query(Attendance).filter(Attendance.id == db_request.attendance_id).first()
    if attendance:
        attendance.check_in_time = db_request.requested_check_in_time
        attendance.check_out_time = db_request.requested_check_out_time
        db.add(attendance)

    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request

@router.put("/{request_id}/reject", response_model=AttendanceCorrectionRequestSchema)
def reject_correction_request(
    request_id: int,
    rejection_in: AttendanceCorrectionRequestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_with_roles([UserRole.ADMIN, UserRole.HR_OFFICER])),
):
    """
    Reject an attendance correction request. (Admin or HR Officer only)
    """
    db_request = db.query(AttendanceCorrectionRequest).filter(AttendanceCorrectionRequest.id == request_id).first()
    if not db_request:
        raise HTTPException(status_code=404, detail="Correction request not found")

    if db_request.status != CorrectionRequestStatus.PENDING:
        raise HTTPException(status_code=400, detail="Request is not pending")

    db_request.status = CorrectionRequestStatus.REJECTED
    db_request.reviewed_by_id = current_user.id
    db_request.reviewed_at = datetime.now()
    db_request.reviewer_comments = rejection_in.reviewer_comments
    
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request

@router.get("/me", response_model=List[AttendanceCorrectionRequestSchema])
def get_my_correction_requests(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get the current employee's attendance correction requests.
    """
    requests = db.query(AttendanceCorrectionRequest).filter(AttendanceCorrectionRequest.requested_by_id == current_user.id).all()
    return requests
