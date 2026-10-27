from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.routers import (
    appointments,
    auth,
    departments,
    doctors,
    patients,
    schedules,
    staff,
)

app = FastAPI(
    title="Hospital Booking API",
    swagger_ui_parameters={"persistAuthorization": True},
)

app.include_router(auth.router)
app.include_router(departments.router)
app.include_router(doctors.router)
app.include_router(schedules.router)
app.include_router(appointments.router)
app.include_router(staff.router)
app.include_router(patients.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/health/db")
def db_health_check(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"database": "connected"}