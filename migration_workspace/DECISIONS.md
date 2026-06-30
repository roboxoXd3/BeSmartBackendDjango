# Migration Decisions Log

> This is a living document. Every architectural decision, exception, interpretation, or trade-off made during the migration must be recorded here.
> Future agents MUST review this file before starting work.

---

## Decision Format

```
### DEC-XXX: [Short Title]
- **Date:** YYYY-MM-DD
- **Agent:** [Agent identifier]
- **Context:** [Why this decision was needed]
- **Decision:** [What was decided]
- **Rationale:** [Why this option was chosen]
- **Alternatives Considered:** [What else was considered]
- **Impact:** [What this affects]
```

---

## Decisions

### DEC-001: Frontend repos are read-only references
- **Date:** 2026-06-18
- **Agent:** First Agent (Migration Coordinator)
- **Context:** Three frontend repos exist alongside the backend. The migration must not modify them.
- **Decision:** Frontend repos (ecom_admin, ecomWebsite, vendor-dashboard) are used exclusively for read-only API discovery and contract analysis. All code changes go into BeSmartBackend only.
- **Rationale:** Frontend changes require separate coordination with frontend engineers. The migration program's scope is backend consolidation.
- **Impact:** Any frontend changes needed will be documented in `VERIFICATION/frontend_fixes.md` for frontend teams.

### DEC-002: Dual API architecture — Next.js API routes act as BFF
- **Date:** 2026-06-18
- **Agent:** First Agent (Migration Coordinator)
- **Context:** Both `ecom_admin` and `vendor-dashboard` use Next.js API routes (`/api/...`) as a Backend-For-Frontend (BFF) layer. These routes internally call either Supabase directly or the Django API (`api.xbesmart.com`). The `ecomWebsite` uses a centralized `api.js` client that directly calls the Django API.
- **Decision:** The inventory captures TWO layers: (1) the frontend service/hook layer that calls the BFF routes, and (2) the BFF routes that call Supabase/Django. The migration target is the Supabase calls inside the BFF routes.
- **Rationale:** Understanding the full call chain is essential for accurate migration. The BFF routes in ecom_admin and vendor-dashboard are where Supabase SDK calls actually happen.
- **Impact:** Migration agents must look at both the service files AND the Next.js API route handlers to understand the full contract.

### DEC-003: ecomWebsite uses centralized Django API client
- **Date:** 2026-06-18
- **Agent:** First Agent (Migration Coordinator)
- **Context:** ecomWebsite's `lib/api.js` defines `apiFetch` and `apiAuthFetch` that call `api.xbesmart.com` directly. Auth is handled via Supabase session tokens passed as Bearer tokens.
- **Decision:** ecomWebsite's API calls are primarily DJANGO_API type already. The auth token injection via `apiAuthFetch` using Supabase session tokens is an AUTH dependency that needs tracking.
- **Rationale:** This frontend is closest to the target architecture already. Its Supabase dependencies are primarily auth (session management, password reset) and some direct SDK calls in BFF routes.
- **Impact:** ecomWebsite has the lowest migration effort for API calls but still needs auth migration.

### DEC-004: Vendor dashboard stores Supabase tokens in vendor_sessions
- **Date:** 2026-06-18
- **Agent:** First Agent (Migration Coordinator)
- **Context:** The vendor-dashboard's `besmart-api.js` retrieves Supabase access tokens from a `vendor_sessions` table, refreshes them, and uses them as Bearer tokens to call the Django API.
- **Decision:** Document this as a critical auth dependency. The vendor-dashboard's auth flow is: Supabase auth → store tokens in vendor_sessions → use tokens to authenticate against Django API.
- **Rationale:** This is the most complex auth flow and needs careful migration planning.
- **Impact:** Any auth migration must handle this token relay pattern.

### DEC-005: Confidence levels in inventory
- **Date:** 2026-06-18
- **Agent:** First Agent (Migration Coordinator)
- **Context:** Some API calls are clearly identifiable (explicit fetch URLs), others require inference from code patterns.
- **Decision:** Use three confidence levels: HIGH (explicit URL/method visible), MEDIUM (URL constructed dynamically but pattern is clear), LOW (inferred from surrounding code, may be incomplete).
- **Rationale:** Future agents need to know which inventory items may need re-verification.
- **Impact:** LOW confidence items should be re-verified during Phase 2.
