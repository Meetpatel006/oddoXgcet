from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from .config import settings
from .database import Base, engine, SessionLocal
from .models import User, UserRole
from .auth.security import get_password_hash
from app.api import auth as auth_router, users as users_router, employees as employees_router, attendance as attendance_router, attendance_correction as attendance_correction_router, leave as leave_router, salary as salary_router, settings as settings_router, dashboard as dashboard_router

app = FastAPI(
    title=settings.OPENAPI_TITLE,
    version=settings.OPENAPI_VERSION,
    debug=settings.DEBUG
)

from fastapi.middleware.cors import CORSMiddleware

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
async def startup_event():
    Base.metadata.create_all(bind=engine)
    
    # Create a new session for the startup event
    db: Session = SessionLocal()
    try:
        if not settings.TESTING: # Only create admin if not in testing mode
            # Check if an admin user already exists
            admin_user = db.query(User).filter(User.email == settings.ADMIN_EMAIL).first()
            if not admin_user:
                # Create the admin user
                hashed_password = get_password_hash(settings.ADMIN_PASSWORD)
                new_admin = User(
                    email=settings.ADMIN_EMAIL,
                    hashed_password=hashed_password,
                    role=UserRole.ADMIN,
                    is_active=True
                )
                db.add(new_admin)
                db.commit()
    finally:
        db.close()


@app.get("/")
def read_root():
    return {"message": "Welcome to Dayflow HRMS API"}

app.include_router(auth_router.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users_router.router, prefix="/api/v1/users", tags=["users"])
app.include_router(employees_router.router, prefix="/api/v1/employees", tags=["employees"])
app.include_router(attendance_router.router, prefix="/api/v1/attendance", tags=["attendance"])
app.include_router(attendance_correction_router.router, prefix="/api/v1/attendance-correction", tags=["attendance-correction"])
app.include_router(leave_router.router, prefix="/api/v1/leave", tags=["leave"])
app.include_router(salary_router.router, prefix="/api/v1/salary", tags=["salary"])
app.include_router(settings_router.router, prefix="/api/v1/settings", tags=["settings"])
app.include_router(dashboard_router.router, prefix="/api/v1/dashboard", tags=["dashboard"])
