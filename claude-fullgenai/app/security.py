"""
Security utilities: bcrypt hashing and HS512 JWT handling.

BCrypt:  uses $2b$ prefix internally (passlib maps $2a$ ↔ $2b$ automatically).
         Java Spring Security BCryptPasswordEncoder stores $2a$10$... hashes;
         passlib verifies these transparently.
JWT:     HS512, no exp claim, sub = accountNumber.
"""
import bcrypt
import jwt as pyjwt
import time
from app.config import SECRET_KEY, ALGORITHM


# ---------------------------------------------------------------------------
# Password / PIN hashing – bcrypt compatible with $2a$10$... Java hashes
# ---------------------------------------------------------------------------

def hash_password(plain: str) -> str:
    """Hash a password with bcrypt (cost 10). Returns $2b$ hash."""
    salt = bcrypt.gensalt(rounds=10)
    return bcrypt.hashpw(plain.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify plain password against a stored bcrypt hash ($2a$ or $2b$)."""
    # Normalise $2a$ → $2b$ for python-bcrypt compatibility
    hashed_bytes = hashed.encode("utf-8")
    if hashed_bytes.startswith(b"$2a$"):
        hashed_bytes = b"$2b$" + hashed_bytes[4:]
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed_bytes)
    except Exception:
        return False


# PIN uses identical bcrypt hashing
hash_pin = hash_password
verify_pin = verify_password


# ---------------------------------------------------------------------------
# JWT – HS512, sub = accountNumber, no exp
# ---------------------------------------------------------------------------

def _get_secret_bytes() -> bytes:
    """Base64-decode the secret key, matching Java's Decoders.BASE64.decode() behaviour."""
    import base64
    try:
        return base64.b64decode(SECRET_KEY)
    except Exception:
        return SECRET_KEY.encode("utf-8")


def create_access_token(account_number: str) -> str:
    payload = {"sub": account_number, "iat": int(time.time())}
    return pyjwt.encode(payload, _get_secret_bytes(), algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and verify an HS512 JWT. Raises jwt.PyJWTError on failure."""
    return pyjwt.decode(
        token,
        _get_secret_bytes(),
        algorithms=[ALGORITHM],
        options={"verify_exp": False},
    )
