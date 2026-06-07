# Keycloak Setup Reference

## Required: tenant_id Protocol Mapper

**Why:** The BFF `auth.ts` middleware extracts `tenant_id` from the JWT payload to populate
`req.user.tenantId`. Without this mapper, the JWT does not contain the user's `tenant_id` attribute
and the `X-User-Tenant-Id` header forwarded to the backend will be an empty string, breaking
tenant isolation.

**When to do this:** Once, after the `backoffice-portal` and `backoffice-bff` Keycloak clients are
provisioned. Applies to the `Apps` realm on `https://oauth2.qa.comsatel.com.pe`.

### Steps

1. Log in to Keycloak Admin Console → select realm **Apps**
2. Go to **Clients** → select **backoffice-portal** (the public PKCE client used by the Vue portal)
3. Open the **Client scopes** tab → click **backoffice-portal-dedicated**
4. In the dedicated scope, click **Add mapper** → **By configuration** → choose **User Attribute**
5. Fill in:
   - **Name:** `tenant_id`
   - **User Attribute:** `tenant_id`
   - **Token Claim Name:** `tenant_id`
   - **Claim JSON Type:** `String`
   - **Add to ID token:** ON
   - **Add to access token:** ON
   - **Add to userinfo:** ON
   - **Multivalued:** OFF (tenant_id is a single value)
6. Save.
7. Repeat steps 2–6 for the **backoffice-bff** client (confidential client used by the BFF).

> **Tip:** You can verify the mapper is working by decoding an access token (paste it at
> https://jwt.io). You should see `"tenant_id": "<uuid>"` in the payload claims.

### Setting tenant_id on existing users

New users created via the Invite Member flow will have `tenant_id` set automatically in their
Keycloak attributes by the backend. For existing test users (e.g., `bo.admin`), you must set the
attribute manually:

1. Keycloak Admin Console → Apps realm → **Users** → select the user
2. **Attributes** tab → **Add attribute**
   - **Key:** `tenant_id`
   - **Value:** `<the tenant's UUID from the tenants table>`
3. Save.

### Verification

After configuring the mapper and setting user attributes, log in as that user and call:

```bash
curl -s http://localhost:3000/auth/me -H "Authorization: Bearer <token>" | jq .
```

The response should include the `tenant_id` from Keycloak. Alternatively, check that the BFF
console does NOT log `[warn] X-User-Tenant-Id is empty` on user list requests.

## backoffice-admin-svc Service Account

See Phase 3 Plan 02 checkpoint for setup instructions. Required env vars in `bff/.env`:

```
KEYCLOAK_ADMIN_CLIENT_ID=backoffice-admin-svc
KEYCLOAK_ADMIN_CLIENT_SECRET=<from Keycloak Credentials tab>
```
