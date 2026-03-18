from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse

from app.api.routes import account, dashboard, users
from app.core.api_errors import ApiError
from app.middleware.timing import ProcessTimeMiddleware


app = FastAPI(title="Banking API", default_response_class=ORJSONResponse)
app.add_middleware(ProcessTimeMiddleware)

app.include_router(users.router)
app.include_router(dashboard.router)
app.include_router(account.router)


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError) -> ORJSONResponse:
    return ORJSONResponse(status_code=exc.status_code, content=exc.payload)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> ORJSONResponse:
    if isinstance(exc.detail, dict):
        payload = exc.detail
    elif isinstance(exc.detail, str):
        payload = {"error": exc.detail}
    else:
        payload = {"error": "Request failed"}
    return ORJSONResponse(status_code=exc.status_code, content=payload)


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(request: Request, exc: RequestValidationError) -> ORJSONResponse:
    return ORJSONResponse(status_code=400, content={"error": "Invalid request structure"})
