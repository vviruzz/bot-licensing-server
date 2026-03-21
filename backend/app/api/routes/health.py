from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


@router.get("/health")
def get_health() -> dict[str, object]:
    return {
        "ok": True,
        "service": "bot-licensing-server",
        "protocol_version": settings.api_protocol_version,
    }
