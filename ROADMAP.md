# GhostCorp / Kestrelattice — Product Roadmap

This roadmap is an execution plan, not a promise of revenue or autonomous success. Build the smallest reliable loop first, prove it with evidence, then expand.

## Product thesis

Make Kestrelattice a **governed agent mesh that can do useful work and prove what happened**. The differentiator should not be “more agents”; it should be that every agent has a narrow role, a bounded budget, observable results, and a traceable approval path.

## Operating principles

- **Free-first:** prefer GitHub Pages, Cloudflare free-tier services, and provider free tiers until real usage proves a paid service is needed.
- **No secret in the browser or repository:** API keys stay in server-side secret stores. Do not paste secrets into issues, chats, or commits.
- **No spending by default:** autonomous spend is disabled unless the owner sets a hard cap, allowed vendors, and an expiry. Sales revenue is not permission to spend.
- **Approval for irreversible actions:** sending outreach, publishing, purchasing, changing billing, deleting data, and deploying production changes require explicit approval until an audited policy safely permits them.
- **Evidence over vibes:** distinguish proposed, queued, approved, executed, verified, and failed. Never report a sale, customer, deployment, or task completion without evidence.
- **Fail closed:** missing credentials, stale product context, failed payment verification, exceeded budgets, and unavailable providers stop the affected operation.
- **Preserve data:** migrations are additive and reversible; never overwrite queue or KV state during a test.

## Milestone 0 — Make the foundation trustworthy

- [x] Add a guarded Cloudflare Worker deployment workflow.
- [x] Add regression tests for public queue behavior, owner-key checks, missing AI configuration, buyer verification gates, and server-keyed product context.
- [x] Prevent an empty or malformed Code Bot catalog upload from replacing the existing catalog.
- [ ] Configure deployment and provider secrets; deploy and verify the live Worker.
- [ ] Rebuild and upload the private admin HTML through its existing private path.
- [ ] Run a real Gumroad test purchase/license flow; verify invalid, refunded, and eligible purchases.
- [ ] Add a documented rollback procedure and a pre-deploy smoke-test checklist.

**Exit criteria:** all CI checks pass; live endpoints behave as expected; existing queue/KV records are unchanged; no secret is exposed in public output.

## Milestone 1 — Turn the dashboard into a real control plane

- Add a fleet status panel showing each worker/agent, last heartbeat, last successful run, queue depth, and the last error.
- Give every job an immutable run ID and a lifecycle: proposed → approved → running → verified/failed/blocked.
- Add an audit receipt for each external action: actor, purpose, inputs hash, approval, cost estimate, result, timestamp, and rollback link where possible.
- Add a kill switch that pauses new jobs and outbound actions without deleting the queue or logs.
- Add a dry-run mode that explains exactly what would happen before an action is approved.

## Milestone 2 — Make the revenue loop measurable

- Maintain a product catalog with a stable product ID, truthful description, price, checkout link, delivery artifact, and support instructions.
- Track funnel stages separately: page view → outbound checkout click → confirmed purchase → delivery/support request. Never infer a sale from a click.
- Build a daily digest of confirmed sales, refunds, product-page changes, support issues, and next best experiments.
- Test one small marketing experiment at a time; define its success metric and stop condition before launch.
- Keep Gumroad as the current checkout provider. Add Stripe only after account ownership, test-mode checkout, signed webhook verification, refund handling, idempotency, and reconciliation are implemented and tested.

## Milestone 3 — Make agents improve safely

- Add a scheduled opportunity radar that collects public evidence, estimates effort and cost, scores fit with the existing catalog, and proposes—not automatically executes—experiments.
- Add a reviewer agent that challenges claims, checks source quality, looks for policy violations, and flags unsupported revenue projections.
- Add an evaluation suite with representative tasks and expected outcomes before changing prompts or models.
- Compare versions against accuracy, task completion, latency, cost, and failure rate. Roll back a regression automatically when the prior version is safer.
- Allow agents to suggest code changes on isolated branches and open pull requests; production merges and deployments remain approval-gated.

## Milestone 4 — Earn the right to be autonomous

Only after reliable metrics and tested controls exist:
- Let low-risk, reversible tasks run within per-task and monthly hard caps.
- Use separate budgets for model calls, hosting, APIs, and advertising; never permit one agent to raise its own caps.
- Require owner approval for new vendors, subscription upgrades, ad spend, payments, legal commitments, and policy changes.
- Add idempotency keys, duplicate-action detection, circuit breakers, and an automatic stop when provider errors or costs exceed thresholds.
- Publish a weekly evidence report: what ran, what it cost, what it produced, what failed, and what the system recommends next.

## Near-term priority order

1. Finish secret setup and deploy the current Worker safely.
2. Verify the private admin chat and Code Bot end-to-end with test credentials and a real eligible Gumroad test license.
3. Make the private dashboard reflect real health, run history, queue state, and confirmed sales.
4. Add end-to-end tests and rollback before enabling any automated outbound actions.
5. Improve one measurable product/marketing funnel at a time.
6. Add more agents only when a specific bottleneck is demonstrated.

## Explicit non-goals for now

- No promise of guaranteed or passive income.
- No unbounded self-reinvestment or agent-controlled budget increases.
- No fabricated testimonials, sales numbers, traffic, or buyer verification.
- No production deployment solely because an AI says a change is ready.
- No replacing the existing checkout provider before a tested migration plan exists.
