from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db, verify_internal_secret
from .schemas import UserCreate, UserUpdate, UserResponse, UserEventResponse
from . import service

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(verify_internal_secret)],
)


@router.get("/", response_model=list[UserResponse])
async def list_users(
    x_user_tenant_id: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    return await service.list_users(tenant_id=x_user_tenant_id, db=db)


@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(
    payload: UserCreate,
    x_user_tenant_id: str = Header(...),
    x_user_sub: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    return await service.create_user(payload, tenant_id=x_user_tenant_id, actor_sub=x_user_sub, db=db)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    payload: UserUpdate,
    x_user_tenant_id: str = Header(...),
    x_user_sub: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    return await service.update_user(user_id, payload, tenant_id=x_user_tenant_id, actor_sub=x_user_sub, db=db)


@router.post("/{user_id}/disable", status_code=204)
async def disable_user(
    user_id: str,
    x_user_tenant_id: str = Header(...),
    x_user_sub: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    await service.set_enabled(user_id, enabled=False, tenant_id=x_user_tenant_id, actor_sub=x_user_sub, db=db)


@router.post("/{user_id}/enable", status_code=204)
async def enable_user(
    user_id: str,
    x_user_tenant_id: str = Header(...),
    x_user_sub: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    await service.set_enabled(user_id, enabled=True, tenant_id=x_user_tenant_id, actor_sub=x_user_sub, db=db)


@router.post("/{user_id}/reset-mfa", status_code=204)
async def reset_mfa(
    user_id: str,
    x_user_tenant_id: str = Header(...),
    x_user_sub: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    await service.reset_mfa(user_id, tenant_id=x_user_tenant_id, actor_sub=x_user_sub, db=db)


@router.get("/{user_id}/events", response_model=list[UserEventResponse])
async def list_user_events(
    user_id: str,
    x_user_tenant_id: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    return await service.list_user_events(user_id=user_id, db=db)
