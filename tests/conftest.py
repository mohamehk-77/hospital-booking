"""Shared pytest fixtures.

Tests run against an in-memory SQLite database.  Production still uses
PostgreSQL; SQLite keeps the suite fast and independent of a live server.
"""

import os
from datetime import date, timedelta

# Must be set before importing the app: Settings is created on import.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "test-secret-key-not-for-production"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import hash_password
from app.main import app
from app.models.user import User, UserRole

ADMIN_PASSWORD = "adminpass123"
PATIENT_PASSWORD = "patientpass123"
DOCTOR_PASSWORD = "doctorpass123"
RECEPTIONIST_PASSWORD = "reception123"

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture()
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def login(client: TestClient, email: str, password: str) -> str:
    response = client.post(
        "/auth/login",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def register_patient(
    client: TestClient,
    email: str = "patient@example.com",
    full_name: str = "Test Patient",
    password: str = PATIENT_PASSWORD,
) -> dict:
    response = client.post(
        "/auth/register",
        json={"full_name": full_name, "email": email, "password": password},
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_user(db, email, password, role, full_name="Test User") -> User:
    user = User(
        full_name=full_name,
        email=email,
        hashed_password=hash_password(password),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def add_schedule(
    client: TestClient,
    headers: dict[str, str],
    doctor_id: int,
    weekday: int,
    start_time: str = "09:00:00",
    end_time: str = "11:00:00",
    slot_minutes: int = 30,
) -> dict:
    response = client.post(
        f"/doctors/{doctor_id}/schedules/",
        json={
            "weekday": weekday,
            "start_time": start_time,
            "end_time": end_time,
            "slot_minutes": slot_minutes,
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def next_weekday(weekday: int, min_days: int = 2) -> date:
    day = date.today() + timedelta(days=min_days)
    while day.weekday() != weekday:
        day += timedelta(days=1)
    return day


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture()
def admin(client, db):
    user = create_user(db, "admin@example.com", ADMIN_PASSWORD, UserRole.ADMIN, "Admin User")
    token = login(client, user.email, ADMIN_PASSWORD)
    return {"user": user, "token": token, "headers": auth_headers(token)}


@pytest.fixture()
def patient(client):
    data = register_patient(client)
    token = login(client, data["email"], PATIENT_PASSWORD)
    return {"user": data, "token": token, "headers": auth_headers(token)}


@pytest.fixture()
def other_patient(client):
    data = register_patient(client, email="other.patient@example.com", full_name="Other Patient")
    token = login(client, data["email"], PATIENT_PASSWORD)
    return {"user": data, "token": token, "headers": auth_headers(token)}


@pytest.fixture()
def department(client, admin):
    response = client.post(
        "/departments/",
        json={"name": "Cardiology", "description": "Heart care"},
        headers=admin["headers"],
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture()
def doctor(client, admin, department):
    response = client.post(
        "/doctors/",
        json={
            "full_name": "Dr. House",
            "email": "doctor@example.com",
            "password": DOCTOR_PASSWORD,
            "department_id": department["id"],
            "specialization": "Cardiology",
            "bio": "Diagnostician",
        },
        headers=admin["headers"],
    )
    assert response.status_code == 201, response.text
    token = login(client, "doctor@example.com", DOCTOR_PASSWORD)
    return {"data": response.json(), "token": token, "headers": auth_headers(token)}


@pytest.fixture()
def receptionist(client, admin):
    response = client.post(
        "/staff/receptionists",
        json={
            "full_name": "Reception Person",
            "email": "reception@example.com",
            "password": RECEPTIONIST_PASSWORD,
        },
        headers=admin["headers"],
    )
    assert response.status_code == 201, response.text
    token = login(client, "reception@example.com", RECEPTIONIST_PASSWORD)
    return {"user": response.json(), "token": token, "headers": auth_headers(token)}