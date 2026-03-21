from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.admin_user import AdminUser


class License(Base):
    __tablename__ = "licenses"
    __table_args__ = (
        UniqueConstraint("license_key", name="uq_licenses_license_key"),
        Index("ix_licenses_status", "status"),
        Index("ix_licenses_product_bot_strategy", "product_code", "bot_family", "strategy_code"),
        Index("ix_licenses_expires_at", "expires_at"),
        Index("ix_licenses_suspicious_flag", "suspicious_flag"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    license_key: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    mode: Mapped[str] = mapped_column(String(32), nullable=False)
    product_code: Mapped[str] = mapped_column(String(64), nullable=False)
    bot_family: Mapped[str] = mapped_column(String(64), nullable=False)
    strategy_code: Mapped[str] = mapped_column(String(64), nullable=False)
    owner_label: Mapped[str | None] = mapped_column(String(255))
    plan_name: Mapped[str | None] = mapped_column(String(128))
    max_instances: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    max_fingerprints: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    allowed_protocol_min: Mapped[int | None] = mapped_column(Integer)
    allowed_protocol_max: Mapped[int | None] = mapped_column(Integer)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    suspicious_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    blocked_reason: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    bot_instances: Mapped[list[BotInstance]] = relationship(back_populates="license")
    heartbeats: Mapped[list[BotHeartbeat]] = relationship(back_populates="license")
    states: Mapped[list[BotState]] = relationship(back_populates="license")
    remote_commands: Mapped[list[RemoteCommand]] = relationship(back_populates="license")
    alerts: Mapped[list[AdminAlert]] = relationship(back_populates="license")


class BotInstance(Base):
    __tablename__ = "bot_instances"
    __table_args__ = (
        UniqueConstraint("bot_instance_id", name="uq_bot_instances_bot_instance_id"),
        Index("ix_bot_instances_license_id_status", "license_id", "status"),
        Index("ix_bot_instances_machine_fingerprint", "machine_fingerprint"),
        Index("ix_bot_instances_last_seen_at", "last_seen_at"),
        Index("ix_bot_instances_authorized_until", "authorized_until"),
        Index("ix_bot_instances_product_bot_strategy", "product_code", "bot_family", "strategy_code"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    bot_instance_id: Mapped[str] = mapped_column(String(128), nullable=False)
    license_id: Mapped[int] = mapped_column(ForeignKey("licenses.id", ondelete="CASCADE"), nullable=False)
    product_code: Mapped[str] = mapped_column(String(64), nullable=False)
    bot_family: Mapped[str] = mapped_column(String(64), nullable=False)
    strategy_code: Mapped[str] = mapped_column(String(64), nullable=False)
    machine_fingerprint: Mapped[str] = mapped_column(String(255), nullable=False)
    fingerprint_version: Mapped[str | None] = mapped_column(String(32))
    hostname: Mapped[str | None] = mapped_column(String(255))
    ip_address_last: Mapped[str | None] = mapped_column(INET)
    bot_version: Mapped[str | None] = mapped_column(String(64))
    protocol_version: Mapped[int] = mapped_column(Integer, nullable=False)
    platform: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    is_authorized: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    authorized_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    first_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_state_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error_code: Mapped[str | None] = mapped_column(String(64))
    last_error_message: Mapped[str | None] = mapped_column(Text)

    license: Mapped[License] = relationship(back_populates="bot_instances")
    heartbeats: Mapped[list[BotHeartbeat]] = relationship(back_populates="bot_instance")
    states: Mapped[list[BotState]] = relationship(back_populates="bot_instance")
    remote_commands: Mapped[list[RemoteCommand]] = relationship(back_populates="bot_instance")
    command_results: Mapped[list[CommandResult]] = relationship(back_populates="bot_instance")
    alerts: Mapped[list[AdminAlert]] = relationship(back_populates="bot_instance")


class BotHeartbeat(Base):
    __tablename__ = "bot_heartbeats"
    __table_args__ = (
        Index("ix_bot_heartbeats_bot_instance_id", "bot_instance_id"),
        Index("ix_bot_heartbeats_license_id_received_at", "license_id", "received_at"),
        Index("ix_bot_heartbeats_session_id", "session_id"),
        Index("ix_bot_heartbeats_status", "status"),
        Index("ix_bot_heartbeats_sent_at", "sent_at"),
        Index("ix_bot_heartbeats_received_at", "received_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    bot_instance_id: Mapped[str] = mapped_column(ForeignKey("bot_instances.bot_instance_id", ondelete="CASCADE"), nullable=False)
    license_id: Mapped[int] = mapped_column(ForeignKey("licenses.id", ondelete="CASCADE"), nullable=False)
    session_id: Mapped[str | None] = mapped_column(String(128))
    product_code: Mapped[str] = mapped_column(String(64), nullable=False)
    bot_family: Mapped[str] = mapped_column(String(64), nullable=False)
    strategy_code: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    ip_address: Mapped[str | None] = mapped_column(INET)
    warnings_json: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSONB)

    bot_instance: Mapped[BotInstance] = relationship(back_populates="heartbeats")
    license: Mapped[License] = relationship(back_populates="heartbeats")


class BotState(Base):
    __tablename__ = "bot_states"
    __table_args__ = (
        Index("ix_bot_states_bot_instance_id", "bot_instance_id"),
        Index("ix_bot_states_license_id_received_at", "license_id", "received_at"),
        Index("ix_bot_states_session_id", "session_id"),
        Index("ix_bot_states_bot_status", "bot_status"),
        Index("ix_bot_states_received_at", "received_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    bot_instance_id: Mapped[str] = mapped_column(ForeignKey("bot_instances.bot_instance_id", ondelete="CASCADE"), nullable=False)
    license_id: Mapped[int] = mapped_column(ForeignKey("licenses.id", ondelete="CASCADE"), nullable=False)
    session_id: Mapped[str | None] = mapped_column(String(128))
    product_code: Mapped[str] = mapped_column(String(64), nullable=False)
    bot_family: Mapped[str] = mapped_column(String(64), nullable=False)
    strategy_code: Mapped[str] = mapped_column(String(64), nullable=False)
    bot_status: Mapped[str | None] = mapped_column(String(32))
    session_status: Mapped[str | None] = mapped_column(String(32))
    connectivity_status: Mapped[str | None] = mapped_column(String(32))
    grace_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    current_symbols_json: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSONB)
    symbol_states_json: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSONB)
    position_snapshots_json: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSONB)
    open_orders_count: Mapped[int | None] = mapped_column(Integer)
    open_positions_count: Mapped[int | None] = mapped_column(Integer)
    equity_snapshot: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    bot_instance: Mapped[BotInstance] = relationship(back_populates="states")
    license: Mapped[License] = relationship(back_populates="states")


class RemoteCommand(Base):
    __tablename__ = "remote_commands"
    __table_args__ = (
        UniqueConstraint("command_id", name="uq_remote_commands_command_id"),
        Index("ix_remote_commands_command_id", "command_id"),
        Index("ix_remote_commands_status", "status"),
        Index("ix_remote_commands_created_at", "created_at"),
        Index("ix_remote_commands_expires_at", "expires_at"),
        Index("ix_remote_commands_license_id_status", "license_id", "status"),
        Index("ix_remote_commands_bot_instance_id", "bot_instance_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    command_id: Mapped[str] = mapped_column(String(128), nullable=False)
    license_id: Mapped[int] = mapped_column(ForeignKey("licenses.id", ondelete="CASCADE"), nullable=False)
    bot_instance_id: Mapped[str | None] = mapped_column(ForeignKey("bot_instances.bot_instance_id", ondelete="SET NULL"))
    session_id: Mapped[str | None] = mapped_column(String(128))
    product_code: Mapped[str] = mapped_column(String(64), nullable=False)
    bot_family: Mapped[str] = mapped_column(String(64), nullable=False)
    strategy_code: Mapped[str] = mapped_column(String(64), nullable=False)
    command_type: Mapped[str] = mapped_column(String(64), nullable=False)
    risk_class: Mapped[str | None] = mapped_column(String(32))
    payload_json: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    created_by_admin_id: Mapped[int | None] = mapped_column(ForeignKey("admin_users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    license: Mapped[License] = relationship(back_populates="remote_commands")
    bot_instance: Mapped[BotInstance | None] = relationship(back_populates="remote_commands")
    created_by_admin: Mapped[AdminUser | None] = relationship(back_populates="remote_commands")
    results: Mapped[list[CommandResult]] = relationship(back_populates="remote_command")


class CommandResult(Base):
    __tablename__ = "command_results"
    __table_args__ = (
        Index("ix_command_results_command_id", "command_id"),
        Index("ix_command_results_bot_instance_id", "bot_instance_id"),
        Index("ix_command_results_result_status", "result_status"),
        Index("ix_command_results_received_at", "received_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    command_id: Mapped[str] = mapped_column(ForeignKey("remote_commands.command_id", ondelete="CASCADE"), nullable=False)
    bot_instance_id: Mapped[str] = mapped_column(ForeignKey("bot_instances.bot_instance_id", ondelete="CASCADE"), nullable=False)
    result_status: Mapped[str] = mapped_column(String(32), nullable=False)
    message: Mapped[str | None] = mapped_column(Text)
    details_json: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSONB)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    remote_command: Mapped[RemoteCommand] = relationship(back_populates="results")
    bot_instance: Mapped[BotInstance] = relationship(back_populates="command_results")


class AuditLog(Base):
    __tablename__ = "audit_log"
    __table_args__ = (
        Index("ix_audit_log_actor", "actor_type", "actor_id"),
        Index("ix_audit_log_target", "target_type", "target_id"),
        Index("ix_audit_log_license_key", "license_key"),
        Index("ix_audit_log_bot_instance_id", "bot_instance_id"),
        Index("ix_audit_log_created_at", "created_at"),
        Index("ix_audit_log_product_bot_strategy", "product_code", "bot_family", "strategy_code"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    actor_type: Mapped[str] = mapped_column(String(32), nullable=False)
    actor_id: Mapped[str | None] = mapped_column(String(128))
    action_type: Mapped[str] = mapped_column(String(64), nullable=False)
    target_type: Mapped[str] = mapped_column(String(64), nullable=False)
    target_id: Mapped[str | None] = mapped_column(String(128))
    license_key: Mapped[str | None] = mapped_column(String(128))
    bot_instance_id: Mapped[str | None] = mapped_column(String(128))
    product_code: Mapped[str | None] = mapped_column(String(64))
    bot_family: Mapped[str | None] = mapped_column(String(64))
    strategy_code: Mapped[str | None] = mapped_column(String(64))
    metadata_json: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class AdminAlert(Base):
    __tablename__ = "admin_alerts"
    __table_args__ = (
        Index("ix_admin_alerts_alert_type", "alert_type"),
        Index("ix_admin_alerts_severity_status", "severity", "status"),
        Index("ix_admin_alerts_license_id", "license_id"),
        Index("ix_admin_alerts_bot_instance_id", "bot_instance_id"),
        Index("ix_admin_alerts_session_id", "session_id"),
        Index("ix_admin_alerts_last_seen_at", "last_seen_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    alert_type: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    license_id: Mapped[int | None] = mapped_column(ForeignKey("licenses.id", ondelete="SET NULL"))
    bot_instance_id: Mapped[str | None] = mapped_column(ForeignKey("bot_instances.bot_instance_id", ondelete="SET NULL"))
    session_id: Mapped[str | None] = mapped_column(String(128))
    product_code: Mapped[str | None] = mapped_column(String(64))
    bot_family: Mapped[str | None] = mapped_column(String(64))
    strategy_code: Mapped[str | None] = mapped_column(String(64))
    summary: Mapped[str] = mapped_column(String(255), nullable=False)
    details_json: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSONB)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    license: Mapped[License | None] = relationship(back_populates="alerts")
    bot_instance: Mapped[BotInstance | None] = relationship(back_populates="alerts")

