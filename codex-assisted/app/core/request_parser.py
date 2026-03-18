import json
from typing import Any

from fastapi import Request

from app.core.api_errors import ApiError


MALFORMED_BODY_ERROR = {"error": "Malformed JSON or missing request body"}


class DuplicateFieldError(Exception):
    pass


async def parse_json_object(request: Request, *, duplicate_error_message: str = "Invalid request structure") -> dict[str, Any]:
    raw = await request.body()
    if not raw or not raw.strip():
        raise ApiError(status_code=400, payload=MALFORMED_BODY_ERROR)

    duplicates: set[str] = set()

    def parse_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        parsed: dict[str, Any] = {}
        for key, value in pairs:
            if key in parsed:
                duplicates.add(key)
            parsed[key] = value
        return parsed

    try:
        parsed = json.loads(raw.decode("utf-8"), object_pairs_hook=parse_pairs)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ApiError(status_code=400, payload=MALFORMED_BODY_ERROR) from exc

    if duplicates:
        raise ApiError(status_code=400, payload={"error": duplicate_error_message})

    if not isinstance(parsed, dict):
        raise ApiError(status_code=400, payload=MALFORMED_BODY_ERROR)

    return parsed
