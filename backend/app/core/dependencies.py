from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.models.user import User
from app.core.security import decode_access_token


# JWT token ko request ke Authorization header se read karega
bearer_scheme = HTTPBearer()


# Database session dependency
DbSession = Annotated[Session, Depends(get_db)]


# 1. Identify currently logged-in user
def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials,
        Depends(bearer_scheme)
    ],
    db: DbSession
) -> User:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials

    payload = decode_access_token(token)

    if payload is None or payload.get("purpose"):
        raise credentials_exception

    user_id = payload.get("sub")

    if not user_id:
        raise credentials_exception

    user = db.get(User, user_id)

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is inactive"
        )

    return user


# 2. Role-based permission checker
def require_roles(*allowed_roles: str):

    def role_checker(
        current_user: Annotated[User, Depends(get_current_user)]
    ) -> User:

        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource"
            )

        return current_user

    return role_checker


# 3. Admin-only access
require_admin = require_roles("admin")


# 4. Admin and Staff access
require_staff_or_admin = require_roles("admin", "staff")


# 5. Customer-only access
require_customer = require_roles("customer")