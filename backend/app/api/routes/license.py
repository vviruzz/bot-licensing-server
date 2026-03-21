from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.dependencies.auth import require_bot_token
from app.schemas.licensing import LicenseCheckRequest, LicenseCheckResponse
from app.services import check_license as check_license_flow

router = APIRouter(prefix="/license", tags=["license"])

@router.post("/check", response_model=LicenseCheckResponse)
def check_license(payload: LicenseCheckRequest, _: str = Depends(require_bot_token), db_session: Session = Depends(get_db_session)) -> LicenseCheckResponse:
    return LicenseCheckResponse.model_validate(check_license_flow(db_session, payload))
