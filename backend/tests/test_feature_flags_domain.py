"""
Tests for the Feature Flags domain.
Covers: evaluate_flag(), _evaluate_rule(), models, schemas.
"""
import pytest
from datetime import datetime


# ---------------------------------------------------------------------------
# Helper: minimal FeatureFlag-like object (avoids DB dependency in unit tests)
# ---------------------------------------------------------------------------

class MockFlag:
    """Lightweight stand-in for FeatureFlag SQLAlchemy model."""
    def __init__(
        self,
        scope: str,
        enabled: int = 1,
        default_val: int = 0,
        tenant_id: str | None = None,
        product_id: str | None = None,
        company_id: str | None = None,
        rules: str | None = None,
        tags: str | None = None,
        name: str = "test_flag",
        description: str | None = None,
        complex: int = 0,
        ttl: int | None = None,
        environment: str = "production",
        rollout: int = 100,
        created_by: str | None = None,
        id: int = 1,
    ):
        self.id = id
        self.name = name
        self.description = description
        self.scope = scope
        self.enabled = enabled
        self.default_val = default_val
        self.tenant_id = tenant_id
        self.product_id = product_id
        self.company_id = company_id
        self.rules = rules
        self.tags = tags
        self.complex = complex
        self.ttl = ttl
        self.environment = environment
        self.rollout = rollout
        self.created_by = created_by
        self.created_at = datetime(2026, 1, 1)
        self.updated_at = datetime(2026, 1, 1)


# ---------------------------------------------------------------------------
# evaluate_flag tests
# ---------------------------------------------------------------------------

def test_evaluate_flag_global_returns_default_val_when_enabled():
    """evaluate_flag([global_flag], {'tenant_id': 'X'}) returns bool(global_flag.default_val)"""
    from app.domains.feature_flags.service import evaluate_flag
    flag = MockFlag(scope="global", enabled=1, default_val=1)
    result = evaluate_flag([flag], {"tenant_id": "tenant-x"})
    assert result is True


def test_evaluate_flag_global_default_val_false():
    """global flag with default_val=0 returns False"""
    from app.domains.feature_flags.service import evaluate_flag
    flag = MockFlag(scope="global", enabled=1, default_val=0)
    result = evaluate_flag([flag], {"tenant_id": "tenant-x"})
    assert result is False


def test_evaluate_flag_tenant_wins_over_global():
    """evaluate_flag([global_flag, tenant_flag], context) returns tenant result — tenant wins"""
    from app.domains.feature_flags.service import evaluate_flag
    global_flag = MockFlag(scope="global", enabled=1, default_val=0, id=1)
    tenant_flag = MockFlag(scope="tenant", enabled=1, default_val=1, tenant_id="tenant-x", id=2)
    result = evaluate_flag([global_flag, tenant_flag], {"tenant_id": "tenant-x"})
    assert result is True


def test_evaluate_flag_tenant_flag_only_applies_to_matching_tenant():
    """Tenant flag for tenant-x does NOT apply when context has tenant-y"""
    from app.domains.feature_flags.service import evaluate_flag
    global_flag = MockFlag(scope="global", enabled=1, default_val=0, id=1)
    tenant_flag = MockFlag(scope="tenant", enabled=1, default_val=1, tenant_id="tenant-x", id=2)
    result = evaluate_flag([global_flag, tenant_flag], {"tenant_id": "tenant-y"})
    # Only global applies to tenant-y, global.default_val=0 → False
    assert result is False


def test_evaluate_flag_empty_list_returns_false():
    """evaluate_flag([], {}) returns False — no candidates"""
    from app.domains.feature_flags.service import evaluate_flag
    assert evaluate_flag([], {}) is False


def test_evaluate_flag_disabled_flag_returns_false():
    """evaluate_flag([disabled_flag], {}) returns False — disabled flag ignored"""
    from app.domains.feature_flags.service import evaluate_flag
    flag = MockFlag(scope="global", enabled=0, default_val=1)
    assert evaluate_flag([flag], {}) is False


def test_evaluate_flag_company_wins_over_product_wins_over_tenant():
    """Company scope has highest priority"""
    from app.domains.feature_flags.service import evaluate_flag
    global_flag = MockFlag(scope="global", enabled=1, default_val=0, id=1)
    tenant_flag = MockFlag(scope="tenant", enabled=1, default_val=0, tenant_id="t1", id=2)
    product_flag = MockFlag(scope="product", enabled=1, default_val=0, product_id="p1", id=3)
    company_flag = MockFlag(scope="company", enabled=1, default_val=1, company_id="c1", id=4)
    context = {"tenant_id": "t1", "product_id": "p1", "company_id": "c1"}
    result = evaluate_flag([global_flag, tenant_flag, product_flag, company_flag], context)
    assert result is True  # company flag wins, default_val=1


# ---------------------------------------------------------------------------
# _evaluate_rule tests
# ---------------------------------------------------------------------------

def test_evaluate_rule_equals_match():
    from app.domains.feature_flags.service import _evaluate_rule
    rule = {"attribute": "country", "operator": "equals", "value": "PE", "result": True}
    assert _evaluate_rule(rule, {"country": "PE"}) is True


def test_evaluate_rule_equals_no_match():
    from app.domains.feature_flags.service import _evaluate_rule
    rule = {"attribute": "country", "operator": "equals", "value": "PE", "result": True}
    assert _evaluate_rule(rule, {"country": "US"}) is False


def test_evaluate_rule_in_match():
    from app.domains.feature_flags.service import _evaluate_rule
    rule = {"attribute": "country", "operator": "in", "value": ["PE", "AR"], "result": True}
    assert _evaluate_rule(rule, {"country": "PE"}) is True


def test_evaluate_rule_in_no_match():
    from app.domains.feature_flags.service import _evaluate_rule
    rule = {"attribute": "country", "operator": "in", "value": ["PE", "AR"], "result": True}
    assert _evaluate_rule(rule, {"country": "US"}) is False


def test_evaluate_rule_not_in_match():
    from app.domains.feature_flags.service import _evaluate_rule
    rule = {"attribute": "country", "operator": "notIn", "value": ["US"], "result": True}
    assert _evaluate_rule(rule, {"country": "PE"}) is True


def test_evaluate_rule_not_in_no_match():
    from app.domains.feature_flags.service import _evaluate_rule
    rule = {"attribute": "country", "operator": "notIn", "value": ["US"], "result": True}
    assert _evaluate_rule(rule, {"country": "US"}) is False


def test_evaluate_rule_contains_match():
    from app.domains.feature_flags.service import _evaluate_rule
    # 'contains': expected in str(actual) — checks if 'PE' is in 'country' value
    rule = {"attribute": "country_code", "operator": "contains", "value": "PE", "result": True}
    assert _evaluate_rule(rule, {"country_code": "LAPE"}) is True


def test_evaluate_rule_contains_no_match():
    from app.domains.feature_flags.service import _evaluate_rule
    rule = {"attribute": "country_code", "operator": "contains", "value": "PE", "result": True}
    assert _evaluate_rule(rule, {"country_code": "LAUS"}) is False


def test_evaluate_rule_regex_match():
    from app.domains.feature_flags.service import _evaluate_rule
    rule = {"attribute": "email", "operator": "regex", "value": r".*@company\.com$", "result": True}
    assert _evaluate_rule(rule, {"email": "user@company.com"}) is True


def test_evaluate_rule_regex_no_match():
    from app.domains.feature_flags.service import _evaluate_rule
    rule = {"attribute": "email", "operator": "regex", "value": r".*@company\.com$", "result": True}
    assert _evaluate_rule(rule, {"email": "user@other.com"}) is False


def test_evaluate_rule_unknown_operator_returns_false():
    """Unknown operator must NOT raise — returns False"""
    from app.domains.feature_flags.service import _evaluate_rule
    rule = {"attribute": "country", "operator": "unknown_op", "value": "PE", "result": True}
    assert _evaluate_rule(rule, {"country": "PE"}) is False


def test_evaluate_rule_missing_attribute_returns_false():
    """When user dict lacks the attribute, return False — not crash"""
    from app.domains.feature_flags.service import _evaluate_rule
    rule = {"attribute": "country", "operator": "equals", "value": "PE", "result": True}
    assert _evaluate_rule(rule, {}) is False


def test_evaluate_rule_missing_attribute_in_no_crash():
    """Missing attribute with 'in' operator — return False, no TypeError"""
    from app.domains.feature_flags.service import _evaluate_rule
    rule = {"attribute": "plan", "operator": "in", "value": ["free", "basic"], "result": True}
    assert _evaluate_rule(rule, {}) is False


# ---------------------------------------------------------------------------
# Model field tests
# ---------------------------------------------------------------------------

def test_feature_flag_model_has_required_fields():
    from app.domains.feature_flags.models import FeatureFlag
    flag = FeatureFlag()
    for field in ("id", "name", "scope", "enabled", "default_val", "complex",
                  "environment", "rollout", "rules", "tags", "created_at", "updated_at"):
        assert hasattr(flag, field), f"FeatureFlag missing field: {field}"


def test_segment_model_has_required_fields():
    from app.domains.feature_flags.models import Segment
    seg = Segment()
    for field in ("id", "name", "tenant_id", "members", "created_at", "updated_at"):
        assert hasattr(seg, field), f"Segment missing field: {field}"


def test_flag_segment_model_has_required_fields():
    from app.domains.feature_flags.models import FlagSegment
    fs = FlagSegment()
    for field in ("flag_id", "segment_id"):
        assert hasattr(fs, field), f"FlagSegment missing field: {field}"


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------

def test_flag_create_schema_defaults():
    from app.domains.feature_flags.schemas import FlagCreate
    payload = FlagCreate(name="test_flag", scope="global")
    assert payload.enabled is True
    assert payload.default_val is False
    assert payload.complex is False
    assert payload.environment == "production"
    assert payload.rollout == 100
    assert payload.rules == []
    assert payload.tags == []


def test_flag_response_schema_parses_text_fields():
    """FlagResponse.parse_text_fields deserializes rules and tags from JSON strings"""
    from app.domains.feature_flags.schemas import FlagResponse
    import json
    rules_json = json.dumps([{"attribute": "country", "operator": "equals", "value": "PE", "result": True}])
    tags_json = json.dumps(["beta", "internal"])
    response = FlagResponse(
        id=1,
        name="test_flag",
        description=None,
        scope="global",
        tenant_id=None,
        product_id=None,
        company_id=None,
        enabled=True,
        default_val=False,
        complex=False,
        ttl=None,
        environment="production",
        rollout=100,
        rules=rules_json,
        tags=tags_json,
        created_by=None,
        created_at=datetime(2026, 1, 1),
        updated_at=datetime(2026, 1, 1),
    )
    assert len(response.rules) == 1
    assert response.rules[0].attribute == "country"
    assert response.tags == ["beta", "internal"]


def test_flag_response_empty_rules_tags():
    """FlagResponse with None rules/tags returns empty lists"""
    from app.domains.feature_flags.schemas import FlagResponse
    response = FlagResponse(
        id=1, name="test_flag", description=None, scope="global",
        tenant_id=None, product_id=None, company_id=None,
        enabled=True, default_val=False, complex=False,
        ttl=None, environment="production", rollout=100,
        rules=None, tags=None, created_by=None,
        created_at=datetime(2026, 1, 1), updated_at=datetime(2026, 1, 1),
    )
    assert response.rules == []
    assert response.tags == []


def test_segment_create_schema_defaults():
    from app.domains.feature_flags.schemas import SegmentCreate
    seg = SegmentCreate(name="beta_users")
    assert seg.tenant_id is None
    assert seg.members == []


def test_rule_schema_validation():
    from app.domains.feature_flags.schemas import RuleSchema
    rule = RuleSchema(attribute="country", operator="equals", value="PE", result=True)
    assert rule.attribute == "country"
    assert rule.result is True

def test_get_scope_filter_platform_admin():
    from app.domains.feature_flags.router import _get_scope_filter
    assert _get_scope_filter(["PlatformAdmin"]) is None
    assert _get_scope_filter(["PlatformAdmin", "TenantAdmin"]) is None

def test_get_scope_filter_product_manager():
    from app.domains.feature_flags.router import _get_scope_filter
    assert _get_scope_filter(["ProductManager"]) == ["global", "tenant", "product"]

def test_get_scope_filter_tenant_admin():
    from app.domains.feature_flags.router import _get_scope_filter
    assert _get_scope_filter(["TenantAdmin"]) == ["global", "tenant"]
    assert _get_scope_filter(["TenantOwner"]) == ["global", "tenant"]

def test_get_scope_filter_default():
    from app.domains.feature_flags.router import _get_scope_filter
    assert _get_scope_filter(["OtherRole"]) == ["global"]

@pytest.mark.asyncio
async def test_list_flags_router_tenant_bypass():
    from unittest.mock import AsyncMock, patch
    from app.domains.feature_flags.router import list_flags

    # Mock database session and service.list_flags
    mock_db = AsyncMock()
    with patch("app.domains.feature_flags.router.service.list_flags", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = []
        
        # 1. PlatformAdmin should bypass tenant_id filter (tenant_id becomes None)
        await list_flags(
            x_user_roles="PlatformAdmin",
            x_user_tenant_id="tenant-123",
            db=mock_db
        )
        mock_list.assert_called_with(mock_db, scope_filter=None, tenant_id=None, q=None)

        # 2. TenantAdmin should retain tenant_id filter
        await list_flags(
            x_user_roles="TenantAdmin",
            x_user_tenant_id="tenant-123",
            db=mock_db
        )
        mock_list.assert_called_with(mock_db, scope_filter=["global", "tenant"], tenant_id="tenant-123", q=None)

