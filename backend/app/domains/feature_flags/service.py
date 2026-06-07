import json
import re
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .models import FeatureFlag, Segment, FlagSegment
from .schemas import FlagCreate, FlagUpdate, SegmentCreate


# ---------------------------------------------------------------------------
# Evaluation Engine
# ---------------------------------------------------------------------------

SCOPE_PRIORITY = {
    'company': 4,
    'product': 3,
    'tenant': 2,
    'global': 1,
}

OPERATORS = {
    'equals':   lambda actual, expected: actual == expected,
    'in':       lambda actual, expected: actual in expected,
    'notIn':    lambda actual, expected: actual not in expected,
    'contains': lambda actual, expected: expected in str(actual),
    'regex':    lambda actual, expected: bool(re.match(expected, str(actual))),
}


def _evaluate_rule(rule: dict, user: dict) -> bool:
    """
    Evaluate a single rule against user attributes.
    Returns False on unknown operator, missing attribute, or any exception.
    """
    attr = rule.get('attribute', '')
    op = rule.get('operator', 'equals')
    val = rule.get('value')
    actual = user.get(attr)
    if actual is None:
        return False
    fn = OPERATORS.get(op)
    if fn is None:
        return False
    try:
        return bool(fn(actual, val))
    except Exception:
        return False


def evaluate_flag(flags: list, context: dict) -> bool:
    """
    Find the most-specific matching flag for the given context and evaluate it.

    Priority: company (4) > product (3) > tenant (2) > global (1).
    Returns bool(winner.default_val) if no rule matches.
    Returns False if no flag candidates exist or winner is disabled.
    """
    candidates = []
    for flag in flags:
        if flag.scope == 'global':
            candidates.append(flag)
        elif flag.scope == 'tenant' and flag.tenant_id == context.get('tenant_id'):
            candidates.append(flag)
        elif flag.scope == 'product' and flag.product_id == context.get('product_id'):
            candidates.append(flag)
        elif flag.scope == 'company' and flag.company_id == context.get('company_id'):
            candidates.append(flag)

    if not candidates:
        return False

    winner = max(candidates, key=lambda f: SCOPE_PRIORITY.get(f.scope, 0))

    if not winner.enabled:
        return False

    # Evaluate rules — first matching rule wins
    rules_raw = winner.rules
    rules = json.loads(rules_raw) if isinstance(rules_raw, str) and rules_raw else (rules_raw if isinstance(rules_raw, list) else [])
    user = context.get('user', {})
    for rule in rules:
        if _evaluate_rule(rule, user):
            return bool(rule.get('result', winner.default_val))

    return bool(winner.default_val)


# ---------------------------------------------------------------------------
# Feature Flag CRUD
# ---------------------------------------------------------------------------

async def list_flags(
    db: AsyncSession,
    scope_filter: Optional[list] = None,
    tenant_id: Optional[str] = None,
    q: Optional[str] = None,
) -> list[FeatureFlag]:
    stmt = select(FeatureFlag)
    if scope_filter:
        stmt = stmt.where(FeatureFlag.scope.in_(scope_filter))
    if tenant_id:
        # Tenant-scoped flags for this tenant + global flags
        stmt = stmt.where(
            (FeatureFlag.tenant_id == tenant_id) | (FeatureFlag.scope == 'global')
        )
    if q:
        stmt = stmt.where(FeatureFlag.name.ilike(f"%{q}%"))
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_flag(
    db: AsyncSession,
    payload: FlagCreate,
    actor_sub: str,
    tenant_id: Optional[str] = None,
) -> FeatureFlag:
    data = payload.model_dump()
    # Serialize list fields to JSON text
    data['rules'] = json.dumps([r if isinstance(r, dict) else r.model_dump() for r in (data.get('rules') or [])])
    data['tags'] = json.dumps(data.get('tags') or [])
    data['created_by'] = actor_sub
    # Convert bool to int for SmallInteger columns
    data['enabled'] = int(data['enabled'])
    data['default_val'] = int(data['default_val'])
    data['complex'] = int(data['complex'])
    flag = FeatureFlag(**data)
    db.add(flag)
    await db.commit()
    await db.refresh(flag)
    return flag


async def get_flag(db: AsyncSession, flag_id: int) -> Optional[FeatureFlag]:
    result = await db.execute(select(FeatureFlag).where(FeatureFlag.id == flag_id))
    return result.scalar_one_or_none()


async def update_flag(
    db: AsyncSession,
    flag_id: int,
    payload: FlagUpdate,
) -> Optional[FeatureFlag]:
    flag = await get_flag(db, flag_id)
    if not flag:
        return None
    update_data = payload.model_dump(exclude_unset=True)
    if 'rules' in update_data and update_data['rules'] is not None:
        update_data['rules'] = json.dumps([r if isinstance(r, dict) else r.model_dump() for r in update_data['rules']])
    if 'tags' in update_data and update_data['tags'] is not None:
        update_data['tags'] = json.dumps(update_data['tags'])
    if 'enabled' in update_data and isinstance(update_data['enabled'], bool):
        update_data['enabled'] = int(update_data['enabled'])
    if 'default_val' in update_data and isinstance(update_data['default_val'], bool):
        update_data['default_val'] = int(update_data['default_val'])
    if 'complex' in update_data and isinstance(update_data['complex'], bool):
        update_data['complex'] = int(update_data['complex'])
    for key, value in update_data.items():
        setattr(flag, key, value)
    await db.commit()
    await db.refresh(flag)
    return flag


async def delete_flag(db: AsyncSession, flag_id: int) -> bool:
    flag = await get_flag(db, flag_id)
    if not flag:
        return False
    await db.delete(flag)
    await db.commit()
    return True


async def set_enabled(db: AsyncSession, flag_id: int, enabled: bool) -> Optional[FeatureFlag]:
    flag = await get_flag(db, flag_id)
    if not flag:
        return None
    flag.enabled = int(enabled)
    await db.commit()
    await db.refresh(flag)
    return flag


# ---------------------------------------------------------------------------
# Segment CRUD
# ---------------------------------------------------------------------------

async def list_segments(
    db: AsyncSession,
    tenant_id: Optional[str] = None,
) -> list[Segment]:
    stmt = select(Segment)
    if tenant_id:
        stmt = stmt.where(
            (Segment.tenant_id == tenant_id) | (Segment.tenant_id == None)  # noqa: E711
        )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_segment(
    db: AsyncSession,
    payload: SegmentCreate,
) -> Segment:
    data = payload.model_dump()
    data['members'] = json.dumps(data.get('members') or [])
    segment = Segment(**data)
    db.add(segment)
    await db.commit()
    await db.refresh(segment)
    return segment


async def get_segment(db: AsyncSession, segment_id: int) -> Optional[Segment]:
    result = await db.execute(select(Segment).where(Segment.id == segment_id))
    return result.scalar_one_or_none()


async def delete_segment(db: AsyncSession, segment_id: int) -> bool:
    segment = await get_segment(db, segment_id)
    if not segment:
        return False
    await db.delete(segment)
    await db.commit()
    return True


# ---------------------------------------------------------------------------
# Flag-Segment Association
# ---------------------------------------------------------------------------

async def add_segment_to_flag(
    db: AsyncSession,
    flag_id: int,
    segment_id: int,
) -> Optional[Segment]:
    """Link a segment to a flag via the flag_segments join table.

    Returns the Segment object on success (idempotent — returns it even if already linked).
    Returns None if flag or segment does not exist.
    """
    flag = await get_flag(db, flag_id)
    segment = await get_segment(db, segment_id)
    if not flag or not segment:
        return None
    # Check for existing link to avoid duplicate PK conflict
    existing = await db.execute(
        select(FlagSegment).where(
            FlagSegment.flag_id == flag_id,
            FlagSegment.segment_id == segment_id,
        )
    )
    if existing.scalar_one_or_none():
        return segment  # Already linked — idempotent
    link = FlagSegment(flag_id=flag_id, segment_id=segment_id)
    db.add(link)
    await db.commit()
    return segment


async def get_flag_segments(
    db: AsyncSession,
    flag_id: int,
) -> list[Segment]:
    """Return all segments linked to the given flag."""
    stmt = (
        select(Segment)
        .join(FlagSegment, FlagSegment.segment_id == Segment.id)
        .where(FlagSegment.flag_id == flag_id)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
