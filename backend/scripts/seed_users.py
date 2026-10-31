"""Create (or reset) the initial admin and staff accounts.

Run from the backend folder:  python -m scripts.seed_users
Dev-only passwords: change them before any real deployment.
"""
from sqlalchemy import select

from app.database.db import get_db
from app.models.user import User
from app.core.security import hash_password

ACCOUNTS = [
    ("Mimansa Sharma", "mimansasharma308@gmail.com", "123456", "admin"),
    ("Nancy", "iamnaincy33@gmail.com", "123456", "staff"),
]


def seed():
    generator = get_db()
    db = next(generator)
    try:
        for name, email, password, role in ACCOUNTS:
            user = db.scalar(select(User).where(User.email == email))
            if user:
                user.hashed_password = hash_password(password)
                user.role, user.is_active, user.email_verified = role, True, True
                print(f"updated {role}: {email}")
            else:
                db.add(User(full_name=name, email=email, hashed_password=hash_password(password),
                            role=role, is_active=True, email_verified=True))
                print(f"created {role}: {email}")
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        generator.close()


if __name__ == "__main__":
    seed()
