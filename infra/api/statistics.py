from uuid import UUID

from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from core.errors import ForbiddenError
from infra.api.dependables import SystemServiceDependable
from infra.api.error_responses import create_forbidden_response

statistics_api = APIRouter(tags=["Statistics"])


class StatisticsResponse(BaseModel):
    total_transactions: int
    platform_profit: float


@statistics_api.get("/statistics", response_model=StatisticsResponse)
async def get_statistics(
    system_service: SystemServiceDependable,
    api_key: UUID = Header(..., alias="X_API-KEY"),
) -> StatisticsResponse | JSONResponse:
    try:
        statistics = system_service.get_statistics(api_key)
        return StatisticsResponse(
            total_transactions=int(statistics["total_transactions"]),
            platform_profit=statistics["platform_profit"],
        )

    except ForbiddenError as e:
        return create_forbidden_response(message=str(e))
