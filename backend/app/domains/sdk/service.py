import json
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert


def _flag_matches_target(f, tenant_id, product_id) -> bool:
    """Per-scope dispatch: does this flag's target match the requesting SDK client?

    - 'global'  -> always matches
    - 'tenant'  -> flag.tenant_id must be set and equal the requesting tenant_id
    - 'product' -> flag.product_id must be set and equal the requesting product_id
    - 'company' -> company target is per-user context (checked by evaluate_flag),
                   NOT per-SDK-client; include in bootstrap unless the flag also
                   carries a tenant_id that mismatches the requesting tenant
    - unknown scope -> excluded
    """
    scope = getattr(f, 'scope', None)
    f_tenant_id = getattr(f, 'tenant_id', None)
    f_product_id = getattr(f, 'product_id', None)

    if scope == 'global':
        return True
    if scope == 'tenant':
        return f_tenant_id is not None and str(f_tenant_id) == str(tenant_id)
    if scope == 'product':
        return f_product_id is not None and f_product_id == product_id
    if scope == 'company':
        return f_tenant_id is None or str(f_tenant_id) == str(tenant_id)
    return False


async def bootstrap_flags(
    db: AsyncSession,
    tenant_id: str,
    product_id: str,
    environment: str,
) -> dict:
    """Assemble SDK bootstrap payload. Does NOT modify list_flags() or get_flag_segments()."""
    from app.domains.feature_flags.service import list_flags, get_flag_segments

    # Fetch unfiltered: list_flags(tenant_id=...) keeps only tenant-scoped + global
    # flags, which starves product-scoped flags (tenant_id NULL) out of the payload
    flags = await list_flags(db)
    # Post-filter by scope/target/environment via per-scope dispatch (list_flags
    # has no such params)
    flags = [
        f for f in flags
        if f.environment == environment
        and _flag_matches_target(f, tenant_id, product_id)
    ]

    result = {}
    for flag in flags:
        segments_raw = await get_flag_segments(db, flag.id)
        inlined_segments = []
        for seg in segments_raw:
            seg_type = getattr(seg, 'type', None) or 'manual'
            conditions_raw = getattr(seg, 'conditions', None)
            conditions = json.loads(conditions_raw) if conditions_raw else []
            members_raw = getattr(seg, 'members', None)
            members = json.loads(members_raw) if members_raw else []
            inlined_segments.append({
                "id": seg.id,
                "type": seg_type,
                "conditions": conditions,
                "members": members,
            })
        rules_raw = flag.rules
        rules = json.loads(rules_raw) if isinstance(rules_raw, str) and rules_raw else []
        result[flag.name] = {
            "enabled": bool(flag.enabled),
            "rules": rules,
            "segments": inlined_segments,
            "default_val": bool(flag.default_val) if hasattr(flag, 'default_val') else False,
            "rule_combination_mode": getattr(flag, 'rule_combination_mode', None) or 'first_match',
            "scope": flag.scope,
            "tenant_id": getattr(flag, 'tenant_id', None),
            "product_id": getattr(flag, 'product_id', None),
            "company_id": getattr(flag, 'company_id', None),
        }
    return result


async def resolve_segment_members(
    db: AsyncSession,
    flag_ids: list[int],
    user: dict,
) -> dict:
    """Returns {flag_id (int): [user_id]} for flags where user qualifies via any linked segment.
    Key is flag_id (int), NOT segment_id — evaluate_flag() expects this format."""
    from app.domains.feature_flags.service import get_flag_segments, _evaluate_rule

    segment_members: dict[int, list[str]] = {}
    user_id = user.get('id') or user.get('sub') or user.get('user_id')
    if not user_id:
        return segment_members

    for flag_id in flag_ids:
        segments = await get_flag_segments(db, flag_id)
        for seg in segments:
            seg_type = getattr(seg, 'type', None) or 'manual'
            if seg_type == 'manual':
                members_raw = getattr(seg, 'members', None)
                members = json.loads(members_raw) if isinstance(members_raw, str) and members_raw else []
                if user_id in members:
                    segment_members.setdefault(flag_id, []).append(user_id)
            elif seg_type == 'rule_based':
                conditions_raw = getattr(seg, 'conditions', None)
                conditions = json.loads(conditions_raw) if conditions_raw else []
                if any(_evaluate_rule(c, user) for c in conditions):
                    segment_members.setdefault(flag_id, []).append(user_id)
    return segment_members


async def bulk_insert_events(
    db: AsyncSession,
    events: list[dict],
    tenant_id: str,
    product_id: Optional[str],
) -> tuple[int, int]:
    """Single INSERT statement for all valid events. Returns (inserted, skipped).
    NEVER use db.add() in a loop — avoids N+1 write problem."""
    from app.domains.feature_flags.models import EvalEvent

    rows = []
    skipped = 0
    for ev in events:
        try:
            # Validate required fields are present and non-None
            if not ev.get('flag_key') or not ev.get('user_id') or ev.get('result') is None or not ev.get('evaluated_at'):
                skipped += 1
                continue
            evaluated_at_str = ev['evaluated_at'].replace('Z', '+00:00')
            rows.append({
                'flag_key': ev['flag_key'],
                'user_id': ev['user_id'],
                'result': int(bool(ev['result'])),
                'evaluated_at': datetime.fromisoformat(evaluated_at_str),
                'tenant_id': tenant_id,
                'product_id': product_id,
            })
        except (KeyError, ValueError):
            skipped += 1
    if rows:
        await db.execute(insert(EvalEvent).values(rows))
        await db.commit()
    return len(rows), skipped
