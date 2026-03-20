from datetime import datetime, timedelta
from uuid import uuid4

import bcrypt
import jwt
from jwt import InvalidTokenError

from app.core.config import settings


def hash_value(raw_value: str) -> str:
    # The Java source uses BCrypt hashes in the $2a$10$... format.
    return bcrypt.hashpw(raw_value.encode("utf-8"), bcrypt.gensalt(rounds=10, prefix=b"2a")).decode("utf-8")


def verify_hash(raw_value: str, hashed_value: str) -> bool:
    try:
        return bcrypt.checkpw(raw_value.encode("utf-8"), hashed_value.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(subject_account_number: str) -> str:
    payload = {
        "sub": subject_account_number,
        "iat": int(datetime.utcnow().timestamp()),
        "exp": int((datetime.utcnow() + timedelta(days=1)).timestamp()),
        "jti": uuid4().hex,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS512")


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=["HS512"])


def is_invalid_token(error: Exception) -> bool:
    return isinstance(error, InvalidTokenError)
