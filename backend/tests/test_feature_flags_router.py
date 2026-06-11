import pytest
from fastapi import HTTPException
from app.domains.feature_flags.router import _get_scope_filter, _check_scope_permission

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
