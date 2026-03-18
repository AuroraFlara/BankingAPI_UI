"""
Application entry point.

Responsibilities:
  - Register all routers
  - Mount TimingMiddleware (X-Process-Time header parity with Java OncePerRequestFilter)
  - Error shape routing:
      {"error": "..."}        — singular string for duplicate/invalid/extra-field/malformed
      {"errors": {"f": "..."}} — object for missing/empty fields (validation)
"""
import json
import time
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from app.routes import banking_routes, dashboard_routes, pin_routes, user_routes

# ---------------------------------------------------------------------------
# Timing Middleware  (Java OncePerRequestFilter parity)
# ---------------------------------------------------------------------------

class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Process-Time"] = f"{elapsed_ms:.2f}ms"
        return response


class DuplicateKeyMiddleware(BaseHTTPMiddleware):
    """
    Detect duplicate keys in JSON request bodies before Pydantic sees them.
    Python's json.loads silently last-value-wins on duplicate keys, so
    extra="forbid" never fires for e.g. {"password":"x","password":"x"}.
    Parsing with object_pairs_hook lets us catch this case and return the
    exact GT error shape.
    """
    async def dispatch(self, request: Request, call_next):
        if request.method in ("POST", "PUT", "PATCH"):
            ct = request.headers.get("content-type", "")
            if "application/json" in ct:
                body = await request.body()  # cached; downstream can still read it
                if body:
                    try:
                        keys_seen: list[str] = []

                        def _check(pairs):
                            for k, _ in pairs:
                                keys_seen.append(k)
                            return dict(pairs)

                        json.loads(body, object_pairs_hook=_check)
                        if len(keys_seen) != len(set(keys_seen)):
                            return ORJSONResponse(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                content={"error": "Invalid request structure"},
                            )
                    except json.JSONDecodeError:
                        pass  # malformed JSON handled downstream by FastAPI
        return await call_next(request)


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def create_app() -> FastAPI:
    app = FastAPI(
        title="BankingAPI — Python (GenAI-Assisted)",
        version="1.0.0",
        default_response_class=ORJSONResponse,
    )

    app.add_middleware(TimingMiddleware)
    app.add_middleware(DuplicateKeyMiddleware)  # outermost: runs first on request

    # ------------------------------------------------------------------
    # Validation error handler
    #
    # Ground-truth error shape rules:
    #   {"errors": {"field": "msg"}}  — missing / empty fields
    #   {"error": "..."}              — extra fields, malformed JSON,
    #                                   password-too-short, invalid email,
    #                                   invalid phone
    #
    # Our model validators encode intent via a tagged dict:
    #   {"__type": "field_errors", "errors": {...}}   -> {"errors": {...}}
    #   {"__type": "single_error", "error": "..."}    -> {"error": "..."}
    # ------------------------------------------------------------------
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> ORJSONResponse:
        field_errors: dict[str, str] = {}
        single_error: str | None = None

        for error in exc.errors():
            err_type = error.get("type", "")
            raw_ctx = error.get("ctx", {})

            # ---- Malformed / missing body -----------------------------------
            if err_type == "json_invalid" or err_type == "missing":
                # json_invalid = truly malformed JSON
                # missing = body absent entirely (FastAPI raises missing for body param)
                return ORJSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"error": "Malformed JSON or missing request body"},
                )

            # ---- Extra (unknown) fields -------------------------------------
            if err_type == "extra_forbidden":
                loc = error.get("loc", ())
                field_name = loc[-1] if loc else "unknown"
                return ORJSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"error": f"Extra field detected: {field_name}"},
                )

            # ---- model_validator ValueError with tagged payload ------------
            if err_type == "value_error":
                raw = raw_ctx.get("error") if raw_ctx else None
                # raw is the ValueError instance; args[0] is our tagged dict
                if isinstance(raw, ValueError) and isinstance(raw.args[0], dict):
                    tagged = raw.args[0]
                    if tagged.get("__type") == "field_errors":
                        field_errors.update(tagged.get("errors", {}))
                        continue
                    if tagged.get("__type") == "single_error":
                        single_error = tagged.get("error", "Validation error")
                        continue
                # Fallback plain ValueError
                loc = error.get("loc", ())
                field = str(loc[-1]) if len(loc) > 1 else "body"
                field_errors[field] = error.get("msg", "invalid").replace("Value error, ", "")
                continue

            # ---- Type / format errors (e.g. int expected) ------------------
            loc = error.get("loc", ())
            field = str(loc[-1]) if len(loc) > 1 else "body"
            field_errors[field] = error.get("msg", "invalid value")

        if single_error:
            return ORJSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": single_error},
            )
        if field_errors:
            return ORJSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"errors": field_errors},
            )
        return ORJSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Validation error"},
        )

    # ------------------------------------------------------------------
    # HTTP exception handler — pass-through detail as {"error": "..."}
    # ------------------------------------------------------------------
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> ORJSONResponse:
        return ORJSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail},
        )

    # Routers
    app.include_router(user_routes.router)
    app.include_router(dashboard_routes.router)
    app.include_router(pin_routes.router)
    app.include_router(banking_routes.router)

    return app


app = create_app()
