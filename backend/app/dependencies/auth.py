from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_admin_access_token
from app.db.session import get_db_session
from app.models.admin_user import AdminUser

admin_bearer_scheme = HTTPBearer(auto_error=False)
bot_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_admin_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(admin_bearer_scheme),
    db_session: Session = Depends(get_db_session),
) -> AdminUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized("admin bearer token required")

    payload = decode_admin_access_token(credentials.credentials)
    user_id = payload.get("sub")
    if user_id is None:
        raise _unauthorized("invalid admin token subject")

    admin_user = db_session.get(AdminUser, int(user_id))
    if admin_user is None or not admin_user.is_active:
        raise _unauthorized("admin user not available")

    return admin_user


def require_bot_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bot_bearer_scheme),
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized("bot bearer token required")

    if credentials.credentials != settings.bot_api_token:
        raise _unauthorized("invalid bot bearer token")

    return credentials.credentials


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )
