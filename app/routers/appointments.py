from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.appointment import Appointment, AppointmentStatus
from app.models.doctor import Doctor
from app.models.doctor_schedule import DoctorSchedule
from app.models.user import User, UserRole
from app.schemas.appointment import AppointmentCreate, AppointmentRead, AvailableSlot

router = APIRouter(prefix="/appointments", tags=["Appointments"])


def get_active_doctor(doctor_id: int, db: Session) -> Doctor:
    doctor = db.get(Doctor, doctor_id)
    if doctor is None or not doctor.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found",
        )
    return doctor


def get_schedule(doctor_id: int, day: date, db: Session) -> DoctorSchedule | None:
    return db.scalar(
        select(DoctorSchedule).where(
            DoctorSchedule.doctor_id == doctor_id,
            DoctorSchedule.weekday == day.weekday(),
            DoctorSchedule.is_active.is_(True),
        )
    )


def build_slots(schedule: DoctorSchedule):
    slots = []
    step = timedelta(minutes=schedule.slot_minutes)
    current = datetime.combine(date.today(), schedule.start_time)
    end = datetime.combine(date.today(), schedule.end_time)
    while current + step <= end:
        slots.append((current.time(), (current + step).time()))
        current += step
    return slots


@router.get("/available", response_model=list[AvailableSlot])
def available_slots(
    doctor_id: int,
    appointment_date: date,
    db: Session = Depends(get_db),
):
    get_active_doctor(doctor_id, db)

    schedule = get_schedule(doctor_id, appointment_date, db)
    if schedule is None:
        return []

    booked = set(
        db.scalars(
            select(Appointment.start_time).where(
                Appointment.doctor_id == doctor_id,
                Appointment.appointment_date == appointment_date,
                Appointment.status == AppointmentStatus.CONFIRMED,
            )
        ).all()
    )

    now = datetime.now()
    result = []
    for start, end in build_slots(schedule):
        if start in booked:
            continue
        if datetime.combine(appointment_date, start) <= now:
            continue
        result.append(AvailableSlot(start_time=start, end_time=end))
    return result


@router.post("/", response_model=AppointmentRead, status_code=status.HTTP_201_CREATED)
def book_appointment(
    data: AppointmentCreate,
    db: Session = Depends(get_db),
    patient: User = Depends(require_roles(UserRole.PATIENT)),
):
    get_active_doctor(data.doctor_id, db)

    if datetime.combine(data.appointment_date, data.start_time) <= datetime.now():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot book a time in the past",
        )

    schedule = get_schedule(data.doctor_id, data.appointment_date, db)
    if schedule is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Doctor does not work on this day",
        )

    slot = next((s for s in build_slots(schedule) if s[0] == data.start_time), None)
    if slot is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid time slot for this doctor",
        )

    appointment = Appointment(
        patient_id=patient.id,
        doctor_id=data.doctor_id,
        appointment_date=data.appointment_date,
        start_time=slot[0],
        end_time=slot[1],
        notes=data.notes,
    )
    db.add(appointment)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This slot is already booked",
        )
    db.refresh(appointment)
    return appointment


@router.get("/my", response_model=list[AppointmentRead])
def my_appointments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        select(Appointment)
        .where(Appointment.patient_id == current_user.id)
        .order_by(Appointment.appointment_date, Appointment.start_time)
    )
    return db.scalars(query).all()


@router.post("/{appointment_id}/cancel", response_model=AppointmentRead)
def cancel_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    appointment = db.get(Appointment, appointment_id)
    is_owner = appointment is not None and appointment.patient_id == current_user.id
    if appointment is None or not (is_owner or current_user.role == UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )

    if appointment.status != AppointmentStatus.CONFIRMED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only confirmed appointments can be cancelled",
        )

    appointment.status = AppointmentStatus.CANCELLED
    db.commit()
    db.refresh(appointment)
    return appointment