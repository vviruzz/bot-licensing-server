from __future__ import annotations

from pydantic import BaseModel, ConfigDict, computed_field


def admin_role_label(*, is_superuser: bool) -> str:
    return "owner" if is_superuser else "admin"


class AdminLoginRequest(BaseModel):
    email: str
    password: str


class AdminUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    username: str
    display_name: str | None = None
    is_active: bool
    is_superuser: bool

    @computed_field
    @property
    def role(self) -> str:
        return admin_role_label(is_superuser=self.is_superuser)


class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: AdminUserResponse
