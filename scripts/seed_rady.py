"""Seed Rady Specialized Hospital clinics, doctors and weekly schedules.

Idempotent: safe to run more than once. It reads DATABASE_URL from the app
settings (your .env), so no credentials are passed on the command line.

Demo only: every seeded doctor account gets the temporary password below.
Change it before any real use.
"""

from datetime import time

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.department import Department
from app.models.doctor import Doctor
from app.models.doctor_schedule import DoctorSchedule
from app.models.user import User, UserRole

TEMP_DOCTOR_PASSWORD = "Doctor@12345"

WEEKDAYS = {
    "السبت": 5,
    "الأحد": 6,
    "الاثنين": 0,
    "الثلاثاء": 1,
    "الأربعاء": 2,
    "الخميس": 3,
    "الجمعة": 4,
}

DEPARTMENTS = [
    (
        "الطب النفسي وعلاج الإدمان",
        "عيادة الطب النفسي وعلاج الإدمان — متابعة شاملة لحياة أفضل.",
    ),
    (
        "المخ والأعصاب",
        "عيادة المخ والأعصاب — تشخيص ومتابعة الحالات العصبية.",
    ),
    (
        "الباطنة",
        "عيادة الباطنة — رعاية الأمراض الداخلية والمزمنة.",
    ),
    (
        "العظام",
        "عيادة العظام — تشخيص وعلاج إصابات ومشاكل العظام والمفاصل.",
    ),
]

DOCTORS = [
    {
        "name": "د. أمنية بحيري",
        "email": "omnia.bahiry@example.com",
        "department": "الطب النفسي وعلاج الإدمان",
        "specialization": "الطب النفسي وعلاج الإدمان",
        "bio": "متابعة شاملة لحياة أفضل.",
        "schedules": [("الخميس", "16:00", "20:00")],
    },
    {
        "name": "د. حسام صقر",
        "email": "hussam.saqr@example.com",
        "department": "المخ والأعصاب",
        "specialization": "المخ والأعصاب",
        "bio": "تشخيص ومتابعة الحالات العصبية.",
        "schedules": [("السبت", "17:00", "19:00"), ("الثلاثاء", "17:00", "19:00")],
    },
    {
        "name": "د. إسلام سلطان",
        "email": "islam.soltan@example.com",
        "department": "المخ والأعصاب",
        "specialization": "المخ والأعصاب",
        "bio": "تشخيص ومتابعة الحالات العصبية.",
        "schedules": [("الأحد", "17:00", "19:00"), ("الأربعاء", "17:00", "19:00")],
    },
    {
        "name": "د. علي سيف",
        "email": "ali.seif@example.com",
        "department": "المخ والأعصاب",
        "specialization": "المخ والأعصاب",
        "bio": "تشخيص ومتابعة الحالات العصبية.",
        "schedules": [("الخميس", "13:00", "16:00")],
    },
    {
        "name": "د. أمير صفوت",
        "email": "amir.safwat@example.com",
        "department": "الباطنة",
        "specialization": "الباطنة",
        "bio": "متابعة الأمراض الداخلية والمزمنة.",
        "schedules": [
            ("الأحد", "12:00", "17:00"),
            ("الثلاثاء", "12:00", "17:00"),
            ("الخميس", "12:00", "17:00"),
        ],
    },
    {
        "name": "د. مصطفى خاطر",
        "email": "mostafa.khater@example.com",
        "department": "الباطنة",
        "specialization": "الباطنة والعناية المركزة",
        "bio": "الباطنة والعناية المركزة.",
        "schedules": [
            ("الثلاثاء", "16:00", "19:00"),
            ("الأربعاء", "16:00", "19:00"),
            ("الخميس", "16:00", "19:00"),
            ("الجمعة", "16:00", "19:00"),
        ],
    },
    {
        "name": "د. محمد علم الدين",
        "email": "mohamed.alameldin@example.com",
        "department": "العظام",
        "specialization": "العظام",
        "bio": "تشخيص وعلاج إصابات ومشاكل العظام والمفاصل.",
        "schedules": [("الاثنين", "09:00", "21:00"), ("الثلاثاء", "09:00", "21:00")],
    },
]


def get_or_create_department(db, name: str, description: str) -> Department:
    department = db.scalar(select(Department).where(Department.name == name))
    if department is None:
        department = Department(name=name, description=description)
        db.add(department)
        db.flush()
    else:
        department.description = description
        department.is_active = True
    return department


def get_or_create_doctor(db, data, departments) -> Doctor:
    user = db.scalar(select(User).where(User.email == data["email"]))
    if user is None:
        user = User(
            full_name=data["name"],
            email=data["email"],
            hashed_password=hash_password(TEMP_DOCTOR_PASSWORD),
            role=UserRole.DOCTOR,
        )
        db.add(user)
        db.flush()
    else:
        user.full_name = data["name"]
        user.role = UserRole.DOCTOR
        user.is_active = True

    doctor = db.scalar(select(Doctor).where(Doctor.user_id == user.id))
    department = departments[data["department"]]
    if doctor is None:
        doctor = Doctor(
            user_id=user.id,
            department_id=department.id,
            specialization=data["specialization"],
            bio=data["bio"],
        )
        db.add(doctor)
        db.flush()
    else:
        doctor.department_id = department.id
        doctor.specialization = data["specialization"]
        doctor.bio = data["bio"]
        doctor.is_active = True

    for day_name, start, end in data["schedules"]:
        weekday = WEEKDAYS[day_name]
        schedule = db.scalar(
            select(DoctorSchedule).where(
                DoctorSchedule.doctor_id == doctor.id,
                DoctorSchedule.weekday == weekday,
            )
        )
        if schedule is None:
            schedule = DoctorSchedule(
                doctor_id=doctor.id,
                weekday=weekday,
                start_time=time.fromisoformat(start),
                end_time=time.fromisoformat(end),
                slot_minutes=30,
            )
            db.add(schedule)
        else:
            schedule.start_time = time.fromisoformat(start)
            schedule.end_time = time.fromisoformat(end)
            schedule.slot_minutes = 30
            schedule.is_active = True

    return doctor


def deactivate_old_test_data(db) -> None:
    old_department = db.scalar(select(Department).where(Department.name == "Cardiology"))
    if old_department is not None:
        old_department.is_active = False

    old_user = db.scalar(select(User).where(User.email == "doctor@example.com"))
    if old_user is not None:
        old_doctor = db.scalar(select(Doctor).where(Doctor.user_id == old_user.id))
        if old_doctor is not None:
            old_doctor.is_active = False

    for doctor in db.scalars(select(Doctor).join(User)).all():
        if doctor.user.full_name == "Dr. Ahmed Hassan":
            doctor.is_active = False
        if doctor.department is not None and not doctor.department.is_active:
            doctor.is_active = False


def main() -> None:
    with SessionLocal() as db:
        departments = {}
        for name, description in DEPARTMENTS:
            departments[name] = get_or_create_department(db, name, description)

        doctors = []
        for data in DOCTORS:
            doctors.append(get_or_create_doctor(db, data, departments))

        deactivate_old_test_data(db)
        db.commit()

        schedule_count = sum(len(data["schedules"]) for data in DOCTORS)
        print(f"Departments ready: {len(DEPARTMENTS)}")
        print(f"Doctors ready: {len(doctors)}")
        print(f"Weekly schedules ready: {schedule_count}")
        print(f"Temporary doctor password: {TEMP_DOCTOR_PASSWORD}")
        print("Change these passwords before production use.")


if __name__ == "__main__":
    main()
