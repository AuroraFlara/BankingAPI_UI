from datetime import datetime, timedelta

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__ident="2a",
    bcrypt__rounds=10,
    bcrypt__truncate_error=False,
)


def _normalize_bcrypt_secret(raw: str) -> str:
    raw_bytes = raw.encode("utf-8")
    if len(raw_bytes) <= 72:
        return raw
    # BCrypt processes only the first 72 bytes; normalize to avoid backend ValueError.
    return raw_bytes[:72].decode("utf-8", errors="ignore")


def hash_value(raw: str) -> str:
    return pwd_context.hash(_normalize_bcrypt_secret(raw))


def verify_value(raw: str, hashed: str) -> bool:
    return pwd_context.verify(_normalize_bcrypt_secret(raw), hashed)


def create_access_token(account_number: str) -> str:
    payload = {"sub": account_number}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def parse_token_subject(token: str) -> str:
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    sub = payload.get("sub")
    if not sub:
        raise ValueError("Invalid token subject")
    return sub


def token_db_expiry() -> datetime:
    return datetime.utcnow() + timedelta(days=36500)
