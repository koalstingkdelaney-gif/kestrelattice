# GhostCorpNet Growth Engine

This document extends the existing governed-agent mesh with a practical, evidence-led growth loop. It is additive: it does not replace the existing catalog, checkout provider, dashboard, KV records, or approval workflow.

## Objective

Move from "many products are listed" to "we know which offers attract qualified visitors, generate checkout intent, convert into confirmed sales, and create useful follow-on work."

No workflow may claim revenue from page views, outbound clicks, test transactions, or unverified webhook events.

## 1. Offer architecture using existing products

Start by making the current AI Break-Test family easier to understand; do not create more products until this funnel has evidence.

| Offer | Current listed price | Role | Buyer outcome to make explicit |
|---|---:|---|---|
| AI Break-Test — Starter | $49 | Entry offer | A clearly scoped first-pass test and concise findings |
| AI Break-Test — Full | $149 | Expanded assessment | Broader attack coverage, findings report, and stated re-test terms |
| AI Break-Test — Fleet | $399 | Multi-agent offer | Compare three authorized bots and prioritize the weakest link |
| AI Break-Test — Enterprise | $999 | High-touch offer | A scoped engagement across the buyer's authorized AI surface |

Before promoting a tier, verify its live checkout, delivery artifact, exact scope, turnaround time, support terms, and any re-test promise. Do not imply that a template pack is a performed security assessment. Security testing requires written authorization and a clearly bounded target.

The existing Prompt-Injection Test Deck ($29) can be positioned as a self-serve learning/testing product, distinct from the performed Starter service. Keep the distinction obvious.

## 2. Funnel measurement contract

Record each stage as its own event:

1. `product_view`: product page rendered.
2. `checkout_click`: visitor intentionally leaves for a known checkout URL.
3. `purchase_confirmed`: payment provider confirms a real transaction through a verified server-side source.
4. `refund_confirmed`: provider confirms a refund or charge reversal.
5. `delivery_confirmed`: delivery system confirms the promised artifact or service handoff.
6. `support_requested`: a customer requests help.

For web analytics, use GA4 events and include stable, non-sensitive product identifiers, page path, and campaign source where available. Never send email addresses, license keys, payment details, secrets, or free-text customer content to analytics.

A checkout click is intent, not a sale. A purchase event must not be synthesized in the browser from a return URL. Confirm purchases using a trusted provider API/webhook or reconciled seller report. Deduplicate provider events using a stable transaction/event ID. Revenue reporting must state currency and whether it is gross, refunded, or net of fees.

## 3. The owner-facing growth scorecard

Show the following by product and by date range, with a source and last-updated timestamp:

- Product views
- Unique outbound checkout clicks
- Checkout-click rate = checkout clicks / product views
- Confirmed paid orders and units
- Gross sales, refunds, fees when available, and net revenue when calculable
- Purchase conversion rate = confirmed paid orders / product views
- Delivery failures and support requests
- Data freshness and any failed integration checks

Use `unknown` rather than zero when a data source is unavailable. Show zero only when a source was successfully queried and returned zero. Label estimates separately from provider-confirmed totals.

## 4. Daily growth loop

A scheduled report should:

1. Read analytics and payment data using read-only credentials where possible.
2. Identify the largest evidenced funnel drop-off or operational failure.
3. Propose one experiment with a baseline, a single change, a success metric, a minimum observation window, and a stop condition.
4. Produce a draft change or recommendation for owner review.
5. After approval, record the experiment ID and compare results to the baseline.
6. Keep an audit receipt of the inputs, decision, approval, changes, outcome, and timestamp.

Initial experiments should be low-risk and reversible: clarify product scope, improve the comparison between tiers, repair broken checkout links, improve the sample preview, or improve the page's call to action. Avoid changing multiple variables at once.

## 5. Catalog and checkout integrity

Run a scheduled, read-only audit of every product in the source catalog:

- Stable product ID and unique slug
- Product title and listed price
- Canonical page and live checkout URL
- Checkout HTTP response where safely checkable
- Expected deliverable exists and is readable
- Product page price matches the approved catalog
- Sitemap inclusion/exclusion is intentional
- Last successful check and last error

Do not use HTTP 200 alone as proof that a checkout is purchasable or that a product has been delivered. Report redirects and provider-side availability separately. Do not automatically edit prices or replace checkout URLs based only on scraped page content.

## 6. Approval and budget boundaries

- Public outreach, paid advertising, purchases, price changes, publishing new claims, and production deploys require owner approval.
- Agents cannot raise their own spend caps or add new payment methods.
- No ad spend or paid API usage by default; free-first until a separately approved, hard-capped budget exists.
- Limit automated research and model calls by per-run and monthly caps; stop on provider errors or missing budget data.
- Preserve existing KV state and customer records; use additive migrations and dry-run previews.
- Keep buyer data and payment secrets out of public logs, source control, analytics, and AI prompts unless strictly necessary and authorized.

## 7. Rollout order and acceptance criteria

### Phase A — Establish the baseline
- [ ] Verify the current GA4 property receives real-time page events.
- [ ] Verify outbound Gumroad clicks appear as events; Google Analytics enhanced measurement can collect outbound clicks when enabled.
- [ ] Inventory every live product and compare it with the current health check's coverage.
- [ ] Reconcile reported sales against the Gumroad seller dashboard for a fixed date range.
- [ ] Record missing data sources explicitly; do not fabricate values.

### Phase B — Improve the flagship funnel
- [ ] Verify Starter, Full, Fleet, Enterprise and the $29 test deck each deliver exactly what their sales page promises.
- [ ] Add clear scope, exclusions, turnaround, deliverable examples, and authorized-testing requirements where applicable.
- [ ] Publish a tier comparison and link only to verified live checkouts.
- [ ] Run one documented conversion experiment at a time.

### Phase C — Connect the control plane
- [ ] Add a private growth scorecard backed by trusted analytics and seller data.
- [ ] Add idempotent purchase/refund reconciliation and a visible freshness/error state.
- [ ] Generate a daily evidence-based recommendation; never auto-publish it.
- [ ] Add tests for duplicate events, refunds, missing credentials, stale data, malformed catalog rows, and source outages.

### Definition of done
The system can distinguish views, intent, verified sales, refunds, delivery, and unknown data; each number has a source and freshness timestamp; one experiment can be traced from hypothesis through approved change to measured result; and existing products, KV records, and checkout links remain intact.

## References

- [Google Analytics: Measure outbound clicks](https://support.google.com/analytics/answer/13566436)
- [Google Analytics: Set up events](https://developers.google.com/analytics/devguides/collection/ga4/events)
- Existing implementation and deployment constraints: [ROADMAP.md](ROADMAP.md), [worker/DEPLOYMENT.md](worker/DEPLOYMENT.md)
