"""Authentication helpers: password hashing and JWT helpers.

This module centralizes security-related utilities and keeps behavior
consistent across the codebase (e.g. bcrypt truncation and HS512 tokens).
"""

import os
from passlib.context import CryptContext
from jose import jwt, JWTError

JWT_SECRET = os.getenv("JWT_SECRET", "change-me")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS512")

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    # bcrypt has a 72-byte input limit; truncate deterministically to match behavior
    def _truncate_to_72(s: str) -> str:
        b = s.encode("utf-8")
        if len(b) <= 72:
            return s
        # truncate bytes and decode safely (drop partial multi-byte sequence)
        return b[:72].decode("utf-8", "ignore")

    return pwd_ctx.hash(_truncate_to_72(password))


def verify_password(plain: str, hashed: str) -> bool:
    try:
        # apply same truncation used when hashing so verification succeeds for long inputs
        def _truncate_to_72(s: str) -> str:
            b = s.encode("utf-8")
            if len(b) <= 72:
                return s
            return b[:72].decode("utf-8", "ignore")

        return pwd_ctx.verify(_truncate_to_72(plain), hashed)
    except Exception:
        return False


def create_token(account_number: str) -> str:
    payload = {"sub": account_number}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload  # Returns {'sub': 'account_number'}
    except JWTError:
        return {}
