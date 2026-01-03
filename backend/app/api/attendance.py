from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime, time, timedelta
from app.database import get_db
from app.models import User, EmployeeProfile, Attendance, AttendanceStatus, UserRole
from app.schemas import Attendance as AttendanceSchema, AttendanceManualCreate
from app.auth.dependencies import get_current_active_user, get_current_active_user_with_roles

router = APIRouter()

@router.post("/check-in", response_model=AttendanceSchema, status_code=status.HTTP_201_CREATED)
def check_in(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Check-in for the current employee. Creates a new attendance record for the day.
    """
    employee_profile = db.query(EmployeeProfile).filter(EmployeeProfile.user_id == current_user.id).first()
    if not employee_profile:
        raise HTTPException(status_code=404, detail="Employee profile not found for this user")

    today = date.today()
    
    # Check if there is already an attendance record for today
    existing_attendance = db.query(Attendance).filter(
        Attendance.employee_profile_id == employee_profile.id,
        Attendance.date == today
    ).first()

    if existing_attendance and existing_attendance.check_in_time:
        raise HTTPException(status_code=400, detail="Already checked in for today")

    if existing_attendance:
        # Update existing record (e.g. if created by admin as ABSENT)
        existing_attendance.check_in_time = datetime.now()
        existing_attendance.status = AttendanceStatus.PRESENT
        db.add(existing_attendance)
        db.commit()
        db.refresh(existing_attendance)
        return existing_attendance
    else:
        # Create new record
        new_attendance = Attendance(
            employee_profile_id=employee_profile.id,
            date=today,
            check_in_time=datetime.now(),
            status=AttendanceStatus.PRESENT
        )
        db.add(new_attendance)
        db.commit()
        db.refresh(new_attendance)
        return new_attendance

@router.post("/check-out", response_model=AttendanceSchema)
def check_out(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Check-out for the current employee. Updates the attendance record for the day.
    """
    employee_profile = db.query(EmployeeProfile).filter(EmployeeProfile.user_id == current_user.id).first()
    if not employee_profile:
        raise HTTPException(status_code=404, detail="Employee profile not found for this user")

    today = date.today()
    
    attendance_record = db.query(Attendance).filter(
        Attendance.employee_profile_id == employee_profile.id,
        Attendance.date == today
    ).first()

    if not attendance_record or not attendance_record.check_in_time:
        raise HTTPException(status_code=400, detail="You have not checked in today")

    if attendance_record.check_out_time:
        raise HTTPException(status_code=400, detail="Already checked out for today")

    attendance_record.check_out_time = datetime.now()
    db.add(attendance_record)
    db.commit()
    db.refresh(attendance_record)
    return attendance_record

@router.get("/daily", response_model=List[AttendanceSchema])
def get_daily_attendance(
    day: date = date.today(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_with_roles([UserRole.ADMIN, UserRole.HR_OFFICER])),
):
    """
    Get all attendance records for a specific day. (Admin or HR Officer only)
    """
    attendances = db.query(Attendance).filter(Attendance.date == day).all()
    return attendances

@router.get("/weekly", response_model=List[AttendanceSchema])
def get_weekly_attendance(
    day_in_week: date = date.today(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_with_roles([UserRole.ADMIN, UserRole.HR_OFFICER])),
):
    """
    Get all attendance records for a specific week. (Admin or HR Officer only)
    """
    start_of_week = day_in_week - timedelta(days=day_in_week.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    attendances = db.query(Attendance).filter(
        Attendance.date >= start_of_week,
        Attendance.date <= end_of_week
    ).all()
    return attendances

@router.get("/me", response_model=List[AttendanceSchema])
def get_my_attendance_history(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get the current employee's attendance history.
    """
    employee_profile = db.query(EmployeeProfile).filter(EmployeeProfile.user_id == current_user.id).first()
    if not employee_profile:
        raise HTTPException(status_code=404, detail="Employee profile not found for this user")

    attendances = db.query(Attendance).filter(
        Attendance.employee_profile_id == employee_profile.id
    ).order_by(Attendance.date.desc()).offset(skip).limit(limit).all()
    
    return attendances

@router.get("/all", response_model=List[AttendanceSchema])
def get_all_attendance_records(
    skip: int = 0,
    limit: int = 100,
    employee_profile_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_with_roles([UserRole.ADMIN, UserRole.HR_OFFICER])),
):
    """
    Get all attendance records. (Admin or HR Officer only)
    """
    query = db.query(Attendance)
    if employee_profile_id:
        query = query.filter(Attendance.employee_profile_id == employee_profile_id)
        
    attendances = query.order_by(Attendance.date.desc()).offset(skip).limit(limit).all()
    return attendances

@router.post("/manual", response_model=AttendanceSchema)
def manual_attendance_entry(
    attendance_in: AttendanceManualCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_with_roles([UserRole.ADMIN, UserRole.HR_OFFICER])),
):
    """
    Manually create or update an attendance record. (Admin or HR Officer only)
    """
    employee_profile = db.query(EmployeeProfile).filter(EmployeeProfile.id == attendance_in.employee_profile_id).first()
    if not employee_profile:
        raise HTTPException(status_code=404, detail="Employee profile not found")

    attendance = db.query(Attendance).filter(
        Attendance.employee_profile_id == attendance_in.employee_profile_id,
        Attendance.date == attendance_in.date
    ).first()

    if attendance:
        # Update existing record
        attendance.check_in_time = attendance_in.check_in_time
        attendance.check_out_time = attendance_in.check_out_time
        attendance.status = attendance_in.status
        attendance.notes = attendance_in.notes
    else:
        # Create new record
        attendance = Attendance(**attendance_in.model_dump())

    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    return attendance
