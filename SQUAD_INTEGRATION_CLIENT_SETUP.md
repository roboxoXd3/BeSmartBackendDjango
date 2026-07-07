# Squad Payment Integration — Client Setup Guide

**Date:** 2026-07-06  
**For:** Client / Squad Account Owner  
**From:** Backend Team  
**Backend deployed at:** Railway (`api.xbesmart.com`)

---

## What We Need From You

### 1. ✅ API Keys — Already Provided

We currently have the following keys configured in the backend:

| Key | Status | Value (masked) |
|:----|:-------|:------|
| Secret Key (`SQUAD_PRIVATE_KEY`) | ✅ Configured | `sk_ff480f...f491` |
| Public Key (`SQUAD_PUBLIC_KEY`) | ✅ Configured | `pk_ff480f...f38e` |
| Base URL (`SQUAD_BASE_URL`) | ✅ Configured | `https://api-d.squadco.com` |

> **Note:** The current base URL (`api-d.squadco.com`) is the **sandbox/development** environment. For production, this needs to be changed to `https://api.squadco.com`. Please confirm when you're ready to switch.

---

### 2. ⚠️ Webhook Secret — MISSING (Action Required)

The backend validates every Squad webhook using **HMAC-SHA512 signature verification**. Squad sends a signature in the `x-squad-encrypted-body` header, and we verify it using a shared secret.

**Currently, the `SQUAD_WEBHOOK_SECRET` env variable is set to a URL — not an actual secret.** This means webhook signature validation will fail for every incoming webhook.

**What we need:** The webhook **hash secret** from your Squad dashboard. This is NOT a URL — it's a random string that Squad provides when you set up a webhook endpoint.

**Where to find it:**
1. Log into your [Squad Dashboard](https://dashboard.squadco.com) (or [Sandbox Dashboard](https://sandbox.squadco.com))
2. Navigate to **Settings** → **API & Webhooks** (or **Webhook Configuration**)
3. Look for the **Webhook Secret** or **Hash** field — it will be a long random string like `sk_test_abc123def456...`
4. Copy this value and share it with us securely

We will set it as the `SQUAD_WEBHOOK_SECRET` environment variable on the backend.

---

### 3. ⚠️ Webhook URL Configuration — Action Required

You need to register our backend webhook URL in your Squad dashboard so Squad knows where to send payment notifications.

**Our webhook URL:**
```
https://api.xbesmart.com/api/payments/webhook/
```

**How to set it up:**
1. Log into your [Squad Dashboard](https://dashboard.squadco.com) (or [Sandbox Dashboard](https://sandbox.squadco.com))
2. Navigate to **Settings** → **API & Webhooks**
3. In the **Webhook URL** field, enter:
   ```
   https://api.xbesmart.com/api/payments/webhook/
   ```
4. Make sure to **include the trailing slash** (`/`) — Django requires it
5. Save the configuration
6. If Squad provides a **Test Webhook** button, click it and let us know the result

**Events we handle:**
- `charge_successful` — when a customer payment succeeds

---

### 4. ⚠️ Card Tokenization — Confirm Enabled

Our backend supports **recurring payments using card tokenization** (saving cards for future charges). For this to work:

1. **Tokenization must be enabled** on your Squad account
2. This is typically not on by default — you may need to request it from Squad support
3. When enabled, successful payment webhooks will include a `token_id` in `Body.payment_information.token_id`
4. We use this token to charge saved cards via Squad's `POST /transaction/charge_card` endpoint

**Please confirm with Squad support that tokenization is enabled for your account.**

---

### 5. ⚠️ Transfer/Payout Capability — Confirm Enabled

Our backend includes vendor payout functionality using Squad's transfer API (`POST /payout/transfer`). For this to work:

1. **Transfer capability must be enabled** on your Squad merchant account
2. You may need to complete additional KYC/compliance steps with Squad
3. **Bank account lookup** uses `POST /payout/account/lookup` — needs to be active too

**Please confirm with Squad that transfers are enabled for your merchant account.**

---

### 6. Production Migration Checklist

When you're ready to go live, the following environment variables need to be updated on Railway:

| Variable | Sandbox Value | Production Value |
|:---------|:-------------|:-----------------|
| `SQUAD_BASE_URL` | `https://api-d.squadco.com` | `https://api.squadco.com` |
| `SQUAD_PRIVATE_KEY` | `sk_ff480f...` (sandbox) | Your **live** secret key |
| `SQUAD_PUBLIC_KEY` | `pk_ff480f...` (sandbox) | Your **live** public key |
| `SQUAD_WEBHOOK_SECRET` | *(to be provided)* | Your **live** webhook hash |

You will also need to register the webhook URL in the **live/production** Squad dashboard (same URL, just register it on the production side).

---

## Summary — Action Items for Client

| # | Action | Who | Status |
|:--|:-------|:----|:-------|
| 1 | Provide the **Webhook Hash Secret** from Squad dashboard | Client | ❌ Needed |
| 2 | Register webhook URL in Squad dashboard | Client | ❌ Needed |
| 3 | Confirm **card tokenization** is enabled on your Squad account | Client | ❌ Needed |
| 4 | Confirm **transfer/payout** capability is enabled | Client | ❌ Needed |
| 5 | Provide **production API keys** when ready to go live | Client | ⏳ Later |
| 6 | Register webhook URL in **production** Squad dashboard | Client | ⏳ Later |

---

## API Endpoints Using Squad

For reference, here are all the backend endpoints that interact with Squad:

| Endpoint | Method | Purpose |
|:---------|:-------|:--------|
| `/api/payments/initiate/` | POST | Start a new payment (creates Squad checkout) |
| `/api/payments/verify/{ref}/` | GET | Verify a payment by transaction reference |
| `/api/payments/webhook/` | POST | Receives webhooks from Squad (auto, not user-facing) |
| `/api/payments/charge-token/` | POST | Charge a saved card using token (recurring) |
| `/api/vendors/bank-accounts/` | CRUD | Vendor bank accounts (used for payouts) |
| *Payout transfer* | Internal | Admin-initiated payout via Squad transfer API |

---

## Technical Details (For Your Records)

- **Webhook signature verification:** HMAC-SHA512 using `x-squad-encrypted-body` header
- **Amount handling:** All amounts are converted from Naira to Kobo (×100) before sending to Squad
- **Transaction refs:** Generated as `BESMART-{random}` for regular payments, `BESMART-REC-{random}` for token charges
- **Token storage:** Saved in `PaymentMethod.squad_token` field, linked to the customer's account
- **Transfer refs:** Must include merchant ID as per Squad docs — format used by our system
