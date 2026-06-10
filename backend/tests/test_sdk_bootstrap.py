"""
Unit tests for SDK bootstrap segment-member inlining and SDK key auth fallback.
Plan: 11-06 — TDD for bootstrap_flags() members[] inlining + verify_sdk_secret sdk_key query fallback
Covers: SDK-05 (DB-free local membership checks), SDK-06 (sendBeacon auth fallback)

bootstrap_flags() tests mock list_flags()/get_flag_segments() with SimpleNamespace
objects — no real DB session required, mirroring test_feature_flags_eval.py's
DB-free pattern.

verify_sdk_secret tests call the dependency function directly with constructed
arguments — it's a plain async function, no FastAPI TestClient required.
"""
import json
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.domains.sdk.service import bootstrap_flags
from app.dependencies import verify_sdk_secret
from app.config import settings


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

def make_flag(name='my_flag', enabled=1, default_val=0, scope='global',
               product_id=None, environment='production', rules=None, id=1):
    return SimpleNamespace(
        id=id,
        name=name,
        enabled=enabled,
        default_val=default_val,
        scope=scope,
        product_id=product_id,
        environment=environment,
        rules=json.dumps(rules) if rules is not None else '[]',
    )


def make_segment(id, seg_type='manual', conditions=None, members=None):
    return SimpleNamespace(
        id=id,
        type=seg_type,
        conditions=json.dumps(conditions) if conditions is not None else None,
        members=json.dumps(members) if members is not None else None,
    )


# ---------------------------------------------------------------------------
# bootstrap_flags() — manual segment members[] inlining
# ---------------------------------------------------------------------------

class TestBootstrapFlagsMembers:

    @pytest.mark.asyncio
    async def test_manual_segment_inlines_members_array(self, monkeypatch):
        """A manual segment with members='["u1","u2"]' is inlined with members: ["u1","u2"]"""
        flag = make_flag(id=10)
        segment = make_segment(id=1, seg_type='manual', conditions=[], members=['u1', 'u2'])

        async def fake_list_flags(db, tenant_id=None):
            return [flag]

        async def fake_get_flag_segments(db, flag_id):
            return [segment]

        monkeypatch.setattr('app.domains.feature_flags.service.list_flags', fake_list_flags)
        monkeypatch.setattr('app.domains.feature_flags.service.get_flag_segments', fake_get_flag_segments)

        result = await bootstrap_flags(db=None, tenant_id='t1', product_id='p1', environment='production')

        assert result['my_flag']['segments'][0] == {
            "id": 1,
            "type": "manual",
            "conditions": [],
            "members": ["u1", "u2"],
        }

    @pytest.mark.asyncio
    async def test_rule_based_segment_has_empty_members(self, monkeypatch):
        """A rule_based segment (no members column data) returns members: [] (empty, not null/missing)"""
        flag = make_flag(id=11)
        segment = make_segment(id=2, seg_type='rule_based', conditions=[{'attribute': 'country', 'operator': 'equals', 'value': 'PE', 'result': True}], members=None)

        async def fake_list_flags(db, tenant_id=None):
            return [flag]

        async def fake_get_flag_segments(db, flag_id):
            return [segment]

        monkeypatch.setattr('app.domains.feature_flags.service.list_flags', fake_list_flags)
        monkeypatch.setattr('app.domains.feature_flags.service.get_flag_segments', fake_get_flag_segments)

        result = await bootstrap_flags(db=None, tenant_id='t1', product_id='p1', environment='production')

        seg = result['my_flag']['segments'][0]
        assert seg['type'] == 'rule_based'
        assert seg['members'] == []
        assert 'members' in seg


# ---------------------------------------------------------------------------
# verify_sdk_secret — header (existing) + sdk_key query-param fallback (new)
# ---------------------------------------------------------------------------

class TestVerifySdkSecret:

    @pytest.mark.asyncio
    async def test_valid_authorization_header_passes(self):
        """Valid Authorization: Bearer <key> header with NO query param → passes (existing behavior)"""
        await verify_sdk_secret(authorization=f"Bearer {settings.sdk_secret_key}", sdk_key=None)

    @pytest.mark.asyncio
    async def test_no_header_valid_sdk_key_query_param_passes(self):
        """No Authorization header but valid ?sdk_key=<key> query param → passes (new fallback)"""
        await verify_sdk_secret(authorization=None, sdk_key=settings.sdk_secret_key)

    @pytest.mark.asyncio
    async def test_neither_header_nor_query_param_raises_401(self):
        """Neither header nor query param → raises 401"""
        with pytest.raises(HTTPException) as exc_info:
            await verify_sdk_secret(authorization=None, sdk_key=None)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_sdk_key_query_param_raises_401(self):
        """Invalid sdk_key query param (no header) → raises 401"""
        with pytest.raises(HTTPException) as exc_info:
            await verify_sdk_secret(authorization=None, sdk_key="wrong-key")
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_authorization_header_raises_401(self):
        """Invalid Authorization header (existing behavior preserved) → raises 401"""
        with pytest.raises(HTTPException) as exc_info:
            await verify_sdk_secret(authorization="Bearer wrong-key", sdk_key=None)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_header_takes_precedence_over_query_param(self):
        """When both header and query param are present, header (valid) wins even if query param invalid"""
        await verify_sdk_secret(authorization=f"Bearer {settings.sdk_secret_key}", sdk_key="wrong-key")
