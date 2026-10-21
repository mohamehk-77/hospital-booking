import enum

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Text,
    Time,
    text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class AppointmentStatus(str, enum.Enum):
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class Appointment(Base):
    __tablename__ = "appointments"
    __table_args__ = (
        Index(
            "uq_doctor_active_slot",
            "doctor_id",
            "appointment_date",
            "start_time",
            unique=True,
            postgresql_where=text("status = 'confirmed'"),
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False, index=True)
    appointment_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    status = Column(
        Enum(
            AppointmentStatus,
            name="appointment_status",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        default=AppointmentStatus.CONFIRMED,
    )
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    patient = relationship("User")
    doctor = relationship("Doctor")