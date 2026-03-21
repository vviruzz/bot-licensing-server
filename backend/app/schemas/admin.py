from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

class AdminLicenseItem(BaseModel):
    license_key: str
    status: str
    effective_mode: str
    product_code: str
    bot_family: str
    strategy_code: str
    owner_label: str | None = None
    suspicious_flag: bool = False
    expires_at: datetime | None = None
    bot_count: int = 0

class AdminBotItem(BaseModel):
    bot_instance_id: str
    license_key: str | None = None
    product_code: str
    bot_family: str
    strategy_code: str
    status: str
    connectivity_status: str
    machine_fingerprint: str
    hostname: str | None = None
    bot_version: str | None = None
    protocol_version: int
    platform: str | None = None
    is_authorized: bool
    authorized_until: datetime | None = None
    last_seen_at: datetime | None = None
    last_state_sync_at: datetime | None = None

class AdminBotDetail(AdminBotItem):
    latest_state: dict[str, Any] | None = None
    recent_commands: list[dict[str, Any]] = Field(default_factory=list)

class AdminAlertItem(BaseModel):
    id: int
    alert_type: str
    severity: str
    status: str
    license_id: int | None = None
    bot_instance_id: str | None = None
    session_id: str | None = None
    summary: str
    details: dict[str, Any] | list[Any] | None = None
    first_seen_at: datetime
    last_seen_at: datetime
    resolved_at: datetime | None = None

class BlockLicenseRequest(BaseModel):
    license_key: str
    reason: str | None = None

class AdminCommandRequest(BaseModel):
    bot_instance_id: str
    reason: str | None = None

class AdminCommandResponse(BaseModel):
    ok: bool = True
    command_id: str | None = None
    status: str
    command_type: str | None = None
