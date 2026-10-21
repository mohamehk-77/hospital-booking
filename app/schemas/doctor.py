from pydantic import BaseModel, ConfigDict, EmailStr, Field


class DoctorCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    department_id: int
    specialization: str = Field(min_length=2, max_length=150)
    bio: str | None = None


class DoctorUpdate(BaseModel):
    department_id: int | None = None
    specialization: str | None = Field(default=None, min_length=2, max_length=150)
    bio: str | None = None
    is_active: bool | None = None


class DoctorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    department_id: int
    specialization: str
    bio: str | None = None
    is_active: bool