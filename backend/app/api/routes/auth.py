from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_admin_access_token, verify_password
from app.db.session import get_db_session
from app.dependencies.auth import get_current_admin_user
from app.models.admin_user import AdminUser
from app.schemas.auth import AdminLoginRequest, AdminLoginResponse, AdminUserResponse
from app.services.security import enforce_admin_login_rate_limit, get_request_id_from_request, log_admin_auth_denial

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=AdminLoginResponse)
def login(payload: AdminLoginRequest, request: Request, db_session: Session = Depends(get_db_session)) -> AdminLoginResponse:
    enforce_admin_login_rate_limit(request=request, email=payload.email)
    request_id = get_request_id_from_request(request)
    admin_user = db_session.scalar(select(AdminUser).where(AdminUser.email == payload.email))
    if admin_user is None or not verify_password(payload.password, admin_user.password_hash):
        log_admin_auth_denial(
            db_session,
            request=request,
            email=payload.email,
            reason_code="invalid_credentials",
            message="invalid email or password",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_credentials", "message": "invalid email or password", "request_id": request_id},
        )

    if not admin_user.is_active:
        log_admin_auth_denial(
            db_session,
            request=request,
            email=payload.email,
            reason_code="inactive_admin",
            message="authentication failed",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "inactive_admin", "message": "authentication failed", "request_id": request_id},
        )

    access_token = create_admin_access_token(
        subject=str(admin_user.id),
        email=admin_user.email,
        role=admin_user.role,
    )
    return AdminLoginResponse(
        access_token=access_token,
        expires_in=settings.admin_jwt_expire_minutes * 60,
        user=AdminUserResponse.model_validate(admin_user),
    )


@router.get("/me", response_model=AdminUserResponse)
def read_me(current_admin: AdminUser = Depends(get_current_admin_user)) -> AdminUserResponse:
    return AdminUserResponse.model_validate(current_admin)
