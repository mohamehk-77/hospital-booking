from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserRead

router = APIRouter(prefix="/staff", tags=["Staff"])


@router.post(
    "/receptionists",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
def create_receptionist(
    data: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    email = data.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = User(
        full_name=data.full_name,
        email=email,
        hashed_password=hash_password(data.password),
        role=UserRole.RECEPTIONIST,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user