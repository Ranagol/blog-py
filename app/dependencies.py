from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User
from app.security import ALGORITHM

# Dependency. Extract the JWT token from the request's Authorization header using the HTTPBearer scheme
# The scheme is simply this: Authorization: Bearer eyJhbGciOiJIUzI1NiIs... Bearer = scheme
bearer_scheme = HTTPBearer(auto_error=False)

# Session: the object you use to talk to the database (query, add, commit)
DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
    ],
    db: DbSession,
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized

    try:
        claims = jwt.decode(
            credentials.credentials,
            settings.secret_key.get_secret_value(),
            algorithms=[ALGORITHM],
            options={"require": ["exp", "sub"]},
        )
    except jwt.InvalidTokenError:
        raise unauthorized from None

    subject = claims.get("sub")
    if not isinstance(subject, str) or not subject.isdecimal():
        raise unauthorized

    user = db.get(User, int(subject))
    if user is None:
        raise unauthorized
    return user

# Dependency for getting the current authenticated user
CurrentUser = Annotated[User, Depends(get_current_user)]




