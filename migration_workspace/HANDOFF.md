# Agent Handoff

> This is the most important file for any resuming agent.
> Read this FIRST to understand where the migration stands and what to do next.
> Last Updated: 2026-06-18 by Antigravity

---

## Current State

**Phase 1 (API Discovery) is COMPLETE.**

All three frontend repositories have been analyzed. The full API inventory has been created with:
- 185 total API interactions discovered
- 94 Django API calls cataloged
- 34 Supabase SDK calls cataloged
- 12 Supabase Auth calls cataloged
- 4 Supabase Storage calls cataloged
- 38 Next.js BFF routes documented
- 3 unknowns flagged

The migration workspace is fully populated with:
- `PLAN.md` — overall strategy and execution phases
- `RULES.md` — mandatory constraints for all agents
- `DECISIONS.md` — 5 architectural decisions recorded
- `PROGRESS.md` — current status numbers
- `INVENTORY/api_inventory.md` — consolidated cross-frontend summary
- `INVENTORY/ecomWebsite_inventory.md` — 52 Django + 6 SDK + 4 Auth calls
- `INVENTORY/ecom_admin_inventory.md` — 8 Django + 18 SDK + 6 Auth + 3 Storage calls
- `INVENTORY/vendor_dashboard_inventory.md` — 34 Django + 10 SDK + 2 Auth + 1 Storage call
- `VERIFICATION/verification_results.md` — template (empty)
- `VERIFICATION/frontend_fixes.md` — 3 issues already identified
- `MIGRATIONS/migration_log.md` — template (empty)
- `TESTING/test_tracker.md` — template (empty)
- `AGENT_STATE/current_batch.md` — idle

---

## What the Next Agent Should Do

### Phase 3: Migration

The verification phase is now 100% complete. You must now begin **Phase 3: Migration**.

**Your Objective:** Implement the missing endpoints, fix the schema mismatches, and rewire the frontends/BFFs to use the Django backend as the single source of truth instead of making direct Supabase SDK calls.

**Recommended Approach:**
1. Start with the simplest backend fixes (e.g., missing fields, sorting fixes, renaming fields like `items` to `order_items` in serializers).
2. Move to implementing missing endpoints (e.g., checkout orchestration, shipping calculations).
3. Update the frontend repositories to use the new/fixed Django endpoints and remove direct Supabase DB queries.
4. Finally, tackle the major architectural shifts (like Admin auth).

**Status update (2026-06-20)**: The Django API mismatch fixes for `ecomWebsite` and `ecom_admin` (Admin APIs) have been fully completed.
The next step is to tackle the Supabase SDK migrations. The next batch should be the first batch of Supabase SDK migrations from `ecom_admin` or `ecomWebsite`.

**Workflow for each migration task:**
1. Document your plan in `MIGRATIONS/migration_log.md`.
2. Implement the backend changes in Django (create missing endpoints for Supabase SDK equivalents).
3. Test the endpoints locally (with scripts like `verify_admin_apis.py`).
4. (Optional) Update the frontend/BFF changes to point to Django if part of the task scope.
5. Record the result and move to the next task.

Update `PROGRESS.md` Phase 3 as you make progress.

---

## Key Findings from Discovery

1. **ecom_admin is the heaviest Supabase user** — 18 SDK calls, custom auth system, storage operations. This will be the hardest to migrate.

2. **vendor-dashboard has dual API patterns** — Some functions call Django directly (`besmart-api.js`), others go through BFF routes (`services/*.js`). Some functions in `productsService.js` and `vendorService.js` call Supabase directly (bug — undefined `supabase` variable in some cases).

3. **ecomWebsite is closest to target architecture** — Uses centralized `api.js` client that already calls Django. Main migration needs are auth (Supabase session → Django JWT) and a few BFF routes.

4. **Admin auth is completely separate from Django** — Uses `admin_sessions` + `admin_users` Supabase tables, not Django JWT. This is a critical migration item.

5. **Existing API docs exist** — `BeSmartBackend/API_ENDPOINTS_BY_APPLICATION.md` documents 154+ planned endpoints. Use this as the verification target.

---

## Files to Read Before Starting

```
1. PLAN.md
2. RULES.md  
3. DECISIONS.md
4. PROGRESS.md
5. AGENT_STATE/current_batch.md
6. INVENTORY/api_inventory.md (consolidated)
7. The specific frontend inventory for your batch
8. BeSmartBackend/API_ENDPOINTS_BY_APPLICATION.md (backend reference)
```

---

## Stop Conditions Reminder

STOP IMMEDIATELY if:
- You've completed a batch of 5 APIs
- You encounter a blocking decision (record in DECISIONS.md)
- You find a breaking change
- Context window is approaching limit

Always update HANDOFF.md before stopping.
