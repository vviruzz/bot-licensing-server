from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import AckResponse, AppMode, BotStatus, CommandType, LicenseStatus, ProductDimensions


class Authorization(BaseModel):
    allowed: bool
    reason_code: str | None
    message: str
    authorized_until: datetime | None = None


class RegisterRequest(ProductDimensions):
    license_key: str
    bot_instance_id: str
    machine_fingerprint: str
    fingerprint_version: str
    session_id: str | None = None
    protocol_version: str
    bot_version: str
    hostname: str
    platform: str
    account_label: str | None = None
    subaccount_label: str | None = None
    mode: AppMode
    demo_mode: bool = False
    symbols: list[str] = Field(default_factory=list)


class RegisterResponse(BaseModel):
    ok: bool
    request_id: str
    server_time: datetime
    protocol_version: str
    license_status: LicenseStatus
    bot_status: BotStatus
    effective_mode: AppMode
    authorization: Authorization


class HeartbeatRequest(ProductDimensions):
    license_key: str
    bot_instance_id: str
    session_id: str | None = None
    protocol_version: str
    status: BotStatus
    account_label: str | None = None
    subaccount_label: str | None = None
    symbol: str | None = None
    sent_at: datetime


class BotState(ProductDimensions):
    bot_status: BotStatus
    session_status: str
    connectivity_status: str
    connectivity_mode: AppMode
    grace_until: datetime | None = None
    can_open_new_orders: bool
    can_manage_existing_orders: bool
    close_only_mode: bool
    current_symbols: list[str]


class SymbolState(BaseModel):
    symbol: str
    symbol_status: str
    side_mode: str
    grid_enabled: bool
    open_orders_count: int
    position_size_long: float
    position_size_short: float
    unrealized_pnl: float


class PositionSnapshot(BaseModel):
    symbol: str
    position_idx: int
    side: str
    qty: float
    entry_price: float
    mark_price: float
    unrealized_pnl: float


class StateRequest(ProductDimensions):
    license_key: str
    bot_instance_id: str
    session_id: str | None = None
    protocol_version: str
    bot_state: BotState
    symbol_states: list[SymbolState]
    position_snapshots: list[PositionSnapshot]
    sent_at: datetime


class CommandResultRequest(ProductDimensions):
    license_key: str
    bot_instance_id: str
    session_id: str | None = None
    protocol_version: str
    command_id: str
    command_type: CommandType
    result_status: str
    message: str
    details: dict[str, Any]
    sent_at: datetime


__all__ = [
    "AckResponse",
    "Authorization",
    "BotState",
    "CommandResultRequest",
    "HeartbeatRequest",
    "PositionSnapshot",
    "RegisterRequest",
    "RegisterResponse",
    "StateRequest",
    "SymbolState",
]
