from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    APP_NAME: str = "Dayflow HRMS"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    SECRET_KEY: str = "your-secret-key-min-32-chars"  # TODO: Change in production

    DATABASE_URL: str = "sqlite:///./dayflow.db"
    TESTING: bool = False # Added for test environment control

    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440 # 24 hours

    OPENAPI_TITLE: str = "Dayflow HRMS API"
    OPENAPI_VERSION: str = "1.0.0"

    ADMIN_EMAIL: str = "admin@example.com"
    ADMIN_PASSWORD: str = "adminpassword"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
