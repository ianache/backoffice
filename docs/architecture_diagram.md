# System Architecture - Sketchnotes

Here is the sketchnote-style system architecture diagram representing the multi-tenant SaaS platform components:

![Architecture Sketchnote](/C:/Users/ianache/.gemini/antigravity-ide/brain/9861aad9-9e25-4562-8e5a-f2beced5e636/architecture_sketchnote_1780851913771.png)

---

## Component Breakdown

### 1. Vue 3 Portal (Frontend)
- **Tech Stack**: Vue 3, Vite, Pinia, TailwindCSS, Material Design Components (M3).
- **Function**: The main user interface. Renders dashboard metrics, tenant tables, user drawers, and security configurations.
- **Auth Flow**: Uses the standard **OAuth2 Authorization Code Flow with PKCE** via Keycloak JS to authenticate users directly.

### 2. Node.js BFF (Backend-For-Frontend)
- **Tech Stack**: Node.js, Express, TypeScript.
- **Port**: `3000`
- **Function**: Acts as a gateway proxy for the frontend.
  - Validates frontend session cookies/tokens.
  - Injects backend communication secrets (`X-Internal-Secret`).
  - Passes down current user identity context (`X-User-Sub`, `X-User-Roles`) to the FastAPI backend.

### 3. FastAPI Backend (Core API)
- **Tech Stack**: Python, FastAPI, SQLAlchemy, Alembic.
- **Port**: `8000`
- **Function**: Implements the main domain business logic and database access.
  - Serves endpoints for **Tenants** (creation, update, whitelabel styling, and product scopes) and **Users** (members listing, invite/creation, status toggle, and MFA reset).
  - Validates input formats against standard ISO codes (`pycountry`).
  - Performs backend-to-backend operations against the Keycloak Admin REST API.

### 4. Keycloak (Identity & Access Provider)
- **Tech Stack**: Keycloak server, OpenID Connect.
- **Function**: Identity provider for SSO. Stores user credentials, assigns realm roles (like `PlatformAdmin`, `TenantOwner`, `TenantAdmin`), and manages user attributes (e.g. `tenant_id` scopes).

### 5. Database (MySQL)
- **Tech Stack**: MySQL (compatible with v5.6).
- **Function**: Relational storage for platform metadata.
  - `tenants` table stores names, domains, standard country/currency/language ISO codes, and JSON-based product lists.
  - `user_events` stores audit records detailing who performed which user profile or permission edits.
