# BeSmartBackendDjango → Supabase Auth Migration Plan

> **Objective:** Update Django backend to use **Supabase Auth** (not native Django JWT) so that users and database remain in Supabase.  
> **Scope:** Auth only – no changes to Flutter app code in this plan.  
> **Date:** February 2025

---

## Current State

| Component | Current | Target |
|-----------|---------|--------|
| **Database** | Supabase Postgres (shared) | Same – Supabase Postgres |
| **Users** | Django `users.User` model (separate table) | Supabase `auth.users` as source of truth |
| **Auth flow** | Flutter → Supabase Auth | Same – Flutter uses Supabase Auth |
| **Django auth** | `rest_framework_simplejwt` (Django-issued JWT) | Supabase JWT validation |
| **Django login/register** | `POST /api/auth/login/`, `register/` | Remove or proxy – auth is Supabase-only |
| **API auth** | Django JWT in `Authorization` header | Supabase access_token in `Authorization` header |

---

## Target Architecture

```
┌─────────────────┐     Supabase Auth      ┌──────────────────┐     Supabase JWT      ┌─────────────────┐
│  Flutter App    │ ────────────────────►  │  Supabase        │                      │  Django         │
│                 │  signIn/signUp/signOut │  auth.users      │                      │  Backend        │
│                 │                        │  (source of      │  Bearer <token>      │                 │
└─────────────────┘                        │   truth)         │ ◄───────────────────│  API endpoints  │
        │                                    └──────────────────┘                      └─────────────────┘
        │                                              │                                        │
        │                                              │ same DB                                │
        └──────────────────────────────────────────────┼────────────────────────────────────────┘
                                                       ▼
                                            ┌──────────────────┐
                                            │  Supabase        │
                                            │  Postgres        │
                                            │  (carts, orders, │
                                            │   products...)   │
                                            └──────────────────┘
```

**Flow:**
1. User logs in via Flutter → Supabase Auth → gets `access_token` (JWT)
2. Flutter sends `Authorization: Bearer <supabase_access_token>` to Django API
3. Django validates the Supabase JWT
4. Django extracts `sub` (user_id) and uses it for `request.user` / authorization
5. Cart, orders, etc. use the same `user_id` as Supabase `auth.users.id`

---

## What Needs to Change

### 1. Django Settings & Dependencies

| Item | Change |
|------|--------|
| `REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES']` | Replace `JWTAuthentication` with custom `SupabaseJWTAuthentication` |
| `rest_framework_simplejwt` | Remove or keep only if needed elsewhere |
| `SIMPLE_JWT` config | Remove or retain for non-auth use |
| New env vars | `SUPABASE_URL`, `SUPABASE_JWT_SECRET` (or `SUPABASE_SERVICE_ROLE_KEY` for server-side validation) |

### 2. New Django Authentication Backend

**File:** `users/authentication.py` (or `besmart_backend/authentication.py`)

**Purpose:** Validate Supabase JWT and attach user to `request`.

**Options for verification:**

| Method | Pros | Cons |
|--------|------|------|
| **A. JWKS URL** | No secret in Django, uses public keys | Needs network for `.well-known/jwks.json`, more code |
| **B. JWT secret (HS256)** | Simple, offline | Secret must be kept secure (JWT secret from Supabase) |
| **C. Call Supabase `/auth/v1/user`** | Server does validation | Extra network call per request |

**Suggested approach:** Start with **B** (JWT secret), then move to **A** if desired.

**Logic:**
```text
1. Read `Authorization: Bearer <token>`
2. Decode and verify JWT (signature, exp, iss)
3. Extract `sub` (user_id) from payload
4. Set request.user = User with id=sub (get_or_create from auth.users/profile if needed)
5. Return 401 if invalid
```

### 3. User Model Strategy

Django models (Cart, Order, etc.) reference `User`. Supabase uses `auth.users` with UUID `id`.

**Options:**

| Option | Description |
|--------|-------------|
| **A. Sync User on first request** | When JWT is valid, `User.objects.get_or_create(id=sub)` using data from Supabase `auth.users` or `profiles` |
| **B. Lazy proxy User** | Custom `User`-like object that only holds `id` from JWT, no DB row |
| **C. Point Django User to auth.users** | `managed=False` model mapped to `auth.users` – schema may not match exactly |

**Recommended:** **A** – keep Django `User` as a mirror of Supabase users, populated on first authenticated request. Ensures FK constraints and ORM keep working.

### 4. Auth Endpoints to Remove or Repurpose

| Endpoint | Current | Target |
|----------|---------|--------|
| `POST /api/auth/login/` | Django JWT login | **Remove** – login stays in Supabase (Flutter) |
| `POST /api/auth/register/` | Django user creation | **Remove or proxy** – registration stays in Supabase |
| `POST /api/auth/logout/` | Blacklist Django refresh token | **Remove or stub** – logout is client-side Supabase |
| `POST /api/auth/refresh/` | Issue new Django JWT | **Remove** – token refresh handled by Supabase |
| `GET /api/auth/me/` | Return Django user profile | **Keep** – return user from Supabase JWT / profiles |
| `PATCH /api/auth/profile/` | Update Django profile | **Keep** – update `profiles` in Supabase DB |

### 5. GET /api/auth/me/ Implementation

- Requires valid Supabase JWT.
- Use `sub` (user_id) from token.
- Fetch user from `auth.users` + `profiles` (or synced Django `User` + `Profile`).
- Return same response shape as today for Flutter compatibility.

### 6. PATCH /api/auth/profile/ Implementation

- Requires valid Supabase JWT.
- Update `profiles` (or equivalent) for `user_id` from JWT.
- Must target the same tables used by Supabase.

### 7. Database Considerations

- **Same DB:** Django and Supabase share Postgres. `carts`, `orders`, etc. use `user_id` that matches `auth.users.id`.
- **User sync:** Ensure `users_user` (or equivalent) has rows for each `auth.users` entry used by the app, with matching `id`.
- **Schema:** Confirm table names (`carts`, `orders`, `profiles`) and that Django models map correctly to Supabase schema.

---

## Implementation Checklist (Django)

### Phase 1: Supabase JWT Authentication

- [ ] Add `PyJWT` (or `python-jose`) if not present.
- [ ] Create `SupabaseJWTAuthentication` class.
- [ ] Verify JWT using Supabase JWT secret.
- [ ] Extract `sub` (user_id) and set `request.user`.
- [ ] Add `SUPABASE_JWT_SECRET` (or similar) to env.
- [ ] Register authentication class in `REST_FRAMEWORK`.
- [ ] Remove or disable `JWTAuthentication` for API routes.

### Phase 2: User Resolution

- [ ] Implement `get_or_create_user_from_supabase(user_id)`.
- [ ] Sync from `auth.users` / `profiles` when creating.
- [ ] Ensure UUID `id` matches `auth.users.id`.

### Phase 3: Auth Endpoints Cleanup

- [ ] Remove `POST /api/auth/login/`.
- [ ] Remove `POST /api/auth/register/`.
- [ ] Remove `POST /api/auth/logout/`.
- [ ] Remove `POST /api/auth/refresh/`.
- [ ] Update `GET /api/auth/me/` to use Supabase user.
- [ ] Update `PATCH /api/auth/profile/` to use Supabase-backed profile.

### Phase 4: Flutter Integration (Separate Task)

- [ ] Revert Phase 1 Flutter auth to Supabase (login, register, logout).
- [ ] Ensure Flutter sends Supabase `access_token` in `Authorization` header.
- [ ] Remove Django JWT usage from Flutter.

---

## Flutter App Changes (Later)

| File | Change |
|------|--------|
| `auth_controller.dart` | Use Supabase Auth again (revert Phase 1 migration) |
| `auth_service.dart` | Use Supabase for auth state |
| `api_client.dart` | Use Supabase `access_token` in `Authorization` header |
| `token_storage_service.dart` | Store Supabase session or remove if unused |

---

## Environment Variables (Django)

```env
# Supabase (already in .env.example)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=...   # or anon for client tokens
SUPABASE_JWT_SECRET=...         # JWT secret from Supabase Dashboard → Settings → API
```

**Where to get JWT secret:** Supabase Dashboard → Project Settings → API → `JWT Secret`.

---

## Risks & Notes

1. **User ID format:** Ensure Supabase `auth.users.id` (UUID) matches Django `User.id` (UUID).
2. **Token refresh:** Supabase handles refresh in the client; Django only validates access tokens.
3. **Anonymous / anon key:** Decide if some endpoints should accept Supabase anon key or remain public.
4. **CORS:** Ensure Django allows requests from Flutter (web, mobile) with the correct origin.
5. **Backward compatibility:** Any client still using Django JWT will break until it switches to Supabase tokens.

---

## Summary: Files to Update

### Django (BeSmartBackendDjango)

| File | Action |
|------|--------|
| `besmart_backend/settings.py` | Add Supabase auth config; switch auth classes |
| `users/authentication.py` | **Create** – Supabase JWT validation |
| `users/views.py` | Remove/modify login, register, logout, refresh |
| `users/urls.py` | Remove login, register, logout, refresh routes |
| `.env` / `.env.example` | Add `SUPABASE_JWT_SECRET` |

### Flutter (ecom_app) – Revert Phase 1

| File | Action |
|------|--------|
| `lib/features/presentation/controllers/auth_controller.dart` | Revert to Supabase Auth |
| `lib/core/services/auth_service.dart` | Revert to Supabase |
| `lib/core/services/django_auth_service.dart` | **Delete** (or keep unused) |
| `lib/features/data/models/django_user_model.dart` | **Delete** (or keep unused) |
| `lib/core/network/api_client.dart` | Use Supabase `access_token` in header instead of stored JWT |
| `lib/core/services/token_storage_service.dart` | Repurpose to store Supabase session, or remove |

---

## References

- [Supabase JWT Docs](https://supabase.com/docs/guides/auth/jwts)
- [Supabase JWT verification (Python)](https://dev.to/zwx00/validating-a-supabase-jwt-locally-with-python-and-fastapi-59jf)
- [Django REST Framework Custom Authentication](https://www.django-rest-framework.org/api-guide/authentication/#custom-authentication)
