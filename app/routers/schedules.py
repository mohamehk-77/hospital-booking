from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.doctor import Doctor
from app.models.doctor_schedule import DoctorSchedule
from app.models.user import User, UserRole
from app.schemas.doctor_schedule import ScheduleCreate, ScheduleRead

router = APIRouter(prefix="/doctors/{doctor_id}/schedules", tags=["Schedules"])


def get_active_doctor(doctor_id: int, db: Session) -> Doctor:
    doctor = db.get(Doctor, doctor_id)
    if doctor is None or not doctor.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found",
        )
    return doctor


@router.get("/", response_model=list[ScheduleRead])
def list_schedules(doctor_id: int, db: Session = Depends(get_db)):
    get_active_doctor(doctor_id, db)
    query = (
        select(DoctorSchedule)
        .where(
            DoctorSchedule.doctor_id == doctor_id,
            DoctorSchedule.is_active.is_(True),
        )
        .order_by(DoctorSchedule.weekday)
    )
    return db.scalars(query).all()


@router.post("/", response_model=ScheduleRead, status_code=status.HTTP_201_CREATED)
def create_schedule(
    doctor_id: int,
    data: ScheduleCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    get_active_doctor(doctor_id, db)

    existing = db.scalar(
        select(DoctorSchedule).where(
            DoctorSchedule.doctor_id == doctor_id,
            DoctorSchedule.weekday == data.weekday,
        )
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Schedule already exists for this weekday",
        )

    schedule = DoctorSchedule(doctor_id=doctor_id, **data.model_dump())
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schedule(
    doctor_id: int,
    schedule_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    schedule = db.get(DoctorSchedule, schedule_id)
    if schedule is None or schedule.doctor_id != doctor_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found",
        )

    db.delete(schedule)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)