"""Custom exception handlers to provide Java-like error shapes.

These handlers convert Pydantic validation errors into the
`{"errors": {...}}` structure and normalize malformed JSON messages.
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Format: {"errors": {"field": "message"}}
    errs = exc.errors()

    # If JSON decode error or similar parse failure, return the Java-shaped message
    for e in errs:
        etype = e.get("type", "")
        msg = e.get("msg", "")
        if "jsondecode" in etype or "JSON decode" in msg or "Expecting value" in msg:
            return JSONResponse(status_code=400, content={"error": "Malformed JSON or missing request body"})

    # If the only error points to the body itself (empty / missing body), treat as malformed
    if len(errs) == 1:
        loc = errs[0].get("loc", [])
        if loc and loc[-1] == "body":
            return JSONResponse(status_code=400, content={"error": "Malformed JSON or missing request body"})

    # Map short/invalid phone number validation to Java-shaped single error
    for e in errs:
        loc = e.get("loc", [])
        msg = e.get("msg", "")
        if loc:
            fld = str(loc[-1]).lower()
        else:
            fld = ""
        if "phone" in fld and "at least" in msg:
            try:
                body = await request.json()
                phone = body.get("phoneNumber") or body.get("phone_number") or ""
                country = body.get("countryCode") or body.get("country_code") or ""
                return JSONResponse(status_code=400, content={"error": f"Invalid phone number: {phone} for country code: {country}"})
            except Exception:
                # fall through to default mapping
                pass
    errors = {}
    for e in errs:
        loc = e.get("loc", [])
        if loc:
            field = loc[-1]
        else:
            field = "body"
        msg = e.get("msg", "")
        # Map pydantic 'field required' to Java wording
        if msg == "field required":
            msg = "must not be empty"

        # Register email format wording
        if e.get("type") == "value_error.email":
            msg = "must be a well-formed email address"

        # Register password short should be returned as top-level error
        if (
            str(request.url.path) == "/api/users/register"
            and str(field) == "password"
            and msg == "Password must be at least 8 characters long"
        ):
            return JSONResponse(status_code=400, content={"error": msg})

        # Extra field default mapping
        if e.get("type") == "value_error.extra":
            return JSONResponse(status_code=400, content={"error": f"Extra field detected: {field}"})
        errors[field] = msg
    return JSONResponse(status_code=400, content={"errors": errors})


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    # Preserve error detail structure when handler raises with dict or string
    detail = exc.detail
    if isinstance(detail, dict):
        return JSONResponse(status_code=exc.status_code, content=detail)
    return JSONResponse(status_code=exc.status_code, content={"error": detail})
