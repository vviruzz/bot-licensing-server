from datetime import datetime, timedelta, timezone

from fastapi import APIRouter

from app.schemas.bot import (
    AckResponse,
    CommandResultRequest,
    HeartbeatRequest,
    RegisterRequest,
    RegisterResponse,
    StateRequest,
)

router = APIRouter()


@router.post("/register", response_model=RegisterResponse)
def register_bot_instance(payload: RegisterRequest) -> RegisterResponse:
    now = datetime.now(timezone.utc)
    return RegisterResponse(
        ok=True,
        request_id="todo-request-id",
        server_time=now,
        protocol_version=payload.protocol_version,
        license_status="active",
        bot_status="online",
        effective_mode=payload.mode,
        authorization={
            "allowed": True,
            "reason_code": None,
            "message": "placeholder registration response",
            "authorized_until": now + timedelta(minutes=30),
        },
    )


@router.post("/heartbeat", response_model=AckResponse)
def post_heartbeat(_: HeartbeatRequest) -> AckResponse:
    return AckResponse(ok=True, message="heartbeat accepted")


@router.post("/state", response_model=AckResponse)
def post_state(_: StateRequest) -> AckResponse:
    return AckResponse(ok=True, message="state snapshot accepted")


@router.post("/commands/results", response_model=AckResponse)
def post_command_result(_: CommandResultRequest) -> AckResponse:
    return AckResponse(ok=True, message="command result accepted")
