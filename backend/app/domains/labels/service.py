import csv
import io
import json
from datetime import datetime
from typing import Optional
from sqlalchemy import select, delete as sa_delete, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from .models import Namespace, LocalizedLabel, MissingLabelReport
from .schemas import (
    NamespaceCreate, NamespaceUpdate, LabelCreate, LabelUpdate, LabelValueUpdate,
    MissingLabelReportCreate,
)

# ---------------------------------------------------------------------------
# In-memory cache for resolved label sets.
# Redis upgrade path: replace this dict's get/set/del operations with redis
# calls — public function signatures (resolve_labels, invalidate_namespace_cache)
# stay the same. No Redis client exists in this codebase (Pitfall 1).
# ---------------------------------------------------------------------------
_label_cache: dict[str, dict[str, str]] = {}


def _cache_key(tenant_id: str, company_id: Optional[str], product_id: Optional[str], namespace: str, locale: str) -> str:
    return f"{tenant_id}:{company_id or ''}:{product_id or ''}:{namespace}:{locale}"


async def _fetch_labels(db: AsyncSession, tenant_id: str, company_id: Optional[str], product_id: Optional[str], namespace: str, locale: str) -> dict[str, str]:
    stmt = select(LocalizedLabel).where(
        LocalizedLabel.tenant_id == tenant_id,
        LocalizedLabel.company_id == company_id,
        LocalizedLabel.product_id == product_id,
        LocalizedLabel.namespace == namespace,
        LocalizedLabel.locale == locale,
    ).order_by(LocalizedLabel.id)
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return {row.label_key: row.label_value for row in rows}


async def resolve_labels(db: AsyncSession, tenant_id: str, company_id: Optional[str], product_id: Optional[str], namespace: str, locale: str) -> dict[str, str]:
    """Override-by-proximity: Tenant -> Company -> Product. Results cached in-memory."""
    key = _cache_key(tenant_id, company_id, product_id, namespace, locale)
    if key in _label_cache:
        return _label_cache[key]

    tenant_labels = await _fetch_labels(db, tenant_id, None, None, namespace, locale)
    tenant_product_labels = await _fetch_labels(db, tenant_id, None, product_id, namespace, locale) if product_id else {}
    company_labels = await _fetch_labels(db, tenant_id, company_id, None, namespace, locale) if company_id else {}
    product_labels = await _fetch_labels(db, tenant_id, company_id, product_id, namespace, locale) if (company_id and product_id) else {}

    resolved = {**tenant_labels, **tenant_product_labels, **company_labels, **product_labels}
    _label_cache[key] = resolved
    return resolved


def invalidate_namespace_cache(tenant_id: str, namespace: Optional[str] = None) -> None:
    """Drop cached resolved sets for a tenant. namespace=None clears all namespaces for that tenant.
    Called after any CREATE/UPDATE/DELETE on localized_labels (LBL-04, LBL-07)."""
    prefix = f"{tenant_id}:"
    keys_to_remove = [
        k for k in _label_cache
        if k.startswith(prefix) and (namespace is None or k.split(':')[3] == namespace)
    ]
    for k in keys_to_remove:
        del _label_cache[k]


def clear_cache() -> None:
    """Test helper — clears the entire module-level cache."""
    _label_cache.clear()


# ---------------------------------------------------------------------------
# Namespace CRUD
# ---------------------------------------------------------------------------

async def list_namespaces(db: AsyncSession) -> list[Namespace]:
    result = await db.execute(select(Namespace).order_by(Namespace.id))
    return list(result.scalars().all())


async def get_namespace(db: AsyncSession, namespace_id: str) -> Optional[Namespace]:
    return await db.get(Namespace, namespace_id)


async def create_namespace(db: AsyncSession, payload: NamespaceCreate) -> Namespace:
    ns = Namespace(
        id=payload.id,
        tenant_id=payload.tenant_id,
        company_id=payload.company_id,
        product_id=payload.product_id,
        strategy=payload.strategy,
        description=payload.description,
    )
    db.add(ns)
    await db.commit()
    await db.refresh(ns)
    return ns


async def update_namespace(db: AsyncSession, namespace_id: str, payload: NamespaceUpdate) -> Optional[Namespace]:
    ns = await db.get(Namespace, namespace_id)
    if ns is None:
        return None
    update_data = payload.model_dump(exclude_unset=True)
    new_namespace_id = update_data.pop("id", None)

    if new_namespace_id and new_namespace_id != namespace_id:
        await db.execute(
            sa_update(LocalizedLabel)
            .where(LocalizedLabel.namespace == namespace_id)
            .values(namespace=new_namespace_id)
        )
        await db.execute(
            sa_update(MissingLabelReport)
            .where(MissingLabelReport.namespace == namespace_id)
            .values(namespace=new_namespace_id)
        )
        ns.id = new_namespace_id

    for field, value in update_data.items():
        setattr(ns, field, value)
    await db.commit()
    await db.refresh(ns)
    if new_namespace_id and new_namespace_id != namespace_id:
        clear_cache()
    return ns


async def delete_namespace(db: AsyncSession, namespace_id: str) -> bool:
    ns = await db.get(Namespace, namespace_id)
    if ns is None:
        return False
    await db.delete(ns)
    await db.commit()
    return True


# ---------------------------------------------------------------------------
# LocalizedLabel CRUD
# ---------------------------------------------------------------------------

async def list_labels(db: AsyncSession, *, tenant_id: str, company_id: Optional[str] = None, product_id: Optional[str] = None, namespace: Optional[str] = None) -> list[LocalizedLabel]:
    stmt = select(LocalizedLabel).where(LocalizedLabel.tenant_id == tenant_id)
    if namespace is not None:
        stmt = stmt.where(LocalizedLabel.namespace == namespace)
    # company_id/product_id filters are additive (not exclusive) — admin UI lists
    # ALL rows visible to the active workspace context (tenant + company + product level)
    if company_id is not None or product_id is not None:
        from sqlalchemy import or_, and_
        conditions = [and_(LocalizedLabel.company_id.is_(None), LocalizedLabel.product_id.is_(None))]
        if company_id is not None:
            conditions.append(and_(LocalizedLabel.company_id == company_id, LocalizedLabel.product_id.is_(None)))
        if product_id is not None:
            conditions.append(and_(LocalizedLabel.company_id == company_id, LocalizedLabel.product_id == product_id))
        stmt = stmt.where(or_(*conditions))
    result = await db.execute(stmt.order_by(LocalizedLabel.label_key, LocalizedLabel.locale))
    return list(result.scalars().all())


async def get_label(db: AsyncSession, label_id: int) -> Optional[LocalizedLabel]:
    return await db.get(LocalizedLabel, label_id)


async def create_label(db: AsyncSession, payload: LabelCreate) -> list[LocalizedLabel]:
    """Creates one LocalizedLabel row per locale in payload.values. Invalidates
    cache and clears any matching MissingLabelReport (PRD RF-06: alerts clean up
    automatically when the key is added)."""
    params_json = json.dumps(payload.params)
    created: list[LocalizedLabel] = []
    for locale, value in payload.values.items():
        row = LocalizedLabel(
            tenant_id=payload.tenant_id,
            company_id=payload.company_id,
            product_id=payload.product_id,
            namespace=payload.namespace,
            locale=locale,
            label_key=payload.label_key,
            label_value=value,
            label_type=payload.label_type,
            params=params_json,
            description=payload.description,
            version=1,
        )
        db.add(row)
        created.append(row)
    await db.commit()
    for row in created:
        await db.refresh(row)

    invalidate_namespace_cache(payload.tenant_id, payload.namespace)

    # Clear matching missing-label reports for this key (any locale)
    await db.execute(sa_delete(MissingLabelReport).where(
        MissingLabelReport.tenant_id == payload.tenant_id,
        MissingLabelReport.namespace == payload.namespace,
        MissingLabelReport.label_key == payload.label_key,
    ))
    await db.commit()

    return created


async def update_label(db: AsyncSession, label_id: int, payload: LabelUpdate) -> LocalizedLabel:
    """Full structure edit (PlatformAdmin/TenantAdmin/ProductManager only). Optimistic
    concurrency: raises 409 if payload.version != label.version (PRD §9.2 PI-02)."""
    label = await db.get(LocalizedLabel, label_id)
    if label is None:
        raise HTTPException(status_code=404, detail="Label not found")
    if label.version != payload.version:
        raise HTTPException(
            status_code=409,
            detail="La clave ha sido modificada por otro usuario. Por favor, recargue el editor para no perder los cambios.",
        )

    # Fetch all sibling locales for this key at the exact same context level
    stmt = select(LocalizedLabel).where(
        LocalizedLabel.tenant_id == label.tenant_id,
        LocalizedLabel.company_id == label.company_id,
        LocalizedLabel.product_id == label.product_id,
        LocalizedLabel.namespace == label.namespace,
        LocalizedLabel.label_key == label.label_key,
    )
    res = await db.execute(stmt)
    siblings = res.scalars().all()
    sibling_by_locale = {s.locale: s for s in siblings}

    new_version = label.version + 1

    # Update/create locales in payload.values
    if payload.values is not None:
        for loc, val in payload.values.items():
            if loc in sibling_by_locale:
                sibling_by_locale[loc].label_value = val
                sibling_by_locale[loc].version = new_version
            else:
                # Create missing locale row
                new_row = LocalizedLabel(
                    tenant_id=label.tenant_id,
                    company_id=label.company_id,
                    product_id=label.product_id,
                    namespace=label.namespace,
                    locale=loc,
                    label_key=label.label_key,
                    label_value=val,
                    label_type=payload.label_type or label.label_type,
                    params=json.dumps(payload.params) if payload.params is not None else label.params,
                    description=payload.description or label.description,
                    version=new_version,
                )
                db.add(new_row)

    # Update common structural attributes on all existing siblings
    for s in siblings:
        s.version = new_version
        if payload.label_type is not None:
            s.label_type = payload.label_type
        if payload.params is not None:
            s.params = json.dumps(payload.params)
        if payload.description is not None:
            s.description = payload.description

    await db.commit()
    await db.refresh(label)
    invalidate_namespace_cache(label.tenant_id, label.namespace)
    return label


async def update_label_value(db: AsyncSession, label_id: int, payload: LabelValueUpdate) -> LocalizedLabel:
    """Narrow value-only edit — UXWriter-allowed (Pitfall 3). Same optimistic
    concurrency check as update_label()."""
    label = await db.get(LocalizedLabel, label_id)
    if label is None:
        raise HTTPException(status_code=404, detail="Label not found")
    if label.locale != payload.locale:
        raise HTTPException(status_code=422, detail="locale mismatch for this label row")
    if label.version != payload.version:
        raise HTTPException(
            status_code=409,
            detail="La clave ha sido modificada por otro usuario. Por favor, recargue el editor para no perder los cambios.",
        )
    label.label_value = payload.label_value
    label.version += 1
    await db.commit()
    await db.refresh(label)
    invalidate_namespace_cache(label.tenant_id, label.namespace)
    return label


async def delete_label(db: AsyncSession, label_id: int) -> bool:
    label = await db.get(LocalizedLabel, label_id)
    if label is None:
        return False
    tenant_id, namespace = label.tenant_id, label.namespace
    await db.delete(label)
    await db.commit()
    invalidate_namespace_cache(tenant_id, namespace)
    return True


async def delete_label_override(db: AsyncSession, *, tenant_id: str, company_id: Optional[str], product_id: Optional[str], namespace: str, locale: str, label_key: str) -> bool:
    """RF-05 'Restaurar' action — deletes the override row at the active context
    level (company or product), forcing inheritance from the level above."""
    stmt = select(LocalizedLabel).where(
        LocalizedLabel.tenant_id == tenant_id,
        LocalizedLabel.company_id == company_id,
        LocalizedLabel.product_id == product_id,
        LocalizedLabel.namespace == namespace,
        LocalizedLabel.locale == locale,
        LocalizedLabel.label_key == label_key,
    )
    result = await db.execute(stmt)
    label = result.scalar_one_or_none()
    if label is None:
        return False
    await db.delete(label)
    await db.commit()
    invalidate_namespace_cache(tenant_id, namespace)
    return True


# ---------------------------------------------------------------------------
# Missing label reports (RF-06 diagnostics)
# ---------------------------------------------------------------------------

def _canonical_missing_label_key(namespace: str, label_key: str) -> str:
    prefix = f"{namespace}."
    if label_key.startswith(prefix):
        return label_key[len(prefix):]
    return label_key


async def report_missing_label(db: AsyncSession, payload: MissingLabelReportCreate) -> Optional[MissingLabelReport]:
    """Dedup via SELECT-then-UPDATE/INSERT on (tenant_id, namespace, label_key, locale).
    Increments hits and last_reported_at on repeat reports (Open Question 2)."""
    label_key = _canonical_missing_label_key(payload.namespace, payload.label_key)
    resolved = await resolve_labels(
        db,
        tenant_id=payload.tenant_id,
        company_id=payload.company_id,
        product_id=payload.product_id,
        namespace=payload.namespace,
        locale=payload.locale,
    )
    if label_key in resolved:
        await db.execute(sa_delete(MissingLabelReport).where(
            MissingLabelReport.tenant_id == payload.tenant_id,
            MissingLabelReport.company_id == payload.company_id,
            MissingLabelReport.product_id == payload.product_id,
            MissingLabelReport.namespace == payload.namespace,
            MissingLabelReport.label_key.in_([payload.label_key, label_key]),
            MissingLabelReport.locale == payload.locale,
        ))
        await db.commit()
        return None

    stmt = select(MissingLabelReport).where(
        MissingLabelReport.tenant_id == payload.tenant_id,
        MissingLabelReport.company_id == payload.company_id,
        MissingLabelReport.product_id == payload.product_id,
        MissingLabelReport.namespace == payload.namespace,
        MissingLabelReport.label_key == label_key,
        MissingLabelReport.locale == payload.locale,
    )
    result = await db.execute(stmt)
    report = result.scalar_one_or_none()
    if report is None:
        report = MissingLabelReport(
            tenant_id=payload.tenant_id,
            company_id=payload.company_id,
            product_id=payload.product_id,
            namespace=payload.namespace,
            label_key=label_key,
            locale=payload.locale,
            hits=1,
        )
        db.add(report)
    else:
        report.hits += 1
        report.last_reported_at = datetime.utcnow()
    await db.commit()
    await db.refresh(report)
    return report


async def list_missing_label_reports(db: AsyncSession, *, tenant_id: str) -> list[MissingLabelReport]:
    stmt = select(MissingLabelReport).where(MissingLabelReport.tenant_id == tenant_id).order_by(MissingLabelReport.hits.desc())
    result = await db.execute(stmt)
    rows = list(result.scalars().all())
    visible: list[MissingLabelReport] = []
    stale: list[MissingLabelReport] = []

    for row in rows:
        resolved = await resolve_labels(
            db,
            tenant_id=row.tenant_id,
            company_id=row.company_id,
            product_id=row.product_id,
            namespace=row.namespace,
            locale=row.locale,
        )
        if _canonical_missing_label_key(row.namespace, row.label_key) in resolved:
            stale.append(row)
        else:
            visible.append(row)

    for row in stale:
        await db.delete(row)
    if stale:
        await db.commit()

    return visible


# ---------------------------------------------------------------------------
# RF-07 export (JSON / CSV)
# ---------------------------------------------------------------------------

async def export_namespace_json(db: AsyncSession, *, tenant_id: str, company_id: Optional[str], product_id: Optional[str], namespace: str) -> dict:
    """RF-07 JSON export: resolved label values for both locales, SDK-bootstrap-like
    shape but nested per locale: {namespace: {label_key: {locale: value}}}."""
    es = await resolve_labels(db, tenant_id=tenant_id, company_id=company_id, product_id=product_id, namespace=namespace, locale='es_PE')
    en = await resolve_labels(db, tenant_id=tenant_id, company_id=company_id, product_id=product_id, namespace=namespace, locale='en_US')
    keys = set(es) | set(en)
    return {namespace: {k: {'es_PE': es.get(k, ''), 'en_US': en.get(k, '')} for k in sorted(keys)}}


async def _resolve_with_level(db: AsyncSession, *, tenant_id: str, company_id: Optional[str], product_id: Optional[str], namespace: str, locale: str) -> dict[str, tuple[str, str]]:
    """Like resolve_labels() but also returns which level ('tenant'|'company'|'product')
    contributed each key's value — used for the CSV 'level' column."""
    tenant_labels = await _fetch_labels(db, tenant_id, None, None, namespace, locale)
    tenant_product_labels = await _fetch_labels(db, tenant_id, None, product_id, namespace, locale) if product_id else {}
    company_labels = await _fetch_labels(db, tenant_id, company_id, None, namespace, locale) if company_id else {}
    product_labels = await _fetch_labels(db, tenant_id, company_id, product_id, namespace, locale) if (company_id and product_id) else {}

    result: dict[str, tuple[str, str]] = {}
    for k, v in tenant_labels.items():
        result[k] = (v, 'tenant')
    for k, v in tenant_product_labels.items():
        result[k] = (v, 'product')
    for k, v in company_labels.items():
        result[k] = (v, 'company')
    for k, v in product_labels.items():
        result[k] = (v, 'product')
    return result


async def export_namespace_csv(db: AsyncSession, *, tenant_id: str, company_id: Optional[str], product_id: Optional[str], namespace: str) -> str:
    """RF-07 CSV export via Python stdlib csv module (RFC 4180 quoting/escaping).
    'level' column reflects the most-specific level contributing the es_PE value."""
    es = await _resolve_with_level(db, tenant_id=tenant_id, company_id=company_id, product_id=product_id, namespace=namespace, locale='es_PE')
    en = await _resolve_with_level(db, tenant_id=tenant_id, company_id=company_id, product_id=product_id, namespace=namespace, locale='en_US')
    keys = sorted(set(es) | set(en))

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['namespace', 'label_key', 'es_PE', 'en_US', 'level'])
    for key in keys:
        es_value, es_level = es.get(key, ('', 'tenant'))
        en_value, _ = en.get(key, ('', 'tenant'))
        writer.writerow([namespace, key, es_value, en_value, es_level])
    return output.getvalue()
