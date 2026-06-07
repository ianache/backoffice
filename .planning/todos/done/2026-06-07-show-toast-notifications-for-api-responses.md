---
created: 2026-06-07T14:07:18.640Z
title: Show toast notifications for API responses
area: ui
files:
  - portal/src/views/UsersView.vue
  - portal/src/stores/users.ts
  - portal/src/services/users.ts
---

## Problem

Currently mutations (Invite Member, update user, disable/enable, reset MFA) silently succeed or fail with no user feedback. Errors surface only via browser console. The backend/BFF returns meaningful error messages in the response body (e.g., validation errors, Keycloak failures) that the user never sees.

## Solution

Add a global toast/snackbar system to the portal:

- **Error toast (red)** for HTTP 4xx/5xx — display the `detail` message from the backend response body, or a generic fallback if none.
- **Success toast (green)** for HTTP 2xx — show a contextual success message (e.g., "Member invited", "User updated", "MFA reset").

Implementation hints:
1. Create a composable `useToast()` or a Pinia `useToastStore` with a queue of `{ type, message, id }` entries.
2. Add a `<ToastContainer>` component (teleported to `body`) that renders and auto-dismisses toasts after ~4s.
3. Wrap all store actions in `UsersView.vue` (and any future mutating views) with try/catch that calls `addToast()`.
4. Extract the error message: `err.response?.data?.detail ?? err.message ?? 'An unexpected error occurred'`.
5. Apply the same pattern to TenantsView.vue for consistency.
