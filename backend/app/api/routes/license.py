from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies.auth import require_bot_token
from app.schemas.auth import LicenseCheckRequest, LicenseCheckResponse

router = APIRouter(prefix="/license", tags=["license"])


@router.post("/check", response_model=LicenseCheckResponse)
def check_license(
    payload: LicenseCheckRequest,
    _: str = Depends(require_bot_token),
) -> LicenseCheckResponse:
    return LicenseCheckResponse(detail=f"bot auth accepted for {payload.bot_instance_id}")
