from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Response
from sqlalchemy.orm import Session
from sqlalchemy import extract
from typing import List
import shutil
import secrets
import string
from pathlib import Path
from datetime import date
from app.database import get_db
from app.models import User, EmployeeProfile, UserRole, BankDetail, Skill, EmployeeSkill, Certification, Attendance, LeaveRequest, LeaveStatus, UserSettings, LeaveBalance, LeaveType, Company
from decimal import Decimal
from app.schemas import EmployeeProfile as EmployeeProfileSchema, EmployeeProfileUpdate, BankDetail as BankDetailSchema, BankDetailCreate, BankDetailUpdate, Skill as SkillSchema, EmployeeSkillCreate, Certification as CertificationSchema, CertificationCreate, CertificationUpdate, EmployeeListResponse, EmployeeCreateBasic, EmployeeBasicResponse, EmployeeProfileMeResponse
from app.auth.security import get_password_hash

from app.auth.dependencies import get_current_active_user, get_current_active_user_with_roles

router = APIRouter()

UPLOAD_DIR = Path("static/profile_pictures")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/", response_model=EmployeeBasicResponse, status_code=status.HTTP_201_CREATED)
def create_employee(
    employee_in: EmployeeCreateBasic,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_with_roles([UserRole.ADMIN, UserRole.HR_OFFICER])),
):
    """
    Create a new employee with basic information.
    Auto-generates Login ID and Password.
    """
    # 1. Check if email already exists
    if db.query(User).filter(User.email == employee_in.work_email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # 2. Generate Login ID
    # Format: OI + First 2 First + First 2 Last + Year + Serial
    # Example: OIJODO20220001
    
    first_part = employee_in.first_name[:2].upper()
    last_part = employee_in.last_name[:2].upper() if employee_in.last_name else "XX"
    year = employee_in.joining_date.year
    
    # Find max serial for this year
    # We look for employees joined in this year
    employees_this_year = db.query(EmployeeProfile).filter(extract('year', EmployeeProfile.joining_date) == year).all()
    
    max_serial = 0
    for emp in employees_this_year:
        # Try to extract serial from the end of employee_id
        # Assuming format ends with YYYYNNNN
        try:
            # ID might be OIJODO20220001
            # Last 4 digits are serial
            serial_str = emp.employee_id[-4:]
            if serial_str.isdigit():
                max_serial = max(max_serial, int(serial_str))
        except:
            pass
            
    new_serial = max_serial + 1
    serial_str = f"{new_serial:04d}"
    
    login_id = f"OI{first_part}{last_part}{year}{serial_str}"
    
    # Ensure uniqueness of login_id (just in case)
    while db.query(EmployeeProfile).filter(EmployeeProfile.employee_id == login_id).first():
        new_serial += 1
        serial_str = f"{new_serial:04d}"
        login_id = f"OI{first_part}{last_part}{year}{serial_str}"

    # 3. Generate Password
    alphabet = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(alphabet) for i in range(12))
    hashed_password = get_password_hash(password)

    # 4. Create User
    # We use work_email as the User.email
    db_user = User(
        email=employee_in.work_email,
        hashed_password=hashed_password,
        role=UserRole.EMPLOYEE,
        is_active=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # 5. Create UserSettings
    user_settings = UserSettings(user_id=db_user.id)
    db.add(user_settings)
    
    # 6. Get Company ID (from current user's profile)
    # HR/Admin must have a profile and company
    hr_profile = db.query(EmployeeProfile).filter(EmployeeProfile.user_id == current_user.id).first()
    if hr_profile:
        company_id = hr_profile.company_id
    else:
        # Fallback if admin has no profile (should not happen in normal flow)
        # Try to find any company or create one? 
        # For now, assume ID 1 exists or fail.
        company_id = 1 

    # 7. Create EmployeeProfile
    new_profile = EmployeeProfile(
        user_id=db_user.id,
        company_id=company_id,
        employee_id=login_id,
        first_name=employee_in.first_name,
        last_name=employee_in.last_name,
        phone=employee_in.mobile,
        designation=employee_in.job_position,
        department=employee_in.department,
        joining_date=employee_in.joining_date,
        # personal_email is optional, we don't set it from work_email
    )
    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)
    
    # 8. Seed default Leave Balances for the current year
    current_year = employee_in.joining_date.year
    leave_defaults = [
        (LeaveType.PAID, 24),
        (LeaveType.SICK, 10),
        (LeaveType.UNPAID, 0)
    ]
    for leave_type, total in leave_defaults:
        new_balance = LeaveBalance(
            employee_profile_id=new_profile.id,
            leave_type=leave_type,
            total_days=Decimal(total),
            used_days=Decimal(0),
            remaining_days=Decimal(total),
            year=current_year
        )
        db.add(new_balance)
    db.commit()
    
    return EmployeeBasicResponse(
        employee_id=login_id,
        password=password,
        work_email=employee_in.work_email,
        message="Employee created successfully. Please save these credentials."
    )

@router.get("/", response_model=List[EmployeeListResponse])
def read_all_employees(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_with_roles([UserRole.ADMIN, UserRole.HR_OFFICER])),
):
    """
    Retrieve all employees with status. (Admin or HR Officer only)
    """
    employees = db.query(EmployeeProfile).offset(skip).limit(limit).all()
    
    result = []
    today = date.today()
    
    for emp in employees:
        # Get email from User
        email = emp.user.email if emp.user else ""
        
        # Determine status
        status_val = "pending"
        
        # Check attendance
        attendance = db.query(Attendance).filter(
            Attendance.employee_profile_id == emp.id,
            Attendance.date == today
        ).first()
        
        if attendance:
            status_val = attendance.status.value if hasattr(attendance.status, 'value') else str(attendance.status)
        else:
            # Check leave
            leave = db.query(LeaveRequest).filter(
                LeaveRequest.employee_profile_id == emp.id,
                LeaveRequest.start_date <= today,
                LeaveRequest.end_date >= today,
                LeaveRequest.status == LeaveStatus.APPROVED
            ).first()
            
            if leave:
                status_val = "leave"
            else:
                status_val = "absent" 
        
        # Create response object
        emp_profile = EmployeeProfileSchema.model_validate(emp)
        emp_data = EmployeeListResponse(
            **emp_profile.model_dump(),
            email=email,
            status=status_val
        )
        result.append(emp_data)
        
    return result

@router.get("/me", response_model=EmployeeProfileMeResponse)
def read_my_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve the current employee's profile.
    """
    employee_profile = db.query(EmployeeProfile).filter(EmployeeProfile.user_id == current_user.id).first()
    if not employee_profile:
        raise HTTPException(status_code=404, detail="Employee profile not found for this user")
    
    # Get company details
    company = db.query(Company).filter(Company.id == employee_profile.company_id).first()
    company_name = company.name if company else None
    company_logo = company.logo if company else None
    
    # Prepend backend URL to company logo if it's a relative path
    if company_logo and not company_logo.startswith("http"):
        company_logo = f"http://localhost:8000{company_logo}"
    
    # Create response with email from user and company info
    return EmployeeProfileMeResponse(
        **EmployeeProfileSchema.model_validate(employee_profile).model_dump(),
        email=current_user.email,
        company_name=company_name,
        company_logo=company_logo
    )

@router.get("/{employee_profile_id}", response_model=EmployeeProfileSchema)
def read_employee_profile_by_id(
    employee_profile_id: int,
    current_user: User = Depends(get_current_active_user_with_roles([UserRole.ADMIN, UserRole.HR_OFFICER])),
    db: Session = Depends(get_db)
):
    """
    Retrieve an employee's profile by ID. (Admin or HR Officer only)
    """
    employee_profile = db.query(EmployeeProfile).filter(EmployeeProfile.id == employee_profile_id).first()
    if not employee_profile:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    return employee_profile

@router.put("/{employee_profile_id}", response_model=EmployeeProfileSchema)
def update_employee_profile(
    employee_profile_id: int,
    profile_update: EmployeeProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update an employee's profile. (Employee can update their own limited fields, Admin can update all)
    """
    db_profile = db.query(EmployeeProfile).filter(EmployeeProfile.id == employee_profile_id).first()
    if not db_profile:
        raise HTTPException(status_code=404, detail="Employee profile not found")

    # Check authorization
    if current_user.role == UserRole.ADMIN:
        # Admin can update any field
        update_data = profile_update.model_dump(exclude_unset=True)
    elif db_profile.user_id == current_user.id:
        # Employee can only update specific fields for their own profile
        allowed_fields = [
            "phone", "date_of_birth", "gender", "marital_status", 
            "nationality", "address", "personal_email", "profile_picture"
        ]
        update_data = profile_update.model_dump(include=set(allowed_fields), exclude_unset=True)
    else:
        raise HTTPException(status_code=403, detail="Not authorized to update this employee profile")

    for field, value in update_data.items():
        setattr(db_profile, field, value)

    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile

@router.post("/me/profile-picture", response_model=EmployeeProfileSchema)
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload a profile picture for the current employee.
    """
    employee_profile = db.query(EmployeeProfile).filter(EmployeeProfile.user_id == current_user.id).first()
    if not employee_profile:
        raise HTTPException(status_code=404, detail="Employee profile not found for this user")

    # Validate file type
    if file.content_type not in ["image/jpeg", "image/png", "image/gif"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG, PNG, GIF allowed.")

    # Generate a unique filename
    file_extension = file.filename.split(".")[-1]
    file_name = f"{employee_profile.id}_profile.{file_extension}"
    file_path = UPLOAD_DIR / file_name

    # Save the file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Update profile_picture field in the database
    employee_profile.profile_picture = f"/static/profile_pictures/{file_name}"
    db.add(employee_profile)
    db.commit()
    db.refresh(employee_profile)

    return employee_profile

# --- Bank Details CRUD ---

@router.post("/me/bank-details", response_model=BankDetailSchema, status_code=status.HTTP_201_CREATED)
def create_my_bank_details(
    bank_detail_in: BankDetailCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Add bank details for the current employee.
    """
    employee_profile = db.query(EmployeeProfile).filter(EmployeeProfile.user_id == current_user.id).first()
    if not employee_profile:
        raise HTTPException(status_code=404, detail="Employee profile not found for this user")

    if bank_detail_in.employee_profile_id != employee_profile.id:
        raise HTTPException(status_code=403, detail="Not authorized to add bank details for this employee profile")

    db_bank_detail = BankDetail(**bank_detail_in.model_dump())
    db.add(db_bank_detail)
    db.commit()
    db.refresh(db_bank_detail)
    return db_bank_detail

@router.get("/me/bank-details", response_model=List[BankDetailSchema])
def read_my_bank_details(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve bank details for the current employee.
    """
    employee_profile = db.query(EmployeeProfile).filter(EmployeeProfile.user_id == current_user.id).first()
    if not employee_profile:
        raise HTTPException(status_code=404, detail="Employee profile not found for this user")
    
    return employee_profile.bank_details

@router.get("/{employee_profile_id}/bank-details", response_model=List[BankDetailSchema])
def read_employee_bank_details(
    employee_profile_id: int,
    current_user: User = Depends(get_current_active_user_with_roles([UserRole.ADMIN, UserRole.HR_OFFICER])),
    db: Session = Depends(get_db)
):
    """
    Retrieve bank details for a specific employee profile. (Admin or HR Officer only)
    """
    employee_profile = db.query(EmployeeProfile).filter(EmployeeProfile.id == employee_profile_id).first()
    if not employee_profile:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    
    return employee_profile.bank_details

@router.put("/bank-details/{bank_detail_id}", response_model=BankDetailSchema)
def update_bank_details(
    bank_detail_id: int,
    bank_detail_in: BankDetailUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update bank details. (Employee can update their own, Admin can update any)
    """
    db_bank_detail = db.query(BankDetail).filter(BankDetail.id == bank_detail_id).first()
    if not db_bank_detail:
        raise HTTPException(status_code=404, detail="Bank details not found")
    
    employee_profile = db.query(EmployeeProfile).filter(EmployeeProfile.id == db_bank_detail.employee_profile_id).first()
    
    if current_user.role != UserRole.ADMIN and (not employee_profile or employee_profile.user_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to update these bank details")

    update_data = bank_detail_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_bank_detail, field, value)
    
    db.add(db_bank_detail)
    db.commit()
    db.refresh(db_bank_detail)
    return db_bank_detail

@router.delete("/bank-details/{bank_detail_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bank_details(
    bank_detail_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete bank details. (Employee can delete their own, Admin can delete any)
    """
    db_bank_detail = db.query(BankDetail).filter(BankDetail.id == bank_detail_id).first()
    if not db_bank_detail:
        raise HTTPException(status_code=404, detail="Bank details not found")

    employee_profile = db.query(EmployeeProfile).filter(EmployeeProfile.id == db_bank_detail.employee_profile_id).first()

    if current_user.role != UserRole.ADMIN and (not employee_profile or employee_profile.user_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to delete these bank details")
    
    db.delete(db_bank_detail)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# --- Skill Management ---

@router.post("/me/skills", response_model=SkillSchema, status_code=status.HTTP_201_CREATED)
def add_my_skill(
    skill_in: str, # Assuming skill name is passed, and we need to create it if it doesn't exist
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Add a skill to the current employee's profile. Creates the skill if it doesn't exist.
    """
    employee_profile = db.query(EmployeeProfile).filter(EmployeeProfile.user_id == current_user.id).first()
    if not employee_profile:
        raise HTTPException(status_code=404, detail="Employee profile not found for this user")

    skill = db.query(Skill).filter(Skill.name == skill_in).first()
    if not skill:
        skill = Skill(name=skill_in)
        db.add(skill)
        db.commit()
        db.refresh(skill)
    
    # Check if skill is already added to employee
    existing_employee_skill = db.query(EmployeeSkill).filter(
        EmployeeSkill.employee_profile_id == employee_profile.id,
        EmployeeSkill.skill_id == skill.id
    ).first()
    if existing_employee_skill:
        raise HTTPException(status_code=400, detail="Skill already added to this employee")

    employee_skill = EmployeeSkill(employee_profile_id=employee_profile.id, skill_id=skill.id)
    db.add(employee_skill)
    db.commit()
    db.refresh(employee_skill)
    return skill

@router.delete("/me/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_my_skill(
    skill_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Remove a skill from the current employee's profile.
    """
    employee_profile = db.query(EmployeeProfile).filter(EmployeeProfile.user_id == current_user.id).first()
    if not employee_profile:
        raise HTTPException(status_code=404, detail="Employee profile not found for this user")

    employee_skill = db.query(EmployeeSkill).filter(
        EmployeeSkill.employee_profile_id == employee_profile.id,
        EmployeeSkill.skill_id == skill_id
    ).first()
    if not employee_skill:
        raise HTTPException(status_code=404, detail="Skill not found for this employee")

    db.delete(employee_skill)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get("/me/skills", response_model=List[SkillSchema])
def list_my_skills(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List skills for the current employee.
    """
    employee_profile = db.query(EmployeeProfile).filter(EmployeeProfile.user_id == current_user.id).first()
    if not employee_profile:
        raise HTTPException(status_code=404, detail="Employee profile not found for this user")
    
    skills = [es.skill for es in employee_profile.employee_skills]
    return skills

@router.get("/{employee_profile_id}/skills", response_model=List[SkillSchema])
def list_employee_skills(
    employee_profile_id: int,
    current_user: User = Depends(get_current_active_user_with_roles([UserRole.ADMIN, UserRole.HR_OFFICER])),
    db: Session = Depends(get_db)
):
    """
    List skills for a specific employee profile. (Admin or HR Officer only)
    """
    employee_profile = db.query(EmployeeProfile).filter(EmployeeProfile.id == employee_profile_id).first()
    if not employee_profile:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    
    skills = [es.skill for es in employee_profile.employee_skills]
    return skills

@router.post("/{employee_profile_id}/skills", response_model=SkillSchema, status_code=status.HTTP_201_CREATED)
def add_skill_to_employee(
    employee_profile_id: int,
    skill_id: int,
    current_user: User = Depends(get_current_active_user_with_roles([UserRole.ADMIN])), # Only admin can assign to others
    db: Session = Depends(get_db)
):
    """
    Add a skill to a specific employee's profile. (Admin only)
    """
    employee_profile = db.query(EmployeeProfile).filter(EmployeeProfile.id == employee_profile_id).first()
    if not employee_profile:
        raise HTTPException(status_code=404, detail="Employee profile not found")

    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    existing_employee_skill = db.query(EmployeeSkill).filter(
        EmployeeSkill.employee_profile_id == employee_profile_id,
        EmployeeSkill.skill_id == skill_id
    ).first()
    if existing_employee_skill:
        raise HTTPException(status_code=400, detail="Skill already added to this employee")

    employee_skill = EmployeeSkill(employee_profile_id=employee_profile_id, skill_id=skill_id)
    db.add(employee_skill)
    db.commit()
    db.refresh(employee_skill)
    return skill

@router.delete("/{employee_profile_id}/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_skill_from_employee(
    employee_profile_id: int,
    skill_id: int,
    current_user: User = Depends(get_current_active_user_with_roles([UserRole.ADMIN])), # Only admin can remove from others
    db: Session = Depends(get_db)
):
    """
    Remove a skill from a specific employee's profile. (Admin only)
    """
    employee_skill = db.query(EmployeeSkill).filter(
        EmployeeSkill.employee_profile_id == employee_profile_id,
        EmployeeSkill.skill_id == skill_id
    ).first()
    if not employee_skill:
        raise HTTPException(status_code=404, detail="Skill not found for this employee")

    db.delete(employee_skill)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Certification Management ---

@router.post("/me/certifications", response_model=CertificationSchema, status_code=status.HTTP_201_CREATED)
def add_my_certification(
    certification_in: CertificationCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Add a certification for the current employee.
    """
    employee_profile = db.query(EmployeeProfile).filter(EmployeeProfile.user_id == current_user.id).first()
    if not employee_profile:
        raise HTTPException(status_code=404, detail="Employee profile not found for this user")

    # Ensure the certification being added belongs to the current employee's profile
    if certification_in.employee_profile_id != employee_profile.id:
        raise HTTPException(status_code=403, detail="Not authorized to add certification for this employee profile")
    
    db_certification = Certification(**certification_in.model_dump())
    db.add(db_certification)
    db.commit()
    db.refresh(db_certification)
    return db_certification

@router.get("/me/certifications", response_model=List[CertificationSchema])
def list_my_certifications(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List certifications for the current employee.
    """
    employee_profile = db.query(EmployeeProfile).filter(EmployeeProfile.user_id == current_user.id).first()
    if not employee_profile:
        raise HTTPException(status_code=404, detail="Employee profile not found for this user")
    
    return employee_profile.certifications

@router.get("/{employee_profile_id}/certifications", response_model=List[CertificationSchema])
def list_employee_certifications(
    employee_profile_id: int,
    current_user: User = Depends(get_current_active_user_with_roles([UserRole.ADMIN, UserRole.HR_OFFICER])),
    db: Session = Depends(get_db)
):
    """
    List certifications for a specific employee profile. (Admin or HR Officer only)
    """
    employee_profile = db.query(EmployeeProfile).filter(EmployeeProfile.id == employee_profile_id).first()
    if not employee_profile:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    
    return employee_profile.certifications

@router.put("/certifications/{certification_id}", response_model=CertificationSchema)
def update_certification(
    certification_id: int,
    certification_in: CertificationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update a certification. (Employee can update their own, Admin can update any)
    """
    db_certification = db.query(Certification).filter(Certification.id == certification_id).first()
    if not db_certification:
        raise HTTPException(status_code=404, detail="Certification not found")
    
    employee_profile = db.query(EmployeeProfile).filter(EmployeeProfile.id == db_certification.employee_profile_id).first()
    
    if current_user.role != UserRole.ADMIN and (not employee_profile or employee_profile.user_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to update this certification")

    update_data = certification_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_certification, field, value)
    
    db.add(db_certification)
    db.commit()
    db.refresh(db_certification)
    return db_certification

@router.delete("/certifications/{certification_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_certification(
    certification_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a certification. (Employee can delete their own, Admin can delete any)
    """
    db_certification = db.query(Certification).filter(Certification.id == certification_id).first()
    if not db_certification:
        raise HTTPException(status_code=404, detail="Certification not found")

    employee_profile = db.query(EmployeeProfile).filter(EmployeeProfile.id == db_certification.employee_profile_id).first()

    if current_user.role != UserRole.ADMIN and (not employee_profile or employee_profile.user_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to delete this certification")
    
    db.delete(db_certification)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)