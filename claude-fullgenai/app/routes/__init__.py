from app.routes.user_routes import router as user_router
from app.routes.dashboard_routes import router as dashboard_router
from app.routes.pin_routes import router as pin_router
from app.routes.banking_routes import router as banking_router

__all__ = ["user_router", "dashboard_router", "pin_router", "banking_router"]
