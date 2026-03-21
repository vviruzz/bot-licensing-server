from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from sqlalchemy import inspect, select

from app.api.health import router as health_router
from app.api.routes import admin_router, auth_router, bot_router, license_router
from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal, engine
from app.models.admin_user import AdminUser

logger = logging.getLogger(__name__)

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth_router)
api_v1_router.include_router(bot_router)
api_v1_router.include_router(license_router)
api_v1_router.include_router(admin_router)


@asynccontextmanager
async def lifespan(_: FastAPI):
    bootstrap_admin_user()
    yield


app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)
app.include_router(health_router)
app.include_router(api_v1_router)


def bootstrap_admin_user() -> None:
    if not settings.bootstrap_admin_email or not settings.bootstrap_admin_password:
        logger.info("bootstrap admin env vars not set; skipping admin bootstrap")
        return

    inspector = inspect(engine)
    if not inspector.has_table("admin_users"):
        logger.warning("admin_users table not found; run Alembic migrations before bootstrap admin creation")
        return

    admin_email = settings.bootstrap_admin_email.lower().strip()
    with SessionLocal() as db_session:
        existing_admin = db_session.scalar(select(AdminUser).where(AdminUser.email == admin_email))
        if existing_admin is not None:
            return

        username = admin_email.split("@", 1)[0][:64] or "admin"
        db_session.add(
            AdminUser(
                email=admin_email,
                username=username,
                password_hash=hash_password(settings.bootstrap_admin_password),
                display_name=settings.bootstrap_admin_name,
                is_active=True,
                is_superuser=True,
            )
        )
        db_session.commit()
        logger.info("bootstrap admin user created for %s", admin_email)
