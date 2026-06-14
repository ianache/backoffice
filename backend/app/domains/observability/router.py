from typing import Optional, Literal
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, verify_internal_secret
from app.domains.observability import service
from app.domains.observability.schemas import ServiceHealthListResponse, MetricsResponse, ServiceHealthResponse, ServiceMetrics

router = APIRouter(
    prefix="/observability",
    tags=["observability"],
    dependencies=[Depends(verify_internal_secret)],
)


@router.get("/health/services", response_model=ServiceHealthListResponse)
async def list_health_services(
    db: AsyncSession = Depends(get_db),
):
    samples = await service.list_current_status(db)
    return ServiceHealthListResponse(
        items=[ServiceHealthResponse.model_validate(s) for s in samples]
    )


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    range: Literal["24h", "7d", "30d"] = Query("24h"),
    tenant_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    # D-05: accepted-not-filtered, true per-tenant metrics arrive in Phase 18
    services = ["fastapi", "mysql", "bff", "keycloak", "ws_gateway"]
    items = []
    for s_name in services:
        aggregated = await service.aggregate_metrics(db, s_name, range)
        items.append(ServiceMetrics(**aggregated))
    
    return MetricsResponse(
        items=items,
        range=range,
    )
