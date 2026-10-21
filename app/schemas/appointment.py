from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field

from app.models.appointment import AppointmentStatus


class AppointmentCreate(BaseModel):
    doctor_id: int
    appointment_date: date
    start_time: time
    notes: str | None = Field(default=None, max_length=500)


class AppointmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    doctor_id: int
    appointment_date: date
    start_time: time
    end_time: time
    status: AppointmentStatus
    notes: str | None = None
    created_at: datetime | None = None


class AvailableSlot(BaseModel):
    start_time: time
    end_time: time