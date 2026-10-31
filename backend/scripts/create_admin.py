from getpass import getpass
from sqlalchemy import select

from app.database.db import get_db
from app.models.user import User
from app.core.security import hash_password


def create_admin():
    full_name = input("Admin name: ").strip()
    email = input("Admin email: ").strip().lower()
    password = getpass("Admin password: ")

    if len(password) < 8:
        print("Password must be at least 8 characters")
        return

    generator = get_db()
    db = next(generator)

    try:
        existing = db.scalar(
            select(User).where(User.email == email)
        )

        if existing:
            print("This email already exists!")
            return

        admin = User(
            full_name=full_name,
            email=email,
            hashed_password=hash_password(password),
            role="admin",
            is_active=True
        )

        db.add(admin)
        db.commit()

        print("Admin account created successfully!")

    except Exception:
        db.rollback()
        raise

    finally:
        generator.close()


if __name__ == "__main__":
    create_admin()