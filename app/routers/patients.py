from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.user import User, UserRole
from app.schemas.user import UserRead

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.get("/search", response_model=list[UserRead])
def search_patients(
    email: str = Query(min_length=3, description="Part of the patient's email"),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.RECEPTIONIST, UserRole.ADMIN)),
):
    term = email.strip().lower()
    query = (
        select(User)
        .where(
            User.role == UserRole.PATIENT,
            User.is_active.is_(True),
            User.email.contains(term, autoescape=True),
        )
        .order_by(User.email)
        .limit(20)
    )
    return db.scalars(query).all()