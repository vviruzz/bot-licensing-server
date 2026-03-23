from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.json import normalize_json_value
from app.models.domain import AdminAlert, BotInstance, License, RemoteCommand

ALERT_STATUS_OPEN = "open"
ALERT_STATUS_RESOLVED = "resolved"
QUIET_COMMAND_ALERT_TYPES = {"noop", "recheck_license"}


def evaluate_bot_connectivity_alerts(db: Session, *, bot: BotInstance, connectivity_status: str, now: datetime | None = None) -> None:
    timestamp = now or datetime.now(UTC)
    if connectivity_status == "online":
        _resolve_alerts(db, alert_types=("bot_stale", "bot_offline"), bot_instance_id=bot.bot_instance_id, resolved_at=timestamp)
        return

    severity = "warning" if connectivity_status == "stale" else "critical"
    alert_type = "bot_stale" if connectivity_status == "stale" else "bot_offline"
    summary = f"Bot {bot.bot_instance_id} is {connectivity_status}"
    details = {
        "connectivity_status": connectivity_status,
        "last_seen_at": bot.last_seen_at,
        "license_id": bot.license_id,
    }
    _upsert_alert(
        db,
        alert_type=alert_type,
        severity=severity,
        summary=summary,
        details=details,
        license_id=bot.license_id,
        bot_instance_id=bot.bot_instance_id,
        product_code=bot.product_code,
        bot_family=bot.bot_family,
        strategy_code=bot.strategy_code,
        now=timestamp,
    )
    alternate_type = "bot_offline" if alert_type == "bot_stale" else "bot_stale"
    _resolve_alerts(db, alert_types=(alternate_type,), bot_instance_id=bot.bot_instance_id, resolved_at=timestamp)


def evaluate_command_alert(db: Session, *, command: RemoteCommand, now: datetime | None = None) -> None:
    timestamp = now or datetime.now(UTC)
    if command.command_type in QUIET_COMMAND_ALERT_TYPES:
        _resolve_alerts(
            db,
            alert_types=("command_failed", "command_expired"),
            license_id=command.license_id,
            bot_instance_id=command.bot_instance_id,
            session_id=command.session_id,
            target_summary_prefix=f"Command {command.command_id}",
            resolved_at=timestamp,
        )
        return

    if command.status == "failed":
        _upsert_alert(
            db,
            alert_type="command_failed",
            severity="critical",
            summary=f"Command {command.command_id} failed",
            details={"command_type": command.command_type, "reason": command.reason, "status": command.status},
            license_id=command.license_id,
            bot_instance_id=command.bot_instance_id,
            session_id=command.session_id,
            product_code=command.product_code,
            bot_family=command.bot_family,
            strategy_code=command.strategy_code,
            now=timestamp,
        )
        return
    if command.status == "expired":
        _upsert_alert(
            db,
            alert_type="command_expired",
            severity="warning",
            summary=f"Command {command.command_id} expired",
            details={"command_type": command.command_type, "reason": command.reason, "status": command.status},
            license_id=command.license_id,
            bot_instance_id=command.bot_instance_id,
            session_id=command.session_id,
            product_code=command.product_code,
            bot_family=command.bot_family,
            strategy_code=command.strategy_code,
            now=timestamp,
        )
        return

    _resolve_alerts(
        db,
        alert_types=("command_failed", "command_expired"),
        license_id=command.license_id,
        bot_instance_id=command.bot_instance_id,
        session_id=command.session_id,
        target_summary_prefix=f"Command {command.command_id}",
        resolved_at=timestamp,
    )


def evaluate_license_alerts(db: Session, *, license_obj: License, bot_instance_id: str | None = None, now: datetime | None = None) -> None:
    timestamp = now or datetime.now(UTC)
    should_alert = license_obj.status in {"blocked", "invalid", "expired"} or bool(license_obj.blocked_reason)
    if should_alert:
        _upsert_alert(
            db,
            alert_type="license_blocked",
            severity="critical" if license_obj.status == "blocked" else "warning",
            summary=f"License {license_obj.license_key} is {license_obj.status}",
            details={"blocked_reason": license_obj.blocked_reason, "status": license_obj.status},
            license_id=license_obj.id,
            bot_instance_id=bot_instance_id,
            product_code=license_obj.product_code,
            bot_family=license_obj.bot_family,
            strategy_code=license_obj.strategy_code,
            now=timestamp,
        )
    else:
        _resolve_alerts(db, alert_types=("license_blocked",), license_id=license_obj.id, resolved_at=timestamp)

    if license_obj.suspicious_flag:
        _upsert_alert(
            db,
            alert_type="license_suspicious",
            severity="warning",
            summary=f"License {license_obj.license_key} flagged as suspicious",
            details={"status": license_obj.status, "blocked_reason": license_obj.blocked_reason},
            license_id=license_obj.id,
            bot_instance_id=bot_instance_id,
            product_code=license_obj.product_code,
            bot_family=license_obj.bot_family,
            strategy_code=license_obj.strategy_code,
            now=timestamp,
        )
    else:
        _resolve_alerts(db, alert_types=("license_suspicious",), license_id=license_obj.id, resolved_at=timestamp)


def evaluate_duplicate_fingerprint_alert(db: Session, *, bot: BotInstance, now: datetime | None = None) -> None:
    timestamp = now or datetime.now(UTC)
    duplicates = db.scalars(
        select(BotInstance)
        .where(BotInstance.license_id == bot.license_id)
        .where(BotInstance.machine_fingerprint == bot.machine_fingerprint)
        .where(BotInstance.bot_instance_id != bot.bot_instance_id)
    ).all()
    if duplicates:
        _upsert_alert(
            db,
            alert_type="duplicate_fingerprint",
            severity="warning",
            summary=f"Duplicate fingerprint detected for {bot.bot_instance_id}",
            details={
                "machine_fingerprint": bot.machine_fingerprint,
                "duplicate_bot_instance_ids": [item.bot_instance_id for item in duplicates],
            },
            license_id=bot.license_id,
            bot_instance_id=bot.bot_instance_id,
            product_code=bot.product_code,
            bot_family=bot.bot_family,
            strategy_code=bot.strategy_code,
            now=timestamp,
        )
    else:
        _resolve_alerts(db, alert_types=("duplicate_fingerprint",), bot_instance_id=bot.bot_instance_id, resolved_at=timestamp)


def list_alert_payloads(db: Session) -> list[dict[str, Any]]:
    alerts = db.scalars(select(AdminAlert).order_by(AdminAlert.last_seen_at.desc(), AdminAlert.id.desc())).all()
    return [
        {
            "id": alert.id,
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "status": alert.status,
            "license_id": alert.license_id,
            "bot_instance_id": alert.bot_instance_id,
            "session_id": alert.session_id,
            "summary": alert.summary,
            "details": normalize_json_value(alert.details_json),
            "first_seen_at": alert.first_seen_at,
            "last_seen_at": alert.last_seen_at,
            "resolved_at": alert.resolved_at,
        }
        for alert in alerts
    ]


def _upsert_alert(
    db: Session,
    *,
    alert_type: str,
    severity: str,
    summary: str,
    details: dict[str, Any] | list[Any] | None,
    license_id: int | None = None,
    bot_instance_id: str | None = None,
    session_id: str | None = None,
    product_code: str | None = None,
    bot_family: str | None = None,
    strategy_code: str | None = None,
    now: datetime,
) -> None:
    stmt = select(AdminAlert).where(AdminAlert.alert_type == alert_type).where(AdminAlert.status == ALERT_STATUS_OPEN)
    if license_id is None:
        stmt = stmt.where(AdminAlert.license_id.is_(None))
    else:
        stmt = stmt.where(AdminAlert.license_id == license_id)
    if bot_instance_id is None:
        stmt = stmt.where(AdminAlert.bot_instance_id.is_(None))
    else:
        stmt = stmt.where(AdminAlert.bot_instance_id == bot_instance_id)
    if session_id is None:
        stmt = stmt.where(AdminAlert.session_id.is_(None))
    else:
        stmt = stmt.where(AdminAlert.session_id == session_id)

    alert = db.scalar(stmt)
    if alert is None:
        db.add(
            AdminAlert(
                alert_type=alert_type,
                severity=severity,
                status=ALERT_STATUS_OPEN,
                license_id=license_id,
                bot_instance_id=bot_instance_id,
                session_id=session_id,
                product_code=product_code,
                bot_family=bot_family,
                strategy_code=strategy_code,
                summary=summary,
                details_json=normalize_json_value(details),
                first_seen_at=now,
                last_seen_at=now,
            )
        )
        return

    alert.severity = severity
    alert.summary = summary
    alert.details_json = normalize_json_value(details)
    alert.last_seen_at = now
    alert.resolved_at = None


def _resolve_alerts(
    db: Session,
    *,
    alert_types: tuple[str, ...],
    resolved_at: datetime,
    license_id: int | None = None,
    bot_instance_id: str | None = None,
    session_id: str | None = None,
    target_summary_prefix: str | None = None,
) -> None:
    stmt = select(AdminAlert).where(AdminAlert.alert_type.in_(alert_types)).where(AdminAlert.status == ALERT_STATUS_OPEN)
    if license_id is not None:
        stmt = stmt.where(AdminAlert.license_id == license_id)
    if bot_instance_id is not None:
        stmt = stmt.where(AdminAlert.bot_instance_id == bot_instance_id)
    if session_id is not None:
        stmt = stmt.where(AdminAlert.session_id == session_id)

    for alert in db.scalars(stmt).all():
        if target_summary_prefix and not alert.summary.startswith(target_summary_prefix):
            continue
        alert.status = ALERT_STATUS_RESOLVED
        alert.resolved_at = resolved_at
        alert.last_seen_at = resolved_at
