from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_admin_access_token, verify_password
from app.db.session import get_db_session
from app.dependencies.auth import get_current_admin_user
from app.models.admin_user import AdminUser
from app.schemas.auth import AdminLoginRequest, AdminLoginResponse, AdminUserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=AdminLoginResponse)
def login(payload: AdminLoginRequest, db_session: Session = Depends(get_db_session)) -> AdminLoginResponse:
    admin_user = db_session.scalar(select(AdminUser).where(AdminUser.email == payload.email.lower().strip()))
    if admin_user is None or not verify_password(payload.password, admin_user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid email or password")

    if not admin_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin user is inactive")

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
