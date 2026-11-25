
from getpass import getpass

from sqlalchemy import select

from app.database import SessionLocal
from app.models import AdminUser
from app.security import hash_password


def create_admin():
    print("\n=== OCR PLATFORM SUPER-ADMIN SETUP ===\n")

    username = input("Enter admin username: ").strip()
    email = input("Enter admin email: ").strip().lower()

    if not username or not email or "@" not in email:
        print("Invalid username or email.")
        return

    password = getpass("Enter admin password: ")
    confirm_password = getpass("Confirm admin password: ")

    if password != confirm_password:
        print("Passwords do not match.")
        return

    if len(password) < 12:
        print("Password must contain at least 12 characters.")
        return

    with SessionLocal() as db:
        existing_admin = db.scalar(select(AdminUser.id).limit(1))

        if existing_admin is not None:
            print("An admin account already exists.")
            print("No additional admin account was created.")
            return

        existing_username = db.scalar(
            select(AdminUser.id).where(AdminUser.username == username)
        )

        existing_email = db.scalar(
            select(AdminUser.id).where(AdminUser.email == email)
        )

        if existing_username or existing_email:
            print("Username or email is already registered.")
            return

        admin = AdminUser(
            username=username,
            email=email,
            password_hash=hash_password(password),
            is_active=True,
        )

        db.add(admin)
        db.commit()

        print("\nSUPER-ADMIN ACCOUNT CREATED SUCCESSFULLY!")
        print("Admin username:", username)
        print("Admin email:", email)


if __name__ == "__main__":
    create_admin()
