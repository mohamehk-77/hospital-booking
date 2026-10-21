from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Integer,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class DoctorSchedule(Base):
    __tablename__ = "doctor_schedules"
    __table_args__ = (
        UniqueConstraint("doctor_id", "weekday", name="uq_doctor_weekday"),
        CheckConstraint("weekday >= 0 AND weekday <= 6", name="ck_weekday_range"),
        CheckConstraint("start_time < end_time", name="ck_start_before_end"),
        CheckConstraint("slot_minutes > 0", name="ck_slot_positive"),
    )

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False, index=True)
    weekday = Column(Integer, nullable=False)  # 0 = Monday ... 6 = Sunday
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    slot_minutes = Column(Integer, nullable=False, default=30)
    is_active = Column(Boolean, default=True, nullable=False)

    doctor = relationship("Doctor")