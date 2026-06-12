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
               product_id=None, environment='production', rules=None, id=1,
               tenant_id=None, company_id=None, rule_combination_mode=None):
    return SimpleNamespace(
        id=id,
        name=name,
        enabled=enabled,
        default_val=default_val,
        scope=scope,
        tenant_id=tenant_id,
        product_id=product_id,
        company_id=company_id,
        environment=environment,
        rules=json.dumps(rules) if rules is not None else '[]',
        rule_combination_mode=rule_combination_mode,
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


# ---------------------------------------------------------------------------
# bootstrap_flags() — per-scope target filtering (TGT-03)
# ---------------------------------------------------------------------------

class TestBootstrapTargetFiltering:

    async def _bootstrap(self, monkeypatch, flags, tenant_id='t1', product_id='p1', environment='production'):
        async def fake_list_flags(db, tenant_id=None):
            return flags

        async def fake_get_flag_segments(db, flag_id):
            return []

        monkeypatch.setattr('app.domains.feature_flags.service.list_flags', fake_list_flags)
        monkeypatch.setattr('app.domains.feature_flags.service.get_flag_segments', fake_get_flag_segments)

        return await bootstrap_flags(db=None, tenant_id=tenant_id, product_id=product_id, environment=environment)

    @pytest.mark.asyncio
    async def test_global_flag_included(self, monkeypatch):
        flag = make_flag(name='global_flag', scope='global')
        result = await self._bootstrap(monkeypatch, [flag], tenant_id='t1', product_id='p1')
        assert 'global_flag' in result

    @pytest.mark.asyncio
    async def test_tenant_scope_matching_tenant_included(self, monkeypatch):
        flag = make_flag(name='tenant_flag', scope='tenant', tenant_id='t1')
        result = await self._bootstrap(monkeypatch, [flag], tenant_id='t1', product_id='p1')
        assert 'tenant_flag' in result

    @pytest.mark.asyncio
    async def test_tenant_scope_mismatched_tenant_excluded(self, monkeypatch):
        flag = make_flag(name='tenant_flag', scope='tenant', tenant_id='t1')
        result = await self._bootstrap(monkeypatch, [flag], tenant_id='t2', product_id='p1')
        assert 'tenant_flag' not in result

    @pytest.mark.asyncio
    async def test_product_scope_matching_product_included(self, monkeypatch):
        flag = make_flag(name='product_flag', scope='product', product_id='p1')
        result = await self._bootstrap(monkeypatch, [flag], tenant_id='t1', product_id='p1')
        assert 'product_flag' in result

    @pytest.mark.asyncio
    async def test_product_scope_mismatched_product_excluded(self, monkeypatch):
        flag = make_flag(name='product_flag', scope='product', product_id='p1')
        result = await self._bootstrap(monkeypatch, [flag], tenant_id='t1', product_id='p2')
        assert 'product_flag' not in result

    @pytest.mark.asyncio
    async def test_product_scope_legacy_no_target_excluded(self, monkeypatch):
        """Legacy product-scoped flag with product_id=None is excluded (same as current behavior)."""
        flag = make_flag(name='product_flag', scope='product', product_id=None)
        result = await self._bootstrap(monkeypatch, [flag], tenant_id='t1', product_id='p1')
        assert 'product_flag' not in result

    @pytest.mark.asyncio
    async def test_company_scope_with_no_tenant_included(self, monkeypatch):
        """Company-scoped flag with tenant_id=None is included (the company-scope gap fix)."""
        flag = make_flag(name='company_flag', scope='company', company_id='acme', tenant_id=None)
        result = await self._bootstrap(monkeypatch, [flag], tenant_id='t1', product_id='p1')
        assert 'company_flag' in result

    @pytest.mark.asyncio
    async def test_company_scope_with_mismatched_tenant_excluded(self, monkeypatch):
        flag = make_flag(name='company_flag', scope='company', company_id='acme', tenant_id='t1')
        result = await self._bootstrap(monkeypatch, [flag], tenant_id='t2', product_id='p1')
        assert 'company_flag' not in result

    @pytest.mark.asyncio
    async def test_entries_contain_target_fields(self, monkeypatch):
        flag = make_flag(name='my_flag', scope='company', company_id='acme', tenant_id=None, product_id='p1')
        result = await self._bootstrap(monkeypatch, [flag], tenant_id='t1', product_id='p1')
        entry = result['my_flag']
        assert entry['tenant_id'] is None
        assert entry['product_id'] == 'p1'
        assert entry['company_id'] == 'acme'

    @pytest.mark.asyncio
    async def test_environment_mismatch_excluded(self, monkeypatch):
        flag = make_flag(name='staging_flag', scope='global', environment='staging')
        result = await self._bootstrap(monkeypatch, [flag], tenant_id='t1', product_id='p1', environment='production')
        assert 'staging_flag' not in result


# ---------------------------------------------------------------------------
# AND-02: bootstrap entries expose rule_combination_mode
# ---------------------------------------------------------------------------

class TestBootstrapRuleCombinationMode:

    async def _bootstrap(self, monkeypatch, flags, tenant_id='t1', product_id='p1', environment='production'):
        async def fake_list_flags(db, tenant_id=None):
            return flags

        async def fake_get_flag_segments(db, flag_id):
            return []

        monkeypatch.setattr('app.domains.feature_flags.service.list_flags', fake_list_flags)
        monkeypatch.setattr('app.domains.feature_flags.service.get_flag_segments', fake_get_flag_segments)

        return await bootstrap_flags(db=None, tenant_id=tenant_id, product_id=product_id, environment=environment)

    @pytest.mark.asyncio
    async def test_and_mode_flag_exposes_and(self, monkeypatch):
        flag = make_flag(name='and_flag', scope='global', rule_combination_mode='and')
        result = await self._bootstrap(monkeypatch, [flag])
        assert result['and_flag']['rule_combination_mode'] == 'and'

    @pytest.mark.asyncio
    async def test_legacy_flag_normalizes_to_first_match(self, monkeypatch):
        flag = make_flag(name='legacy_flag', scope='global', rule_combination_mode=None)
        result = await self._bootstrap(monkeypatch, [flag])
        assert result['legacy_flag']['rule_combination_mode'] == 'first_match'


# ---------------------------------------------------------------------------
# /sdk/evaluate — unfiltered fetch fix (TGT-03)
# ---------------------------------------------------------------------------

class TestSdkEvaluateScoping:

    async def _evaluate(self, monkeypatch, flags, user, flag_key='my_flag'):
        from app.domains.sdk.router import evaluate
        from app.domains.sdk.schemas import EvaluateRequest

        async def fake_list_flags(db, tenant_id=None):
            # Replicate the real list_flags() tenant filter: when tenant_id is
            # truthy, only tenant-matching or global flags are returned. This
            # is the filter that starves product/company-scoped flags
            # (tenant_id NULL) when /sdk/evaluate passes payload.user.get('tenant_id').
            if tenant_id:
                return [
                    f for f in flags
                    if f.scope == 'global' or (f.tenant_id is not None and str(f.tenant_id) == str(tenant_id))
                ]
            return flags

        async def fake_resolve_segment_members(db, flag_ids, user):
            return {}

        monkeypatch.setattr('app.domains.feature_flags.service.list_flags', fake_list_flags)
        monkeypatch.setattr('app.domains.sdk.service.resolve_segment_members', fake_resolve_segment_members)

        payload = EvaluateRequest(flag_key=flag_key, user=user)
        response = await evaluate(payload, db=None)
        return response.result

    @pytest.mark.asyncio
    async def test_product_scoped_flag_resolves(self, monkeypatch):
        """Product-scoped flag (tenant_id=None) was previously unreachable via list_flags tenant filter
        when the requesting user context also carries a tenant_id."""
        flag = make_flag(name='my_flag', scope='product', product_id='p1', tenant_id=None,
                          enabled=1, default_val=1, rules=[])
        result = await self._evaluate(monkeypatch, [flag], user={'product_id': 'p1', 'tenant_id': 't1'})
        assert result is True

    @pytest.mark.asyncio
    async def test_company_scoped_flag_matching_company_resolves_true(self, monkeypatch):
        flag = make_flag(name='my_flag', scope='company', company_id='acme', tenant_id=None,
                          enabled=1, default_val=1, rules=[])
        result = await self._evaluate(monkeypatch, [flag], user={'company_id': 'acme', 'tenant_id': 't1'})
        assert result is True

    @pytest.mark.asyncio
    async def test_company_scoped_flag_mismatched_company_resolves_false(self, monkeypatch):
        flag = make_flag(name='my_flag', scope='company', company_id='acme', tenant_id=None,
                          enabled=1, default_val=1, rules=[])
        result = await self._evaluate(monkeypatch, [flag], user={'company_id': 'other', 'tenant_id': 't1'})
        assert result is False
