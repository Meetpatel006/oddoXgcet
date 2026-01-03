import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

# Use a separate sqlite file for e2e tests
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_e2e.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Ensure tables exist for the test DB
Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def cleanup_database():
    yield
    # Clean up the database by deleting all records from the tables
    with engine.connect() as connection:
        transaction = connection.begin()
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())
        transaction.commit()


client = TestClient(app)


def test_root_endpoint():
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json().get("message") == "Welcome to Dayflow HRMS API"


def test_register_login_and_me_flow():
    # Register
    r = client.post(
        "/api/v1/auth/register",
        json={"email": "e2e@example.com", "password": "password", "role": "employee", "is_active": True},
    )
    assert r.status_code == 201

    # Login
    login = client.post(
        "/api/v1/auth/login",
        data={"username": "e2e@example.com", "password": "password"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    # Access protected endpoint
    headers = {"Authorization": f"Bearer {token}"}
    me = client.get("/api/v1/auth/users/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == "e2e@example.com"


def test_protected_requires_auth():
    r = client.get("/api/v1/auth/users/me")
    assert r.status_code == 401


def test_register_existing_user():
    client.post(
        "/api/v1/auth/register",
        json={"email": "dup@example.com", "password": "password", "role": "employee", "is_active": True},
    )
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "dup@example.com", "password": "password", "role": "employee", "is_active": True},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Email already registered"
