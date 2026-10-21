from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.deps import require_roles
from app.core.security import hash_password
from app.models.department import Department
from app.models.doctor import Doctor
from app.models.user import User, UserRole
from app.schemas.doctor import DoctorCreate, DoctorRead, DoctorUpdate

router = APIRouter(prefix="/doctors", tags=["Doctors"])


@router.get("/", response_model=list[DoctorRead])
def list_doctors(department_id: int | None = None, db: Session = Depends(get_db)):
    query = (
        select(Doctor)
        .options(joinedload(Doctor.user))
        .where(Doctor.is_active.is_(True))
        .order_by(Doctor.id)
    )
    if department_id is not None:
        query = query.where(Doctor.department_id == department_id)
    return db.scalars(query).all()


@router.get("/{doctor_id}", response_model=DoctorRead)
def get_doctor(doctor_id: int, db: Session = Depends(get_db)):
    doctor = db.get(Doctor, doctor_id)
    if doctor is None or not doctor.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found",
        )
    return doctor


@router.post("/", response_model=DoctorRead, status_code=status.HTTP_201_CREATED)
def create_doctor(
    data: DoctorCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    email = data.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    department = db.get(Department, data.department_id)
    if department is None or not department.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department not found",
        )

    user = User(
        full_name=data.full_name,
        email=email,
        hashed_password=hash_password(data.password),
        role=UserRole.DOCTOR,
    )
    doctor = Doctor(
        user=user,
        department_id=data.department_id,
        specialization=data.specialization,
        bio=data.bio,
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor


@router.patch("/{doctor_id}", response_model=DoctorRead)
def update_doctor(
    doctor_id: int,
    data: DoctorUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    doctor = db.get(Doctor, doctor_id)
    if doctor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found",
        )

    changes = data.model_dump(exclude_unset=True)

    for field in ("department_id", "specialization", "is_active"):
        if field in changes and changes[field] is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{field} cannot be null",
            )

    new_department_id = changes.get("department_id")
    if new_department_id is not None:
        department = db.get(Department, new_department_id)
        if department is None or not department.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department not found",
            )

    for field, value in changes.items():
        setattr(doctor, field, value)

    db.commit()
    db.refresh(doctor)
    return doctor