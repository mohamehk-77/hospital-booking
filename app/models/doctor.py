from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    specialization = Column(String(150), nullable=False)
    bio = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    user = relationship("User")
    department = relationship("Department")

    @property
    def full_name(self) -> str:
        return self.user.full_name