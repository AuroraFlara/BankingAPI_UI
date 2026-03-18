"""Application entrypoint and FastAPI app configuration.

This module wires routes and exception handlers and attempts to
create database tables on startup (when the database is available).
"""
import time # <--- Add this import
from fastapi import FastAPI, Request # <--- Add Request here
from .db import engine
from .models import Base
from .routes import router
from .exceptions import validation_exception_handler, http_exception_handler
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

app = FastAPI(title="BankingAPI Async Migration")

# --- ADD TIMING MIDDLEWARE HERE ---
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = (time.perf_counter() - start_time) * 1000
    response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
    return response
# ----------------------------------

# register routes
app.include_router(router)

# register exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)

@app.on_event("startup")
async def startup():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception:
        pass

@app.get("/")
async def root():
    return {"msg": "Banking API (Async) — migrated from Java Spring Boot"}