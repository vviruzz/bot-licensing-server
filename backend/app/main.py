from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings

app = FastAPI(
    title="bot-licensing-server",
    version=settings.api_protocol_version,
    description="Initial contract-first MVP skeleton for licensing/admin APIs.",
)
app.include_router(api_router, prefix="/api/v1")
