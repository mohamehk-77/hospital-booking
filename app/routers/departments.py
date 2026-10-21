from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.department import Department
from app.models.user import User, UserRole
from app.schemas.department import DepartmentCreate, DepartmentRead, DepartmentUpdate

router = APIRouter(prefix="/departments", tags=["Departments"])


@router.get("/", response_model=list[DepartmentRead])
def list_departments(db: Session = Depends(get_db)):
    query = select(Department).where(Department.is_active.is_(True)).order_by(Department.name)
    return db.scalars(query).all()


@router.post("/", response_model=DepartmentRead, status_code=status.HTTP_201_CREATED)
def create_department(
    data: DepartmentCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    name = data.name.strip()
    if db.scalar(select(Department).where(Department.name == name)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department already exists",
        )

    department = Department(name=name, description=data.description)
    db.add(department)
    db.commit()
    db.refresh(department)
    return department


@router.patch("/{department_id}", response_model=DepartmentRead)
def update_department(
    department_id: int,
    data: DepartmentUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    department = db.get(Department, department_id)
    if department is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found",
        )

    changes = data.model_dump(exclude_unset=True)

    new_name = changes.get("name")
    if new_name is not None:
        new_name = new_name.strip()
        duplicate = db.scalar(
            select(Department).where(
                Department.name == new_name, Department.id != department_id
            )
        )
        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department name already in use",
            )
        changes["name"] = new_name

    for field, value in changes.items():
        setattr(department, field, value)

    db.commit()
    db.refresh(department)
    return department