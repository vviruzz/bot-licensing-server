from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.models.admin_user import AdminRole


class AdminLoginRequest(BaseModel):
    email: str
    password: str


class AdminUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    role: AdminRole
    is_active: bool


class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: AdminUserResponse


class LicenseCheckRequest(BaseModel):
    license_key: str
    bot_instance_id: str
    product_code: str
    bot_family: str
    strategy_code: str
    protocol_version: str


class LicenseCheckResponse(BaseModel):
    ok: bool = True
    license_status: str = "active"
    effective_mode: str = "monitor"
    detail: str = "bot token accepted"
