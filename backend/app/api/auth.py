from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, UserSettings # Added UserSettings
from app.schemas import UserCreate, User as UserSchema
from app.schemas.token import Token
from app.auth.security import get_password_hash, verify_password, create_access_token
from app.auth.dependencies import get_current_active_user
from app.services.activity_service import log_activity

router = APIRouter()

def authenticate_user(db: Session, email: str, password: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

@router.post("/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    """
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        role=user.role,
        is_active=user.is_active,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create default settings for the new user
    user_settings = UserSettings(user_id=db_user.id)
    db.add(user_settings)
    db.commit()
    db.refresh(user_settings)
    
    log_activity(db, db_user.id, "User registration", f"User {db_user.email} registered.")
    
    return db_user

@router.post("/login", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Authenticate user and return a JWT token.
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})
    
    log_activity(db, user.id, "User login", f"User {user.email} logged in.")
    
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
