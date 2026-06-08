from __future__ import annotations
from datetime import datetime
from typing import Optional
import pycountry
from pydantic import BaseModel, ConfigDict, field_validator

def validate_iso_country(v: str) -> str:
    if not v:
        raise ValueError("Country code cannot be empty")
    code = v.strip().upper()
    country = pycountry.countries.get(alpha_2=code)
    if not country:
        raise ValueError(f"Invalid country ISO 3166-1 alpha-2 code: '{v}'")
    return country.alpha_2

def validate_iso_language(v: str) -> str:
    if not v:
        raise ValueError("Language code cannot be empty")
    code = v.strip()
    # Support locale formats like en-US or es_ES by extracting base language
    lang_part = code.replace('_', '-').split('-')[0].lower()
    lang = pycountry.languages.get(alpha_2=lang_part) or pycountry.languages.get(alpha_3=lang_part)
    if not lang:
        raise ValueError(f"Invalid language ISO 639 code: '{v}'")
    return code

def validate_iso_currency(v: str) -> str:
    if not v:
        raise ValueError("Currency code cannot be empty")
    code = v.strip().upper()
    currency = pycountry.currencies.get(alpha_3=code)
    if not currency:
        raise ValueError(f"Invalid currency ISO 4217 code: '{v}'")
    return currency.alpha_3


class TenantCreate(BaseModel):
    name: str
    country: str
    default_language: str
    default_currency: str
    default_units: str
    status: str = "active"
    # Whitelabel fields — all optional
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    font_family: Optional[str] = None
    font_weight: Optional[str] = None
    domain: Optional[str] = None

    @field_validator('country')
    @classmethod
    def check_country(cls, v: str) -> str:
        return validate_iso_country(v)

    @field_validator('default_language')
    @classmethod
    def check_language(cls, v: str) -> str:
        return validate_iso_language(v)

    @field_validator('default_currency')
    @classmethod
    def check_currency(cls, v: str) -> str:
        return validate_iso_currency(v)


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    country: Optional[str] = None
    default_language: Optional[str] = None
    default_currency: Optional[str] = None
    default_units: Optional[str] = None
    status: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    font_family: Optional[str] = None
    font_weight: Optional[str] = None
    domain: Optional[str] = None

    @field_validator('country')
    @classmethod
    def check_country(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return validate_iso_country(v)

    @field_validator('default_language')
    @classmethod
    def check_language(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return validate_iso_language(v)

    @field_validator('default_currency')
    @classmethod
    def check_currency(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return validate_iso_currency(v)


class TenantResponse(TenantCreate):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
