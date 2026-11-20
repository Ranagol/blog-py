from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.config import settings

# Needed for creating a JWT access token with expiration time
ALGORITHM = "HS256"

# Creates a hashed password from a plain text password
def hash_password(password: str) -> str:
    return PasswordHash.recommended().hash(password)

# Verifies a plain text password against a hashed password
def verify_password(password: str, hashed_password: str) -> bool:
    return PasswordHash.recommended().verify(password, hashed_password)

# Creates a JWT access token for a given user ID with an expiration time
def create_access_token(user_id: int) -> str:
    expires_at = datetime.now(UTC) + timedelta(
        # We are using the settings object, that has all things from the .env file
        minutes=settings.access_token_expire_minutes
    )
    # Claims is the payload of the JWT token containing the subject (user ID) and expiration time.
    claims = {"sub": str(user_id), "exp": expires_at}
    return jwt.encode(
        claims,
        settings.secret_key.get_secret_value(),
        algorithm=ALGORITHM,
    )
