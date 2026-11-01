🏥 Hospital Booking System

A hospital appointment booking platform built with FastAPI, SQLAlchemy, and PostgreSQL. The system provides role-based workflows for patients, doctors, receptionists, and administrators, along with a web interface and RESTful API.

"Python" (https://img.shields.io/badge/Python-3.13-blue?logo=python&logoColor=white)
"FastAPI" (https://img.shields.io/badge/FastAPI-Framework-009688?logo=fastapi&logoColor=white)
"PostgreSQL" (https://img.shields.io/badge/PostgreSQL-Database-4169E1?logo=postgresql&logoColor=white)
"SQLAlchemy" (https://img.shields.io/badge/SQLAlchemy-ORM-D71F00)
"Docker" (https://img.shields.io/badge/Docker-Supported-2496ED?logo=docker&logoColor=white)

---

📌 Table of Contents

- "Overview" (#-overview)
- "Features" (#-features)
- "Technology Stack" (#-technology-stack)
- "Architecture" (#-architecture)
- "User Roles & Permissions" (#-user-roles--permissions)
- "Database Design" (#-database-design)
- "API Reference" (#-api-reference)
- "Getting Started" (#-getting-started)
- "Environment Variables" (#-environment-variables)
- "Database Migrations" (#-database-migrations)
- "Testing" (#-testing)
- "Deployment" (#-deployment)
- "Security" (#-security)
- "Project Structure" (#-project-structure)
- "Future Improvements" (#-future-improvements)
- "License" (#-license)

---

🚀 Overview

Hospital Booking is a backend-driven hospital appointment management system designed to simplify the interaction between patients and healthcare providers.

Patients can browse doctors, check available appointment slots, book appointments, and manage their bookings.

Doctors can manage their assigned appointments, while receptionists handle patient searches and bookings on behalf of patients. Administrators manage doctors, departments, schedules, staff accounts, and appointment records.

The project focuses on clean backend architecture, authentication, authorization, database integrity, and real-world appointment scheduling rules.

✨ Features

👤 Patient Management

- Patient account registration and login.
- Secure password hashing.
- View personal appointment history.
- Browse available doctors and departments.
- Check available appointment slots.
- Book appointments with optional notes.
- Cancel personal appointments.

🩺 Doctor Management

- Doctor profile management.
- Specialization and department assignment.
- View personal confirmed appointments.
- Filter appointments by date.
- Complete appointments after their scheduled start time.

🧑‍💼 Receptionist Management

- Search active patients by email.
- Book appointments on behalf of patients.
- Cancel appointments for patients.

🛡️ Admin Dashboard Capabilities

- Create and update departments.
- Create and update doctor profiles.
- Manage doctor schedules.
- Configure appointment slot durations.
- Create receptionist accounts.
- View and filter all appointments.
- Manage appointment records with pagination.

📅 Appointment Scheduling

- Automatic appointment slot generation.
- Weekly doctor availability schedules.
- Configurable appointment durations.
- Prevention of double booking.
- Rejection of past appointments.
- Validation of appointment times against doctor schedules.
- Appointment status management:
  - "confirmed"
  - "cancelled"
  - "completed"

---

🛠️ Technology Stack

Technology| Purpose
Python 3.13| Backend programming language
FastAPI| REST API framework
SQLAlchemy| ORM and database interaction
PostgreSQL| Relational database
Pydantic v2| Data validation and serialization
Alembic| Database migrations
JWT| Token-based authentication
OAuth2| Authentication flow
Passlib & bcrypt| Password hashing
Jinja2| Server-side HTML templates
HTML / CSS / JavaScript| Web interface
Uvicorn| ASGI application server
Pytest| Automated testing
Docker| Containerization
Docker Compose| Multi-container setup
Render| Deployment configuration

---

🏗️ Architecture

The project follows a modular FastAPI architecture.

Main Components

1. Routers

- Handle HTTP requests and API endpoints.
- Apply authentication and authorization rules.
- Coordinate application workflows.

2. Models

- Define SQLAlchemy database entities.
- Manage relationships between users, doctors, departments, schedules, and appointments.

3. Schemas

- Validate incoming request data.
- Serialize database objects into API responses.
- Enforce input constraints using Pydantic.

4. Core

- Application configuration.
- Database connection and session management.
- JWT authentication.
- Password hashing and verification.
- Role-based access control.

5. Templates & Static Files

- Jinja2 HTML templates.
- CSS styling.
- JavaScript functionality.

---

🔐 User Roles & Permissions

The system implements Role-Based Access Control (RBAC).

Role| Permissions
Patient| Register, login, browse doctors, book appointments, view and cancel personal bookings
Doctor| View personal appointments and complete assigned appointments
Receptionist| Search patients, create bookings for patients, and cancel bookings
Admin| Manage doctors, departments, schedules, receptionists, and all appointments

Important: Public registration always assigns the "patient" role. Privileged roles cannot be assigned through the public registration request.

---

🗄️ Database Design

The main database entities include:

Entity| Description
Users| Account information, email, password hash, role, and active status
Departments| Hospital department records
Doctors| Doctor profiles, specialization, and department association
Doctor Schedules| Weekly working hours and appointment duration
Appointments| Patient bookings, doctor assignment, time, notes, and status

Main Relationships

- A doctor is associated with a user account and a department.
- A department can contain multiple doctors.
- A doctor can have multiple weekly schedule records.
- An appointment belongs to one patient and one doctor.
- A database-level unique partial index prevents duplicate confirmed bookings for the same doctor, date, and start time.

Database schema changes are managed through Alembic migrations.

---

🌐 API Reference

All protected endpoints require a valid JWT Bearer token.

Authentication — "/auth"

Method| Endpoint| Access
POST| "/auth/register"| Public
POST| "/auth/login"| Public
GET| "/auth/me"| Authenticated

Departments — "/departments"

Method| Endpoint| Access
GET| "/departments/"| Public
POST| "/departments/"| Admin
PATCH| "/departments/{department_id}"| Admin

Doctors — "/doctors"

Method| Endpoint| Access
GET| "/doctors/"| Public
GET| "/doctors/{doctor_id}"| Public
POST| "/doctors/"| Admin
PATCH| "/doctors/{doctor_id}"| Admin

Doctor Schedules

Method| Endpoint| Access
GET| "/doctors/{doctor_id}/schedules/"| Public
POST| "/doctors/{doctor_id}/schedules/"| Admin
DELETE| "/doctors/{doctor_id}/schedules/{schedule_id}"| Admin

Appointments — "/appointments"

Method| Endpoint| Access
GET| "/appointments/available"| Public
POST| "/appointments/"| Patient
GET| "/appointments/my"| Authenticated
GET| "/appointments/doctor/me"| Doctor
GET| "/appointments/"| Admin
POST| "/appointments/for-patient"| Receptionist / Admin
POST| "/appointments/{appointment_id}/cancel"| Owner / Receptionist / Admin
POST| "/appointments/{appointment_id}/complete"| Assigned Doctor

Staff & Patient Search

Method| Endpoint| Access
POST| "/staff/receptionists"| Admin
GET| "/patients/search"| Receptionist / Admin

Health Checks

Method| Endpoint| Access
GET| "/health"| Public
GET| "/health/db"| Public

API Documentation

During development, interactive API documentation is available at:

- Swagger UI: "/docs"
- ReDoc: "/redoc"
- OpenAPI Schema: "/openapi.json"

These documentation endpoints are disabled in production mode.

---

⚙️ Getting Started

Prerequisites

Make sure you have installed:

- Python 3.13
- PostgreSQL
- Git

Alternatively, you can use Docker and Docker Compose.

1. Clone the Repository

git clone https://github.com/mohamehk-77/hospital-booking.git

cd hospital-booking

2. Create a Virtual Environment

python -m venv .venv

Activate it:

Windows:

.venv\Scripts\Activate.ps1

Linux / macOS:

source .venv/bin/activate

3. Install Dependencies

pip install -r requirements.txt

pip install -r requirements-dev.txt

4. Configure Environment Variables

Copy the example environment file:

cp .env.example .env

On Windows, you can use:

Copy-Item .env.example .env

Configure your database connection and secret key in ".env".

5. Run Database Migrations

alembic upgrade head

6. Start the Application

uvicorn app.main:app --reload

The application will be available at:

Web Application:
http://127.0.0.1:8000

API Documentation:
http://127.0.0.1:8000/docs

---

🔑 Environment Variables

Variable| Description
"DATABASE_URL"| PostgreSQL database connection URL
"SECRET_KEY"| Secret key used for JWT signing
"ENVIRONMENT"| Application environment ("development" or "production")

Example configuration:

DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/hospital_db

SECRET_KEY=your_secure_random_secret_key

ENVIRONMENT=development

Generate a secure secret key:

python -c "import secrets; print(secrets.token_hex(32))"

Never commit real credentials, production secrets, or ".env" files to GitHub.

---

🔄 Database Migrations

The project uses Alembic to manage database schema changes.

Apply existing migrations:

alembic upgrade head

Generate a new migration after model changes:

alembic revision --autogenerate -m "describe your changes"

Always review generated migration files before applying them.

---

🧪 Testing

The project includes automated tests using Pytest and FastAPI TestClient.

Run the test suite:

pytest

Tests cover:

- User registration and authentication.
- JWT authentication and protected routes.
- Role-based authorization.
- Doctor and department workflows.
- Appointment availability.
- Booking validation.
- Double-booking prevention.
- Appointment cancellation.
- Receptionist workflows.
- Administrator permissions and appointment filtering.

---

🚀 Deployment

Deployment configurations are included in the repository.

Docker Compose

Build and start the application:

docker compose up --build -d

The configuration starts PostgreSQL and the FastAPI application.

Set secure values for "POSTGRES_PASSWORD" and "SECRET_KEY" before using this configuration in a real deployment.

Render

The repository includes a "render.yaml" Blueprint configuration for:

- Python web service.
- Managed PostgreSQL database.
- Environment variable configuration.
- Generated production secret key.
- Automatic database migrations during startup.

Connect the GitHub repository to Render and deploy using the Blueprint configuration.

Additional deployment instructions:

- "DEPLOY.md" (DEPLOY.md)
- "DEPLOY-ORACLE.md" (DEPLOY-ORACLE.md)

---

🛡️ Security

Security mechanisms implemented in the application include:

- Password hashing using bcrypt.
- JWT-based authentication.
- OAuth2 password authentication flow.
- Role-based access control.
- Protected administrative endpoints.
- Server-side role assignment during registration.
- Validation of user input through Pydantic.
- Database constraints for confirmed appointment slots.
- Disabled API documentation in production mode.

Production note: Before using this project with real patient data, perform a thorough security and privacy review, configure HTTPS and production secrets, and establish appropriate backups and access controls.

---

📂 Project Structure

hospital-booking/
│
├── app/
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── deps.py
│   │   └── security.py
│   │
│   ├── models/
│   ├── routers/
│   ├── schemas/
│   │
│   ├── static/
│   ├── templates/
│   │
│   └── main.py
│
├── alembic/
│   └── versions/
│
├── deploy/
├── scripts/
├── tests/
│
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── render.yaml
├── requirements.txt
├── requirements-dev.txt
│
└── README.md

---

🔮 Future Improvements

Potential enhancements for future versions:

- Appointment reminder notifications.
- Email and SMS integration.
- Advanced reporting and analytics.
- Audit logging for sensitive operations.
- Doctor holiday and leave management.
- Appointment rescheduling workflows.
- Enhanced administrative dashboards.
- End-to-end browser testing.

These are proposed improvements, not features currently claimed as implemented.

---

📸 Screenshots & Demo

Screenshots and a live demo URL can be added here when available.

---

📄 License

No license file is currently included in this repository. Please contact the repository owner regarding permissions before reusing or distributing the project.

---

👨‍💻 Author

Mohamed Abdalwahed

Backend Developer | Healthcare Professional

GitHub: "@mohamehk-77" (https://github.com/mohamehk-77)

Project Repository: "Hospital Booking System" (https://github.com/mohamehk-77/hospital-booking)

---

⭐ If you find this project interesting, feel free to explore the repository and follow its development.
