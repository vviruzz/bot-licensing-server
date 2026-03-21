from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query

from app.dependencies.auth import require_bot_auth
from app.schemas.bot import (
    CommandResultRequest,
    CommandsResponse,
    CommandPayload,
    HeartbeatRequest,
    HeartbeatResponse,
    LicenseCheckRequest,
    LicenseCheckResponse,
    RegisterRequest,
    RegisterResponse,
    StateRequest,
    StateResponse,
)
from app.schemas.common import AuthorizationInfo, BotStatusEnum, CommandTypeEnum, LicenseStatusEnum, ModeEnum

router = APIRouter(prefix="/api/v1", tags=["bot"], dependencies=[Depends(require_bot_auth)])


@router.post("/bot/register", response_model=RegisterResponse)
def register_bot(payload: RegisterRequest) -> RegisterResponse:
    # TODO: persist/update bot_instance, trading_session, and machine_fingerprint records.
    return RegisterResponse(
        license_status=LicenseStatusEnum.ACTIVE,
        bot_status=BotStatusEnum.ONLINE,
        effective_mode=payload.mode,
        authorization=AuthorizationInfo(
            allowed=True,
            message="stub authorization granted",
            authorized_until=datetime.now(timezone.utc) + timedelta(minutes=30),
        ),
    )


@router.post("/bot/heartbeat", response_model=HeartbeatResponse)
def bot_heartbeat(payload: HeartbeatRequest) -> HeartbeatResponse:
    # TODO: update last_seen/last_heartbeat timestamps and fetch pending command counts from storage.
    return HeartbeatResponse(
        license_status=LicenseStatusEnum.ACTIVE,
        bot_status=payload.status,
        effective_mode=ModeEnum.MONITOR,
        authorization=AuthorizationInfo(allowed=True, message="heartbeat accepted"),
        message="heartbeat accepted",
        pending_commands=0,
    )


@router.post("/bot/state", response_model=StateResponse)
def bot_state(payload: StateRequest) -> StateResponse:
    # TODO: store bot_state, symbol_state, and position snapshot records.
    return StateResponse(
        message="state accepted",
        data={"symbol_count": len(payload.symbol_states), "position_count": len(payload.position_snapshots)},
        license_status=LicenseStatusEnum.ACTIVE,
        bot_status=payload.bot_state.bot_status,
        effective_mode=payload.bot_state.connectivity_mode,
    )


@router.get("/bot/commands", response_model=CommandsResponse)
def get_bot_commands(
    license_key: str = Query(min_length=3, max_length=128),
    product_code: str = Query(min_length=1, max_length=64),
    bot_family: str = Query(min_length=1, max_length=64),
    strategy_code: str = Query(min_length=1, max_length=64),
    bot_instance_id: str = Query(min_length=3, max_length=128),
    session_id: str = Query(min_length=1, max_length=128),
    protocol_version: str = Query(min_length=1, max_length=32),
) -> CommandsResponse:
    # TODO: query queued commands scoped to the bot/license/session target.
    del license_key, product_code, bot_family, strategy_code, bot_instance_id, session_id, protocol_version
    return CommandsResponse(commands=[])


@router.post("/bot/command-result", response_model=StateResponse)
def post_command_result(payload: CommandResultRequest) -> StateResponse:
    # TODO: persist remote command acknowledgements/results and update command status.
    return StateResponse(
        message="command result accepted",
        data={"command_id": payload.command_id, "result_status": payload.result_status},
        license_status=LicenseStatusEnum.ACTIVE,
        bot_status=BotStatusEnum.ONLINE,
        effective_mode=ModeEnum.MONITOR,
    )


@router.post("/license/check", response_model=LicenseCheckResponse)
def check_license(payload: LicenseCheckRequest) -> LicenseCheckResponse:
    # TODO: evaluate stored license policy, protocol compatibility, and machine-fingerprint risk rules.
    return LicenseCheckResponse(
        license_status=LicenseStatusEnum.ACTIVE,
        bot_status=BotStatusEnum.ONLINE,
        effective_mode=payload.mode,
        authorization=AuthorizationInfo(allowed=True, message="license check passed"),
        flags={"suspicious": False, "license_recheck_required": False},
    )
