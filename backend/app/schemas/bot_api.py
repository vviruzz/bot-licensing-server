from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import (
    ApiResponseEnvelope,
    AuthorizationDecision,
    BotStatusEnum,
    CommandPayload,
    CommandStatusEnum,
    DecisionFlags,
    LicenseStatusEnum,
    ModeEnum,
    PollingTimers,
)


class BotContractRequest(BaseModel):
    license_key: str
    product_code: str
    bot_family: str
    strategy_code: str
    bot_instance_id: str
    protocol_version: str
    session_id: str | None = None


class BotRegisterRequest(BotContractRequest):
    machine_fingerprint: str
    fingerprint_version: str | None = None
    bot_version: str | None = None
    hostname: str | None = None
    platform: str | None = None
    mode: ModeEnum | None = None
    account_label: str | None = None
    subaccount_label: str | None = None
    demo_mode: bool = False
    symbols: list[str] = Field(default_factory=list)


class BotRegisterResponse(ApiResponseEnvelope):
    license_status: LicenseStatusEnum
    bot_status: BotStatusEnum
    effective_mode: ModeEnum
    authorization: AuthorizationDecision
    timers: PollingTimers = Field(default_factory=PollingTimers)
    flags: DecisionFlags = Field(default_factory=DecisionFlags)


class BotHeartbeatRequest(BotContractRequest):
    status: BotStatusEnum
    account_label: str | None = None
    subaccount_label: str | None = None
    symbol: str | None = None
    sent_at: datetime | None = None


class BotHeartbeatResponse(ApiResponseEnvelope):
    license_status: LicenseStatusEnum
    bot_status: BotStatusEnum
    effective_mode: ModeEnum
    authorization: AuthorizationDecision
    flags: DecisionFlags = Field(default_factory=DecisionFlags)


class BotStateSnapshot(BaseModel):
    product_code: str
    bot_family: str
    strategy_code: str
    bot_status: BotStatusEnum
    session_status: str | None = None
    connectivity_status: str | None = None
    connectivity_mode: ModeEnum | None = None
    grace_until: datetime | None = None
    can_open_new_orders: bool | None = None
    can_manage_existing_orders: bool | None = None
    close_only_mode: bool | None = None
    current_symbols: list[str] = Field(default_factory=list)


class SymbolStateSnapshot(BaseModel):
    symbol: str
    symbol_status: str | None = None
    side_mode: str | None = None
    grid_enabled: bool | None = None
    open_orders_count: int | None = None
    position_size_long: Decimal | None = None
    position_size_short: Decimal | None = None
    unrealized_pnl: Decimal | None = None


class PositionSnapshot(BaseModel):
    symbol: str
    position_idx: int | None = None
    side: str | None = None
    qty: Decimal | None = None
    entry_price: Decimal | None = None
    mark_price: Decimal | None = None
    unrealized_pnl: Decimal | None = None


class BotStateRequest(BotContractRequest):
    bot_state: BotStateSnapshot
    symbol_states: list[SymbolStateSnapshot] = Field(default_factory=list)
    position_snapshots: list[PositionSnapshot] = Field(default_factory=list)
    sent_at: datetime | None = None


class BotStateResponse(ApiResponseEnvelope):
    accepted: bool = True
    bot_status: BotStatusEnum
    effective_mode: ModeEnum


class BotCommandsResponse(ApiResponseEnvelope):
    bot_status: BotStatusEnum
    commands: list[CommandPayload] = Field(default_factory=list)


class CommandResultRequest(BotContractRequest):
    command_id: str
    command_type: str
    result_status: CommandStatusEnum
    message: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    sent_at: datetime | None = None


class CommandResultResponse(ApiResponseEnvelope):
    accepted: bool = True
    command_id: str
    command_status: CommandStatusEnum


class LicenseCheckRequest(BotContractRequest):
    machine_fingerprint: str | None = None


class LicenseCheckResponse(ApiResponseEnvelope):
    license_status: LicenseStatusEnum
    effective_mode: ModeEnum
    bot_status: BotStatusEnum
    authorization: AuthorizationDecision
    flags: DecisionFlags = Field(default_factory=DecisionFlags)
