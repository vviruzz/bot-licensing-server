"""domain models schema

Revision ID: 20260321_000003
Revises: 20260321_000002
Create Date: 2026-03-21 00:00:03
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260321_000003"
down_revision = "20260321_000002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "licenses",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("license_key", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("mode", sa.String(length=32), nullable=False),
        sa.Column("product_code", sa.String(length=64), nullable=False),
        sa.Column("bot_family", sa.String(length=64), nullable=False),
        sa.Column("strategy_code", sa.String(length=64), nullable=False),
        sa.Column("owner_label", sa.String(length=255), nullable=True),
        sa.Column("plan_name", sa.String(length=128), nullable=True),
        sa.Column("max_instances", sa.Integer(), nullable=False),
        sa.Column("max_fingerprints", sa.Integer(), nullable=False),
        sa.Column("allowed_protocol_min", sa.Integer(), nullable=True),
        sa.Column("allowed_protocol_max", sa.Integer(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("suspicious_flag", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("blocked_reason", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("license_key", name="uq_licenses_license_key"),
    )
    op.create_index("ix_licenses_expires_at", "licenses", ["expires_at"], unique=False)
    op.create_index("ix_licenses_license_key", "licenses", ["license_key"], unique=False)
    op.create_index("ix_licenses_product_bot_strategy", "licenses", ["product_code", "bot_family", "strategy_code"], unique=False)
    op.create_index("ix_licenses_status", "licenses", ["status"], unique=False)
    op.create_index("ix_licenses_suspicious_flag", "licenses", ["suspicious_flag"], unique=False)

    op.create_table(
        "bot_instances",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("bot_instance_id", sa.String(length=128), nullable=False),
        sa.Column("license_id", sa.BigInteger(), nullable=False),
        sa.Column("product_code", sa.String(length=64), nullable=False),
        sa.Column("bot_family", sa.String(length=64), nullable=False),
        sa.Column("strategy_code", sa.String(length=64), nullable=False),
        sa.Column("machine_fingerprint", sa.String(length=255), nullable=False),
        sa.Column("fingerprint_version", sa.String(length=32), nullable=True),
        sa.Column("hostname", sa.String(length=255), nullable=True),
        sa.Column("ip_address_last", postgresql.INET(), nullable=True),
        sa.Column("bot_version", sa.String(length=64), nullable=True),
        sa.Column("protocol_version", sa.Integer(), nullable=False),
        sa.Column("platform", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("is_authorized", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("authorized_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_state_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_code", sa.String(length=64), nullable=True),
        sa.Column("last_error_message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["license_id"], ["licenses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("bot_instance_id", name="uq_bot_instances_bot_instance_id"),
    )
    op.create_index("ix_bot_instances_authorized_until", "bot_instances", ["authorized_until"], unique=False)
    op.create_index("ix_bot_instances_bot_instance_id", "bot_instances", ["bot_instance_id"], unique=False)
    op.create_index("ix_bot_instances_last_seen_at", "bot_instances", ["last_seen_at"], unique=False)
    op.create_index("ix_bot_instances_license_id_status", "bot_instances", ["license_id", "status"], unique=False)
    op.create_index("ix_bot_instances_machine_fingerprint", "bot_instances", ["machine_fingerprint"], unique=False)
    op.create_index("ix_bot_instances_product_bot_strategy", "bot_instances", ["product_code", "bot_family", "strategy_code"], unique=False)
    op.create_index("ix_bot_instances_status", "bot_instances", ["status"], unique=False)

    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("actor_type", sa.String(length=32), nullable=False),
        sa.Column("actor_id", sa.String(length=128), nullable=True),
        sa.Column("action_type", sa.String(length=64), nullable=False),
        sa.Column("target_type", sa.String(length=64), nullable=False),
        sa.Column("target_id", sa.String(length=128), nullable=True),
        sa.Column("license_key", sa.String(length=128), nullable=True),
        sa.Column("bot_instance_id", sa.String(length=128), nullable=True),
        sa.Column("product_code", sa.String(length=64), nullable=True),
        sa.Column("bot_family", sa.String(length=64), nullable=True),
        sa.Column("strategy_code", sa.String(length=64), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_log_actor", "audit_log", ["actor_type", "actor_id"], unique=False)
    op.create_index("ix_audit_log_bot_instance_id", "audit_log", ["bot_instance_id"], unique=False)
    op.create_index("ix_audit_log_created_at", "audit_log", ["created_at"], unique=False)
    op.create_index("ix_audit_log_license_key", "audit_log", ["license_key"], unique=False)
    op.create_index("ix_audit_log_product_bot_strategy", "audit_log", ["product_code", "bot_family", "strategy_code"], unique=False)
    op.create_index("ix_audit_log_target", "audit_log", ["target_type", "target_id"], unique=False)

    op.create_table(
        "admin_alerts",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("alert_type", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("license_id", sa.BigInteger(), nullable=True),
        sa.Column("bot_instance_id", sa.String(length=128), nullable=True),
        sa.Column("session_id", sa.String(length=128), nullable=True),
        sa.Column("product_code", sa.String(length=64), nullable=True),
        sa.Column("bot_family", sa.String(length=64), nullable=True),
        sa.Column("strategy_code", sa.String(length=64), nullable=True),
        sa.Column("summary", sa.String(length=255), nullable=False),
        sa.Column("details_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["bot_instance_id"], ["bot_instances.bot_instance_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["license_id"], ["licenses.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_admin_alerts_alert_type", "admin_alerts", ["alert_type"], unique=False)
    op.create_index("ix_admin_alerts_bot_instance_id", "admin_alerts", ["bot_instance_id"], unique=False)
    op.create_index("ix_admin_alerts_last_seen_at", "admin_alerts", ["last_seen_at"], unique=False)
    op.create_index("ix_admin_alerts_license_id", "admin_alerts", ["license_id"], unique=False)
    op.create_index("ix_admin_alerts_session_id", "admin_alerts", ["session_id"], unique=False)
    op.create_index("ix_admin_alerts_severity_status", "admin_alerts", ["severity", "status"], unique=False)

    op.create_table(
        "remote_commands",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("command_id", sa.String(length=128), nullable=False),
        sa.Column("license_id", sa.BigInteger(), nullable=False),
        sa.Column("bot_instance_id", sa.String(length=128), nullable=True),
        sa.Column("session_id", sa.String(length=128), nullable=True),
        sa.Column("product_code", sa.String(length=64), nullable=False),
        sa.Column("bot_family", sa.String(length=64), nullable=False),
        sa.Column("strategy_code", sa.String(length=64), nullable=False),
        sa.Column("command_type", sa.String(length=64), nullable=False),
        sa.Column("risk_class", sa.String(length=32), nullable=True),
        sa.Column("payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_by_admin_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["bot_instance_id"], ["bot_instances.bot_instance_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_admin_id"], ["admin_users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["license_id"], ["licenses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("command_id", name="uq_remote_commands_command_id"),
    )
    op.create_index("ix_remote_commands_bot_instance_id", "remote_commands", ["bot_instance_id"], unique=False)
    op.create_index("ix_remote_commands_command_id", "remote_commands", ["command_id"], unique=False)
    op.create_index("ix_remote_commands_created_at", "remote_commands", ["created_at"], unique=False)
    op.create_index("ix_remote_commands_expires_at", "remote_commands", ["expires_at"], unique=False)
    op.create_index("ix_remote_commands_license_id_status", "remote_commands", ["license_id", "status"], unique=False)
    op.create_index("ix_remote_commands_status", "remote_commands", ["status"], unique=False)

    op.create_table(
        "bot_heartbeats",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("bot_instance_id", sa.String(length=128), nullable=False),
        sa.Column("license_id", sa.BigInteger(), nullable=False),
        sa.Column("session_id", sa.String(length=128), nullable=True),
        sa.Column("product_code", sa.String(length=64), nullable=False),
        sa.Column("bot_family", sa.String(length=64), nullable=False),
        sa.Column("strategy_code", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column("warnings_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["bot_instance_id"], ["bot_instances.bot_instance_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["license_id"], ["licenses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_bot_heartbeats_bot_instance_id", "bot_heartbeats", ["bot_instance_id"], unique=False)
    op.create_index("ix_bot_heartbeats_license_id_received_at", "bot_heartbeats", ["license_id", "received_at"], unique=False)
    op.create_index("ix_bot_heartbeats_received_at", "bot_heartbeats", ["received_at"], unique=False)
    op.create_index("ix_bot_heartbeats_sent_at", "bot_heartbeats", ["sent_at"], unique=False)
    op.create_index("ix_bot_heartbeats_session_id", "bot_heartbeats", ["session_id"], unique=False)
    op.create_index("ix_bot_heartbeats_status", "bot_heartbeats", ["status"], unique=False)

    op.create_table(
        "bot_states",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("bot_instance_id", sa.String(length=128), nullable=False),
        sa.Column("license_id", sa.BigInteger(), nullable=False),
        sa.Column("session_id", sa.String(length=128), nullable=True),
        sa.Column("product_code", sa.String(length=64), nullable=False),
        sa.Column("bot_family", sa.String(length=64), nullable=False),
        sa.Column("strategy_code", sa.String(length=64), nullable=False),
        sa.Column("bot_status", sa.String(length=32), nullable=True),
        sa.Column("session_status", sa.String(length=32), nullable=True),
        sa.Column("connectivity_status", sa.String(length=32), nullable=True),
        sa.Column("grace_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_symbols_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("symbol_states_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("position_snapshots_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("open_orders_count", sa.Integer(), nullable=True),
        sa.Column("open_positions_count", sa.Integer(), nullable=True),
        sa.Column("equity_snapshot", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["bot_instance_id"], ["bot_instances.bot_instance_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["license_id"], ["licenses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_bot_states_bot_instance_id", "bot_states", ["bot_instance_id"], unique=False)
    op.create_index("ix_bot_states_bot_status", "bot_states", ["bot_status"], unique=False)
    op.create_index("ix_bot_states_license_id_received_at", "bot_states", ["license_id", "received_at"], unique=False)
    op.create_index("ix_bot_states_received_at", "bot_states", ["received_at"], unique=False)
    op.create_index("ix_bot_states_session_id", "bot_states", ["session_id"], unique=False)

    op.create_table(
        "command_results",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("command_id", sa.String(length=128), nullable=False),
        sa.Column("bot_instance_id", sa.String(length=128), nullable=False),
        sa.Column("result_status", sa.String(length=32), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("details_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["bot_instance_id"], ["bot_instances.bot_instance_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["command_id"], ["remote_commands.command_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_command_results_bot_instance_id", "command_results", ["bot_instance_id"], unique=False)
    op.create_index("ix_command_results_command_id", "command_results", ["command_id"], unique=False)
    op.create_index("ix_command_results_received_at", "command_results", ["received_at"], unique=False)
    op.create_index("ix_command_results_result_status", "command_results", ["result_status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_command_results_result_status", table_name="command_results")
    op.drop_index("ix_command_results_received_at", table_name="command_results")
    op.drop_index("ix_command_results_command_id", table_name="command_results")
    op.drop_index("ix_command_results_bot_instance_id", table_name="command_results")
    op.drop_table("command_results")

    op.drop_index("ix_bot_states_session_id", table_name="bot_states")
    op.drop_index("ix_bot_states_received_at", table_name="bot_states")
    op.drop_index("ix_bot_states_license_id_received_at", table_name="bot_states")
    op.drop_index("ix_bot_states_bot_status", table_name="bot_states")
    op.drop_index("ix_bot_states_bot_instance_id", table_name="bot_states")
    op.drop_table("bot_states")

    op.drop_index("ix_bot_heartbeats_status", table_name="bot_heartbeats")
    op.drop_index("ix_bot_heartbeats_session_id", table_name="bot_heartbeats")
    op.drop_index("ix_bot_heartbeats_sent_at", table_name="bot_heartbeats")
    op.drop_index("ix_bot_heartbeats_received_at", table_name="bot_heartbeats")
    op.drop_index("ix_bot_heartbeats_license_id_received_at", table_name="bot_heartbeats")
    op.drop_index("ix_bot_heartbeats_bot_instance_id", table_name="bot_heartbeats")
    op.drop_table("bot_heartbeats")

    op.drop_index("ix_remote_commands_status", table_name="remote_commands")
    op.drop_index("ix_remote_commands_license_id_status", table_name="remote_commands")
    op.drop_index("ix_remote_commands_expires_at", table_name="remote_commands")
    op.drop_index("ix_remote_commands_created_at", table_name="remote_commands")
    op.drop_index("ix_remote_commands_command_id", table_name="remote_commands")
    op.drop_index("ix_remote_commands_bot_instance_id", table_name="remote_commands")
    op.drop_table("remote_commands")

    op.drop_index("ix_admin_alerts_severity_status", table_name="admin_alerts")
    op.drop_index("ix_admin_alerts_session_id", table_name="admin_alerts")
    op.drop_index("ix_admin_alerts_license_id", table_name="admin_alerts")
    op.drop_index("ix_admin_alerts_last_seen_at", table_name="admin_alerts")
    op.drop_index("ix_admin_alerts_bot_instance_id", table_name="admin_alerts")
    op.drop_index("ix_admin_alerts_alert_type", table_name="admin_alerts")
    op.drop_table("admin_alerts")

    op.drop_index("ix_audit_log_target", table_name="audit_log")
    op.drop_index("ix_audit_log_product_bot_strategy", table_name="audit_log")
    op.drop_index("ix_audit_log_license_key", table_name="audit_log")
    op.drop_index("ix_audit_log_created_at", table_name="audit_log")
    op.drop_index("ix_audit_log_bot_instance_id", table_name="audit_log")
    op.drop_index("ix_audit_log_actor", table_name="audit_log")
    op.drop_table("audit_log")

    op.drop_index("ix_bot_instances_status", table_name="bot_instances")
    op.drop_index("ix_bot_instances_product_bot_strategy", table_name="bot_instances")
    op.drop_index("ix_bot_instances_machine_fingerprint", table_name="bot_instances")
    op.drop_index("ix_bot_instances_license_id_status", table_name="bot_instances")
    op.drop_index("ix_bot_instances_last_seen_at", table_name="bot_instances")
    op.drop_index("ix_bot_instances_bot_instance_id", table_name="bot_instances")
    op.drop_index("ix_bot_instances_authorized_until", table_name="bot_instances")
    op.drop_table("bot_instances")

    op.drop_index("ix_licenses_suspicious_flag", table_name="licenses")
    op.drop_index("ix_licenses_status", table_name="licenses")
    op.drop_index("ix_licenses_product_bot_strategy", table_name="licenses")
    op.drop_index("ix_licenses_license_key", table_name="licenses")
    op.drop_index("ix_licenses_expires_at", table_name="licenses")
    op.drop_table("licenses")
