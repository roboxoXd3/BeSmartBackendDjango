# Setting up alerts in Grafana

This is written for whoever is doing the Grafana setup, not for a developer. No code
changes are needed for anything in this document — it's all clicking around in Grafana.

Background: the backend already sends metrics (numbers, like "how many requests failed")
to Prometheus, and logs (text lines, like "payment failed for order X") to Loki. Grafana
can already show both. What's missing is Grafana **telling someone** when something looks
wrong, instead of you having to go look at a dashboard to notice.

An alert has three parts:
1. **The rule** — what to watch, and how bad is "bad enough to tell someone".
2. **The contact point** — where the message goes (Slack channel, email, phone call).
3. **The notification policy** — which rule goes to which contact point, and how often
   it's allowed to repeat.

Do these in order: contact point first, then notification policy, then the rules
themselves — a rule with nowhere to send its alert just fails silently.

---

## Part A — What to set up in Grafana

### Step 1: Contact point

In Grafana: **Alerting → Contact points → Add contact point**.

Pick where alerts should go. A Slack channel is the easiest to start with (Grafana has a
built-in Slack integration — you just need a Slack webhook URL). Email works too but
people tend to miss it. If you want night-time alerts to actually wake someone up, you'll
need something like PagerDuty or Opsgenie, which are separate services Grafana can send
to — that's more setup and probably not needed on day one.

**Suggestion for day one:** one Slack channel, e.g. `#backend-alerts`, for everything. You
can split into separate channels per team later once you see how much volume comes in.

### Step 2: Notification policy

**Alerting → Notification policies**.

This is the rule for "which alert goes where, and how often it can repeat". At minimum,
set:
- **Group wait**: 30s (wait a bit to bundle alerts that fire at the same time into one
  message, instead of five separate pings)
- **Repeat interval**: 4h (if something is still broken, remind again every 4 hours
  instead of every minute)

You can add more specific routing later (e.g. "payment alerts go to the payments team
channel, site-down alerts go to everyone") once you know who owns what.

### Step 3: The alert rules

For each rule below: **Alerting → Alert rules → New alert rule**, paste the query, set
the threshold, write the description, pick the contact point from Step 1.

Every query already works today — the metrics and logs it reads already exist in
production. You do not need to wait for anything else before setting these up.

---

#### 1. Service is down

**What it watches:** whether the backend responds to a basic health check at all.

**Query (Prometheus):**
```
up{job="besmart-backend"} == 0
```
(The exact `job` label name depends on how Prometheus is configured to scrape this
service — check your Prometheus config or the Grafana Explore view if `up{job="..."}`
doesn't match anything.)

There is now also a dedicated endpoint at `/health/` built specifically for this kind of
check — it returns HTTP 200 when the database (and Redis, where used) are reachable, and
503 otherwise. If your Prometheus/Grafana setup can alert on an HTTP status code directly
(a "blackbox" style check), point it at `/health/` instead — it's a more meaningful
"is the service actually working" check than just "did it respond to a network ping".

**Suggested threshold:** fire if this is true for **2 minutes** straight (avoids alerting
on a single missed scrape).

**What firing means, in plain words:** the backend is completely unreachable, or its
database (or Redis) connection is broken. Nobody can place an order, log in, or do
anything. This is the most urgent alert — treat it like the site is down.

---

#### 2. Too many failed requests (5xx errors)

**What it watches:** the rate of server errors across the whole API.

**Query:**
```
rate(django_http_responses_total_by_status_total{status=~"5.."}[5m])
```

**Suggested threshold:** fire if this is above **1 per second sustained for 5 minutes**.
This number is a guess — see "tuning thresholds" at the end.

**What firing means, in plain words:** something in the backend is throwing errors more
than usual. Could be one broken endpoint, could be everything. Check the Grafana
dashboard or Loki logs filtered to `error` level to see what's actually failing.

---

#### 3. Requests are slow

**What it watches:** how long requests are taking to answer (95th percentile — meaning
19 out of 20 requests are faster than this number).

**Query:**
```
histogram_quantile(0.95, rate(django_http_requests_latency_seconds_by_view_method_bucket[5m]))
```

**Suggested threshold:** fire if this is above **3 seconds** for 10 minutes. Ask the
business team what "too slow" means for checkout specifically (see Part B) — this is a
site-wide number and a single slow endpoint (like a report) shouldn't page anyone.

**What firing means, in plain words:** the site is working but sluggish. Customers are
waiting longer than normal for pages to load.

---

#### 4. Database problems

**What it watches:** database errors (connection failures, bad queries).

**Query:**
```
rate(django_db_errors_total[5m]) > 0
```

**Suggested threshold:** fire on **any** sustained rate above zero for 5 minutes — this
metric should normally be flat at zero, so any real activity here is worth a look.

**What firing means, in plain words:** the backend is having trouble talking to the
database. Could turn into the site being fully down if it gets worse — treat as urgent.

---

#### 5. Payments failing

**What it watches:** the payment success/failure counter that was just added to the code
(`besmart_payment_attempts_total`, tagged by whether it was starting a payment,
confirming one, or a webhook from Squad, and whether it succeeded or failed).

**Query — failure ratio over the last 15 minutes:**
```
sum(rate(besmart_payment_attempts_total{status=~"failed|error"}[15m]))
/
sum(rate(besmart_payment_attempts_total[15m]))
```

**Suggested threshold:** fire if this ratio is above **10%** for 15 minutes, **and** there
were at least a handful of attempts (so 1 failure out of 1 attempt at 3am doesn't page
anyone — Grafana can combine two conditions like this in one rule).

**What firing means, in plain words:** a noticeable share of customers trying to pay are
failing. This is a revenue-impacting alert — see Part B for who should get this one and
how urgently.

---

#### 6. Vendor payouts failing

**What it watches:** `besmart_payout_transfers_total`, same idea as payments but for money
going *out* to vendors.

**Query:**
```
increase(besmart_payout_transfers_total{status=~"failed|error"}[1h]) > 0
```

**Suggested threshold:** fire on **any** failure in the last hour — payouts happen far
less often than customer payments, so even one failure is worth a look, not an emergency
page. Ask the business team whether this should wait until morning (see Part B).

**What firing means, in plain words:** money that was supposed to go to a vendor's bank
account didn't go through.

---

#### 7. Login/auth problems

**What it watches:** `besmart_auth_attempts_total`, specifically the `misconfigured` and
`error` outcomes (not `invalid_token` — that one just means someone's login expired,
which is normal and happens constantly; it's excluded on purpose).

**Query:**
```
increase(besmart_auth_attempts_total{result=~"misconfigured|error"}[10m]) > 0
```

**Suggested threshold:** fire on **any** occurrence. This should be rare — if Grafana
alerts on this and it turns out to fire often, that's itself useful information (it means
something about the login integration is flaky and worth digging into, regardless of
whether you'd originally call it "alert-worthy").

**What firing means, in plain words:** logins are breaking for a reason that isn't just
"someone's session expired" — either the connection to the login provider (Supabase) is
down, or it's misconfigured. If this fires, potentially nobody can log in at all.

---

### A note on the log-based option

Everything above uses Prometheus (numbers). You can also alert directly off Loki (the
logs), which is useful for one-off or rare events that don't have a counter yet. Example —
alert if any of these specific error events show up at all:
```
{app="besmart_backend", env="production"} | json | event=~"vendor_payout_error|admin_squad_transfer_exception|payment_webhook_order_not_found"
```
This is a reasonable fallback for anything not covered by a metric above, but prefer the
Prometheus rules where they exist — counters are cheaper for Grafana to evaluate
repeatedly and don't depend on log message text staying exactly the same over time.

---

## Part B — Questions to ask the business team

These aren't technical questions — they're judgment calls about how the business wants to
be woken up (or not) when something breaks. Each one has a default so alerting can go live
today without waiting for a meeting; update the rule later once you have a real answer.

1. **If payments start failing at 3am, does someone need to be woken up, or can it wait
   until morning?**
   Default until answered: wake someone up. Money coming in stopping is usually the
   worst-case scenario for a shopping site.

2. **What's an acceptable amount of failed payments before it's a real problem, versus
   just normal card declines?** (e.g. some percentage of attempts failing is completely
   normal — declined cards, insufficient funds, are the customer's problem, not ours.)
   Default until answered: 10% of attempts failing within 15 minutes.

3. **If a vendor payout fails, does someone need to act immediately, or is "we'll look at
   it in the morning" fine?**
   Default until answered: not urgent — goes to a Slack channel, no phone call.

4. **How slow is "too slow"?** e.g. is 1 second acceptable for checkout but 5 seconds for
   a big product listing page is fine?
   Default until answered: 3 seconds, measured across the whole site (not checkout
   specifically — that would need its own rule later).

5. **Who is the contact for "money is broken" (payments/payouts) versus "the site is
   broken" (it's down, or slow)?** These are often different people or teams.
   Default until answered: same person/channel gets both for now.

6. **Is there a quiet-hours policy** — e.g. non-urgent alerts shouldn't ping anyone
   between certain hours, but the "site is down" alert always should, regardless of time?
   Default until answered: no quiet hours yet; every alert notifies immediately.

7. **How many admin login failures in a row look like an attack rather than someone
   forgetting their password?** This isn't covered by a rule above yet — worth deciding
   once you have a sense of normal failed-login volume.
   Default until answered: not alerted on yet — needs a real number from watching normal
   traffic first.

---

## One more thing: these numbers are guesses

Every threshold in Part A (10%, 3 seconds, 1 error/second, etc.) is a reasonable starting
point, not a measured one — there's no history of real traffic to base them on yet. Plan
to revisit every rule after about a week of it running in production: look at how often
each one actually fired, and whether that matched something genuinely worth knowing about.
If a rule fires constantly and nobody acts on it, loosen it — an alert nobody trusts gets
ignored, which defeats the point of having it.
