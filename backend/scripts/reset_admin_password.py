from getpass import getpass
from sqlalchemy import select

from app.database.db import get_db
from app.models.user import User
from app.core.security import hash_password


def reset_password():
    email = input("Admin email: ").strip().lower()

    new_password = getpass("New password: ")
    confirm_password = getpass("Confirm password: ")

    if len(new_password) < 8:
        print("Password must be at least 8 characters!")
        return

    if new_password != confirm_password:
        print("Passwords do not match!")
        return

    generator = get_db()
    db = next(generator)

    try:
        admin = db.scalar(
            select(User).where(
                User.email == email,
                User.role == "admin"
            )
        )

        if not admin:
            print("Admin account not found!")
            return

        admin.hashed_password = hash_password(new_password)
        db.commit()

        print("Admin password reset successfully!")

    finally:
        db.close()


if __name__ == "__main__":
    reset_password()