from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.dependencies.auth import require_bot_token
from app.schemas.licensing import BotCommandsRequest, BotCommandsResponse, BotHeartbeatRequest, BotHeartbeatResponse, BotRegisterRequest, BotRegisterResponse, BotStateRequest, BotStateResponse, CommandResultRequest, CommandResultResponse
from app.services import get_commands, record_command_result, record_heartbeat, record_state, register_bot
from app.services.security import BotRequestMeta, enforce_bot_request_security

router = APIRouter(prefix="/bot", tags=["bot"])


@router.post("/register", response_model=BotRegisterResponse)
def register(payload: BotRegisterRequest, request: Request, _: str = Depends(require_bot_token), db_session: Session = Depends(get_db_session)) -> BotRegisterResponse:
    enforce_bot_request_security(
        request=request,
        db=db_session,
        meta=BotRequestMeta(
            endpoint_key="register",
            license_key=payload.license_key,
            bot_instance_id=payload.bot_instance_id,
            product_code=payload.product_code,
            bot_family=payload.bot_family,
            strategy_code=payload.strategy_code,
            protocol_version=payload.protocol_version,
            request_timestamp=payload.request_timestamp,
        ),
    )
    return BotRegisterResponse.model_validate(register_bot(db_session, payload, request.client.host if request.client else None))


@router.post("/heartbeat", response_model=BotHeartbeatResponse)
def heartbeat(payload: BotHeartbeatRequest, request: Request, _: str = Depends(require_bot_token), db_session: Session = Depends(get_db_session)) -> BotHeartbeatResponse:
    enforce_bot_request_security(
        request=request,
        db=db_session,
        meta=BotRequestMeta(
            endpoint_key="heartbeat",
            license_key=payload.license_key,
            bot_instance_id=payload.bot_instance_id,
            product_code=payload.product_code,
            bot_family=payload.bot_family,
            strategy_code=payload.strategy_code,
            protocol_version=payload.protocol_version,
            request_timestamp=payload.sent_at,
        ),
    )
    return BotHeartbeatResponse.model_validate(record_heartbeat(db_session, payload, request.client.host if request.client else None))


@router.post("/state", response_model=BotStateResponse)
def state(payload: BotStateRequest, request: Request, _: str = Depends(require_bot_token), db_session: Session = Depends(get_db_session)) -> BotStateResponse:
    enforce_bot_request_security(
        request=request,
        db=db_session,
        meta=BotRequestMeta(
            endpoint_key="state",
            license_key=payload.license_key,
            bot_instance_id=payload.bot_instance_id,
            product_code=payload.product_code,
            bot_family=payload.bot_family,
            strategy_code=payload.strategy_code,
            protocol_version=payload.protocol_version,
            request_timestamp=payload.sent_at,
        ),
    )
    return BotStateResponse.model_validate(record_state(db_session, payload))


@router.get("/commands", response_model=BotCommandsResponse)
def commands(
    request: Request,
    license_key: str,
    product_code: str,
    bot_family: str,
    strategy_code: str,
    bot_instance_id: str,
    session_id: str | None = None,
    protocol_version: str = Query(...),
    request_timestamp: datetime | None = None,
    _: str = Depends(require_bot_token),
    db_session: Session = Depends(get_db_session),
) -> BotCommandsResponse:
    payload = BotCommandsRequest(
        license_key=license_key,
        product_code=product_code,
        bot_family=bot_family,
        strategy_code=strategy_code,
        bot_instance_id=bot_instance_id,
        session_id=session_id,
        protocol_version=protocol_version,
        request_timestamp=request_timestamp,
    )
    enforce_bot_request_security(
        request=request,
        db=db_session,
        meta=BotRequestMeta(
            endpoint_key="commands",
            license_key=payload.license_key,
            bot_instance_id=payload.bot_instance_id,
            product_code=payload.product_code,
            bot_family=payload.bot_family,
            strategy_code=payload.strategy_code,
            protocol_version=payload.protocol_version,
            request_timestamp=payload.request_timestamp,
        ),
    )
    return BotCommandsResponse.model_validate(get_commands(db_session, payload))


@router.post("/command-result", response_model=CommandResultResponse)
def command_result(payload: CommandResultRequest, request: Request, _: str = Depends(require_bot_token), db_session: Session = Depends(get_db_session)) -> CommandResultResponse:
    enforce_bot_request_security(
        request=request,
        db=db_session,
        meta=BotRequestMeta(
            endpoint_key="command_result",
            license_key=payload.license_key,
            bot_instance_id=payload.bot_instance_id,
            product_code=payload.product_code,
            bot_family=payload.bot_family,
            strategy_code=payload.strategy_code,
            protocol_version=payload.protocol_version,
            request_timestamp=payload.sent_at,
        ),
    )
    return CommandResultResponse.model_validate(record_command_result(db_session, payload))
