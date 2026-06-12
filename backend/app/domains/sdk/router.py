from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import verify_sdk_secret, get_db
from .schemas import EvaluateRequest, EvaluateResponse, EvalEventBatch, EvalEventResponse
from . import service

router = APIRouter(
    prefix="/api/v1/sdk",
    tags=["sdk"],
    dependencies=[Depends(verify_sdk_secret)],
)


@router.get("/bootstrap")
async def bootstrap(
    tenant_id: str = Query(...),
    product_id: str = Query(...),
    environment: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Returns consolidated flag snapshot for SDK local evaluation."""
    return await service.bootstrap_flags(db, tenant_id=tenant_id, product_id=product_id, environment=environment)


@router.post("/evaluate", response_model=EvaluateResponse)
async def evaluate(
    payload: EvaluateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Remote flag evaluation. Pre-resolves rule_based segment membership before calling evaluate_flag()."""
    from app.domains.feature_flags.service import list_flags, evaluate_flag

    # Fetch unfiltered: list_flags(tenant_id=...) keeps only tenant-scoped (matching
    # tenant_id) + global flags, which excludes product/company-scoped flags whose
    # tenant_id is NULL. evaluate_flag() already does per-scope candidate matching
    # (company_id/product_id/tenant_id) against `context`, so filtering here would
    # incorrectly starve those flags before evaluate_flag() ever sees them.
    flags = await list_flags(db)
    target_flags = [f for f in flags if f.name == payload.flag_key]
    flag_ids = [f.id for f in target_flags]

    segment_members = await service.resolve_segment_members(db, flag_ids, payload.user)
    context = {**payload.user, 'segment_members': segment_members}
    result = evaluate_flag(target_flags, context)

    return EvaluateResponse(flag_key=payload.flag_key, result=result)


@router.post("/eval-events", response_model=EvalEventResponse)
async def ingest_eval_events(
    payload: EvalEventBatch,
    db: AsyncSession = Depends(get_db),
):
    """Batch telemetry ingestion. Uses single INSERT statement — no N+1 writes."""
    # tenant_id and product_id come from the SDK auth context
    # For Phase 8, derive from payload.product_id since auth is a shared secret (not per-tenant)
    # TODO Phase 11: derive tenant_id from per-tenant SDK key when per-tenant keys are implemented
    events_dicts = [e.model_dump() for e in payload.events]
    inserted, skipped = await service.bulk_insert_events(
        db,
        events=events_dicts,
        tenant_id='unknown',      # Phase 8: shared secret has no tenant context
        product_id=payload.product_id,
    )
    return EvalEventResponse(inserted=inserted, skipped=skipped)
