# Autonomy and operations status

This repository is not yet fully autonomous. This file defines what is verified and what remains blocked; a green CI run is not proof that sales or delivery occurred.

## Automated checks now in the repository

- Worker syntax and regression tests run in GitHub Actions.
- Builder Python syntax is validated in CI.
- Scheduled health checks run every six hours against the public homepage, flagship product page, sitemap, robots file, and flagship Gumroad checkout.
- The Worker exposes a public, read-only `GET /health` liveness endpoint. It does not read or write KV and does not expose secrets.
- The scheduled health workflow can check the Worker too when the repository variable `CLOUDFLARE_WORKER_URL` is set to its deployed base URL (for example, a URL ending in `.workers.dev`, if that is the deployed address).

## Still required before unattended operation

1. **Deployment:** Add the Cloudflare API token as the GitHub Actions secret `CLOUDFLARE_API_TOKEN`. The secret value must only be entered in GitHub's secret form; never put it in source code or chat.
2. **Worker live check:** Set the repository variable `CLOUDFLARE_WORKER_URL` to the real deployed Worker URL. Do not guess the URL.
3. **Secrets and integrations:** Verify the Worker has its required `WRITE_KEY`, `SERVER_KEY`, `GROQ_API_KEY`, and `GUMROAD_API_KEY` secrets configured in Cloudflare.
4. **Product context:** Load a verified, non-empty product catalog into the private Code Bot context. Never upload an empty catalog to production.
5. **Revenue truth:** Count a sale only after the payment provider confirms it. Checkout clicks and pageviews are not revenue.
6. **Delivery and refunds:** Verify delivery, refund/chargeback handling, and support escalation against real test transactions before unattended customer operations.
7. **Autonomy limits:** Keep spend at $0 by default, preserve existing product prices/checkout links/customer data, and require human approval for paid spend, public outreach at scale, account/security changes, and destructive data operations.

## What scheduled checks mean

A successful health run verifies only the endpoints listed in that run. It does not prove that the Worker was deployed, that API keys work, that a sale happened, or that a buyer received a file. A failed run appears in GitHub Actions and should be treated as an operational alert.
