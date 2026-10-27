from app.models.user import User
from tests.conftest import (
    ADMIN_PASSWORD,
    PATIENT_PASSWORD,
    auth_headers,
    login,
    register_patient,
)


def test_register_forces_patient_role(client):
    response = client.post(
        "/auth/register",
        json={
            "full_name": "Sneaky Admin",
            "email": "sneaky@example.com",
            "password": PATIENT_PASSWORD,
            "role": "admin",
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["role"] == "patient"
    assert "hashed_password" not in body
    assert "password" not in body


def test_register_rejects_duplicate_email(client):
    register_patient(client)
    response = client.post(
        "/auth/register",
        json={
            "full_name": "Another Patient",
            "email": "PATIENT@example.com",
            "password": PATIENT_PASSWORD,
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


def test_register_validates_email_and_password(client):
    bad_email = client.post(
        "/auth/register",
        json={"full_name": "Bad Email", "email": "not-an-email", "password": PATIENT_PASSWORD},
    )
    assert bad_email.status_code == 422

    short_password = client.post(
        "/auth/register",
        json={"full_name": "Short", "email": "short@example.com", "password": "short"},
    )
    assert short_password.status_code == 422


def test_login_and_me(client, patient):
    response = client.post(
        "/auth/login",
        data={"username": patient["user"]["email"], "password": PATIENT_PASSWORD},
    )
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"

    me = client.get("/auth/me", headers=auth_headers(response.json()["access_token"]))
    assert me.status_code == 200
    assert me.json()["email"] == patient["user"]["email"]
    assert me.json()["role"] == "patient"


def test_login_wrong_password_is_generic(client, patient):
    response = client.post(
        "/auth/login",
        data={"username": patient["user"]["email"], "password": "wrong-password"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"

    unknown = client.post(
        "/auth/login",
        data={"username": "nobody@example.com", "password": "whatever123"},
    )
    assert unknown.status_code == 401
    assert unknown.json()["detail"] == "Incorrect email or password"


def test_me_requires_token(client):
    assert client.get("/auth/me").status_code == 401
    assert client.get("/auth/me", headers=auth_headers("garbage")).status_code == 401


def test_disabled_user_cannot_login(client, db, patient):
    user = db.get(User, patient["user"]["id"])
    user.is_active = False
    db.commit()

    response = client.post(
        "/auth/login",
        data={"username": patient["user"]["email"], "password": PATIENT_PASSWORD},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Account is disabled"

    assert client.get("/auth/me", headers=patient["headers"]).status_code == 401


def test_admin_has_privileged_role(client, admin):
    me = client.get("/auth/me", headers=admin["headers"])
    assert me.status_code == 200
    assert me.json()["role"] == "admin"

    assert client.post(
        "/auth/login",
        data={"username": "admin@example.com", "password": ADMIN_PASSWORD},
    ).status_code == 200