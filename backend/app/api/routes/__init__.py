from app.api.routes.admin import router as admin_router
from app.api.routes.auth import router as auth_router
from app.api.routes.bot import router as bot_router
from app.api.routes.license import router as license_router

__all__ = ["admin_router", "auth_router", "bot_router", "license_router"]
