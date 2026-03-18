"""
FastAPI application entrypoint.

Global exception handlers ensure:
- Pydantic extra-field validation → 400 {"error": "Extra field detected: <name>"}
- Pydantic field validation errors → 400 {"errors": {"field": "message"}}
- JSON decode errors → 400 {"error": "Malformed JSON or missing request body"}
- HTTPException detail passthrough
"""
import time
import json
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.routes import user_router, dashboard_router, pin_router, banking_router

app = FastAPI(title="Banking Portal API")

# Register all routers
app.include_router(user_router)
app.include_router(dashboard_router)
app.include_router(pin_router)
app.include_router(banking_router)


# ---------------------------------------------------------------------------
# Custom "missing field" messages matching Java behavior per endpoint
# ---------------------------------------------------------------------------
_MISSING_MESSAGES: dict[str, str] = {
    # Register
    "name": "must not be empty",
    "email": "must not be empty",
    "password": "must not be empty",
    "phoneNumber": "must not be empty",
    "address": "must not be empty",
    "countryCode": "must not be empty",
    # Login
    "identifier": "Identifier must not be empty",
    # PIN create
    "pin": "PIN cannot be empty",
    # PIN update
    "oldPin": "Old PIN cannot be empty",
    "newPin": "New PIN cannot be empty",
    # Banking
    "amount": "Amount cannot be empty",
    "targetAccountNumber": "Target account number cannot be empty",
}

# Per-field password missing messages differ by endpoint path
_PASSWORD_MISSING_BY_PATH: dict[str, str] = {
    "/api/users/login": "Password must not be empty",
    "/api/account/pin/create": "Password cannot be empty",
    "/api/account/pin/update": "Password cannot be empty",
}


def _missing_msg(field: str, path: str) -> str:
    if field == "password":
        for route, msg in _PASSWORD_MISSING_BY_PATH.items():
            if path.startswith(route):
                return msg
        return "must not be empty"
    return _MISSING_MESSAGES.get(field, "must not be empty")


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    
    # Calculate in milliseconds to match your Manual Migration and Java baseline
    process_time = (time.perf_counter() - start_time) * 1000
    response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
    
    return response

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    detail = exc.detail
    if isinstance(detail, dict):
        return JSONResponse(status_code=exc.status_code, content=detail)
    return JSONResponse(status_code=exc.status_code, content={"error": str(detail)})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handles Pydantic v2 validation errors from request bodies/params.
    - extra='forbid' violations → 400 {"error": "Extra field detected: <name>"}
    - Normal validation failures → 400 {"errors": {"field": "message"}}
    """
    errors = exc.errors()
    path = request.url.path

    # Check for extra field (forbid) errors first
    for err in errors:
        if err.get("type") == "extra_forbidden":
            field_name = err["loc"][-1] if err.get("loc") else "unknown"
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": f"Extra field detected: {field_name}"},
            )

    # Normal validation errors → {"errors": {"field": "message"}}
    field_errors: dict = {}
    for err in errors:
        loc = err.get("loc", [])
        # Skip "body" prefix from loc tuple
        field_parts = [str(l) for l in loc if l != "body"]
        field = ".".join(field_parts) if field_parts else "unknown"

        err_type = err.get("type", "")
        if err_type == "missing":
            msg = _missing_msg(field, path)
        else:
            msg = err.get("msg", "invalid value")
            # Strip "Value error, " prefix added by Pydantic v2 for @field_validator
            msg = msg.removeprefix("Value error, ")

        field_errors[field] = msg

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"errors": field_errors},
    )


@app.exception_handler(json.JSONDecodeError)
async def json_decode_error_handler(request: Request, exc: json.JSONDecodeError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "Malformed JSON or missing request body"},
    )


@app.middleware("http")
async def catch_malformed_json(request: Request, call_next):
    """
    Catch JSON decode errors that occur during request body parsing
    before they reach the validation layer.
    Detects duplicate keys (e.g. duplicate "password") and returns
    {"error": "Invalid request structure"} for login endpoint.
    """
    if request.method in ("POST", "PUT", "PATCH"):
        body = await request.body()
        content_type = request.headers.get("content-type", "")

        # Empty body (with or without content-type) → malformed
        if not body:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Malformed JSON or missing request body"},
            )

        if "application/json" in content_type:
            try:
                # Detect duplicate keys using a custom object_pairs_hook
                seen_keys: list = []

                def check_duplicate(pairs):
                    keys = [k for k, _ in pairs]
                    for k in keys:
                        if keys.count(k) > 1:
                            seen_keys.append(k)
                    return dict(pairs)

                json.loads(body, object_pairs_hook=check_duplicate)

                if seen_keys:
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content={"error": "Invalid request structure"},
                    )
            except json.JSONDecodeError:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"error": "Malformed JSON or missing request body"},
                )
    return await call_next(request)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = (time.perf_counter() - start_time) * 1000
    response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
    return response