from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.request_context import get_request_id
from app.core.security import decode_admin_access_token
from app.db.session import get_db_session
from app.models.admin_user import AdminUser

admin_bearer_scheme = HTTPBearer(auto_error=False)
bot_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_admin_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(admin_bearer_scheme),
    db_session: Session = Depends(get_db_session),
) -> AdminUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized("authentication required")

    payload = decode_admin_access_token(credentials.credentials)
    user_id = payload.get("sub")
    if user_id is None:
        raise _unauthorized("authentication failed")

    try:
        admin_user = db_session.get(AdminUser, int(user_id))
    except (TypeError, ValueError) as exc:
        raise _unauthorized("authentication failed") from exc
    if admin_user is None or not admin_user.is_active:
        raise _unauthorized("authentication failed")

    request.state.admin_user_id = admin_user.id
    return admin_user


def require_bot_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bot_bearer_scheme),
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized("authentication required")

    token = credentials.credentials.strip()
    if not token or token != settings.bot_api_token:
        raise _unauthorized("authentication failed")

    request.state.bot_authenticated = True
    return token


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"code": "unauthorized", "message": detail, "request_id": get_request_id()},
        headers={"WWW-Authenticate": "Bearer"},
    )
