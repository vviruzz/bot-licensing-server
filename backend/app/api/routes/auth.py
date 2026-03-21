from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.config import settings
from app.dependencies.auth import get_current_admin, issue_admin_access_token
from app.schemas.admin import AdminLoginRequest, AdminLoginResponse, AdminMeResponse

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=AdminLoginResponse)
def login(payload: AdminLoginRequest) -> AdminLoginResponse:
    # TODO: replace bootstrap credential check with persisted admin authentication.
    admin = {"username": settings.admin_username, "role": "admin", "display_name": "Bootstrap Admin"}
    if payload.username != settings.admin_username or payload.password != settings.admin_password:
        return AdminLoginResponse(
            ok=False,
            access_token="",
            admin=admin,
            errors=[{"code": "invalid_credentials", "message": "Invalid username or password."}],
        )

    return AdminLoginResponse(
        access_token=issue_admin_access_token(username=settings.admin_username, role="admin"),
        admin=admin,
    )


@router.get("/me", response_model=AdminMeResponse)
def me(admin: dict = Depends(get_current_admin)) -> AdminMeResponse:
    return AdminMeResponse(
        admin={
            "username": admin.get("username", settings.admin_username),
            "role": admin.get("role", "admin"),
            "display_name": "Bootstrap Admin",
        }
    )
