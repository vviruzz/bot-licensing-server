from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

class AuthorizationDecision(BaseModel):
    allowed: bool
    reason_code: str | None = None
    message: str
    authorized_until: datetime | None = None

class RegisterTimers(BaseModel):
    heartbeat_sec: int
    state_sync_sec: int
    command_poll_sec: int

class RegisterFlags(BaseModel):
    suspicious: bool = False
    license_recheck_required: bool = False

class BotRegisterRequest(BaseModel):
    license_key: str
    product_code: str
    bot_family: str
    strategy_code: str
    bot_instance_id: str
    machine_fingerprint: str
    fingerprint_version: str | None = None
    session_id: str | None = None
    protocol_version: str | int
    bot_version: str | None = None
    hostname: str | None = None
    platform: str | None = None

class BotRegisterResponse(BaseModel):
    ok: bool = True
    request_id: str
    server_time: datetime
    protocol_version: str
    license_status: str
    bot_status: str
    effective_mode: str
    authorization: AuthorizationDecision
    timers: RegisterTimers
    flags: RegisterFlags
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

class LicenseCheckRequest(BaseModel):
    license_key: str
    bot_instance_id: str
    product_code: str
    bot_family: str
    strategy_code: str
    protocol_version: str | int

class LicenseCheckResponse(BaseModel):
    ok: bool = True
    license_status: str
    effective_mode: str
    bot_status: str
    authorization: AuthorizationDecision
    detail: str

class BotHeartbeatRequest(BaseModel):
    license_key: str
    product_code: str
    bot_family: str
    strategy_code: str
    bot_instance_id: str
    session_id: str | None = None
    protocol_version: str | int
    status: str
    sent_at: datetime | None = None
    warnings: list[str] | None = None

class BotHeartbeatResponse(BaseModel):
    ok: bool = True
    bot_instance_id: str
    status: str
    connectivity_status: str

class BotStatePayload(BaseModel):
    bot_status: str | None = None
    session_status: str | None = None
    connectivity_status: str | None = None
    grace_until: datetime | None = None
    current_symbols: list[str] = Field(default_factory=list)
    open_orders_count: int | None = None
    open_positions_count: int | None = None
    equity_snapshot: Decimal | None = None

class SymbolState(BaseModel):
    model_config = ConfigDict(extra="allow")

class PositionSnapshot(BaseModel):
    model_config = ConfigDict(extra="allow")

class BotStateRequest(BaseModel):
    license_key: str
    product_code: str
    bot_family: str
    strategy_code: str
    bot_instance_id: str
    session_id: str | None = None
    protocol_version: str | int
    bot_state: BotStatePayload
    symbol_states: list[SymbolState] = Field(default_factory=list)
    position_snapshots: list[PositionSnapshot] = Field(default_factory=list)
    sent_at: datetime | None = None

class BotStateResponse(BaseModel):
    ok: bool = True
    bot_instance_id: str
    last_state_sync_at: datetime | None = None

class BotCommandsRequest(BaseModel):
    license_key: str
    product_code: str
    bot_family: str
    strategy_code: str
    bot_instance_id: str
    session_id: str | None = None
    protocol_version: str | int

class RemoteCommandPayload(BaseModel):
    command_id: str
    bot_instance_id: str | None = None
    session_id: str | None = None
    product_code: str
    bot_family: str
    strategy_code: str
    command_type: str
    risk_class: str | None = None
    payload: dict[str, Any] | list[Any] | None = None
    status: str
    reason: str | None = None
    created_at: datetime
    expires_at: datetime | None = None
    acknowledged_at: datetime | None = None
    completed_at: datetime | None = None

class BotCommandsResponse(BaseModel):
    ok: bool = True
    commands: list[RemoteCommandPayload] = Field(default_factory=list)

class CommandResultRequest(BaseModel):
    license_key: str
    product_code: str
    bot_family: str
    strategy_code: str
    bot_instance_id: str
    session_id: str | None = None
    protocol_version: str | int
    command_id: str
    command_type: str
    result_status: str
    message: str | None = None
    details: dict[str, Any] | list[Any] | None = None
    sent_at: datetime | None = None

class CommandResultResponse(BaseModel):
    ok: bool = True
    command_id: str
    status: str
