import time
import json

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.routes.dashboard_routes import router as dashboard_router
from app.api.routes.pin_routes import router as pin_router
from app.api.routes.transaction_routes import router as transaction_router
from app.api.routes.user_routes import router as user_router
from app.core.config import settings


app = FastAPI(title=settings.app_name)


FIELD_LABELS = {
    "name": "name",
    "email": "email",
    "password": "password",
    "phone_number": "phoneNumber",
    "phoneNumber": "phoneNumber",
    "address": "address",
    "country_code": "countryCode",
    "countryCode": "countryCode",
    "identifier": "identifier",
    "pin": "pin",
    "old_pin": "oldPin",
    "oldPin": "oldPin",
    "new_pin": "newPin",
    "newPin": "newPin",
    "amount": "amount",
    "target_account_number": "targetAccountNumber",
    "targetAccountNumber": "targetAccountNumber",
}


MISSING_FIELD_MESSAGES = {
    "/api/users/register": {
        "phoneNumber": "must not be empty",
        "password": "must not be empty",
        "address": "must not be empty",
        "countryCode": "must not be empty",
        "email": "must not be empty",
        "name": "must not be empty",
    },
    "/api/users/login": {
        "identifier": "Identifier must not be empty",
        "password": "Password must not be empty",
    },
    "/api/account/pin/create": {
        "pin": "PIN cannot be empty",
        "password": "Password cannot be empty",
    },
    "/api/account/pin/update": {
        "oldPin": "Old PIN cannot be empty",
        "newPin": "New PIN cannot be empty",
        "password": "Password cannot be empty",
    },
    "/api/account/deposit": {
        "pin": "PIN cannot be empty",
        "amount": "Amount cannot be empty",
    },
    "/api/account/withdraw": {
        "pin": "PIN cannot be empty",
        "amount": "Amount cannot be empty",
    },
    "/api/account/fund-transfer": {
        "targetAccountNumber": "Target account number cannot be empty",
        "pin": "PIN cannot be empty",
        "amount": "Amount cannot be empty",
    },
    "/api/account/transfer": {
        "targetAccountNumber": "Target account number cannot be empty",
        "pin": "PIN cannot be empty",
        "amount": "Amount cannot be empty",
    },
}

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    # Start high-precision timer
    start_time = time.perf_counter()
    
    # Process the request through routers and exception handlers
    response = await call_next(request)
    
    # Calculate duration in milliseconds to match your research standards
    process_time_ms = (time.perf_counter() - start_time) * 1000
    
    # Inject the standardized header
    response.headers["X-Process-Time"] = f"{process_time_ms:.2f}ms"
    
    return response

@app.middleware("http")
async def detect_login_duplicate_fields(request: Request, call_next):
    request.state.login_invalid_structure = False
    if request.url.path == "/api/users/login" and request.method == "POST":
        try:
            body = await request.body()
            if body:
                duplicate_found = False

                def _detect_duplicates(pairs):
                    nonlocal duplicate_found
                    seen = set()
                    parsed = {}
                    for k, v in pairs:
                        if k in seen:
                            duplicate_found = True
                        seen.add(k)
                        parsed[k] = v
                    return parsed

                json.loads(body.decode("utf-8"), object_pairs_hook=_detect_duplicates)
                request.state.login_invalid_structure = duplicate_found
        except Exception:
            request.state.login_invalid_structure = False
    return await call_next(request)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    _ = request
    if isinstance(exc.detail, dict):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"error": str(exc.detail)})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    if request.url.path == "/api/users/login" and getattr(request.state, "login_invalid_structure", False):
        return JSONResponse(status_code=400, content={"error": "Invalid request structure"})

    errors = exc.errors()

    for error in errors:
        if error.get("type") == "json_invalid":
            return JSONResponse(
                status_code=400,
                content={"error": "Malformed JSON or missing request body"},
            )
        if error.get("type") == "missing" and error.get("loc") == ("body",):
            return JSONResponse(
                status_code=400,
                content={"error": "Malformed JSON or missing request body"},
            )

    first_error = errors[0] if errors else {}
    msg = first_error.get("msg", "")
    path = request.url.path
    path_mapping = MISSING_FIELD_MESSAGES.get(path, {})

    missing_fields = []
    for error in errors:
        if error.get("type") == "missing" and len(error.get("loc", ())) >= 2 and error.get("loc", ())[0] == "body":
            raw_field = str(error.get("loc", ())[-1])
            normalized_field = FIELD_LABELS.get(raw_field, raw_field)
            missing_fields.append(normalized_field)

    # Java parity: for empty register payloads, email may surface as format-invalid
    # while all other fields are missing; normalize email to missing in that case.
    if path == "/api/users/register":
        register_missing_order = ["phoneNumber", "password", "address", "countryCode", "email", "name"]
        missing_set = set(missing_fields)
        has_email_format_error = any(
            len(error.get("loc", ())) >= 2
            and error.get("loc", ())[0] == "body"
            and FIELD_LABELS.get(str(error.get("loc", ())[-1]), str(error.get("loc", ())[-1])) == "email"
            and isinstance(error.get("msg"), str)
            and "email" in error.get("msg", "").lower()
            for error in errors
        )
        if missing_set == {"phoneNumber", "password", "address", "countryCode", "name"} and has_email_format_error:
            return JSONResponse(
                status_code=400,
                content={"errors": {field: "must not be empty" for field in register_missing_order}},
            )

    if path == "/api/account/pin/create" and len(missing_fields) == 1:
        field = missing_fields[0]
        if field == "password":
            return JSONResponse(status_code=401, content={"error": "Password cannot be empty"})
        if field == "pin":
            return JSONResponse(status_code=400, content={"error": "PIN cannot be empty"})

    if missing_fields:
        ordered_fields = list(path_mapping.keys()) if path_mapping else missing_fields
        error_map = {}
        for field in ordered_fields:
            if field in missing_fields:
                error_map[field] = path_mapping.get(field, "must not be empty")
        for field in missing_fields:
            if field not in error_map:
                error_map[field] = path_mapping.get(field, "must not be empty")
        return JSONResponse(status_code=400, content={"errors": error_map})

    if isinstance(msg, str) and "Extra field detected:" in msg:
        extra_name = msg.split("Extra field detected:", 1)[1].strip()
        if "]" in extra_name:
            extra_name = extra_name.split("]", 1)[0].strip()
        return JSONResponse(status_code=400, content={"error": f"Extra field detected: {extra_name}"})

    loc = first_error.get("loc", ())
    field_name = "field"
    if len(loc) >= 2 and loc[0] == "body":
        field_name = FIELD_LABELS.get(str(loc[-1]), str(loc[-1]))

    normalized_message = "must not be empty"
    if path == "/api/users/register" and field_name == "email" and ("valid email" in msg.lower() or "email" in msg.lower()):
        normalized_message = "must be a well-formed email address"
    elif "field required" in msg.lower() or "missing" in msg.lower():
        normalized_message = "must not be empty"
    elif "at least" in msg.lower() or "too short" in msg.lower():
        normalized_message = "must not be empty"
    elif msg:
        normalized_message = msg

    return JSONResponse(status_code=400, content={"errors": {field_name: normalized_message}})


@app.get("/health")
async def health_check():
    return {"msg": "ok"}


app.include_router(user_router)
app.include_router(dashboard_router)
app.include_router(pin_router)
app.include_router(transaction_router)
