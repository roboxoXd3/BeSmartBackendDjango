# Summary of API Changes

This branch (`feature/user-admin-currency-apis`) contains changes implemented to support extended user options, verification, avatar upload, and admin platform settings.

## Summary of Changes

### 1. User & Authentication App (`users/`)
* **New Views (`users/views.py`):**
  * `PasswordResetConfirmView`: Confirms email password resets via OTP (`type: "recovery"`) and updates the user's password using the resulting session token.
  * `UploadAvatarView`: Handles uploading profile images (`avatar` field) for authenticated users using standard Django file storage.
  * `VerifyEmailView`: Verifies a user's signup email using a verification token (OTP).
  * `ResendVerificationEmailView`: Allows resending signup verification emails using Supabase's `auth.resend`.
  * `UserAddressesView`: Lists the authenticated user's shipping addresses from the database.
  * `UserPaymentMethodsView`: Lists the authenticated user's saved payment methods.
  * `AccountDeleteView`: Refactored to map to the `DELETE` HTTP verb instead of `POST`, changing the endpoint route.
* **URL Router Updates (`users/urls.py`):**
  * Configured paths for all the new views.
  * Standardized/Renamed the following endpoints:
    * `/token/refresh/` $\rightarrow$ `/refresh/`
    * `/password/reset/` $\rightarrow$ `/password-reset/`
    * `/password/change/` $\rightarrow$ `/change-password/`
    * `/account/delete/` $\rightarrow$ `/account/`

---

### 2. Admin & Settings App (`admin_api/`)
* **New Views (`admin_api/views.py`):**
  * `PlatformSettingsView` (`GET`/`PATCH`): Fetches and updates platform-wide configuration settings stored key-value style.
  * `AppConfigSettingsView` (`GET`/`PATCH`): Fetches and updates specific configuration options tailored for the mobile applications.
  * `AdminCurrencyRatesView` (`GET`): Lists all currency exchange rates.
  * `AdminUpdateCurrencyRatesView` (`POST`): Batch updates or creates exchange rates.
* **URL Router Updates (`admin_api/urls.py`):**
  * Mapped settings endpoints to router paths under `/settings/platform/`, `/settings/app-settings/`, `/settings/currency-rates/`, and `/settings/update-rates/`.

---

### 3. Currency App (`currency/`)
* **URL Endpoint Renames (`currency/urls.py`):**
  * Renamed `/rates/` to `/supported/`.
  * Renamed `/preference/` to `/user-preference/`.
