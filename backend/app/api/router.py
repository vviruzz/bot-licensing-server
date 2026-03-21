from fastapi import APIRouter

from app.api.routes import admin, bot, health

api_router = APIRouter()
api_router.include_router(health.router, tags=["system"])
api_router.include_router(bot.router, prefix="/bot", tags=["bot"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
