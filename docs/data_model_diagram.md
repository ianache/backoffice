# Data Model Diagram

The solution uses a relational database schema (MySQL) to store tenant configurations, audit events, segments, and feature flags. The ER diagram below represents the tables, column types, keys, and their relationships.

```mermaid
erDiagram
    TENANTS {
        int id PK
        string name "String(255)"
        string country "String(2)"
        string default_language "String(5)"
        string default_currency "String(3)"
        string default_units "String(10)"
        string status "String(20)"
        string logo_url "String(500), Nullable"
        string primary_color "String(20), Nullable"
        string secondary_color "String(20), Nullable"
        string accent_color "String(20), Nullable"
        string font_family "String(100), Nullable"
        string font_weight "String(20), Nullable"
        string domain "String(255), Nullable"
        json products "JSON Array"
        datetime created_at
        datetime updated_at
    }

    USER_EVENTS {
        int id PK
        string keycloak_user_id "String(36)"
        string tenant_id "String(100), conceptually references tenants.id"
        string actor_sub "String(36)"
        string action "String(50)"
        text context "TEXT, serialized JSON context"
        datetime created_at
    }

    FEATURE_FLAGS {
        int id PK
        string name "String(100)"
        string description "String(500), Nullable"
        string scope "String(20) - global|tenant|product|company"
        string tenant_id "String(100), conceptually references tenants.id, Nullable"
        string product_id "String(100), Nullable"
        string company_id "String(100), Nullable"
        smallint enabled "Default 1"
        smallint default_val "Default 0"
        smallint complex "Default 0"
        int ttl "Nullable"
        string environment "String(20) - Default 'production'"
        int rollout "Default 100"
        text rules "TEXT, serialized JSON rules"
        text tags "TEXT, serialized JSON tags"
        string created_by "String(36), Nullable"
        datetime created_at
        datetime updated_at
    }

    SEGMENTS {
        int id PK
        string name "String(100)"
        string description "String(500), Nullable"
        string tenant_id "String(100), conceptually references tenants.id, Nullable"
        text members "TEXT, JSON list of user UUIDs"
        datetime created_at
        datetime updated_at
    }

    FLAG_SEGMENTS {
        int flag_id PK, FK "references feature_flags.id"
        int segment_id PK, FK "references segments.id"
    }

    %% Relationships
    FEATURE_FLAGS ||--o{ FLAG_SEGMENTS : "mapped to"
    SEGMENTS ||--o{ FLAG_SEGMENTS : "mapped to"
    TENANTS |o--o{ USER_EVENTS : "conceptually scopes"
    TENANTS |o--o{ FEATURE_FLAGS : "conceptually scopes"
    TENANTS |o--o{ SEGMENTS : "conceptually scopes"
```

---

## Table Descriptions

### 1. `tenants`
Stores corporate accounts, active modules (products), localizations (ISO-3166-1 country, ISO-639-1 language, ISO-4217 currency, standard units), and customized white-label branding configurations.

### 2. `user_events`
Stores security audit logs. Captures user lifecycle events (creation, profile updates, status toggles, MFA resets) within a tenant. The context details (like which roles were added/removed) are stored as JSON serialized text to remain compatible with MySQL 5.6.

### 3. `feature_flags`
Stores configurations for feature toggles. Toggles can be scoped globally, by tenant, by product, or by company. Includes progression rollout percentages, complex activation rules, environments, and Time-To-Live (TTL).

### 4. `segments`
Stores user groups/cohorts for targeting. Represents a static cohort of user UUIDs (stored in the `members` text field) scoped under a tenant.

### 5. `flag_segments`
Junction table implementing a Many-to-Many association between `feature_flags` and targeting `segments`.
