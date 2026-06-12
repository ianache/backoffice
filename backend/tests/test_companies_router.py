import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.domains.companies.schemas import CompanyCreate, CompanyUpdate
from app.domains.companies.router import (
    _require_companies_role,
    _tenant_filter_for,
    _check_create_tenant,
)


def test_company_create_accepts_valid_slug():
    payload = CompanyCreate(id="acme_01", name="Acme Corp", tenant_id="t1")
    assert payload.id == "acme_01"


def test_company_create_rejects_bad_slug():
    with pytest.raises(ValueError):
        CompanyCreate(id="Bad Slug!", name="Acme Corp", tenant_id="t1")


def test_company_create_rejects_empty_slug():
    with pytest.raises(ValueError):
        CompanyCreate(id="", name="Acme Corp", tenant_id="t1")


def test_company_create_requires_tenant_id():
    with pytest.raises(ValidationError):
        CompanyCreate(id="acme_01", name="Acme Corp")


def test_company_update_has_no_id_or_tenant_id_fields():
    assert "id" not in CompanyUpdate.model_fields
    assert "tenant_id" not in CompanyUpdate.model_fields


def test_require_companies_role_platform_admin():
    _require_companies_role(["PlatformAdmin"])


def test_require_companies_role_tenant_admin():
    _require_companies_role(["TenantAdmin"])


def test_require_companies_role_tenant_owner():
    _require_companies_role(["TenantOwner"])


def test_require_companies_role_tenant_viewer_raises_403():
    with pytest.raises(HTTPException) as exc:
        _require_companies_role(["TenantViewer"])
    assert exc.value.status_code == 403


def test_require_companies_role_empty_raises_403():
    with pytest.raises(HTTPException) as exc:
        _require_companies_role([])
    assert exc.value.status_code == 403


def test_tenant_filter_for_platform_admin_returns_none():
    assert _tenant_filter_for(["PlatformAdmin"], "t1") is None


def test_tenant_filter_for_tenant_admin_returns_own_tenant():
    assert _tenant_filter_for(["TenantAdmin"], "t1") == "t1"


def test_check_create_tenant_non_platform_admin_other_tenant_raises_403():
    with pytest.raises(HTTPException) as exc:
        _check_create_tenant(["TenantAdmin"], payload_tenant_id="t2", own_tenant="t1")
    assert exc.value.status_code == 403


def test_check_create_tenant_platform_admin_other_tenant_passes():
    _check_create_tenant(["PlatformAdmin"], payload_tenant_id="t2", own_tenant="t1")


def test_check_create_tenant_tenant_admin_own_tenant_passes():
    _check_create_tenant(["TenantAdmin"], payload_tenant_id="t1", own_tenant="t1")
