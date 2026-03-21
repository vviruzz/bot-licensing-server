import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    api_protocol_version: str = os.getenv("API_PROTOCOL_VERSION", "1.0")


settings = Settings()
