import pytest
from app.domains.tenants.schemas import TenantCreate, TenantUpdate, TenantResponse
from app.domains.tenants.models import Tenant
from datetime import datetime

def test_tenant_create_schema_defaults():
    # This should fail because the module doesn't exist yet
    payload = {
        "name": "Test Tenant",
        "country": "PE",
        "default_language": "es",
        "default_currency": "PEN",
        "default_units": "metric"
    }
    schema = TenantCreate(**payload)
    assert schema.status == "active"
    assert schema.products == []

def test_tenant_model_fields():
    # This should fail because the model doesn't exist yet
    from sqlalchemy import inspect
    tenant = Tenant()
    assert hasattr(tenant, "id")
    assert hasattr(tenant, "name")
    assert hasattr(tenant, "status")
    assert hasattr(tenant, "products")
