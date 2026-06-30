# BeSmart Migration Plan

> **Program:** Migrate Supabase direct-access patterns to Django-mediated APIs
> **Created:** 2026-06-18
> **Status:** Phase 1 — API Discovery COMPLETE
> **Last Agent:** First Agent (Migration Coordinator)

---

## 1. Problem Statement

Three frontend applications (ecom_admin, ecomWebsite, vendor-dashboard) currently use a **hybrid** approach:
- Some calls go to the **Django backend** (`api.xbesmart.com`)
- Some calls go **directly to Supabase** (SDK / REST / Storage / Auth)

The goal is to consolidate all data access through the Django backend so that:
- Supabase becomes an internal implementation detail, not a frontend dependency.
- All business logic lives in one place.
- Auth, validation, and access control are centralized.
- Frontend apps only talk to `api.xbesmart.com`.

---

## 2. Architecture Overview

```
CURRENT STATE:
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  ecom_admin  │     │  ecomWebsite │     │vendor-dashboard│
└──────┬───────┘     └──────┬───────┘     └──────┬────────┘
       │                    │                     │
       ├───→ Django API ←───┤───→ Django API ←────┤
       │                    │                     │
       └───→ Supabase ←────┘───→ Supabase ←──────┘
             (direct)             (direct)

TARGET STATE:
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  ecom_admin  │     │  ecomWebsite │     │vendor-dashboard│
└──────┬───────┘     └──────┬───────┘     └──────┬────────┘
       │                    │                     │
       └────────→ Django API ←────────────────────┘
                     │
                     ├──→ Supabase (internal)
                     ├──→ Cloudflare R2 (storage)
                     └──→ Railway (hosting)
```

---

## 3. Execution Phases

### Phase 1: API Discovery & Inventory ✅ COMPLETE
- Analyze all three frontend repositories (read-only)
- Discover all API calls (Django, Supabase, Storage, Auth)
- Classify and catalog every API interaction
- Create machine-readable inventory
- **Deliverable:** `INVENTORY/` directory fully populated

### Phase 2: Verification (NEXT)
- For each Django API in inventory: verify backend implementation exists
- Compare frontend contract vs backend contract
- Identify mismatches and missing endpoints
- Document frontend issues that need resolution
- **Deliverable:** `VERIFICATION/` directory populated

### Phase 3: Supabase Migration
- For each Supabase SDK/REST/Storage/Auth call:
  - Design Django endpoint that provides equivalent functionality
  - Implement endpoint
  - Test against frontend contract
  - Document migration in `MIGRATIONS/migration_log.md`
- **Deliverable:** Django endpoints replacing all direct Supabase access

### Phase 4: Integration Testing
- Validate all migrated endpoints
- Run comprehensive API tests
- Verify response schemas match frontend expectations
- **Deliverable:** Passing test suite

### Phase 5: Frontend Coordination (out of scope for backend)
- Provide frontend engineers with:
  - New endpoint documentation
  - Migration guide per frontend app
  - Required frontend changes (from `VERIFICATION/frontend_fixes.md`)

---

## 4. Agent Responsibilities

### First Agent (Migration Coordinator) — COMPLETED
- Created artifact structure
- Performed full API discovery
- Created inventory files
- Wrote all framework documentation

### Future Verification Agent
- Read all framework docs (PLAN, RULES, DECISIONS, PROGRESS, HANDOFF)
- Process Django APIs in batches of 15 for verification
- Find backend implementations
- Compare contracts
- Record findings in VERIFICATION/

### Future Migration Agent
- Read all framework docs
- Process Supabase APIs in batches of 5
- Implement Django endpoints
- Test endpoints
- Record in MIGRATIONS/migration_log.md

---

## 5. Batch Workflow

```
1. Read HANDOFF.md → understand current state
2. Read current_batch.md → check for in-progress work
3. Claim next batch (max 15 APIs for verification, max 5 for migration)
4. Update current_batch.md
5. Do work (verify or migrate)
6. Test results
7. Update PROGRESS.md
8. Update relevant inventory/verification/migration files
9. Clear current_batch.md
10. Update HANDOFF.md
11. STOP — wait for user approval before next batch
```

---

## 6. Completion Criteria

The migration is complete when:
- [ ] All Django APIs verified (contract matches)
- [ ] All Supabase REST calls have Django equivalents
- [ ] All Supabase SDK calls have Django equivalents
- [ ] All Storage operations have Django equivalents
- [ ] All Auth operations have Django equivalents
- [ ] All unknown items resolved
- [ ] All tests pass
- [ ] PROGRESS.md shows 100% completion

---

## 7. Stop Conditions

An agent must STOP and update HANDOFF.md when:
- A verification batch of 15 APIs or migration batch of 5 APIs is complete
- A blocking decision needs user input (record in DECISIONS.md)
- An ambiguous contract is found
- A breaking change would be required
- Context window is approaching limit
- Any error that cannot be resolved independently

---

## 8. Resume Instructions

To resume this migration program:

1. Read files in this order:
   - `PLAN.md` (this file) — overall strategy
   - `RULES.md` — mandatory constraints
   - `DECISIONS.md` — past decisions and context
   - `PROGRESS.md` — current status numbers
   - `HANDOFF.md` — what to do next
   - `AGENT_STATE/current_batch.md` — any in-progress work

2. Check PROGRESS.md to determine which phase you're in
3. Read HANDOFF.md to know exactly what the last agent was doing
4. Continue from where the last agent stopped

---

## 9. Repository Map

| Repository | Type | Location | Modifiable? |
|---|---|---|---|
| BeSmartBackend | Django Backend | `/home/unthinkable/Projects/BeSmartBackend` | YES |
| ecom_admin | Admin Frontend (Next.js) | `/home/unthinkable/Projects/ecom_admin` | READ ONLY |
| ecomWebsite | Customer Frontend (Next.js) | `/home/unthinkable/Projects/ecomWebsite` | READ ONLY |
| vendor-dashboard | Vendor Frontend (Next.js) | `/home/unthinkable/Projects/vendor-dashboard` | READ ONLY |

---

## 10. Target Stack

- **Backend:** Django (Python)
- **Database:** Supabase (PostgreSQL) — accessed only from Django
- **Storage:** Cloudflare R2
- **Hosting:** Railway
- **Auth:** Django-managed (using Supabase tokens internally)
