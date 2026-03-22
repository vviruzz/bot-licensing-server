from __future__ import annotations

import logging
import re
import threading
from collections import deque
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.request_context import get_request_id, set_request_id
from app.services.audit import write_audit_log

logger = logging.getLogger("app.security")
PROTOCOL_VERSION_PATTERN = re.compile(r"^\d+(?:\.\d+){0,2}$")


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._events: dict[str, deque[datetime]] = {}
        self._lock = threading.Lock()

    def check(self, *, bucket: str, limit: int, window_seconds: int, now: datetime | None = None) -> tuple[bool, int]:
        current_time = now or datetime.now(UTC)
        window_start = current_time - timedelta(seconds=window_seconds)
        with self._lock:
            entries = self._events.setdefault(bucket, deque())
            while entries and entries[0] < window_start:
                entries.popleft()
            if len(entries) >= limit:
                retry_after = max(1, int((entries[0] + timedelta(seconds=window_seconds) - current_time).total_seconds()))
                return False, retry_after
            entries.append(current_time)
            return True, 0


admin_login_rate_limiter = InMemoryRateLimiter()
bot_rate_limiter = InMemoryRateLimiter()


@dataclass(slots=True)
class BotRequestMeta:
    endpoint_key: str
    license_key: str | None
    bot_instance_id: str | None
    product_code: str | None
    bot_family: str | None
    strategy_code: str | None
    protocol_version: str | int | None
    request_timestamp: datetime | None


def get_request_id_from_request(request: Request) -> str:
    request_id = getattr(request.state, "request_id", None)
    if request_id:
        set_request_id(request_id)
        return request_id
    generated = get_request_id()
    request.state.request_id = generated
    set_request_id(generated)
    return generated


def build_error_detail(*, code: str, message: str, request_id: str | None = None) -> dict[str, str]:
    return {"code": code, "message": message, "request_id": request_id or get_request_id()}


def raise_security_error(*, status_code: int, code: str, message: str, request_id: str | None = None, headers: dict[str, str] | None = None) -> None:
    raise HTTPException(status_code=status_code, detail=build_error_detail(code=code, message=message, request_id=request_id), headers=headers)


def normalize_protocol_version(value: str | int) -> str:
    if isinstance(value, int):
        if value < 0:
            raise ValueError("protocol_version must be a positive integer")
        return str(value)
    normalized = str(value).strip()
    if not normalized:
        raise ValueError("protocol_version is required")
    if not PROTOCOL_VERSION_PATTERN.fullmatch(normalized):
        raise ValueError("protocol_version must contain only dot-separated numeric segments")
    return normalized


def validate_protocol_version(value: str | int) -> str:
    return normalize_protocol_version(value)


def validate_request_timestamp(timestamp: datetime | None) -> datetime | None:
    if timestamp is None:
        return None
    value = timestamp.replace(tzinfo=UTC) if timestamp.tzinfo is None else timestamp.astimezone(UTC)
    now = datetime.now(UTC)
    max_age = timedelta(seconds=settings.bot_request_max_age_seconds)
    future_skew = timedelta(seconds=settings.bot_request_max_future_skew_seconds)
    if value < now - max_age:
        raise ValueError("request timestamp is too old")
    if value > now + future_skew:
        raise ValueError("request timestamp is too far in the future")
    return value


def enforce_admin_login_rate_limit(*, request: Request, email: str | None) -> None:
    request_id = get_request_id_from_request(request)
    client_host = request.client.host if request.client else "unknown"
    bucket = f"admin-login:{client_host}:{(email or '').strip().lower()}"
    allowed, retry_after = admin_login_rate_limiter.check(
        bucket=bucket,
        limit=settings.admin_login_rate_limit,
        window_seconds=settings.admin_login_rate_window_seconds,
    )
    if allowed:
        return
    logger.warning("admin login rate limit exceeded request_id=%s ip=%s email=%s", request_id, client_host, email)
    raise_security_error(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        code="rate_limited",
        message="too many authentication attempts",
        request_id=request_id,
        headers={"Retry-After": str(retry_after)},
    )


def enforce_bot_request_security(*, request: Request, db: Session, meta: BotRequestMeta) -> str:
    request_id = get_request_id_from_request(request)
    client_host = request.client.host if request.client else "unknown"
    bucket = f"bot:{meta.endpoint_key}:{client_host}:{meta.bot_instance_id or meta.license_key or 'unknown'}"
    allowed, retry_after = bot_rate_limiter.check(
        bucket=bucket,
        limit=settings.bot_endpoint_rate_limit,
        window_seconds=settings.bot_endpoint_rate_window_seconds,
    )
    if not allowed:
        _log_bot_denial(
            db,
            meta=meta,
            action_type=f"{meta.endpoint_key}_denied",
            reason_code="rate_limited",
            message="bot request rate limit exceeded",
            request_id=request_id,
            client_host=client_host,
        )
        raise_security_error(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            code="rate_limited",
            message="bot request rate limit exceeded",
            request_id=request_id,
            headers={"Retry-After": str(retry_after)},
        )

    try:
        validate_protocol_version(meta.protocol_version if meta.protocol_version is not None else "")
    except ValueError as exc:
        _log_bot_denial(
            db,
            meta=meta,
            action_type=f"{meta.endpoint_key}_denied",
            reason_code="invalid_protocol_version",
            message=str(exc),
            request_id=request_id,
            client_host=client_host,
        )
        raise_security_error(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="invalid_protocol_version",
            message=str(exc),
            request_id=request_id,
        )

    try:
        validate_request_timestamp(meta.request_timestamp)
    except ValueError as exc:
        _log_bot_denial(
            db,
            meta=meta,
            action_type=f"{meta.endpoint_key}_denied",
            reason_code="invalid_request_timestamp",
            message=str(exc),
            request_id=request_id,
            client_host=client_host,
        )
        raise_security_error(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="invalid_request_timestamp",
            message=str(exc),
            request_id=request_id,
        )

    logger.info(
        "bot request accepted request_id=%s endpoint=%s bot_instance_id=%s license_key=%s",
        request_id,
        meta.endpoint_key,
        meta.bot_instance_id,
        meta.license_key,
    )
    return request_id


def _log_bot_denial(
    db: Session,
    *,
    meta: BotRequestMeta,
    action_type: str,
    reason_code: str,
    message: str,
    request_id: str,
    client_host: str,
) -> None:
    logger.warning(
        "bot request denied request_id=%s endpoint=%s reason=%s bot_instance_id=%s license_key=%s ip=%s",
        request_id,
        meta.endpoint_key,
        reason_code,
        meta.bot_instance_id,
        meta.license_key,
        client_host,
    )
    write_audit_log(
        db,
        actor_type="bot",
        actor_id=meta.bot_instance_id,
        action_type=action_type,
        target_type="security",
        target_id=meta.bot_instance_id or meta.license_key,
        license_key=meta.license_key,
        bot_instance_id=meta.bot_instance_id,
        product_code=meta.product_code,
        bot_family=meta.bot_family,
        strategy_code=meta.strategy_code,
        metadata={"reason_code": reason_code, "message": message, "request_id": request_id, "ip_address": client_host},
    )
    db.commit()


def log_admin_auth_denial(
    db: Session,
    *,
    request: Request,
    email: str | None,
    reason_code: str,
    message: str,
) -> None:
    request_id = get_request_id_from_request(request)
    client_host = request.client.host if request.client else "unknown"
    normalized_email = (email or "").strip().lower() or None
    logger.warning("admin auth denied request_id=%s email=%s ip=%s reason=%s", request_id, normalized_email, client_host, reason_code)
    write_audit_log(
        db,
        actor_type="admin",
        actor_id=normalized_email,
        action_type="admin_auth_denied",
        target_type="security",
        target_id=normalized_email,
        metadata={"reason_code": reason_code, "message": message, "request_id": request_id, "ip_address": client_host},
    )
    db.commit()
