"""
Compatibility shim: re-exports everything from app.core.security so that
existing imports (``from app.security import ...``) continue to work unchanged.
The canonical implementation with bcrypt__ident="2a" lives in app/core/security.py.
"""
from app.core.security import (  # noqa: F401
    ALGORITHM,
    pwd_context,
    hash_password,
    verify_password,
    create_token,
    decode_token,
)
