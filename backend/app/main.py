from fastapi import FastAPI

from app.api import admin_router, auth_router, bot_router, health_router
from app.core.config import settings

app = FastAPI(title=settings.app_name, version=settings.app_version)
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(bot_router)
app.include_router(admin_router)
