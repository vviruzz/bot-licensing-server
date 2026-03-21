from typing import Literal

from pydantic import BaseModel

AppMode = Literal["off", "monitor", "enforce"]
LicenseStatus = Literal["active", "blocked", "revoked", "expired", "suspicious"]
BotStatus = Literal["online", "offline", "stale", "paused", "blocked", "stopping", "closing_positions"]
CommandType = Literal["pause", "resume", "stop", "close_positions"]


class ProductDimensions(BaseModel):
    product_code: str
    bot_family: str
    strategy_code: str


class AckResponse(BaseModel):
    ok: bool
    message: str
