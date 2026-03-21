from pydantic import BaseModel

from app.schemas.common import AppMode, BotStatus, LicenseStatus, ProductDimensions


class LicenseSummary(ProductDimensions):
    license_key: str
    status: LicenseStatus
    mode: AppMode


class BotInstanceSummary(ProductDimensions):
    bot_instance_id: str
    license_key: str
    status: BotStatus
    server_effective_mode: AppMode


class ListLicensesResponse(BaseModel):
    items: list[LicenseSummary]


class ListBotInstancesResponse(BaseModel):
    items: list[BotInstanceSummary]
