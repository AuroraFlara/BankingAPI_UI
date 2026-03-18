from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.api_errors import ApiError
from app.core.security import parse_token_subject


bearer = HTTPBearer(auto_error=True)


def get_account_number_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
) -> str:
    try:
        return parse_token_subject(credentials.credentials)
    except Exception as exc:
        raise ApiError(status_code=401, payload={"error": "Invalid token"}) from exc
