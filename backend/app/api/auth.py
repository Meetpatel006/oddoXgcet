from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, UserSettings, UserRole, Company, EmployeeProfile
from app.schemas import UserCreate, User as UserSchema
from app.schemas.token import Token
from app.auth.security import get_password_hash, verify_password, create_access_token
from app.auth.dependencies import get_current_active_user
from app.services.activity_service import log_activity
import shutil
from pathlib import Path
from datetime import datetime

router = APIRouter()

COMPANY_LOGO_DIR = Path("static/company_logos")
COMPANY_LOGO_DIR.mkdir(parents=True, exist_ok=True)

def authenticate_user(db: Session, email: str, password: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

# --- Admin Auth ---

@router.post("/admin/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def register_admin(
    email: str = Form(...),
    password: str = Form(...),
    company_name: str = Form(...),
    full_name: str = Form(...),
    phone: str = Form(...),
    logo: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    """
    Register a new Admin with Company and Profile.
    """
    # 1. Check if email exists
    db_user = db.query(User).filter(User.email == email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # 2. Create Company
    logo_path_str = None
    if logo:
        # Validate file type
        if logo.content_type not in ["image/jpeg", "image/png", "image/gif"]:
            raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG, PNG, GIF allowed.")
        
        file_extension = logo.filename.split(".")[-1]
        file_name = f"company_{datetime.now().timestamp()}_{logo.filename}" # simple unique name
        file_path = COMPANY_LOGO_DIR / file_name
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(logo.file, buffer)
        
        logo_path_str = f"/static/company_logos/{file_name}"

    new_company = Company(name=company_name, logo=logo_path_str)
    db.add(new_company)
    db.commit()
    db.refresh(new_company)

    # 3. Create User
    hashed_password = get_password_hash(password)
    db_user = User(
        email=email,
        hashed_password=hashed_password,
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # 4. Create UserSettings
    user_settings = UserSettings(user_id=db_user.id)
    db.add(user_settings)
    
    # 5. Create EmployeeProfile
    name_parts = full_name.strip().split(" ", 1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ""
    
    # Generate Employee ID (e.g., ADM-YYYY-ID)
    emp_id_str = f"ADM-{datetime.now().year}-{db_user.id}"

    new_profile = EmployeeProfile(
        user_id=db_user.id,
        company_id=new_company.id,
        employee_id=emp_id_str,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        personal_email=email, # Assuming personal email is same as login for admin init
        joining_date=datetime.now().date(),
        designation="Administrator"
    )
    db.add(new_profile)
    db.commit()
    db.refresh(db_user) # Refresh user to load relationships if needed
    
    log_activity(db, db_user.id, "Admin registration", f"Admin {db_user.email} registered with Company {company_name}.")
    
    return db_user

@router.post("/admin/login", response_model=Token)
def login_admin(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Authenticate Admin and return a JWT token.
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, # Or 403, but 401 is common for login failure
            detail="Unauthorized: User is not an Admin",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.email})
    
    log_activity(db, user.id, "Admin login", f"Admin {user.email} logged in.")
    
    return {"access_token": access_token, "token_type": "bearer"}

# --- HR Auth ---

@router.post("/hr/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def register_hr(
    email: str = Form(...),
    password: str = Form(...),
    company_name: str = Form(...),
    full_name: str = Form(...),
    phone: str = Form(...),
    logo: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    """
    Register a new HR Officer with Company and Profile.
    """
    # 1. Check if email exists
    db_user = db.query(User).filter(User.email == email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # 2. Create Company
    logo_path_str = None
    if logo:
        # Validate file type
        if logo.content_type not in ["image/jpeg", "image/png", "image/gif"]:
            raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG, PNG, GIF allowed.")
        
        file_extension = logo.filename.split(".")[-1]
        file_name = f"company_{datetime.now().timestamp()}_{logo.filename}"
        file_path = COMPANY_LOGO_DIR / file_name
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(logo.file, buffer)
        
        logo_path_str = f"/static/company_logos/{file_name}"

    new_company = Company(name=company_name, logo=logo_path_str)
    db.add(new_company)
    db.commit()
    db.refresh(new_company)

    # 3. Create User
    hashed_password = get_password_hash(password)
    db_user = User(
        email=email,
        hashed_password=hashed_password,
        role=UserRole.HR_OFFICER,
        is_active=user.is_active if 'user' in locals() else True, # Default to True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # 4. Create UserSettings
    user_settings = UserSettings(user_id=db_user.id)
    db.add(user_settings)
    
    # 5. Create EmployeeProfile
    name_parts = full_name.strip().split(" ", 1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ""
    
    # Generate Employee ID (e.g., HR-YYYY-ID)
    emp_id_str = f"HR-{datetime.now().year}-{db_user.id}"

    new_profile = EmployeeProfile(
        user_id=db_user.id,
        company_id=new_company.id,
        employee_id=emp_id_str,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        personal_email=email,
        joining_date=datetime.now().date(),
        designation="HR Officer"
    )
    db.add(new_profile)
    db.commit()
    db.refresh(db_user) 
    
    log_activity(db, db_user.id, "HR registration", f"HR {db_user.email} registered with Company {company_name}.")
    
    return db_user

@router.post("/hr/login", response_model=Token)
def login_hr(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Authenticate HR Officer and return a JWT token.
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if user.role != UserRole.HR_OFFICER:
         raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Unauthorized: User is not an HR Officer",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.email})
    
    log_activity(db, user.id, "HR login", f"HR {user.email} logged in.")
    
    return {"access_token": access_token, "token_type": "bearer"}

# --- Employee Auth ---

@router.post("/employee/login", response_model=Token)
def login_employee(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Authenticate Employee and return a JWT token.
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if user.role != UserRole.EMPLOYEE:
         raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Unauthorized: User is not an Employee",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.email})
    
    log_activity(db, user.id, "Employee login", f"Employee {user.email} logged in.")
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users/me", response_model=UserSchema)
def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Get current user.
    """
    return current_user

@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """
    Log out the current user. (Client-side token invalidation)
    """
    log_activity(db, current_user.id, "User logout", f"User {current_user.email} logged out.")
    return {"message": "Successfully logged out. Please discard your token."}
