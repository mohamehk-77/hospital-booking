from tests.conftest import add_schedule, next_weekday


def book(client, headers, doctor_id, day, start_time):
    return client.post(
        "/appointments/",
        json={
            "doctor_id": doctor_id,
            "appointment_date": day.isoformat(),
            "start_time": start_time,
        },
        headers=headers,
    )


def two_appointments(client, admin, patient, other_patient, doctor):
    day = next_weekday(0)
    add_schedule(client, admin["headers"], doctor["data"]["id"], day.weekday())
    first = book(client, patient["headers"], doctor["data"]["id"], day, "09:00:00")
    second = book(
        client, other_patient["headers"], doctor["data"]["id"], day, "09:30:00"
    )
    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text
    return day, first.json(), second.json()


def test_admin_lists_all_appointments(
    client, admin, patient, other_patient, doctor
):
    _, first, second = two_appointments(
        client, admin, patient, other_patient, doctor
    )

    response = client.get("/appointments/", headers=admin["headers"])
    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [first["id"], second["id"]]


def test_admin_filters_appointments(
    client, admin, patient, other_patient, doctor
):
    day, first, second = two_appointments(
        client, admin, patient, other_patient, doctor
    )

    by_date = client.get(
        "/appointments/",
        params={"appointment_date": day.isoformat()},
        headers=admin["headers"],
    )
    assert len(by_date.json()) == 2

    by_doctor = client.get(
        "/appointments/",
        params={"doctor_id": doctor["data"]["id"]},
        headers=admin["headers"],
    )
    assert len(by_doctor.json()) == 2

    no_doctor = client.get(
        "/appointments/", params={"doctor_id": 999}, headers=admin["headers"]
    )
    assert no_doctor.json() == []

    cancelled = client.post(
        f"/appointments/{second['id']}/cancel", headers=admin["headers"]
    )
    assert cancelled.status_code == 200

    confirmed = client.get(
        "/appointments/", params={"status": "confirmed"}, headers=admin["headers"]
    )
    assert [item["id"] for item in confirmed.json()] == [first["id"]]

    only_cancelled = client.get(
        "/appointments/", params={"status": "cancelled"}, headers=admin["headers"]
    )
    assert [item["id"] for item in only_cancelled.json()] == [second["id"]]


def test_admin_pagination(client, admin, patient, other_patient, doctor):
    _, first, second = two_appointments(
        client, admin, patient, other_patient, doctor
    )

    page_one = client.get(
        "/appointments/",
        params={"skip": 0, "limit": 1},
        headers=admin["headers"],
    )
    assert [item["id"] for item in page_one.json()] == [first["id"]]

    page_two = client.get(
        "/appointments/",
        params={"skip": 1, "limit": 1},
        headers=admin["headers"],
    )
    assert [item["id"] for item in page_two.json()] == [second["id"]]


def test_admin_list_permissions(
    client, admin, patient, receptionist, doctor
):
    url = "/appointments/"

    assert client.get(url).status_code == 401
    assert client.get(url, headers=patient["headers"]).status_code == 403
    assert client.get(url, headers=doctor["headers"]).status_code == 403
    assert client.get(url, headers=receptionist["headers"]).status_code == 403
    assert client.get(url, headers=admin["headers"]).status_code == 200


def test_admin_list_validation(client, admin):
    bad_status = client.get(
        "/appointments/", params={"status": "bogus"}, headers=admin["headers"]
    )
    assert bad_status.status_code == 422

    zero_limit = client.get(
        "/appointments/", params={"limit": 0}, headers=admin["headers"]
    )
    assert zero_limit.status_code == 422

    too_many = client.get(
        "/appointments/", params={"limit": 101}, headers=admin["headers"]
    )
    assert too_many.status_code == 422