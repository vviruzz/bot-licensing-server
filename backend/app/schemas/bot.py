from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import (
    AuthorizationInfo,
    BasicAckResponse,
    BotStatusEnum,
    CommandStatusEnum,
    CommandTypeEnum,
    LicenseStatusEnum,
    MachineBoundRequest,
    ModeEnum,
    ResponseEnvelope,
    SessionScopedRequest,
)


class RegisterRequest(MachineBoundRequest):
    fingerprint_version: str = Field(min_length=1, max_length=32)
    session_id: str = Field(min_length=1, max_length=128)
    bot_version: str = Field(min_length=1, max_length=64)
    hostname: str = Field(min_length=1, max_length=255)
    platform: str = Field(min_length=1, max_length=128)
    account_label: str = Field(min_length=1, max_length=128)
    subaccount_label: str | None = Field(default=None, max_length=128)
    mode: ModeEnum
    demo_mode: bool = False
    symbols: list[str] = Field(default_factory=list)


class TimersInfo(BaseModel):
    heartbeat_sec: int = 15
    state_sync_sec: int = 60
    command_poll_sec: int = 10


class FlagsInfo(BaseModel):
    suspicious: bool = False
    license_recheck_required: bool = False


class RegisterResponse(ResponseEnvelope):
    license_status: LicenseStatusEnum
    bot_status: BotStatusEnum
    effective_mode: ModeEnum
    authorization: AuthorizationInfo
    timers: TimersInfo
    flags: FlagsInfo


class HeartbeatRequest(SessionScopedRequest):
    status: BotStatusEnum
    account_label: str = Field(min_length=1, max_length=128)
    subaccount_label: str | None = Field(default=None, max_length=128)
    symbol: str | None = Field(default=None, max_length=64)
    sent_at: datetime


class HeartbeatResponse(ResponseEnvelope):
    license_status: LicenseStatusEnum
    bot_status: BotStatusEnum
    effective_mode: ModeEnum
    authorization: AuthorizationInfo
    message: str
    pending_commands: int = 0


class BotStatePayload(BaseModel):
    product_code: str = Field(min_length=1, max_length=64)
    bot_family: str = Field(min_length=1, max_length=64)
    strategy_code: str = Field(min_length=1, max_length=64)
    bot_status: BotStatusEnum
    session_status: str = Field(min_length=1, max_length=64)
    connectivity_status: str = Field(min_length=1, max_length=64)
    connectivity_mode: ModeEnum
    grace_until: datetime | None = None
    can_open_new_orders: bool
    can_manage_existing_orders: bool
    close_only_mode: bool
    current_symbols: list[str] = Field(default_factory=list)


class SymbolStatePayload(BaseModel):
    symbol: str = Field(min_length=1, max_length=64)
    symbol_status: str = Field(min_length=1, max_length=64)
    side_mode: str = Field(min_length=1, max_length=32)
    grid_enabled: bool
    open_orders_count: int = 0
    position_size_long: float | None = None
    position_size_short: float | None = None
    unrealized_pnl: float | None = None


class PositionSnapshotPayload(BaseModel):
    symbol: str = Field(min_length=1, max_length=64)
    position_idx: int
    side: str = Field(min_length=1, max_length=32)
    qty: float
    entry_price: float | None = None
    mark_price: float | None = None
    unrealized_pnl: float | None = None


class StateRequest(SessionScopedRequest):
    bot_state: BotStatePayload
    symbol_states: list[SymbolStatePayload] = Field(default_factory=list)
    position_snapshots: list[PositionSnapshotPayload] = Field(default_factory=list)
    sent_at: datetime


class StateResponse(BasicAckResponse):
    license_status: LicenseStatusEnum
    bot_status: BotStatusEnum
    effective_mode: ModeEnum


class CommandPayload(BaseModel):
    command_id: str
    product_code: str
    bot_family: str
    strategy_code: str
    command_type: CommandTypeEnum
    risk_class: str
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    expires_at: datetime | None = None
    reason: str | None = None
    requires_ack: bool = True


class CommandsResponse(ResponseEnvelope):
    commands: list[CommandPayload] = Field(default_factory=list)


class CommandResultRequest(SessionScopedRequest):
    command_id: str = Field(min_length=1, max_length=128)
    command_type: CommandTypeEnum
    result_status: CommandStatusEnum
    message: str = Field(min_length=1, max_length=512)
    details: dict[str, Any] = Field(default_factory=dict)
    sent_at: datetime


class LicenseCheckRequest(MachineBoundRequest):
    session_id: str | None = Field(default=None, max_length=128)
    bot_version: str | None = Field(default=None, max_length=64)
    mode: ModeEnum


class LicenseCheckResponse(ResponseEnvelope):
    license_status: LicenseStatusEnum
    bot_status: BotStatusEnum
    effective_mode: ModeEnum
    authorization: AuthorizationInfo
    flags: FlagsInfo
