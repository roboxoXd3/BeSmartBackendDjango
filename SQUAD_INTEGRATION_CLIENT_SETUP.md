# Squad Payment Setup Guide

Hello! We are finalizing the payment setup for the platform. We need you to do 3 quick things on your Squad account so that payments and payouts can work automatically.

### 1. Set the Webhook URL
We need your Squad account to send payment alerts to our system. 
**Where to do it:**
1. Log in to your [Squad Dashboard](https://dashboard.squadco.com/).
2. On the left menu, click on **Settings** or **Developers**, then click on **API / Webhooks**.
3. Look for a field labeled **Webhook URL**.
4. Copy and paste exactly this text into that box:
   `https://api.xbesmart.com/api/payments/webhook`
5. Click Save.

### 2. Send us your Webhook Hash (If you have one)
On that exact same **API / Webhooks** page, look for a field named **Webhook Hash** or **Webhook Secret**.
**What we need:**
- If you see a Webhook Hash there, please copy it and send it to us.
- *(If there is no Webhook Hash field shown on your dashboard, just tell us and we'll use your standard keys instead.)*

### 3. Verify Transfers are Enabled
Our system needs to automatically send payouts to your vendors' bank accounts.
**What we need:**
- Please contact Squad Support (or check your account status) and simply confirm with them: *"Are Transfers and Payouts enabled for my live account?"*
- Let us know once you've confirmed this with them.

That's it! Please let us know once you've pasted the link and copied the hash (if any).
