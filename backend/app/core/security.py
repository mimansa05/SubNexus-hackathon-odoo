from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.core.config import settings


# Password hashing utility
password_hash = PasswordHash.recommended()


# 1. Hash password before storing in database
def hash_password(password: str) -> str:
    return password_hash.hash(password)


# 2. Verify entered password during login
def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:

    return password_hash.verify(
        plain_password,
        hashed_password
    )


# 3. Generate JWT access token
def create_access_token(data: dict) -> str:

    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({
        "exp": expire
    })

    token = jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )

    return token


# Email confirmation token (single purpose, so it cannot be used to log in)
def create_email_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        hours=settings.EMAIL_VERIFY_EXPIRE_HOURS
    )
    return jwt.encode(
        {"sub": user_id, "purpose": "verify_email", "exp": expire},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )


def decode_email_token(token: str) -> str | None:
    payload = decode_access_token(token)
    if not payload or payload.get("purpose") != "verify_email":
        return None
    return payload.get("sub")


# 4. Verify JWT access token
def decode_access_token(token: str):

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )

        return payload

    except jwt.InvalidTokenError:
        return None