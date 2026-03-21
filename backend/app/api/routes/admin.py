from fastapi import APIRouter, Query

from app.schemas.admin import BotInstanceSummary, LicenseSummary, ListBotInstancesResponse, ListLicensesResponse

router = APIRouter()


@router.get("/licenses", response_model=ListLicensesResponse)
def list_licenses(
    product_code: str | None = Query(default=None),
    bot_family: str | None = Query(default=None),
    strategy_code: str | None = Query(default=None),
) -> ListLicensesResponse:
    item = LicenseSummary(
        license_key="TODO-LICENSE",
        product_code=product_code or "grid",
        bot_family=bot_family or "grid",
        strategy_code=strategy_code or "grid_v1",
        status="active",
        mode="monitor",
    )
    return ListLicensesResponse(items=[item])


@router.get("/bot-instances", response_model=ListBotInstancesResponse)
def list_bot_instances(
    product_code: str | None = Query(default=None),
    bot_family: str | None = Query(default=None),
    strategy_code: str | None = Query(default=None),
) -> ListBotInstancesResponse:
    item = BotInstanceSummary(
        bot_instance_id="TODO-BOT-INSTANCE",
        license_key="TODO-LICENSE",
        product_code=product_code or "grid",
        bot_family=bot_family or "grid",
        strategy_code=strategy_code or "grid_v1",
        status="offline",
        server_effective_mode="monitor",
    )
    return ListBotInstancesResponse(items=[item])
