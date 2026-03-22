from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.domain import AdminAlert, BotHeartbeat, BotInstance, BotState, License
from app.demo.constants import (
    DEMO_ALERT_DETAILS,
    DEMO_ALERT_SUMMARY,
    DEMO_ALERT_TYPE,
    DEMO_BOT_FAMILY,
    DEMO_BOT_INSTANCE_ID,
    DEMO_BOT_VERSION,
    DEMO_FINGERPRINT_VERSION,
    DEMO_HOSTNAME,
    DEMO_LICENSE_KEY,
    DEMO_LICENSE_OWNER,
    DEMO_MACHINE_FINGERPRINT,
    DEMO_PLAN_NAME,
    DEMO_PLATFORM,
    DEMO_PRODUCT_CODE,
    DEMO_PROTOCOL_VERSION,
    DEMO_SESSION_ID,
    DEMO_STRATEGY_CODE,
)


@dataclass(slots=True)
class SeedSummary:
    license_key: str
    bot_instance_id: str
    session_id: str
    alerts_seeded: int
    license_status: str
    bot_status: str


def seed_demo_data() -> SeedSummary:
    now = datetime.now(timezone.utc)
    protocol_version = 1000
    with SessionLocal() as db:
        license_obj = db.scalar(select(License).where(License.license_key == DEMO_LICENSE_KEY))
        if license_obj is None:
            license_obj = License(
                license_key=DEMO_LICENSE_KEY,
                status="active",
                mode="monitor",
                product_code=DEMO_PRODUCT_CODE,
                bot_family=DEMO_BOT_FAMILY,
                strategy_code=DEMO_STRATEGY_CODE,
                owner_label=DEMO_LICENSE_OWNER,
                plan_name=DEMO_PLAN_NAME,
                max_instances=1,
                max_fingerprints=1,
                allowed_protocol_min=protocol_version,
                allowed_protocol_max=protocol_version,
                expires_at=now + timedelta(days=30),
                suspicious_flag=False,
                blocked_reason=None,
                notes="MVP demo seed data for local and VDS smoke validation.",
            )
            db.add(license_obj)
            db.flush()
        else:
            license_obj.status = "active"
            license_obj.mode = "monitor"
            license_obj.product_code = DEMO_PRODUCT_CODE
            license_obj.bot_family = DEMO_BOT_FAMILY
            license_obj.strategy_code = DEMO_STRATEGY_CODE
            license_obj.owner_label = DEMO_LICENSE_OWNER
            license_obj.plan_name = DEMO_PLAN_NAME
            license_obj.max_instances = 1
            license_obj.max_fingerprints = 1
            license_obj.allowed_protocol_min = protocol_version
            license_obj.allowed_protocol_max = protocol_version
            license_obj.expires_at = now + timedelta(days=30)
            license_obj.suspicious_flag = False
            license_obj.blocked_reason = None
            license_obj.notes = "MVP demo seed data for local and VDS smoke validation."

        bot = db.scalar(select(BotInstance).where(BotInstance.bot_instance_id == DEMO_BOT_INSTANCE_ID))
        authorized_until = now + timedelta(minutes=30)
        if bot is None:
            bot = BotInstance(
                bot_instance_id=DEMO_BOT_INSTANCE_ID,
                license_id=license_obj.id,
                product_code=DEMO_PRODUCT_CODE,
                bot_family=DEMO_BOT_FAMILY,
                strategy_code=DEMO_STRATEGY_CODE,
                machine_fingerprint=DEMO_MACHINE_FINGERPRINT,
                fingerprint_version=DEMO_FINGERPRINT_VERSION,
                hostname=DEMO_HOSTNAME,
                ip_address_last="127.0.0.1",
                bot_version=DEMO_BOT_VERSION,
                protocol_version=protocol_version,
                platform=DEMO_PLATFORM,
                status="online",
                is_authorized=True,
                authorized_until=authorized_until,
                first_seen_at=now,
                last_seen_at=now,
                last_state_sync_at=now,
                last_error_code=None,
                last_error_message=None,
            )
            db.add(bot)
        else:
            bot.license_id = license_obj.id
            bot.product_code = DEMO_PRODUCT_CODE
            bot.bot_family = DEMO_BOT_FAMILY
            bot.strategy_code = DEMO_STRATEGY_CODE
            bot.machine_fingerprint = DEMO_MACHINE_FINGERPRINT
            bot.fingerprint_version = DEMO_FINGERPRINT_VERSION
            bot.hostname = DEMO_HOSTNAME
            bot.ip_address_last = "127.0.0.1"
            bot.bot_version = DEMO_BOT_VERSION
            bot.protocol_version = protocol_version
            bot.platform = DEMO_PLATFORM
            bot.status = "online"
            bot.is_authorized = True
            bot.authorized_until = authorized_until
            bot.last_seen_at = now
            bot.last_state_sync_at = now
            bot.last_error_code = None
            bot.last_error_message = None

        heartbeat = db.scalar(
            select(BotHeartbeat)
            .where(BotHeartbeat.bot_instance_id == DEMO_BOT_INSTANCE_ID)
            .order_by(BotHeartbeat.received_at.desc())
        )
        if heartbeat is None:
            db.add(
                BotHeartbeat(
                    bot_instance_id=DEMO_BOT_INSTANCE_ID,
                    license_id=license_obj.id,
                    session_id=DEMO_SESSION_ID,
                    product_code=DEMO_PRODUCT_CODE,
                    bot_family=DEMO_BOT_FAMILY,
                    strategy_code=DEMO_STRATEGY_CODE,
                    status="online",
                    sent_at=now,
                    received_at=now,
                    ip_address="127.0.0.1",
                    warnings_json=["demo-seed"],
                )
            )
        else:
            heartbeat.license_id = license_obj.id
            heartbeat.session_id = DEMO_SESSION_ID
            heartbeat.product_code = DEMO_PRODUCT_CODE
            heartbeat.bot_family = DEMO_BOT_FAMILY
            heartbeat.strategy_code = DEMO_STRATEGY_CODE
            heartbeat.status = "online"
            heartbeat.sent_at = now
            heartbeat.received_at = now
            heartbeat.ip_address = "127.0.0.1"
            heartbeat.warnings_json = ["demo-seed"]

        state = db.scalar(
            select(BotState)
            .where(BotState.bot_instance_id == DEMO_BOT_INSTANCE_ID)
            .order_by(BotState.received_at.desc())
        )
        if state is None:
            db.add(
                BotState(
                    bot_instance_id=DEMO_BOT_INSTANCE_ID,
                    license_id=license_obj.id,
                    session_id=DEMO_SESSION_ID,
                    product_code=DEMO_PRODUCT_CODE,
                    bot_family=DEMO_BOT_FAMILY,
                    strategy_code=DEMO_STRATEGY_CODE,
                    bot_status="online",
                    session_status="running",
                    connectivity_status="online",
                    grace_until=authorized_until,
                    current_symbols_json=["BTCUSDT"],
                    symbol_states_json=[{"symbol": "BTCUSDT", "status": "watching"}],
                    position_snapshots_json=[{"symbol": "BTCUSDT", "side": "flat", "qty": 0}],
                    open_orders_count=0,
                    open_positions_count=0,
                    equity_snapshot=10000,
                    received_at=now,
                )
            )
        else:
            state.license_id = license_obj.id
            state.session_id = DEMO_SESSION_ID
            state.product_code = DEMO_PRODUCT_CODE
            state.bot_family = DEMO_BOT_FAMILY
            state.strategy_code = DEMO_STRATEGY_CODE
            state.bot_status = "online"
            state.session_status = "running"
            state.connectivity_status = "online"
            state.grace_until = authorized_until
            state.current_symbols_json = ["BTCUSDT"]
            state.symbol_states_json = [{"symbol": "BTCUSDT", "status": "watching"}]
            state.position_snapshots_json = [{"symbol": "BTCUSDT", "side": "flat", "qty": 0}]
            state.open_orders_count = 0
            state.open_positions_count = 0
            state.equity_snapshot = 10000
            state.received_at = now

        alerts = db.scalars(select(AdminAlert).where(AdminAlert.alert_type == DEMO_ALERT_TYPE)).all()
        if not alerts:
            alerts = [
                AdminAlert(
                    alert_type=DEMO_ALERT_TYPE,
                    severity="info",
                    status="open",
                    license_id=license_obj.id,
                    bot_instance_id=DEMO_BOT_INSTANCE_ID,
                    session_id=DEMO_SESSION_ID,
                    product_code=DEMO_PRODUCT_CODE,
                    bot_family=DEMO_BOT_FAMILY,
                    strategy_code=DEMO_STRATEGY_CODE,
                    summary=DEMO_ALERT_SUMMARY,
                    details_json=DEMO_ALERT_DETAILS,
                    first_seen_at=now,
                    last_seen_at=now,
                    resolved_at=None,
                )
            ]
            db.add_all(alerts)
        else:
            for alert in alerts:
                alert.license_id = license_obj.id
                alert.bot_instance_id = DEMO_BOT_INSTANCE_ID
                alert.session_id = DEMO_SESSION_ID
                alert.product_code = DEMO_PRODUCT_CODE
                alert.bot_family = DEMO_BOT_FAMILY
                alert.strategy_code = DEMO_STRATEGY_CODE
                alert.severity = "info"
                alert.status = "open"
                alert.summary = DEMO_ALERT_SUMMARY
                alert.details_json = DEMO_ALERT_DETAILS
                alert.first_seen_at = alert.first_seen_at or now
                alert.last_seen_at = now
                alert.resolved_at = None

        db.commit()

        return SeedSummary(
            license_key=license_obj.license_key,
            bot_instance_id=DEMO_BOT_INSTANCE_ID,
            session_id=DEMO_SESSION_ID,
            alerts_seeded=len(alerts),
            license_status=license_obj.status,
            bot_status=bot.status,
        )


def main() -> None:
    summary = seed_demo_data()
    print(json.dumps(asdict(summary), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
