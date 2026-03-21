from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.dependencies.auth import require_bot_token
from app.schemas.licensing import BotCommandsRequest, BotCommandsResponse, BotHeartbeatRequest, BotHeartbeatResponse, BotRegisterRequest, BotRegisterResponse, BotStateRequest, BotStateResponse, CommandResultRequest, CommandResultResponse
from app.services import get_commands, record_command_result, record_heartbeat, record_state, register_bot

router = APIRouter(prefix="/bot", tags=["bot"])

@router.post("/register", response_model=BotRegisterResponse)
def register(payload: BotRegisterRequest, request: Request, _: str = Depends(require_bot_token), db_session: Session = Depends(get_db_session)) -> BotRegisterResponse:
    return BotRegisterResponse.model_validate(register_bot(db_session, payload, request.client.host if request.client else None))

@router.post("/heartbeat", response_model=BotHeartbeatResponse)
def heartbeat(payload: BotHeartbeatRequest, request: Request, _: str = Depends(require_bot_token), db_session: Session = Depends(get_db_session)) -> BotHeartbeatResponse:
    return BotHeartbeatResponse.model_validate(record_heartbeat(db_session, payload, request.client.host if request.client else None))

@router.post("/state", response_model=BotStateResponse)
def state(payload: BotStateRequest, _: str = Depends(require_bot_token), db_session: Session = Depends(get_db_session)) -> BotStateResponse:
    return BotStateResponse.model_validate(record_state(db_session, payload))

@router.get("/commands", response_model=BotCommandsResponse)
def commands(license_key: str, product_code: str, bot_family: str, strategy_code: str, bot_instance_id: str, session_id: str | None = None, protocol_version: str | int = "1.0", _: str = Depends(require_bot_token), db_session: Session = Depends(get_db_session)) -> BotCommandsResponse:
    payload = BotCommandsRequest(license_key=license_key, product_code=product_code, bot_family=bot_family, strategy_code=strategy_code, bot_instance_id=bot_instance_id, session_id=session_id, protocol_version=protocol_version)
    return BotCommandsResponse.model_validate(get_commands(db_session, payload))

@router.post("/command-result", response_model=CommandResultResponse)
def command_result(payload: CommandResultRequest, _: str = Depends(require_bot_token), db_session: Session = Depends(get_db_session)) -> CommandResultResponse:
    return CommandResultResponse.model_validate(record_command_result(db_session, payload))
