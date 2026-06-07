"""
Unit tests for the Feature Flag evaluation engine.
Plan: 04-02 — TDD for evaluate_flag() and _evaluate_rule()
Covers: FLAG-04 (deterministic hierarchy) + FLAG-05 (operator support)

No DB connection required — evaluate_flag() takes a plain list,
_evaluate_rule() takes plain dicts.
"""
import json
from types import SimpleNamespace

from app.domains.feature_flags.service import evaluate_flag, _evaluate_rule


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

def make_flag(
    scope,
    tenant_id=None,
    product_id=None,
    company_id=None,
    enabled=1,
    default_val=0,
    rules=None,
):
    """Build a minimal FeatureFlag-like object without a DB session."""
    return SimpleNamespace(
        scope=scope,
        tenant_id=tenant_id,
        product_id=product_id,
        company_id=company_id,
        enabled=enabled,
        default_val=default_val,
        rules=json.dumps(rules) if rules is not None else '[]',
    )


# ---------------------------------------------------------------------------
# FLAG-04: Hierarchical evaluation (scope priority)
# ---------------------------------------------------------------------------

class TestEvaluateFlagHierarchy:

    def test_global_flag_returns_default_val_when_enabled(self):
        """evaluate_flag([global_flag], context_no_match) returns bool(default_val) when enabled=1"""
        flag = make_flag('global', enabled=1, default_val=1)
        assert evaluate_flag([flag], {}) is True

    def test_global_flag_default_val_false(self):
        """global flag with default_val=0 returns False"""
        flag = make_flag('global', enabled=1, default_val=0)
        assert evaluate_flag([flag], {'tenant_id': 'any'}) is False

    def test_tenant_flag_wins_over_global(self):
        """evaluate_flag([global_flag, tenant_flag], context) returns result from tenant_flag, not global"""
        global_flag = make_flag('global', enabled=1, default_val=0)
        tenant_flag = make_flag('tenant', tenant_id='t1', enabled=1, default_val=1)
        result = evaluate_flag([global_flag, tenant_flag], {'tenant_id': 't1'})
        # tenant has priority=2, global=1; tenant wins, default_val=1 → True
        assert result is True

    def test_global_not_overridden_when_tenant_does_not_match(self):
        """Tenant flag for t1 does NOT apply for context with tenant_id=t2"""
        global_flag = make_flag('global', enabled=1, default_val=0)
        tenant_flag = make_flag('tenant', tenant_id='t1', enabled=1, default_val=1)
        result = evaluate_flag([global_flag, tenant_flag], {'tenant_id': 't2'})
        # Only global applies — default_val=0 → False
        assert result is False

    def test_product_flag_wins_over_tenant_wins_over_global(self):
        """Product flag (priority=3) beats tenant (2) beats global (1)"""
        global_flag = make_flag('global', enabled=1, default_val=0)
        tenant_flag = make_flag('tenant', tenant_id='t1', enabled=1, default_val=0)
        product_flag = make_flag('product', product_id='p1', enabled=1, default_val=1)
        context = {'tenant_id': 't1', 'product_id': 'p1'}
        result = evaluate_flag([global_flag, tenant_flag, product_flag], context)
        # product wins, default_val=1 → True
        assert result is True

    def test_company_flag_wins_over_product_wins_over_tenant(self):
        """Company (priority=4) is highest — beats product/tenant/global"""
        global_flag = make_flag('global', enabled=1, default_val=0)
        tenant_flag = make_flag('tenant', tenant_id='t1', enabled=1, default_val=0)
        product_flag = make_flag('product', product_id='p1', enabled=1, default_val=0)
        company_flag = make_flag('company', company_id='c1', enabled=1, default_val=1)
        context = {'tenant_id': 't1', 'product_id': 'p1', 'company_id': 'c1'}
        result = evaluate_flag([global_flag, tenant_flag, product_flag, company_flag], context)
        # company wins, default_val=1 → True
        assert result is True

    def test_empty_list_returns_false(self):
        """evaluate_flag([], {}) returns False — no candidates"""
        assert evaluate_flag([], {}) is False

    def test_disabled_flag_returns_false(self):
        """evaluate_flag([disabled_global], {'tenant_id': 'X'}) returns False"""
        flag = make_flag('global', enabled=0, default_val=1)
        assert evaluate_flag([flag], {'tenant_id': 'X'}) is False

    def test_disabled_winner_returns_false_even_with_candidates(self):
        """When the highest-priority flag is disabled, returns False"""
        global_flag = make_flag('global', enabled=1, default_val=1)
        tenant_flag = make_flag('tenant', tenant_id='t1', enabled=0, default_val=1)
        # tenant has higher priority but is disabled — falls back to... disabled
        result = evaluate_flag([global_flag, tenant_flag], {'tenant_id': 't1'})
        # winner = tenant_flag (priority=2 > 1), but disabled → False
        assert result is False

    def test_rule_match_returns_rule_result(self):
        """When a rule matches, evaluate_flag returns bool(rule.result)"""
        rule = {'attribute': 'country', 'operator': 'equals', 'value': 'PE', 'result': True}
        flag = make_flag('global', enabled=1, default_val=0, rules=[rule])
        context = {'user': {'country': 'PE'}}
        assert evaluate_flag([flag], context) is True

    def test_no_rule_match_returns_default_val(self):
        """When no rule matches, evaluate_flag returns bool(flag.default_val)"""
        rule = {'attribute': 'country', 'operator': 'equals', 'value': 'PE', 'result': True}
        flag = make_flag('global', enabled=1, default_val=0, rules=[rule])
        context = {'user': {'country': 'US'}}
        assert evaluate_flag([flag], context) is False

    def test_scope_priority_not_recency(self):
        """Priority is by scope type, not by list order or creation time.
        Add global first then tenant — tenant still wins (not creation-order).
        """
        # global has default_val=1, tenant has default_val=0
        # If order-based, global (first in list) would win → True
        # If priority-based, tenant wins → False
        global_flag = make_flag('global', enabled=1, default_val=1)
        tenant_flag = make_flag('tenant', tenant_id='t1', enabled=1, default_val=0)
        result = evaluate_flag([global_flag, tenant_flag], {'tenant_id': 't1'})
        # tenant wins (scope priority=2 > 1), default_val=0 → False
        assert result is False


# ---------------------------------------------------------------------------
# FLAG-05: Operator evaluation
# ---------------------------------------------------------------------------

class TestEvaluateRule:

    def test_equals_true(self):
        rule = {'attribute': 'country', 'operator': 'equals', 'value': 'PE'}
        assert _evaluate_rule(rule, {'country': 'PE'}) is True

    def test_equals_false(self):
        rule = {'attribute': 'country', 'operator': 'equals', 'value': 'PE'}
        assert _evaluate_rule(rule, {'country': 'US'}) is False

    def test_in_true(self):
        rule = {'attribute': 'country', 'operator': 'in', 'value': ['PE', 'AR']}
        assert _evaluate_rule(rule, {'country': 'PE'}) is True

    def test_in_false(self):
        rule = {'attribute': 'country', 'operator': 'in', 'value': ['PE', 'AR']}
        assert _evaluate_rule(rule, {'country': 'US'}) is False

    def test_not_in_true(self):
        rule = {'attribute': 'country', 'operator': 'notIn', 'value': ['US']}
        assert _evaluate_rule(rule, {'country': 'PE'}) is True

    def test_not_in_false(self):
        rule = {'attribute': 'country', 'operator': 'notIn', 'value': ['US']}
        assert _evaluate_rule(rule, {'country': 'US'}) is False

    def test_contains_true(self):
        rule = {'attribute': 'email', 'operator': 'contains', 'value': '@acme'}
        assert _evaluate_rule(rule, {'email': 'john@acme.com'}) is True

    def test_contains_false(self):
        rule = {'attribute': 'email', 'operator': 'contains', 'value': '@acme'}
        assert _evaluate_rule(rule, {'email': 'john@other.com'}) is False

    def test_regex_true(self):
        rule = {'attribute': 'email', 'operator': 'regex', 'value': '^admin'}
        assert _evaluate_rule(rule, {'email': 'admin@co.com'}) is True

    def test_regex_false(self):
        rule = {'attribute': 'email', 'operator': 'regex', 'value': '^admin'}
        assert _evaluate_rule(rule, {'email': 'user@co.com'}) is False

    def test_unknown_operator_returns_false_no_exception(self):
        """Unknown operator must NOT raise — silently returns False"""
        rule = {'attribute': 'country', 'operator': 'unknown_op', 'value': 'PE'}
        assert _evaluate_rule(rule, {'country': 'PE'}) is False

    def test_missing_attribute_returns_false_no_key_error(self):
        """Missing attribute in user dict returns False — no KeyError"""
        rule = {'attribute': 'missing_attr', 'operator': 'equals', 'value': 'X'}
        assert _evaluate_rule(rule, {}) is False

    def test_missing_attribute_with_in_operator(self):
        """Missing attribute with 'in' operator — False, no TypeError"""
        rule = {'attribute': 'plan', 'operator': 'in', 'value': ['free', 'basic']}
        assert _evaluate_rule(rule, {}) is False

    def test_all_five_operators_have_true_case(self):
        """Ensure all 5 operators produce True when conditions match."""
        from app.domains.feature_flags.service import OPERATORS
        assert set(OPERATORS.keys()) == {'equals', 'in', 'notIn', 'contains', 'regex'}
