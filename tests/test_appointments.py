from datetime import date, time, timedelta

from app.models.appointment import Appointment, AppointmentStatus
from tests.conftest import add_schedule, next_weekday


def book(client, headers, doctor_id, day, start_time="09:00:00", **extra):
    payload = {
        "doctor_id": doctor_id,
        "appointment_date": day.isoformat(),
        "start_time": start_time,
    }
    payload.update(extra)
    return client.post("/appointments/", json=payload, headers=headers)


def setup_day(client, admin, doctor, weekday=0):
    day = next_weekday(weekday)
    add_schedule(client, admin["headers"], doctor["data"]["id"], day.weekday())
    return day


def test_slots_are_computed_from_schedule(client, admin, doctor):
    day = setup_day(client, admin, doctor)

    response = client.get(
        "/appointments/available",
        params={"doctor_id": doctor["data"]["id"], "appointment_date": day.isoformat()},
    )
    assert response.status_code == 200
    slots = response.json()
    assert [s["start_time"] for s in slots] == [
        "09:00:00",
        "09:30:00",
        "10:00:00",
        "10:30:00",
    ]


def test_no_schedule_means_no_slots(client, doctor):
    day = next_weekday(0)
    response = client.get(
        "/appointments/available",
        params={"doctor_id": doctor["data"]["id"], "appointment_date": day.isoformat()},
    )
    assert response.status_code == 200
    assert response.json() == []


def test_available_slots_excludes_past_and_booked(client, admin, patient, doctor):
    day = setup_day(client, admin, doctor)

    assert book(client, patient["headers"], doctor["data"]["id"], day).status_code == 201
    slots = client.get(
        "/appointments/available",
        params={"doctor_id": doctor["data"]["id"], "appointment_date": day.isoformat()},
    ).json()
    assert "09:00:00" not in [s["start_time"] for s in slots]
    assert len(slots) == 3

    past = date.today() - timedelta(days=3)
    if past.weekday() == day.weekday():
        past -= timedelta(days=1)
    add_schedule(client, admin["headers"], doctor["data"]["id"], past.weekday())

    past_slots = client.get(
        "/appointments/available",
        params={"doctor_id": doctor["data"]["id"], "appointment_date": past.isoformat()},
    )
    assert past_slots.status_code == 200
    assert past_slots.json() == []


def test_available_slots_for_unknown_doctor_returns_404(client):
    response = client.get(
        "/appointments/available",
        params={"doctor_id": 999, "appointment_date": next_weekday(0).isoformat()},
    )
    assert response.status_code == 404


def test_booking_creates_confirmed_appointment(client, admin, patient, doctor):
    day = setup_day(client, admin, doctor)
    response = book(
        client,
        patient["headers"],
        doctor["data"]["id"],
        day,
        notes="First visit",
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["patient_id"] == patient["user"]["id"]
    assert body["status"] == "confirmed"
    assert body["start_time"] == "09:00:00"
    assert body["end_time"] == "09:30:00"
    assert body["notes"] == "First visit"


def test_double_booking_is_rejected(client, admin, patient, other_patient, doctor):
    day = setup_day(client, admin, doctor)
    assert book(client, patient["headers"], doctor["data"]["id"], day).status_code == 201

    second = book(client, other_patient["headers"], doctor["data"]["id"], day)
    assert second.status_code == 409
    assert second.json()["detail"] == "This slot is already booked"


def test_cannot_book_off_grid_time(client, admin, patient, doctor):
    day = setup_day(client, admin, doctor)
    response = book(client, patient["headers"], doctor["data"]["id"], day, start_time="09:15:00")
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid time slot for this doctor"


def test_cannot_book_on_day_off(client, admin, patient, doctor):
    workday = next_weekday(0)
    add_schedule(client, admin["headers"], doctor["data"]["id"], workday.weekday())
    day_off = next_weekday(1)

    response = book(client, patient["headers"], doctor["data"]["id"], day_off)
    assert response.status_code == 400
    assert response.json()["detail"] == "Doctor does not work on this day"


def test_cannot_book_in_the_past(client, patient, doctor):
    yesterday = date.today() - timedelta(days=1)
    response = book(client, patient["headers"], doctor["data"]["id"], yesterday)
    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot book a time in the past"


def test_only_patients_can_book_through_the_patient_endpoint(
    client, admin, doctor, receptionist
):
    day = next_weekday(0)
    add_schedule(client, admin["headers"], doctor["data"]["id"], day.weekday())

    assert book(client, receptionist["headers"], doctor["data"]["id"], day).status_code == 403
    assert book(client, admin["headers"], doctor["data"]["id"], day).status_code == 403
    assert book(client, {}, doctor["data"]["id"], day).status_code == 401


def test_cancel_frees_the_slot(client, admin, patient, doctor):
    day = setup_day(client, admin, doctor)
    booking = book(client, patient["headers"], doctor["data"]["id"], day).json()

    cancelled = client.post(
        f"/appointments/{booking['id']}/cancel", headers=patient["headers"]
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"

    slots = client.get(
        "/appointments/available",
        params={"doctor_id": doctor["data"]["id"], "appointment_date": day.isoformat()},
    ).json()
    assert "09:00:00" in [s["start_time"] for s in slots]

    assert book(client, patient["headers"], doctor["data"]["id"], day).status_code == 201

    twice = client.post(f"/appointments/{booking['id']}/cancel", headers=patient["headers"])
    assert twice.status_code == 400


def test_cancel_permissions(client, admin, patient, other_patient, doctor):
    day = setup_day(client, admin, doctor)
    booking = book(client, patient["headers"], doctor["data"]["id"], day).json()

    stranger = client.post(
        f"/appointments/{booking['id']}/cancel", headers=other_patient["headers"]
    )
    assert stranger.status_code == 404

    missing = client.post("/appointments/9999/cancel", headers=patient["headers"])
    assert missing.status_code == 404

    by_admin = client.post(
        f"/appointments/{booking['id']}/cancel", headers=admin["headers"]
    )
    assert by_admin.status_code == 200


def test_patient_lists_only_their_appointments(
    client, admin, patient, other_patient, doctor
):
    day = setup_day(client, admin, doctor)
    book(client, patient["headers"], doctor["data"]["id"], day)
    book(
        client,
        other_patient["headers"],
        doctor["data"]["id"],
        day,
        start_time="09:30:00",
    )

    mine = client.get("/appointments/my", headers=patient["headers"])
    assert mine.status_code == 200
    assert {item["patient_id"] for item in mine.json()} == {patient["user"]["id"]}

    assert client.get("/appointments/my").status_code == 401


def test_doctor_lists_own_confirmed_appointments(client, admin, patient, doctor):
    day = setup_day(client, admin, doctor)
    booking = book(client, patient["headers"], doctor["data"]["id"], day).json()

    response = client.get("/appointments/doctor/me", headers=doctor["headers"])
    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [booking["id"]]

    filtered = client.get(
        "/appointments/doctor/me",
        params={"appointment_date": day.isoformat()},
        headers=doctor["headers"],
    )
    assert len(filtered.json()) == 1

    empty = client.get(
        "/appointments/doctor/me",
        params={"appointment_date": (day + timedelta(days=1)).isoformat()},
        headers=doctor["headers"],
    )
    assert empty.json() == []

    assert client.get("/appointments/doctor/me", headers=patient["headers"]).status_code == 403


def test_doctor_cannot_complete_before_start(client, admin, patient, doctor):
    day = setup_day(client, admin, doctor)
    booking = book(client, patient["headers"], doctor["data"]["id"], day).json()

    response = client.post(
        f"/appointments/{booking['id']}/complete", headers=doctor["headers"]
    )
    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Cannot complete an appointment before its start time"
    )


def test_doctor_completes_a_past_appointment(client, db, patient, doctor):
    appointment = Appointment(
        patient_id=patient["user"]["id"],
        doctor_id=doctor["data"]["id"],
        appointment_date=date.today() - timedelta(days=1),
        start_time=time(9, 0),
        end_time=time(9, 30),
        status=AppointmentStatus.CONFIRMED,
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)

    response = client.post(
        f"/appointments/{appointment.id}/complete", headers=doctor["headers"]
    )
    assert response.status_code == 200
    assert response.json()["status"] == "completed"

    again = client.post(
        f"/appointments/{appointment.id}/complete", headers=doctor["headers"]
    )
    assert again.status_code == 400


def test_foreign_doctor_cannot_complete(client, db, admin, patient, doctor):
    other = client.post(
        "/doctors/",
        json={
            "full_name": "Dr. Other",
            "email": "other.doctor@example.com",
            "password": "doctorpass123",
            "department_id": doctor["data"]["department_id"],
            "specialization": "Cardiology",
        },
        headers=admin["headers"],
    )
    assert other.status_code == 201

    appointment = Appointment(
        patient_id=patient["user"]["id"],
        doctor_id=other.json()["id"],
        appointment_date=date.today() - timedelta(days=1),
        start_time=time(9, 0),
        end_time=time(9, 30),
        status=AppointmentStatus.CONFIRMED,
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)

    assert client.post(
        f"/appointments/{appointment.id}/complete", headers=doctor["headers"]
    ).status_code == 404

    assert client.post(
        f"/appointments/{appointment.id}/complete", headers=patient["headers"]
    ).status_code == 403