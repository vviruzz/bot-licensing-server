from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone

from fastapi import Depends, Header, HTTPException, status

from app.core.config import settings


class AuthPrincipal(dict):
    pass


class BotPrincipal(AuthPrincipal):
    pass


class AdminPrincipal(AuthPrincipal):
    pass


class InvalidAdminTokenError(ValueError):
    pass


ADMIN_TOKEN_TYPE = "admin_access"


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


def _encode_token(payload: dict[str, str]) -> str:
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    body = base64.urlsafe_b64encode(raw).decode("utf-8")
    signature = hmac.new(settings.admin_token_secret.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{body}.{signature}"


def _decode_token(token: str) -> dict[str, str]:
    try:
        body, signature = token.split(".", 1)
    except ValueError as exc:
        raise InvalidAdminTokenError("malformed token") from exc

    expected_signature = hmac.new(
        settings.admin_token_secret.encode("utf-8"),
        body.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(signature, expected_signature):
        raise InvalidAdminTokenError("invalid signature")

    try:
        payload = json.loads(base64.urlsafe_b64decode(body.encode("utf-8")).decode("utf-8"))
    except (ValueError, json.JSONDecodeError) as exc:
        raise InvalidAdminTokenError("invalid payload") from exc

    if payload.get("typ") != ADMIN_TOKEN_TYPE:
        raise InvalidAdminTokenError("unexpected token type")

    expires_at = payload.get("exp")
    if not isinstance(expires_at, str):
        raise InvalidAdminTokenError("missing expiration")
    if datetime.fromisoformat(expires_at) <= datetime.now(timezone.utc):
        raise InvalidAdminTokenError("token expired")

    return payload


def issue_admin_access_token(username: str, role: str = "admin") -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.admin_token_ttl_minutes)
    payload = {
        "sub": username,
        "role": role,
        "typ": ADMIN_TOKEN_TYPE,
        "exp": expires_at.isoformat(),
    }
    return _encode_token(payload)


def require_bot_auth(authorization: str | None = Header(default=None)) -> BotPrincipal:
    expected = f"Bearer {settings.bot_api_token}"
    if authorization != expected:
        raise _unauthorized("invalid bot credentials")
    return BotPrincipal(role="bot", auth_scheme="bearer")


def require_admin_auth(authorization: str | None = Header(default=None)) -> AdminPrincipal:
    if not authorization or not authorization.startswith("Bearer "):
        raise _unauthorized("invalid admin credentials")

    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = _decode_token(token)
    except InvalidAdminTokenError as exc:
        raise _unauthorized(f"invalid admin credentials: {exc}") from exc

    return AdminPrincipal(
        username=payload["sub"],
        role=payload.get("role", "admin"),
        auth_scheme="bearer",
        token_type=payload["typ"],
    )


def get_current_admin(principal: AdminPrincipal = Depends(require_admin_auth)) -> AdminPrincipal:
    return principal
