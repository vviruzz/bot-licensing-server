from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.dependencies.auth import require_bot_token
from app.schemas.licensing import LicenseCheckRequest, LicenseCheckResponse
from app.services import check_license as check_license_flow
from app.services.security import BotRequestMeta, enforce_bot_request_security

router = APIRouter(prefix="/license", tags=["license"])


@router.post("/check", response_model=LicenseCheckResponse)
def check_license(payload: LicenseCheckRequest, request: Request, _: str = Depends(require_bot_token), db_session: Session = Depends(get_db_session)) -> LicenseCheckResponse:
    enforce_bot_request_security(
        request=request,
        db=db_session,
        meta=BotRequestMeta(
            endpoint_key="license_check",
            license_key=payload.license_key,
            bot_instance_id=payload.bot_instance_id,
            product_code=payload.product_code,
            bot_family=payload.bot_family,
            strategy_code=payload.strategy_code,
            protocol_version=payload.protocol_version,
            request_timestamp=payload.request_timestamp,
        ),
    )
    return LicenseCheckResponse.model_validate(check_license_flow(db_session, payload))
