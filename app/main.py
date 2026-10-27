from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
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

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

is_production = settings.ENVIRONMENT == "production"

app = FastAPI(
    title="Hospital Booking API",
    docs_url=None if is_production else "/docs",
    redoc_url=None if is_production else "/redoc",
    openapi_url=None if is_production else "/openapi.json",
    swagger_ui_parameters={"persistAuthorization": True},
)

@app.get("/departments", include_in_schema=False)
def departments_page(request: Request):
    return templates.TemplateResponse(
        request, "departments.html", {"active": "departments"}
    )


@app.get("/doctors", include_in_schema=False)
def doctors_page(request: Request):
    return templates.TemplateResponse(request, "doctors.html", {"active": "doctors"})


@app.get("/booking", include_in_schema=False)
def booking_page(request: Request):
    return templates.TemplateResponse(request, "booking.html", {"active": "booking"})


@app.get("/about", include_in_schema=False)
def about_page(request: Request):
    return templates.TemplateResponse(request, "about.html", {"active": "about"})


@app.get("/contact", include_in_schema=False)
def contact_page(request: Request):
    return templates.TemplateResponse(request, "contact.html", {"active": "contact"})


app.include_router(auth.router)
app.include_router(departments.router)
app.include_router(doctors.router)
app.include_router(schedules.router)
app.include_router(appointments.router)
app.include_router(staff.router)
app.include_router(patients.router)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/health/db")
def db_health_check(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"database": "connected"}


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(STATIC_DIR / "index.html")