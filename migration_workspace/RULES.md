# Migration Rules

> All agents working on this migration program MUST follow these rules without exception.
> Violations may corrupt migration state or break production systems.

---

## Repository Rules

1. **Frontend repositories are READ ONLY.** Never modify `ecom_admin`, `ecomWebsite`, or `vendor-dashboard`.
2. **All code changes must occur only inside `BeSmartBackend`.**
3. **Never modify migration artifacts from outside `migration_workspace/`** unless explicitly told to.

## Batch Processing Rules

4. **Batch limits:** Max 15 APIs for verification/discovery batches, and max 5 APIs for actual migration/implementation batches.
5. **Always update `AGENT_STATE/current_batch.md` before starting work on a batch.**
6. **Always clear `AGENT_STATE/current_batch.md` after completing a batch.**
7. **Never continue to the next batch automatically.** Stop and wait for user approval.

## Documentation Rules

8. **Update artifacts before stopping.** Every agent must update PROGRESS.md and HANDOFF.md before ending.
9. **Record all decisions.** Any migration decision, exception, interpretation, or architectural choice goes in DECISIONS.md.
10. **Future agents must read DECISIONS.md before work.** Do not repeat decisions already made.

## Git & Version Control Rules

11. **Git branching:** All migration work must happen on a dedicated `migration/supabase-to-django` branch created from `main`.
12. **Commit strategy:** Commits should be grouped logically by module/entity (e.g., "fix: orders serializer contract alignment", "fix: loyalty voucher validation GET support") and made after each batch is verified.

## Compatibility Rules

13. **Maintain API contract compatibility whenever possible.** The frontend should require minimal changes.
14. **Match existing routes/contracts first.** If a Supabase endpoint provides data at `/xyz`, the Django replacement should also serve `/xyz` or document the deviation.
15. **Match request schemas.** Incoming request shapes should remain the same.
16. **Match response schemas.** Response shapes must remain the same unless documented as a breaking change in DECISIONS.md.
17. **Match error behavior.** Error formats and HTTP status codes should be preserved.
18. **Swagger Documentation:** Ensure APIs are well documented in Swagger via `drf-spectacular` annotations.
19. **Testing via Server:** Ensure dev server runs correctly after changes to ensure buildability.

## Verification Rules

20. **Validate before marking complete.** An API is not "verified" or "migrated" until it has been tested.
21. **Never mark an API as complete without testing.**
22. **Testing methodology:** APIs must be tested by running the dev server locally (`python manage.py runserver`) and hitting the endpoints with real HTTP requests (e.g., `curl`). This verifies: the server builds, URLs resolve, middleware/auth works, and response schemas match. `RequestFactory`/`manage.py shell` testing alone is insufficient.
23. **Build verification:** The dev server must start without errors before any batch is considered complete.
24. **Record all frontend issues in `VERIFICATION/frontend_fixes.md`.** Write findings in plain language suitable for frontend engineers and AI agents.

## Implementation Standards

25. **Every migrated API must include:** proper routing, serializers/schemas, validation, error handling, logging, and Swagger/OpenAPI documentation.
26. **Include automated tests where applicable** under `TESTING/`.
27. **Any contract deviation must be documented** in DECISIONS.md with reasoning.

## Safety Rules

28. **Never delete production data.**
29. **Never push to git without explicit user permission.**
30. **Never commit blindly unless explicitly told to do so.**
31. **Always work within the local venv for Python work.** If no venv exists, create one.

## Agent Startup Checklist

Every future agent must read these files in order before beginning work:

```
1. PLAN.md         — overall strategy
2. RULES.md        — this file
3. DECISIONS.md    — past decisions
4. PROGRESS.md     — current numbers
5. HANDOFF.md      — what to do next
6. current_batch.md — any in-progress work
```

Only then may the agent begin work.
