from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import Select, desc, func, or_, select
from sqlalchemy.orm import Session

from app.models.admin_user import AdminUser
from app.models.domain import AdminAlert, AuditLog, BotHeartbeat, BotInstance, BotState, CommandResult, License, RemoteCommand

ONLINE_THRESHOLD = timedelta(seconds=45)
STALE_THRESHOLD = timedelta(seconds=180)
AUTH_WINDOW = timedelta(minutes=30)
COMMAND_TTL = timedelta(minutes=5)
PENDING_COMMAND_STATUSES = ("queued", "sent", "acknowledged")
ALLOWED_MODES = {"off", "monitor", "enforce"}


@dataclass(slots=True)
class LicenseDecision:
    license_status: str
    effective_mode: str
    bot_status: str
    allowed: bool
    reason_code: str | None
    message: str
    authorized_until: datetime | None
    suspicious: bool
    errors: list[str]
    warnings: list[str]


def register_bot(db: Session, payload: Any, ip_address: str | None = None) -> dict[str, Any]:
    license_obj = _find_license(db, payload.license_key)
    if license_obj is None:
        return _build_denied_response(payload, "unknown_license", "license key not found")

    decision = _evaluate_license(license_obj, payload.protocol_version)
    if not decision.allowed:
        _write_audit_log(db, actor_type="bot", actor_id=payload.bot_instance_id, action_type="register_denied", target_type="license", target_id=str(license_obj.id), license_key=license_obj.license_key, bot_instance_id=payload.bot_instance_id, product_code=payload.product_code, bot_family=payload.bot_family, strategy_code=payload.strategy_code, metadata={"reason_code": decision.reason_code, "message": decision.message})
        db.commit()
        return _build_response(payload, decision)

    bot_instance = db.scalar(select(BotInstance).where(BotInstance.bot_instance_id == payload.bot_instance_id))
    now = datetime.now(UTC)
    if bot_instance is None:
        bot_instance = BotInstance(bot_instance_id=payload.bot_instance_id, license_id=license_obj.id, product_code=payload.product_code, bot_family=payload.bot_family, strategy_code=payload.strategy_code, machine_fingerprint=payload.machine_fingerprint, fingerprint_version=payload.fingerprint_version, hostname=payload.hostname, ip_address_last=ip_address, bot_version=payload.bot_version, protocol_version=_protocol_to_int(payload.protocol_version), platform=payload.platform, status=decision.bot_status, is_authorized=decision.allowed, authorized_until=decision.authorized_until, first_seen_at=now, last_seen_at=now)
        db.add(bot_instance)
    else:
        bot_instance.license_id = license_obj.id
        bot_instance.product_code = payload.product_code
        bot_instance.bot_family = payload.bot_family
        bot_instance.strategy_code = payload.strategy_code
        bot_instance.machine_fingerprint = payload.machine_fingerprint
        bot_instance.fingerprint_version = payload.fingerprint_version
        bot_instance.hostname = payload.hostname
        bot_instance.ip_address_last = ip_address
        bot_instance.bot_version = payload.bot_version
        bot_instance.protocol_version = _protocol_to_int(payload.protocol_version)
        bot_instance.platform = payload.platform
        bot_instance.status = decision.bot_status
        bot_instance.is_authorized = decision.allowed
        bot_instance.authorized_until = decision.authorized_until
        bot_instance.last_seen_at = now
        bot_instance.last_error_code = decision.reason_code
        bot_instance.last_error_message = None if decision.allowed else decision.message

    _write_audit_log(db, actor_type="bot", actor_id=payload.bot_instance_id, action_type="register", target_type="bot_instance", target_id=payload.bot_instance_id, license_key=license_obj.license_key, bot_instance_id=payload.bot_instance_id, product_code=payload.product_code, bot_family=payload.bot_family, strategy_code=payload.strategy_code, metadata={"session_id": payload.session_id})
    db.commit()
    return _build_response(payload, decision)


def check_license(db: Session, payload: Any) -> dict[str, Any]:
    license_obj = _find_license(db, payload.license_key)
    if license_obj is None:
        return {"ok": True, "license_status": "unknown", "effective_mode": "off", "bot_status": "blocked", "authorization": {"allowed": False, "reason_code": "unknown_license", "message": "license key not found", "authorized_until": None}, "detail": "license denied"}

    decision = _evaluate_license(license_obj, payload.protocol_version)
    return {"ok": True, "license_status": decision.license_status, "effective_mode": decision.effective_mode, "bot_status": decision.bot_status, "authorization": {"allowed": decision.allowed, "reason_code": decision.reason_code, "message": decision.message, "authorized_until": decision.authorized_until}, "detail": decision.message}


def record_heartbeat(db: Session, payload: Any, ip_address: str | None = None) -> dict[str, Any]:
    license_obj, bot_instance = _get_bound_bot_context(db, payload)
    db.add(BotHeartbeat(bot_instance_id=bot_instance.bot_instance_id, license_id=license_obj.id, session_id=payload.session_id, product_code=payload.product_code, bot_family=payload.bot_family, strategy_code=payload.strategy_code, status=payload.status, sent_at=payload.sent_at, ip_address=ip_address, warnings_json=payload.warnings))
    bot_instance.last_seen_at = datetime.now(UTC)
    bot_instance.status = _normalize_bot_runtime_status(payload.status)
    db.commit()
    return {"ok": True, "bot_instance_id": bot_instance.bot_instance_id, "status": bot_instance.status, "connectivity_status": compute_connectivity_status(bot_instance.last_seen_at)}


def record_state(db: Session, payload: Any) -> dict[str, Any]:
    license_obj, bot_instance = _get_bound_bot_context(db, payload)
    db.add(BotState(bot_instance_id=bot_instance.bot_instance_id, license_id=license_obj.id, session_id=payload.session_id, product_code=payload.product_code, bot_family=payload.bot_family, strategy_code=payload.strategy_code, bot_status=payload.bot_state.bot_status, session_status=payload.bot_state.session_status, connectivity_status=payload.bot_state.connectivity_status, grace_until=payload.bot_state.grace_until, current_symbols_json=payload.bot_state.current_symbols, symbol_states_json=[item.model_dump(mode="json") for item in payload.symbol_states], position_snapshots_json=[item.model_dump(mode="json") for item in payload.position_snapshots], open_orders_count=payload.bot_state.open_orders_count, open_positions_count=payload.bot_state.open_positions_count, equity_snapshot=payload.bot_state.equity_snapshot))
    bot_instance.last_state_sync_at = datetime.now(UTC)
    if payload.bot_state.bot_status:
        bot_instance.status = payload.bot_state.bot_status
    db.commit()
    return {"ok": True, "bot_instance_id": bot_instance.bot_instance_id, "last_state_sync_at": bot_instance.last_state_sync_at}


def get_commands(db: Session, payload: Any) -> dict[str, Any]:
    license_obj, bot_instance = _get_bound_bot_context(db, payload)
    stmt: Select[tuple[RemoteCommand]] = select(RemoteCommand).where(RemoteCommand.license_id == license_obj.id).where(RemoteCommand.status.in_(PENDING_COMMAND_STATUSES)).where(or_(RemoteCommand.bot_instance_id.is_(None), RemoteCommand.bot_instance_id == bot_instance.bot_instance_id)).where(or_(RemoteCommand.session_id.is_(None), RemoteCommand.session_id == payload.session_id)).order_by(RemoteCommand.created_at.asc())
    commands = db.scalars(stmt).all()
    now = datetime.now(UTC)
    items: list[dict[str, Any]] = []
    for command in commands:
        if command.expires_at and _ensure_utc(command.expires_at) < now:
            command.status = "expired"
            continue
        if command.status == "queued":
            command.status = "sent"
        items.append(_serialize_command(command))
    db.commit()
    return {"ok": True, "commands": items}


def record_command_result(db: Session, payload: Any) -> dict[str, Any]:
    license_obj, bot_instance = _get_bound_bot_context(db, payload)
    command = db.scalar(select(RemoteCommand).where(RemoteCommand.command_id == payload.command_id))
    if command is None or command.license_id != license_obj.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="remote command not found")
    db.add(CommandResult(command_id=payload.command_id, bot_instance_id=bot_instance.bot_instance_id, result_status=payload.result_status, message=payload.message, details_json=payload.details, sent_at=payload.sent_at))
    command.status = _map_result_status_to_command_status(payload.result_status)
    if command.status in {"acknowledged", "running"}:
        command.acknowledged_at = datetime.now(UTC)
    if command.status in {"completed", "failed"}:
        command.completed_at = datetime.now(UTC)
    db.commit()
    return {"ok": True, "command_id": payload.command_id, "status": command.status}


def list_admin_licenses(db: Session) -> list[dict[str, Any]]:
    licenses = db.scalars(select(License).order_by(License.created_at.desc())).all()
    return [{"license_key": l.license_key, "status": l.status, "effective_mode": l.mode, "product_code": l.product_code, "bot_family": l.bot_family, "strategy_code": l.strategy_code, "owner_label": l.owner_label, "suspicious_flag": l.suspicious_flag, "expires_at": l.expires_at, "bot_count": db.scalar(select(func.count()).select_from(BotInstance).where(BotInstance.license_id == l.id)) or 0} for l in licenses]


def list_admin_bots(db: Session) -> list[dict[str, Any]]:
    return [_serialize_bot_instance(db, bot) for bot in db.scalars(select(BotInstance).order_by(desc(BotInstance.last_seen_at))).all()]


def get_admin_bot_detail(db: Session, bot_instance_id: str) -> dict[str, Any]:
    bot = db.scalar(select(BotInstance).where(BotInstance.bot_instance_id == bot_instance_id))
    if bot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="bot instance not found")
    latest_state = db.scalar(select(BotState).where(BotState.bot_instance_id == bot_instance_id).order_by(BotState.received_at.desc()))
    recent_commands = db.scalars(select(RemoteCommand).where(RemoteCommand.bot_instance_id == bot_instance_id).order_by(RemoteCommand.created_at.desc()).limit(20)).all()
    payload = _serialize_bot_instance(db, bot)
    payload["latest_state"] = None if latest_state is None else {"bot_status": latest_state.bot_status, "session_status": latest_state.session_status, "connectivity_status": latest_state.connectivity_status, "current_symbols": latest_state.current_symbols_json, "received_at": latest_state.received_at}
    payload["recent_commands"] = [_serialize_command(command) for command in recent_commands]
    return payload


def list_admin_alerts(db: Session) -> list[dict[str, Any]]:
    alerts = db.scalars(select(AdminAlert).order_by(AdminAlert.last_seen_at.desc())).all()
    return [{"id": a.id, "alert_type": a.alert_type, "severity": a.severity, "status": a.status, "license_id": a.license_id, "bot_instance_id": a.bot_instance_id, "session_id": a.session_id, "summary": a.summary, "details": a.details_json, "first_seen_at": a.first_seen_at, "last_seen_at": a.last_seen_at, "resolved_at": a.resolved_at} for a in alerts]


def block_license(db: Session, payload: Any, admin_user: AdminUser) -> dict[str, Any]:
    license_obj = _find_license(db, payload.license_key)
    if license_obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="license not found")
    license_obj.status = "blocked"
    license_obj.mode = "off"
    license_obj.blocked_reason = payload.reason
    _write_audit_log(db, actor_type="admin", actor_id=str(admin_user.id), action_type="license_block", target_type="license", target_id=str(license_obj.id), license_key=license_obj.license_key, metadata={"reason": payload.reason})
    db.commit()
    return {"ok": True, "license_key": license_obj.license_key, "status": license_obj.status}


def create_admin_bot_command(db: Session, *, bot_instance_id: str, command_type: str, reason: str | None, admin_user: AdminUser) -> dict[str, Any]:
    bot = db.scalar(select(BotInstance).where(BotInstance.bot_instance_id == bot_instance_id))
    if bot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="bot instance not found")
    command = RemoteCommand(command_id=f"cmd_{uuid4().hex}", license_id=bot.license_id, bot_instance_id=bot.bot_instance_id, session_id=None, product_code=bot.product_code, bot_family=bot.bot_family, strategy_code=bot.strategy_code, command_type=command_type, risk_class="medium-risk", payload_json={}, status="queued", reason=reason, created_by_admin_id=admin_user.id, expires_at=datetime.now(UTC) + COMMAND_TTL)
    db.add(command)
    bot.status = {"pause": "paused", "resume": "online", "stop": "stopping", "close_positions": "closing_positions"}[command_type]
    _write_audit_log(db, actor_type="admin", actor_id=str(admin_user.id), action_type=f"bot_{command_type}", target_type="bot_instance", target_id=bot.bot_instance_id, license_key=bot.license.license_key, bot_instance_id=bot.bot_instance_id, product_code=bot.product_code, bot_family=bot.bot_family, strategy_code=bot.strategy_code, metadata={"command_id": command.command_id, "reason": reason})
    db.commit()
    return {"ok": True, "command_id": command.command_id, "status": command.status, "command_type": command.command_type}


def compute_connectivity_status(last_seen_at: datetime | None, now: datetime | None = None) -> str:
    if last_seen_at is None:
        return "offline"
    delta = (now or datetime.now(UTC)) - _ensure_utc(last_seen_at)
    if delta <= ONLINE_THRESHOLD:
        return "online"
    if delta <= STALE_THRESHOLD:
        return "stale"
    return "offline"


def _serialize_bot_instance(db: Session, bot: BotInstance) -> dict[str, Any]:
    license_obj = bot.license or db.get(License, bot.license_id)
    return {"bot_instance_id": bot.bot_instance_id, "license_key": None if license_obj is None else license_obj.license_key, "product_code": bot.product_code, "bot_family": bot.bot_family, "strategy_code": bot.strategy_code, "status": bot.status, "connectivity_status": compute_connectivity_status(bot.last_seen_at), "machine_fingerprint": bot.machine_fingerprint, "hostname": bot.hostname, "bot_version": bot.bot_version, "protocol_version": bot.protocol_version, "platform": bot.platform, "is_authorized": bot.is_authorized, "authorized_until": bot.authorized_until, "last_seen_at": bot.last_seen_at, "last_state_sync_at": bot.last_state_sync_at}


def _serialize_command(command: RemoteCommand) -> dict[str, Any]:
    return {"command_id": command.command_id, "bot_instance_id": command.bot_instance_id, "session_id": command.session_id, "product_code": command.product_code, "bot_family": command.bot_family, "strategy_code": command.strategy_code, "command_type": command.command_type, "risk_class": command.risk_class, "payload": command.payload_json, "status": command.status, "reason": command.reason, "created_at": command.created_at, "expires_at": command.expires_at, "acknowledged_at": command.acknowledged_at, "completed_at": command.completed_at}


def _find_license(db: Session, license_key: str) -> License | None:
    return db.scalar(select(License).where(License.license_key == license_key.strip()))


def _evaluate_license(license_obj: License, protocol_version: str | int) -> LicenseDecision:
    errors: list[str] = []
    warnings: list[str] = []
    license_status = license_obj.status
    effective_mode = license_obj.mode if license_obj.mode in ALLOWED_MODES else "off"
    now = datetime.now(UTC)
    if license_obj.expires_at and _ensure_utc(license_obj.expires_at) <= now:
        return LicenseDecision("expired", "off", "blocked", False, "expired", "license expired", None, license_obj.suspicious_flag, errors, warnings)
    if license_status != "active":
        return LicenseDecision(license_status, effective_mode if license_status == "suspicious" else "off", "blocked", False, license_status, f"license {license_status}", None, license_obj.suspicious_flag, errors, warnings)
    protocol_number = _protocol_to_int(protocol_version)
    if license_obj.allowed_protocol_min is not None and protocol_number < license_obj.allowed_protocol_min:
        errors.append("protocol below minimum")
    if license_obj.allowed_protocol_max is not None and protocol_number > license_obj.allowed_protocol_max:
        errors.append("protocol above maximum")
    if errors:
        return LicenseDecision(license_status, "off", "blocked", False, "protocol_mismatch", "protocol version outside allowed range", None, license_obj.suspicious_flag, errors, warnings)
    if license_obj.suspicious_flag:
        warnings.append("license marked suspicious")
    return LicenseDecision(license_status, effective_mode, "online", True, None, "allowed", now + AUTH_WINDOW, license_obj.suspicious_flag, errors, warnings)


def _build_denied_response(payload: Any, reason_code: str, message: str) -> dict[str, Any]:
    return {"ok": True, "request_id": f"req_{uuid4().hex}", "server_time": datetime.now(UTC), "protocol_version": str(payload.protocol_version), "license_status": "unknown", "bot_status": "blocked", "effective_mode": "off", "authorization": {"allowed": False, "reason_code": reason_code, "message": message, "authorized_until": None}, "timers": {"heartbeat_sec": 15, "state_sync_sec": 60, "command_poll_sec": 10}, "flags": {"suspicious": False, "license_recheck_required": True}, "errors": [message], "warnings": []}


def _build_response(payload: Any, decision: LicenseDecision) -> dict[str, Any]:
    return {"ok": True, "request_id": f"req_{uuid4().hex}", "server_time": datetime.now(UTC), "protocol_version": str(payload.protocol_version), "license_status": decision.license_status, "bot_status": decision.bot_status, "effective_mode": decision.effective_mode, "authorization": {"allowed": decision.allowed, "reason_code": decision.reason_code, "message": decision.message, "authorized_until": decision.authorized_until}, "timers": {"heartbeat_sec": 15, "state_sync_sec": 60, "command_poll_sec": 10}, "flags": {"suspicious": decision.suspicious, "license_recheck_required": not decision.allowed}, "errors": decision.errors, "warnings": decision.warnings}


def _get_bound_bot_context(db: Session, payload: Any) -> tuple[License, BotInstance]:
    license_obj = _find_license(db, payload.license_key)
    if license_obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="license not found")
    bot_instance = db.scalar(select(BotInstance).where(BotInstance.bot_instance_id == payload.bot_instance_id))
    if bot_instance is None or bot_instance.license_id != license_obj.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="bot instance not found")
    return license_obj, bot_instance


def _write_audit_log(db: Session, *, actor_type: str, actor_id: str | None, action_type: str, target_type: str, target_id: str | None, license_key: str | None = None, bot_instance_id: str | None = None, product_code: str | None = None, bot_family: str | None = None, strategy_code: str | None = None, metadata: dict[str, Any] | None = None) -> None:
    db.add(AuditLog(actor_type=actor_type, actor_id=actor_id, action_type=action_type, target_type=target_type, target_id=target_id, license_key=license_key, bot_instance_id=bot_instance_id, product_code=product_code, bot_family=bot_family, strategy_code=strategy_code, metadata_json=metadata))


def _protocol_to_int(value: str | int) -> int:
    if isinstance(value, int):
        return value
    normalized = str(value).strip()
    if normalized.isdigit():
        return int(normalized)
    major, dot, minor = normalized.partition('.')
    if dot and major.isdigit() and minor.isdigit():
        return int(major) * 1000 + int(minor)
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="invalid protocol version")


def _normalize_bot_runtime_status(status_value: str | None) -> str:
    value = (status_value or "online").strip().lower()
    return value if value in {"online", "paused", "blocked", "stopping", "closing_positions", "offline", "stale"} else "online"


def _map_result_status_to_command_status(result_status: str) -> str:
    return {"acknowledged": "acknowledged", "running": "running", "completed": "completed", "failed": "failed"}.get(result_status, "acknowledged")


def _ensure_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
