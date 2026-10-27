from app.models.user import User
from tests.conftest import add_schedule, next_weekday


def book_for_patient(client, headers, patient_id, doctor_id, day, start_time="09:00:00"):
    return client.post(
        "/appointments/for-patient",
        json={
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "appointment_date": day.isoformat(),
            "start_time": start_time,
            "notes": "Booked at the desk",
        },
        headers=headers,
    )


def test_admin_creates_receptionist(client, patient, receptionist):
    assert receptionist["user"]["role"] == "receptionist"
    assert "hashed_password" not in receptionist["user"]

    forbidden = client.post(
        "/staff/receptionists",
        json={
            "full_name": "No Rights",
            "email": "norights@example.com",
            "password": "reception123",
        },
        headers=patient["headers"],
    )
    assert forbidden.status_code == 403


def test_receptionist_searches_patients(
    client, patient, other_patient, receptionist
):
    response = client.get(
        "/patients/search",
        params={"email": "example.com"},
        headers=receptionist["headers"],
    )
    assert response.status_code == 200
    emails = [user["email"] for user in response.json()]
    assert set(emails) == {"patient@example.com", "other.patient@example.com"}
    assert all("hashed_password" not in user for user in response.json())

    doctors_and_staff = client.get(
        "/patients/search",
        params={"email": "doctor"},
        headers=receptionist["headers"],
    )
    assert doctors_and_staff.json() == []


def test_patient_search_requires_staff(client, patient, doctor):
    assert (
        client.get("/patients/search", params={"email": "example.com"}).status_code
        == 401
    )
    assert (
        client.get(
            "/patients/search",
            params={"email": "example.com"},
            headers=patient["headers"],
        ).status_code
        == 403
    )
    assert (
        client.get(
            "/patients/search",
            params={"email": "example.com"},
            headers=doctor["headers"],
        ).status_code
        == 403
    )


def test_patient_search_validates_term(client, receptionist):
    response = client.get(
        "/patients/search",
        params={"email": "ab"},
        headers=receptionist["headers"],
    )
    assert response.status_code == 422


def test_receptionist_books_for_patient(client, admin, patient, receptionist, doctor):
    day = next_weekday(0)
    add_schedule(client, admin["headers"], doctor["data"]["id"], day.weekday())

    response = book_for_patient(
        client,
        receptionist["headers"],
        patient["user"]["id"],
        doctor["data"]["id"],
        day,
    )
    assert response.status_code == 201, response.text
    booking = response.json()
    assert booking["patient_id"] == patient["user"]["id"]
    assert booking["notes"] == "Booked at the desk"

    mine = client.get("/appointments/my", headers=patient["headers"]).json()
    assert [item["id"] for item in mine] == [booking["id"]]

    duplicate = book_for_patient(
        client,
        receptionist["headers"],
        patient["user"]["id"],
        doctor["data"]["id"],
        day,
    )
    assert duplicate.status_code == 409


def test_receptionist_booking_rejects_non_patient_ids(
    client, db, admin, patient, receptionist, doctor
):
    day = next_weekday(0)
    add_schedule(client, admin["headers"], doctor["data"]["id"], day.weekday())

    doctor_user = db.query(User).filter(User.email == "doctor@example.com").one()
    for target in (doctor_user.id, admin["user"].id, 9999):
        response = book_for_patient(
            client,
            receptionist["headers"],
            target,
            doctor["data"]["id"],
            day,
        )
        assert response.status_code == 404, (target, response.text)

    inactive = db.get(User, patient["user"]["id"])
    inactive.is_active = False
    db.commit()

    response = book_for_patient(
        client,
        receptionist["headers"],
        inactive.id,
        doctor["data"]["id"],
        day,
    )
    assert response.status_code == 404


def test_receptionist_can_cancel_for_patient(
    client, admin, patient, receptionist, doctor
):
    day = next_weekday(0)
    add_schedule(client, admin["headers"], doctor["data"]["id"], day.weekday())

    booking = book_for_patient(
        client,
        receptionist["headers"],
        patient["user"]["id"],
        doctor["data"]["id"],
        day,
    ).json()

    cancelled = client.post(
        f"/appointments/{booking['id']}/cancel",
        headers=receptionist["headers"],
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"

    slots = client.get(
        "/appointments/available",
        params={"doctor_id": doctor["data"]["id"], "appointment_date": day.isoformat()},
    ).json()
    assert "09:00:00" in [slot["start_time"] for slot in slots]


def test_receptionist_cannot_use_admin_or_doctor_endpoints(client, receptionist):
    assert (
        client.post(
            "/departments/",
            json={"name": "X Ray"},
            headers=receptionist["headers"],
        ).status_code
        == 403
    )
    assert (
        client.get(
            "/appointments/doctor/me", headers=receptionist["headers"]
        ).status_code
        == 403
    )
    assert client.get(
        "/appointments/my", headers=receptionist["headers"]
    ).json() == []