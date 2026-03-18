"""
Security utilities: BCrypt password/PIN hashing + JWT (HS512, no expiry).

bcrypt__ident="2a"
    Forces passlib to emit the $2a$10$... prefix that Spring Security's
    BCryptPasswordEncoder generates, matching every hash in the legacy
    CSV ground truth exactly.  Without this, passlib defaults to $2b$
    which is compatible for *verification* but produces divergent hash
    strings on *creation*, breaking parity in stored-value comparisons.
"""
from passlib.context import CryptContext
from jose import jwt, JWTError

from app.database import settings

ALGORITHM = "HS512"

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__ident="2a",
)


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_token(subject: str) -> str:
    """Generate a HS512 JWT with sub=account_number and NO expiry claim."""
    payload = {"sub": subject}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> str:
    """Return the 'sub' claim (account_number) or raise JWTError."""
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    sub: str = payload.get("sub")
    if sub is None:
        raise JWTError("Missing sub claim")
    return sub
