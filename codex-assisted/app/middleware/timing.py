import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class ProcessTimeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Start high-precision timer
        start = time.perf_counter()
        
        response = await call_next(request)
        
        # Calculate duration in milliseconds (sec * 1000)
        elapsed_ms = (time.perf_counter() - start) * 1000
        
        # Format to 2 decimal places with "ms" suffix for standardization
        response.headers["X-Process-Time"] = f"{elapsed_ms:.2f}ms"
        
        return response