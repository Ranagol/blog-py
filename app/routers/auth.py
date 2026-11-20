from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.dependencies import DbSession
from app.models import User
from app.schemas.auth import TokenResponse, UserCreate, UserCredentials, UserRead
from app.security import (
    create_access_token,
    hash_password,
    verify_password,
)

# This is actually a router for user-related operations like registration and login
router = APIRouter(prefix="/users", tags=["users"])

# Used for preventing timing attacks by always verifying a password hash, even if the user does not exist
DUMMY_PASSWORD_HASH = hash_password("not-a-real-user-password")

@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
def register_user(payload: UserCreate, db: DbSession) -> User:
    email = str(payload.email).lower()
    existing_user = db.scalar(select(User).where(User.email == email))
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user = User(email=email, hashed_password=hash_password(payload.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        ) from None
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: UserCredentials, db: DbSession) -> TokenResponse:
    email = str(payload.email).lower()
    user = db.scalar(select(User).where(User.email == email))
    # WHY DO WE NEED DUMMY_PASSWORD_HASH? 
    hashed_password = user.hashed_password if user is not None else DUMMY_PASSWORD_HASH
    password_is_valid = verify_password(payload.password, hashed_password)
    if user is None or not password_is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResponse(access_token=create_access_token(user.id))
