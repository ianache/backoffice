import pytest
from pydantic import ValidationError
from app.domains.tenants.schemas import TenantCreate, TenantUpdate, TenantResponse
from app.domains.tenants.models import Tenant
from datetime import datetime

def test_tenant_create_schema_defaults():
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
    assert schema.country == "PE"
    assert schema.default_currency == "PEN"

def test_tenant_model_fields():
    tenant = Tenant()
    assert hasattr(tenant, "id")
    assert hasattr(tenant, "name")
    assert hasattr(tenant, "status")
    assert hasattr(tenant, "products")

def test_tenant_validation_success_normalization():
    # Test lowercase values are normalized to standard formats (uppercase for country and currency)
    payload = {
        "name": "Acme Test",
        "country": "us",
        "default_language": "en-us",
        "default_currency": "eur",
        "default_units": "metric"
    }
    schema = TenantCreate(**payload)
    assert schema.country == "US"
    assert schema.default_language == "en-us"
    assert schema.default_currency == "EUR"

def test_tenant_validation_invalid_country():
    payload = {
        "name": "Acme Test",
        "country": "XX",  # Invalid country code
        "default_language": "es",
        "default_currency": "EUR",
        "default_units": "metric"
    }
    with pytest.raises(ValidationError) as exc_info:
        TenantCreate(**payload)
    assert "Invalid country ISO 3166-1 alpha-2 code" in str(exc_info.value)

def test_tenant_validation_invalid_language():
    payload = {
        "name": "Acme Test",
        "country": "ES",
        "default_language": "zz",  # Invalid language code
        "default_currency": "EUR",
        "default_units": "metric"
    }
    with pytest.raises(ValidationError) as exc_info:
        TenantCreate(**payload)
    assert "Invalid language ISO 639 code" in str(exc_info.value)

def test_tenant_validation_invalid_currency():
    payload = {
        "name": "Acme Test",
        "country": "ES",
        "default_language": "es",
        "default_currency": "XYZ",  # Invalid currency code
        "default_units": "metric"
    }
    with pytest.raises(ValidationError) as exc_info:
        TenantCreate(**payload)
    assert "Invalid currency ISO 4217 code" in str(exc_info.value)

def test_tenant_update_validation():
    # Test TenantUpdate validations
    update_ok = TenantUpdate(country="de", default_currency="gbp", default_language="de-de")
    assert update_ok.country == "DE"
    assert update_ok.default_currency == "GBP"
    assert update_ok.default_language == "de-de"

    with pytest.raises(ValidationError):
        TenantUpdate(country="invalid")

