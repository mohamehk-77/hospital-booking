import getpass

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User, UserRole


def main():
    full_name = input("Full name: ").strip()
    email = input("Email: ").strip().lower()
    password = getpass.getpass("Password (8-72 chars): ")
    confirm = getpass.getpass("Confirm password: ")

    if password != confirm:
        print("Passwords do not match.")
        return
    if not 8 <= len(password) <= 72:
        print("Password must be between 8 and 72 characters.")
        return

    with SessionLocal() as db:
        if db.scalar(select(User).where(User.email == email)):
            print("A user with this email already exists.")
            return

        admin = User(
            full_name=full_name,
            email=email,
            hashed_password=hash_password(password),
            role=UserRole.ADMIN,
        )
        db.add(admin)
        db.commit()
        print(f"Admin created: {email}")


if __name__ == "__main__":
    main()