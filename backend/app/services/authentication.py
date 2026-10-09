from datetime import datetime, timedelta, timezone
import secrets

import jwt
from argon2 import PasswordHasher, Type
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.config import settings
from app.models.user import User

password_hasher = PasswordHasher(type=Type.ID)
_dummy_password_hash = password_hasher.hash(secrets.token_urlsafe(32))


def normalize_email(email: str) -> str:
    return email.strip().casefold()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    hash_to_check = password_hash or _dummy_password_hash
    try:
        return password_hasher.verify(hash_to_check, password)
    except (InvalidHashError, VerificationError, VerifyMismatchError):
        return False


def create_access_token(user: User) -> tuple[str, int]:
    secret = settings.JWT_SECRET_KEY
    if len(secret.encode("utf-8")) < 32:
        raise RuntimeError("JWT_SECRET_KEY must contain at least 32 characters")

    expires_in = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "ver": user.token_version,
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
    }
    return jwt.encode(payload, secret, algorithm="HS256"), expires_in