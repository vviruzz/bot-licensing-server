from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies.auth import require_bot_token
from app.schemas.bot_api import LicenseCheckRequest, LicenseCheckResponse
from app.schemas.common import AuthorizationDecision, BotStatusEnum, LicenseStatusEnum, ModeEnum

router = APIRouter(prefix="/license", tags=["license"])


@router.post("/check", response_model=LicenseCheckResponse)
def check_license(
    payload: LicenseCheckRequest,
    _: str = Depends(require_bot_token),
) -> LicenseCheckResponse:
    # TODO: implement license validation, protocol-range checks, and authorization windows.
    return LicenseCheckResponse(
        protocol_version=payload.protocol_version,
        license_status=LicenseStatusEnum.active,
        effective_mode=ModeEnum.monitor,
        bot_status=BotStatusEnum.online,
        authorization=AuthorizationDecision(allowed=True, message=f"stub license accepted for {payload.bot_instance_id}"),
    )
