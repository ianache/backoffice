import pytest
from pydantic import ValidationError
from fastapi import HTTPException
from app.domains.feature_flags.router import _get_scope_filter, _check_scope_permission, _validate_update_target
from app.domains.feature_flags.schemas import FlagCreate, FlagUpdate

def test_get_scope_filter_platform_admin():
    assert _get_scope_filter(["PlatformAdmin"]) is None
    assert _get_scope_filter(["PlatformAdmin", "TenantAdmin"]) is None

def test_get_scope_filter_tenant_admin_owner():
    assert _get_scope_filter(["TenantAdmin"]) == ["global", "tenant", "product", "company"]
    assert _get_scope_filter(["TenantOwner"]) == ["global", "tenant", "product", "company"]
    assert _get_scope_filter(["TenantAdmin", "ProductManager"]) == ["global", "tenant", "product", "company"]

def test_get_scope_filter_product_manager():
    assert _get_scope_filter(["ProductManager"]) == ["global", "tenant", "product"]

def test_get_scope_filter_other():
    assert _get_scope_filter(["TenantViewer"]) == ["global"]
    assert _get_scope_filter([]) == ["global"]


def test_check_scope_permission_global():
    # PlatformAdmin should succeed
    _check_scope_permission("global", ["PlatformAdmin"], "create")
    
    # Others should raise 403
    with pytest.raises(HTTPException) as exc:
        _check_scope_permission("global", ["TenantAdmin"], "create")
    assert exc.value.status_code == 403
    assert "Only PlatformAdmin can create global flags" in exc.value.detail


def test_check_scope_permission_tenant():
    # PlatformAdmin, TenantAdmin, TenantOwner should succeed
    _check_scope_permission("tenant", ["PlatformAdmin"], "update")
    _check_scope_permission("tenant", ["TenantAdmin"], "update")
    _check_scope_permission("tenant", ["TenantOwner"], "update")
    
    # ProductManager/others should raise 403
    with pytest.raises(HTTPException) as exc:
        _check_scope_permission("tenant", ["ProductManager"], "update")
    assert exc.value.status_code == 403
    assert "Only PlatformAdmin or TenantAdmin/TenantOwner can update tenant flags" in exc.value.detail


def test_check_scope_permission_product():
    # PlatformAdmin, TenantAdmin, TenantOwner, ProductManager should succeed
    _check_scope_permission("product", ["PlatformAdmin"], "delete")
    _check_scope_permission("product", ["TenantAdmin"], "delete")
    _check_scope_permission("product", ["TenantOwner"], "delete")
    _check_scope_permission("product", ["ProductManager"], "delete")
    
    # Others should raise 403
    with pytest.raises(HTTPException) as exc:
        _check_scope_permission("product", ["TenantViewer"], "delete")
    assert exc.value.status_code == 403
    assert "Only PlatformAdmin, TenantAdmin/TenantOwner, or ProductManager can delete product flags" in exc.value.detail


def test_check_scope_permission_company():
    # PlatformAdmin, TenantAdmin, TenantOwner should succeed
    _check_scope_permission("company", ["PlatformAdmin"], "enable")
    _check_scope_permission("company", ["TenantAdmin"], "enable")
    _check_scope_permission("company", ["TenantOwner"], "enable")
    
    # ProductManager/others should raise 403
    with pytest.raises(HTTPException) as exc:
        _check_scope_permission("company", ["ProductManager"], "enable")
    assert exc.value.status_code == 403
    assert "Only PlatformAdmin or TenantAdmin/TenantOwner can enable company flags" in exc.value.detail


# ---------------------------------------------------------------------------
# FlagCreate scope-target validation (TGT-02)
# ---------------------------------------------------------------------------

class TestFlagCreateScopeTargetValidation:

    def test_product_scope_without_product_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            FlagCreate(name="f1", scope="product", product_id=None)
        assert "product_id is required" in str(exc.value)

    def test_tenant_scope_without_tenant_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            FlagCreate(name="f1", scope="tenant", tenant_id=None)
        assert "tenant_id is required" in str(exc.value)

    def test_company_scope_without_company_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            FlagCreate(name="f1", scope="company", company_id=None)
        assert "company_id is required" in str(exc.value)

    def test_global_scope_with_no_targets_is_valid(self):
        flag = FlagCreate(name="f1", scope="global")
        assert flag.scope == "global"

    def test_product_scope_with_product_id_is_valid(self):
        flag = FlagCreate(name="f1", scope="product", product_id="backoffice")
        assert flag.product_id == "backoffice"


# ---------------------------------------------------------------------------
# FlagUpdate gains scope/tenant_id/product_id/company_id (TGT-02)
# ---------------------------------------------------------------------------

class TestFlagUpdateScopeTargetFields:

    def test_flag_update_has_target_fields(self):
        assert "scope" in FlagUpdate.model_fields
        assert "tenant_id" in FlagUpdate.model_fields
        assert "product_id" in FlagUpdate.model_fields
        assert "company_id" in FlagUpdate.model_fields


# ---------------------------------------------------------------------------
# _validate_update_target() — merged-state validation on PATCH (TGT-02)
# ---------------------------------------------------------------------------

from types import SimpleNamespace


def make_flag(scope='global', tenant_id=None, product_id=None, company_id=None):
    return SimpleNamespace(scope=scope, tenant_id=tenant_id, product_id=product_id, company_id=company_id)


class TestValidateUpdateTarget:

    def test_legacy_flag_untouched_scope_no_exception(self):
        """update_data={'enabled': True} on legacy flag (scope='company', company_id=None) -> no exception."""
        flag = make_flag(scope='company', company_id=None)
        result = _validate_update_target(flag, {'enabled': True})
        assert result == {'enabled': True}

    def test_scope_change_to_product_without_product_id_raises_422(self):
        flag = make_flag(scope='global')
        with pytest.raises(HTTPException) as exc:
            _validate_update_target(flag, {'scope': 'product'})
        assert exc.value.status_code == 422

    def test_product_id_set_on_product_scoped_flag_passes(self):
        flag = make_flag(scope='product', product_id=None)
        result = _validate_update_target(flag, {'product_id': 'backoffice'})
        assert result['product_id'] == 'backoffice'

    def test_scope_change_to_tenant_clears_other_targets(self):
        flag = make_flag(scope='global')
        result = _validate_update_target(flag, {'scope': 'tenant', 'tenant_id': 't1'})
        assert result['scope'] == 'tenant'
        assert result['tenant_id'] == 't1'
        assert result['product_id'] is None
        assert result['company_id'] is None
