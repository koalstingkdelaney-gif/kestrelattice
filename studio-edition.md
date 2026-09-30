# The Governed Agent Mesh Playbook — Studio Edition

**The $29 companion to the free playbook: policies, schemas, worksheets, and rollout plans you can adopt as-is.**

By GhostCorp · ghostcorpnet · September 2026

---

## How to use this edition

The free playbook told you *what* governed agent operations look like: eight layers, three risk tiers, a fourteen-day outline. This edition is the *how* — the documents, schemas, worksheets, and day-by-day plans you fill in and adopt directly.

**What it assumes you've read.** The free playbook, in full. Nothing here re-explains the eight-layer stack, the tier definitions, or why warnings decay into ignored banners. Every part of this edition maps to a section of that playbook; cross-references are marked as you go.

**How to work through it.**

1. **Adopt the six policies (Part 1) first.** They are written fill-in-the-brackets so you can copy them into your repo or wiki as-is. A policy with your team name, your amounts, and your dates in it beats a perfect policy you never publish.
2. **Stand up the two schemas (Part 2).** The plan bound is the unit your governance operates on; the audit row is the unit your evidence lives in. Validate against them from day one.
3. **Decide what to buy (Part 3), then tier what you run (Part 4).** The vendor matrix keeps you honest about what tooling does and doesn't give you. The worksheet forces every capability into a tier with a named owner.
4. **Run the fourteen days (Part 5).** Each day has concrete tasks and checkable acceptance criteria. Do them in order — the layers stack, and each assumes the ones before it.
5. **Sell it (Part 6)** only when the governance is real. The first-customer kit gives you pricing guidance, honest funnel math, and one cold-email template — all built from the same evidence files as the free playbook.

**The evidence discipline, unchanged.** Every number in this edition comes from exactly two sources: our pricing-and-economics research and our buyer-demand ledger. No invented benchmarks, no "industry experts say." Where a value is yours to decide, it appears as a bracket: [LIKE THIS]. Fill every bracket before you call a policy adopted.

**Who this is for.** Venture studios, AI-native founders, and small teams running multi-agent workflows who need governance this month — not after a vendor evaluation cycle. If you have more lawyers than engineers, hire the lawyers. Everyone else: start day 1 tomorrow.

---

## Part 1 — Approval & spend-limit policy templates

Six policies, written to be adopted as-is. Copy each into your repo or wiki, fill every bracket, set an effective date, and name an owner. A policy counts as adopted when all three are true: brackets filled, owner named, team notified.

Convention: [BRACKETED CAPS] are your inputs. Nothing else needs editing.

### Template 1 — Agent identity policy

```
AGENT IDENTITY POLICY — [TEAM NAME]
Version [VERSION] · Effective [DATE] · Owner: [POLICY OWNER]

1. Every agent, script, cron job, or scheduled workflow that can take an action
   in [TEAM NAME]'s stack MUST hold a stable, owner-scoped identity before its
   first action.
2. Identity format: agent:[OWNER]/[NAME] (e.g. agent:[OWNER]/researcher).
3. Anonymous, shared, or unregistered actors are REJECTED at the dispatch path.
   They are never warned about.
4. A capability request arriving with no recorded identity parks as
   REQUIRES_OWNER_ACTION and appears in [OWNER]'s queue within [TIME].
5. Identities are recorded in [IDENTITY REGISTRY LOCATION] with: identity,
   owner, date issued, status.
6. Decommissioned agents have their identities revoked within [TIME] of
   retirement. A revoked identity is never reissued to a different agent.
```

### Template 2 — Grant issuance policy

```
GRANT ISSUANCE POLICY — [TEAM NAME]
Version [VERSION] · Effective [DATE] · Owner: [POLICY OWNER]

1. No action runs without an explicit grant. Grants are records, not assumptions.
2. Every grant records: capability, scope, issuing owner, date issued, expiry
   date, and the identity it is issued to.
3. Least privilege by default: each grant covers the minimum capability and
   scope the agent has demonstrated it needs.
4. Grants expire after [DURATION]. Permanent grants are prohibited.
5. Auto-grant is prohibited. Every grant requires an explicit issuance decision
   by [GRANT AUTHORITY ROLE].
6. Changing a grant (a permission change) is a Hard-gated action: it requires
   human approval under the Hard-Gated Action Policy.
```

### Template 3 — Hard-gated action policy

```
HARD-GATED ACTION POLICY — [TEAM NAME]
Version [VERSION] · Effective [DATE] · Owner: [POLICY OWNER]

The following actions ALWAYS require a recorded human approval. No auto-grant
path exists for them, ever:

1. Moving money or committing spend above [THRESHOLD].
2. Accepting contracts, terms of service, or legal agreements.
3. External outreach: emails, messages, posts, or calls to anyone outside
   [TEAM NAME].
4. Accessing, reading, or transmitting credentials or secrets.
5. Changing agent permissions or grants.
6. Any action with legal or regulatory consequences in [JURISDICTION].

Rules:

7. The approver must be a human holding the [APPROVER ROLE] role. The acting
   agent can never approve its own action.
8. Each approval is recorded in the audit log with: approver identity,
   timestamp, action reference, and decision.
9. A denied or missing approval produces a recorded BLOCK, persisted with the
   exact blocked result — never a silent skip.
```

### Template 4 — Spend-limit & expiry policy

```
SPEND-LIMIT & EXPIRY POLICY — [TEAM NAME]
Version [VERSION] · Effective [DATE] · Owner: [POLICY OWNER]

1. Every plan carries a cost ceiling: [AMOUNT] [CURRENCY] per plan. Ceilings
   apply per plan, never per account.
2. Every plan expires on [EXPIRY RULE — e.g. its stated end date, or 30 days
   from issuance, whichever is sooner].
3. Spend is counted against the plan ceiling in real time. The owner is alerted
   at [ALERT THRESHOLDS — e.g. 50% and 80%].
4. When a ceiling is reached, the action FAILS CLOSED: it is blocked, recorded
   as blocked, and never retried automatically.
5. Raising a ceiling is a Hard-gated action: it requires human approval and a
   recorded reason.
6. Frameworks with no native budget controls run behind a meter (see rollout
   day 7). Unmetered execution is prohibited.
```

### Template 5 — Fail-closed block policy

```
FAIL-CLOSED BLOCK POLICY — [TEAM NAME]
Version [VERSION] · Effective [DATE] · Owner: [POLICY OWNER]

1. When required evidence is missing — identity, grant, approval, budget
   headroom, or terms record — the action is BLOCKED. It is never degraded
   to a warning.
2. Every block persists an audit row with: actor, action, target,
   outcome=blocked, timestamp, and the exact reason.
3. Every block tells the owner, in plain language, exactly which piece of
   evidence would unblock it.
4. Blocked actions are never retried automatically. A retry requires new
   evidence, not a timer.
5. Warning-only paths are prohibited for any action with external or financial
   side effects (see rollout day 12 sweep).
```

### Template 6 — Audit-row retention policy

```
AUDIT-ROW RETENTION POLICY — [TEAM NAME]
Version [VERSION] · Effective [DATE] · Owner: [POLICY OWNER]

1. Every request, approval, block, and outcome writes an audit row conforming
   to the Audit Row schema (Part 2).
2. Rows are hash-linked: each row's hash chains to the previous row. A broken
   chain is investigated, never ignored.
3. Rows are retained for [RETENTION PERIOD] from the date written.
4. Synthetic or demo rows are labeled "synthetic demo" in the row. Unlabeled
   fake telemetry is prohibited.
5. Early deletion or modification of rows requires [APPROVAL ROLE] approval,
   and is itself recorded as an audit row.
6. Audit data never contains secrets or credentials. Terms and credential
   material live outside the log.
```

### Adopting the policies

Adopt in the order listed: identity first, then grants, then hard gates, then spend limits and fail-closed, then retention. Each policy names an owner and an effective date — a policy without both is a draft, not a policy. Store them where the team already works (repo, wiki, or shared drive) and link them from the rollout tracker. Review all six quarterly, or sooner if a red-team exercise (day 14) finds a gap the policies didn't cover. When a policy changes, record the change as an audit row: policy text is evidence too.

---

## Part 2 — Plan-bound and audit-row JSON schemas

Two schemas, two jobs. The **plan bound** is the unit your governance operates on: if a unit of work can't be expressed in this schema, it isn't a plan and it doesn't run (free playbook §4). The **audit row** is the unit your evidence lives in: every request, approval, block, and outcome writes one, hash-linked to the last (free playbook §6).

Both are JSON Schema draft 2020-12. Validate at the boundary — plans at creation, rows at write time — and reject what doesn't validate. That rejection is itself an audit row.

*Note: example instances use `//` comments for readability. Strip them before validating.*

### Schema 1 — Plan bound

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://kestrelattice.example/schemas/plan-bound.json",
  "title": "PlanBound",
  "description": "The bounded unit of agent work. If any bound is missing, this is not a plan.",
  "type": "object",
  "required": [
    "plan_id", "owner_identity", "agent_identity", "workload",
    "data_class", "resources", "time_window", "location",
    "egress", "storage", "cost_ceiling", "expiry", "grant_refs"
  ],
  "properties": {
    "plan_id":        { "type": "string", "pattern": "^plan_[a-z0-9-]{8,64}$" },
    "owner_identity": { "type": "string", "pattern": "^owner:[a-z0-9-]{1,64}$" },
    "agent_identity": { "type": "string", "pattern": "^agent:[a-z0-9-]+/[a-z0-9-]+$" },
    "workload":       { "type": "string", "minLength": 1, "maxLength": 500 },
    "data_class":     { "type": "string", "enum": ["public", "internal", "confidential", "restricted"] },
    "resources": {
      "type": "object",
      "required": ["model_allowlist", "max_parallel_calls"],
      "properties": {
        "model_allowlist":   { "type": "array", "items": { "type": "string" }, "minItems": 1 },
        "max_parallel_calls": { "type": "integer", "minimum": 1 }
      },
      "additionalProperties": true
    },
    "time_window": {
      "type": "object",
      "required": ["start", "end"],
      "properties": {
        "start": { "type": "string", "format": "date-time" },
        "end":   { "type": "string", "format": "date-time" }
      }
    },
    "location": { "type": "string", "minLength": 1 },
    "egress": {
      "type": "object",
      "required": ["allowed_domains", "max_mb"],
      "properties": {
        "allowed_domains": { "type": "array", "items": { "type": "string" } },
        "max_mb":          { "type": "number", "minimum": 0 }
      }
    },
    "storage": {
      "type": "object",
      "required": ["scope", "max_mb"],
      "properties": {
        "scope":  { "type": "string", "minLength": 1 },
        "max_mb": { "type": "number", "minimum": 0 }
      }
    },
    "cost_ceiling": {
      "type": "object",
      "required": ["amount", "currency"],
      "properties": {
        "amount":   { "type": "number", "exclusiveMinimum": 0 },
        "currency": { "type": "string", "pattern": "^[A-Z]{3}$" }
      }
    },
    "expiry":     { "type": "string", "format": "date-time" },
    "grant_refs": { "type": "array", "items": { "type": "string" }, "minItems": 1 }
  },
  "additionalProperties": false
}
```

Example instance:

```jsonc
// Strip // comments before validating.
{
  "plan_id": "plan_9f2c-7a1b-research-01",   // unique per plan; never reused
  "owner_identity": "owner:koalstin",
  "agent_identity": "agent:koalstin/researcher",
  "workload": "Nightly competitor pricing scrape and summary",
  "data_class": "internal",                  // highest class the workload touches
  "resources": {
    "model_allowlist": ["claude-haiku-4-5", "gpt-4o-mini"],
    "max_parallel_calls": 4
  },
  "time_window": {
    "start": "2026-10-01T02:00:00Z",
    "end":   "2026-10-01T04:00:00Z"
  },
  "location": "us-east-1",                   // where compute may run
  "egress": {
    "allowed_domains": ["competitor-a.com", "competitor-b.com"],
    "max_mb": 50
  },
  "storage": {
    "scope": "s3://acme-agent-artifacts/research/",
    "max_mb": 500
  },
  "cost_ceiling": { "amount": 25.00, "currency": "USD" },
  "expiry": "2026-10-02T02:00:00Z",          // at or after time_window.end
  "grant_refs": ["grant_2026-09-30_webread", "grant_2026-09-30_s3write"]
}
```

**Plan-bound validation rules**

- All 13 top-level fields are required. A plan missing any bound is rejected — "if you can't state the bounds, you don't have a plan" (free playbook §4).
- `cost_ceiling.amount` must be greater than zero; `currency` must be a 3-letter ISO 4217 code.
- `time_window.end` must be after `time_window.start`; `expiry` must be at or after `time_window.end`, and must be a future timestamp at issuance.
- `grant_refs` must be non-empty, and every referenced grant must exist, be unexpired, and be issued to the plan's `agent_identity`.
- `agent_identity` and `owner_identity` must match the patterns in the Agent Identity Policy (Part 1) and exist in the identity registry.
- `data_class` uses your own four-level scale; record the highest class the workload touches.
- Plans are immutable once execution starts. A changed bound means a new `plan_id` — never an edit in place.

### Schema 2 — Audit row

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://kestrelattice.example/schemas/audit-row.json",
  "title": "AuditRow",
  "description": "One hash-linked evidence row. Every request, approval, block, and outcome writes one.",
  "type": "object",
  "required": [
    "row_id", "seq", "ts", "actor", "action",
    "target", "outcome", "prev_hash", "row_hash"
  ],
  "properties": {
    "row_id":    { "type": "string", "pattern": "^row_[a-z0-9-]{8,64}$" },
    "seq":       { "type": "integer", "minimum": 0 },
    "ts":        { "type": "string", "format": "date-time" },
    "actor":     { "type": "string", "minLength": 1 },
    "action":    { "type": "string", "minLength": 1 },
    "target":    { "type": "string", "minLength": 1 },
    "outcome":   { "type": "string", "enum": ["approved", "executed", "blocked", "rejected"] },
    "reason":    { "type": "string", "minLength": 1 },
    "prev_hash": { "type": "string", "pattern": "^([0-9a-f]{64}|GENESIS)$" },
    "row_hash":  { "type": "string", "pattern": "^[0-9a-f]{64}$" },
    "labels":    { "type": "array", "items": { "type": "string" } }
  },
  "if":   { "properties": { "outcome": { "enum": ["blocked", "rejected"] } } },
  "then": { "required": ["reason"] },
  "additionalProperties": false
}
```

Example instance:

```jsonc
// Strip // comments before validating.
{
  "row_id": "row_9f2c-7a1b-000142",          // unique per row
  "seq": 142,                                 // increments by exactly 1 per row
  "ts": "2026-10-01T02:14:33Z",               // RFC 3339, UTC
  "actor": "agent:koalstin/researcher",
  "action": "http.get",
  "target": "https://competitor-a.com/pricing",
  "outcome": "executed",
  // "reason" is required only when outcome is "blocked" or "rejected"
  "prev_hash": "c41d9e2f0a7b3c5d8e6f1a2b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
  "row_hash":  "7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7",
  "labels": []                                // use ["synthetic demo"] for demo rows
}
```

**Audit-row validation rules**

- `row_id`, `seq`, `ts`, `actor`, `action`, `target`, `outcome`, `prev_hash`, and `row_hash` are always required. `reason` is additionally required when `outcome` is `blocked` or `rejected`.
- `ts` must be RFC 3339 / ISO 8601 in UTC.
- **Hash-chain rule:** `row_hash` is the lowercase hex SHA-256 digest of the canonical JSON of the row *with `row_hash` removed*, concatenated with `prev_hash`. `seq` increments by exactly 1 per row. `prev_hash` must equal the previous row's `row_hash`. The first row in a chain uses `prev_hash: "GENESIS"`.
- **Verification:** recompute every row in sequence order. Any mismatch fails the entire chain visibly — a bad row is never skipped silently.
- Rows are append-only: no updates, no deletes. Retention-driven removal follows the Audit-Row Retention Policy (Part 1) and is itself recorded as a row.
- Synthetic rows must carry the label `"synthetic demo"`. Unlabeled fake telemetry is prohibited (free playbook §6).
- No secrets or credentials in any field, ever.

### Verifying the chain by hand

You don't need special tooling to check the chain — that's the point. To verify: (1) fetch the rows in `seq` order; (2) for each row, confirm `prev_hash` equals the previous row's `row_hash` (or `"GENESIS"` for seq 0); (3) recompute the SHA-256 digest over the canonical JSON of the row with `row_hash` removed, concatenated with `prev_hash`, and compare it to `row_hash`; (4) confirm `seq` increments by exactly 1 with no gaps. Any failure at any step fails the whole chain — investigate, don't skip. Run this check on a schedule (daily is a sane default) and after every incident.

---

## Part 3 — Vendor evaluation matrix

Eight tools, verified pricing from our September 2026 research, evaluated against one question: what governance gap does each leave you to fill yourself? Every tool below is good at something — observability, execution, evaluation, routing. None of them is a governance control plane. That is not an insult; it is the build-vs-buy boundary, stated plainly so you can plan around it.

*Gaps are stated against the eight-layer stack in the free playbook — what each tool does not provide as a governance control — not a claim about any vendor's roadmap.*

| Tool | Verified pricing | Governance gap it leaves | Best fit | Free-tier ceiling |
|------|------------------|--------------------------|----------|-------------------|
| LangSmith | Free (5k traces) · **$39/seat/mo** Plus · Enterprise custom | Answers "what did it do" (traces), not "was it allowed to": no agent identity-grant model, no approval gates, no spend ceilings that block. | Teams on LangChain/LangGraph needing trace-level debugging. | 5k traces on free |
| CrewAI AMP | Free (~50 executions/mo) · **$25–$99/mo** · $225/mo at 500 executions | Managed execution, not governance: no hard-gated approvals, no per-plan spend ceilings, no identity-authority records. | CrewAI-native teams wanting managed multi-agent runs. | ~50 executions/mo free |
| AgentOps | Free (5–10k traces) · **$49/mo** · **$199/mo** · Enterprise custom | Session replay + cost tracking is visibility without enforcement: it tracks what was spent but doesn't block at a ceiling; no approval gates, no grant store. | Teams that need session replay and cost visibility first. | 5–10k traces free |
| LangWatch | Free (200k events/mo) · **$29/mo + $6/100k events** · Enterprise custom | Event telemetry, not a control plane: no runtime blocks, no approval flow, no identity grants. | Event-level monitoring of agent behavior. | 200k events/mo free |
| Arize Phoenix | OSS free · **$199/mo** Cloud Starter · Enterprise custom | Observability layer only: it monitors, it doesn't govern — no spend enforcement, no approval gates, no hash-linked audit. | Open-source-first teams that self-host. | OSS free (self-hosted) |
| Helicone | Free (10k requests/mo) · **$29–$79/mo** · $799/mo Team | Proxy metering, not governance: it logs what was spent, it doesn't stop it; no gates, no grants, no approvals. | Cheap LLM proxy logging and caching. | 10k requests/mo free |
| Braintrust | Free Starter · **$249/mo** Pro | Evaluation-first: no money/outreach gating, no spend ceilings, no agent identity-authority model. | Eval-driven teams shipping model improvements. | Starter free |
| OpenRouter | Free models tier · PAYG, $0 minimum | Credit metering with a $0 minimum: no per-plan ceilings, no approvals, no audit trail — and PAYG means a runaway loop keeps spending. | Low-cost multi-model routing and experimentation. | Free models tier |

### How to run the evaluation

Score each tool against the gaps column, not the feature list. For every tool you trial, write down which of the eight governance layers it covers and which it leaves to you — then check the free-tier ceiling against your actual metered volume from rollout day 7. If you outgrow a free tier, that's evidence, not failure: upgrade the tool that proved itself, and only that one. Revisit this matrix quarterly; vendor pricing in this space moves fast, and today's free tier is tomorrow's paywall.

### The build-vs-buy read

Buy the observability; build the governance. Nothing in the matrix sells identity-scoped grants, hard-gated human approvals, spend ceilings that fail closed, and hash-linked audit as one layer — that is the product gap this playbook exists to fill, and the practitioner pain behind it (the $700 runaway loop, the "who gave your agent authority" threads) is precisely the absence of it. The meter is worth buying at $0: Helicone's free tier (10k requests/mo) or LangWatch's free tier (200k events/mo) gives you the watchdog the rollout's day 7 requires. The paid tiers — $199–$2,499/mo across Langfuse, AgentOps, Arize, and Braintrust — are priced for funded studios and enterprises, which sits above the $100–$200/mo single-tool ceiling that teams under 10 FTE resist. So: adopt free-tier observability now, build the six policies and two schemas in this edition during the 14-day rollout, and revisit paid tooling only when your metered spend justifies it.

---

## Part 4 — Risk-tier classification worksheet

Tier by consequence, not by frequency. Walk every capability in your stack through this table before rollout day 9. The three tiers come from the free playbook §4: **Hard-gated** (money, contracts, external outreach, credentials, permission changes, legal actions — always a human, no auto-grant ever), **Bounded auto** (routine compute inside an approved plan — auto-runs, fully audited, auto-blocks at any bound), **Draft-only** (preparing proposals, composing messages, planning — recorded, never executed, never contacts anyone).

Eight example rows are pre-filled. Add your own in the twelve blank rows. A row is done when all five columns are filled and the owner has signed off.

| Action / capability | Consequence if wrong | Tier | Owner | Evidence required to unblock |
|---|---|---|---|---|
| Send a payment / move money | Double-spend, fraud, unrecoverable loss | Hard-gated | [Finance owner] | Recorded human approval + invoice reference |
| Accept contract or terms of service | Legal liability, auto-accepted obligations | Hard-gated | [Legal owner] | Signed terms document + approver identity |
| Send external outreach (email/DM/post) | Reputation damage, spam violations | Hard-gated | [Growth owner] | Approved draft + reviewed recipient list |
| Read or transmit a credential/secret | Credential leak, account takeover | Hard-gated | [Security owner] | Grant record + time-bounded stated purpose |
| Change agent permissions or grants | Privilege escalation, scope creep | Hard-gated | [Platform owner] | Change request + owner signature |
| Run inference batch inside plan bounds | Cost overrun if bounds are wrong | Bounded auto | [ML engineer] | Active plan with cost ceiling + expiry |
| Write intermediate artifacts to plan storage | Data sprawl, wrong data class exposure | Bounded auto | [Data owner] | Storage bound recorded in the plan |
| Draft a proposal / compose an outreach message | None — drafts never execute | Draft-only | [Author] | n/a (sending is a separate hard-gated action) |
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |

**How to fill the blank rows:** list capabilities the way your agents actually invoke them (tool names, API calls, cron jobs), not the way your architecture diagram describes them. If you can't name the consequence of an action being wrong, default it to Hard-gated until you can. If two owners disagree on a tier, the higher tier wins — downgrading a tier is itself a Hard-gated decision under the Grant Issuance Policy.

### Tiering heuristics

Three rules of thumb from teams that have done this. First: when in doubt, tier up — a Bounded-auto action that should have been Hard-gated is an incident; a Hard-gated action that could have been Bounded-auto is just a slow afternoon. Second: the most commonly mis-tiered actions are "read-only" ones — reading a credential store, exporting a customer list, or dumping a production database are reads with write-grade consequences; tier them accordingly. Third: re-tier whenever the blast radius changes. A new integration, a new data class, or a bigger spend ceiling all change the consequence column, and the tier follows the consequence.

---

## Part 5 — 14-day rollout

Follows the free playbook §9 phasing — days 1–2 identity, 3–5 grants + audit, 6–8 spend limits, 9–11 approval gates, 12–14 fail-closed sweep — broken into concrete daily tasks. Do the days in order: each layer assumes the ones before it. Each day ends with checkable acceptance criteria.

**Weekly rhythm.** Week 1 (days 1–5) is foundation: identity, grants, audit. Nothing runs ungoverned after day 5 that wasn't already running. Week 2 (days 6–11) is control: spend limits, meters, gates. Days 12–14 are the fail-closed sweep and red-team. If you slip a day, slip the schedule — don't skip the layer. A half-built approval gate is worse than none, because it teaches the team that gates are theater.

### Day 1 — Inventory actors, assign identities

1. List every agent, script, cron job, and scheduled workflow that can take an action in your stack. Record name, owner, and what it can touch.
2. Adopt the identity format `agent:[OWNER]/[NAME]` from the Identity Policy (Part 1) and assign an identity to each inventoried actor.
3. Add a dispatch-path check that rejects anonymous or shared-identity actors outright — a block, not a warning.

- [ ] Every actor that ran in the last 7 days has a recorded owner-scoped identity.
- [ ] A test anonymous request is rejected with a recorded block.

### Day 2 — Identity registry and no-identity behavior

1. Create the identity registry (a versioned JSON file or table) with identity, owner, date issued, and status for each actor.
2. Wire every action call path to attach the acting identity; verify attribution end to end on one real workflow.
3. Define the no-identity behavior: requests with no recorded identity park as `REQUIRES_OWNER_ACTION` (free playbook §3).

- [ ] A test capability request with no identity parks as `REQUIRES_OWNER_ACTION` and appears in the owner queue.

### Day 3 — Grant store

1. Stand up the grant store using the Grant Issuance Policy (Part 1): each grant records capability, scope, issuing owner, dates, and the identity it is issued to.
2. Issue least-privilege grants for your two most-used agents; default everything else to no grant.
3. Wire the capability check: request → evaluate against the grant store → record the decision (approved or rejected) linked to the acting identity.

- [ ] A capability request outside any grant is rejected, and the rejection is recorded with the requesting identity.

### Day 4 — Least-privilege pass

1. Review every existing agent permission and shrink each grant to the minimum capability and scope the agent has demonstrated it needs.
2. Set expiries on all grants per your filled [DURATION] — no permanent grants.
3. Document the grant request flow: who can request, who approves ([GRANT AUTHORITY ROLE]), how expiry renewal works.

- [ ] No agent holds a grant broader than its demonstrated need.
- [ ] Every grant has an expiry date.

### Day 5 — Hash-linked audit log

1. Implement the Audit Row schema (Part 2): every request, approval, block, and outcome writes a row.
2. Verify the hash chain: tamper with a test row and confirm verification fails visibly.
3. Label any synthetic or demo rows `"synthetic demo"` (free playbook §6).

- [ ] The last 24 hours of agent activity is fully represented in hash-linked rows.
- [ ] Chain verification passes; a tampered test row fails verification visibly.

### Day 6 — Cost ceilings per plan

1. Put a cost ceiling on every active plan using the PlanBound schema (Part 2) — ceiling per plan, never per account.
2. Fill in the [AMOUNT] [CURRENCY] in your adopted Spend-Limit & Expiry Policy (Part 1) for each plan tier.
3. Instrument cost counting: every billable call increments the plan's spend counter.

- [ ] Every active plan has a recorded cost ceiling.
- [ ] Spend is counted against the ceiling in real time.

### Day 7 — Meter the framework

1. Put a meter in front of any framework with no native budget controls — Helicone's free tier (10k requests/mo) or LangWatch's free tier (200k events/mo), per the free playbook §5.
2. Alert the owner at your policy's [ALERT THRESHOLDS] (e.g. 50% and 80% of each plan's ceiling). Alerts are information; the block is the control.
3. Confirm the meter's counts reconcile with the provider's billing within one reporting period.

- [ ] Every framework without native budget controls now runs behind a meter.
- [ ] Meter counts reconcile with provider billing.

### Day 8 — Expiry and fail-closed on budget

1. Give every plan an expiry date — a workload with no end date is a subscription you forgot you bought (free playbook §5).
2. Implement fail-closed on budget: when a ceiling is hit, the action is blocked and recorded as blocked — not retried, not warned, not billed.
3. Replay the $700-loop scenario in a sandbox: confirm the loop exhausts its own plan and stops.

- [ ] Breaching a ceiling produces a recorded block, with no automatic retry.
- [ ] A simulated runaway loop terminates at its plan ceiling.

### Day 9 — Tier every action

1. Complete the Risk-Tier Worksheet (Part 4) for your own stack: every capability tiered Hard-gated / Bounded auto / Draft-only.
2. Get the worksheet signed off by each listed owner.
3. Publish the tier list where the whole team can see it.

- [ ] Every capability in the worksheet has a tier, an owner, and sign-off.

### Day 10 — Hard gates live

1. Implement the human approval path for all Hard-gated actions (money, contracts, external outreach, credentials, permission changes, legal) per the Hard-Gated Action Policy (Part 1).
2. Verify there is no auto-grant path for these actions — attempt one in a test and confirm it cannot succeed.
3. Record the rejection path: a denied approval persists an exact blocked result (free playbook §4).

- [ ] A test hard-gated action cannot complete without a recorded human approval.
- [ ] A denied approval persists an exact blocked result.

### Day 11 — Draft-only paths

1. Route all proposal, message, and planning generation through draft-only paths: recorded, never executed, never contacts anyone.
2. Separate "compose" from "send": sending is a distinct hard-gated action requiring its own approval.
3. Audit the last 30 days for any draft that executed or contacted anyone — remediate what you find.

- [ ] No draft-only output from the last 30 days reached an external party.
- [ ] Compose and send are separate actions; send requires its own approval.

### Day 12 — Warning-to-block sweep

1. Inventory every warning-only path in your stack: missing-identity warnings, soft budget alerts, unlogged rejections.
2. Convert each into a block with a recorded reason, per the Fail-Closed Block Policy (Part 1).
3. Trigger each converted path and confirm the block plus the recorded reason.

- [ ] Zero warning-only paths remain on any action with external or financial side effects.

### Day 13 — Unblock checklists

1. For every block type, write the exact evidence that would unblock it (owner identity, grant record, approval, budget headroom).
2. Surface the unblock checklist to the owner at block time — governance as a to-do list, not a maze (free playbook §7).
3. Test with a real owner: hand them a blocked action and time the unblock; simplify anything confusing.

- [ ] Every block type has a documented unblock checklist.
- [ ] An owner successfully unblocked a test action using only that checklist.

### Day 14 — Red-team sweep and sign-off

1. Red-team the full stack: no identity, expired grant, ceiling breach, unapproved hard-gated action, tampered audit row.
2. Confirm each attack is blocked and recorded; fix anything that isn't before proceeding.
3. Complete the Acceptance Checklist at the end of this edition, sign it, and archive it with the audit log.

- [ ] All five red-team attacks were blocked and recorded.
- [ ] The acceptance checklist is signed and archived.

---

## Part 6 — First-customer kit

Sell the governance only once it's real — a prospect who asks "who gave the agent authority?" should get a demo of your answer, not a slide. When the fourteen days are done, price and prospect from the same evidence base as everything else in this edition.

### Pricing guidance

- **Per-developer willingness to pay** for core AI/dev tooling: **$20–$50/developer/mo**.
- **Aggregate AI stack spend** runs **$50–$200/developer/mo**; a 5-person studio's total tooling budget is **$250–$1,000/mo** across all software.
- **The line not to cross early:** single-tool ceiling for teams under 10 FTE shows strong resistance above **$100–$200/mo** unless the tool directly offsets compute or headcount.
- **The funded-studio band:** comparables at **$199–$2,499/mo** — Langfuse Pro $199/mo to Enterprise $2,499/mo, AgentOps Pro $199/mo with Enterprise from $2,000/mo, Arize Phoenix Cloud Starter $199/mo, Braintrust Pro $249/mo — sell to venture studios with $1.36M–$2.49M median budgets putting 40–60% of year-1 engineering burn into shared platform stacks.
- **The recommendation:** launch under $100/mo for small teams; align per-seat pricing with the $20–$50/dev/mo band; consider hybrid seat+usage once you have usage to meter (61%–86% of high-growth SaaS prices that way). Price the funded-studio tier separately — same product, different buyer, different budget.

**What not to do.** Don't launch at the comparables' price ($199+/mo) hoping to "move downmarket later" — the single-tool ceiling for sub-10-FTE teams is $100–$200/mo, and teams above that line buy through enterprise sales motions you don't have yet. Don't discount the governance story to win on price either: the buyer-demand ledger shows studios are already procuring multi-agent execution stacks (one documented case at €18,000/mo) — the budget exists where the control is proven. Price for the proof you have, then earn the higher tier with evidence.

### Honest funnel math

Plan from the bottom of each benchmark range and let recorded evidence revise upward.

| Stage | Benchmark (source: pricing-and-economics research) |
|---|---|
| Cold email reply, technical audiences | 1.00%–3.50% |
| Cold email → demo booking | 0.50%–1.50% of contacts |
| Landing page visitor → signup (median) | 2.35%–3.50% (top quartile 6.60%–11.45%) |
| Dev-tool visitor → free signup (median) | 10% |
| Free → paid within 6 months (median) | 5% |
| LinkedIn connection acceptance | 20%–30% |
| LinkedIn DM response | 10%–15% |

**Worked example — 1,000 visitors.** 1,000 visitors × 10% (dev-tool visitor→signup, median) = 100 signups. 100 × 5% (free→paid within 6 months, median) = 5 paying customers within six months. At $49/mo — inside the under-$100/mo early ceiling and the $20–$50/dev/mo WTP band (AgentOps' Starter tier, cited as evidence, not a recommendation) — that's $245/mo in new MRR per 1,000 visitors. Conservative read: halve both rates → 1,000 → 50 signups → 2–3 paid → $98–$147/mo at $49. Either way the lesson is the same: traffic is not the constraint; conversion evidence is.

**Worked example — outbound.** Gmail personal caps at 500 emails/24 hrs. 500 emails/day × 20 working days = 10,000 contacts. At the bottom of the technical-audience benchmarks — 1% reply, 0.5% demo booking — that's 100 replies and 50 demos booked per month of steady, personal outreach. LinkedIn adds ~100 connection requests/week at 20–30% acceptance. Keep every email 1:1 and personal; the free tier is a relationship channel, not a blast tool.

**Measure it with the $0 stack.** Google Analytics 4 covers unlimited standard events with 1M events/day BigQuery export — more than enough to track the visitor→signup→paid funnel above. Short.io's free tier (1,000 branded links/mo, 50k clicks) gives every cold email and post its own tracked link, so replies and signups attribute to the exact message that caused them. Record the numbers weekly; the funnel math only improves if you can see it.

### Cold-email template

Under 120 words, personal, non-spammy. Replace every bracket with something specific — a template with unfilled brackets is spam with extra steps.

```
Subject: quick question about [Company]'s agent setup

Hi [First Name],

I saw [Company]'s [specific detail — e.g. your multi-agent demo last week].
Quick question we keep hearing from teams at your stage: when your agents
act, who gave them authority — and where's the receipt?

We put together a short playbook on governed agent operations: owner-scoped
identity, per-plan spend ceilings, human approval gates, and hash-linked
audit rows. It's the layer that stops the runaway-loop class of incident
(one dev burned $700 in 72 hours with no budget control).

Happy to send it over — no pitch, just the PDF. Worth a look?

[Your Name], [Title] — [Studio]
```

Send it to people, not lists. One specific detail per email, or don't send it.

---

## Acceptance checklist

Copy this page, date it, and archive it with your audit log. The rollout isn't done until every box is checked.

**Policies (Part 1)**

- [ ] Identity policy adopted: every agent holds an owner-scoped identity; anonymous actors are rejected.
- [ ] Grant issuance policy adopted: all grants are least-privilege records with expiries; no auto-grant.
- [ ] Hard-gated action policy adopted: money, contracts, outreach, credentials, permission changes, legal — human approval only.
- [ ] Spend-limit & expiry policy adopted: every plan has a ceiling and an expiry; breaches fail closed.
- [ ] Fail-closed block policy adopted: zero warning-only paths on side-effecting actions.
- [ ] Audit-row retention policy adopted: retention period set, synthetic rows labeled, no secrets in rows.

**Schemas (Part 2)**

- [ ] Every active plan validates against the PlanBound schema — all 13 bounds present.
- [ ] Every request, approval, block, and outcome writes an audit row; chain verification passes end to end.

**Vendors (Part 3)**

- [ ] Evaluation matrix completed; observability tooling chosen — free tier until metered spend justifies paid.

**Risk tiers (Part 4)**

- [ ] Worksheet completed for the full stack; every row has a tier, an owner, and sign-off.

**Rollout (Part 5)**

- [ ] Days 1–2: identity complete — no anonymous actors.
- [ ] Days 3–5: grant store and audit log live.
- [ ] Days 6–8: spend ceilings, metering, and expiry on every plan.
- [ ] Days 9–11: approval gates live; hard-gated actions require recorded human approval.
- [ ] Days 12–14: fail-closed sweep complete; all five red-team attacks blocked and recorded.

**First customer (Part 6)**

- [ ] Pricing set under the evidence-backed ceiling; funnel math recorded from the bottom of the ranges.
- [ ] First [N] personal cold emails sent; replies and demos logged as evidence.

Signed: [NAME] · Date: [DATE]

---

*The Governed Agent Mesh Playbook — Studio Edition. An original GhostCorp work. Every figure in this edition traces to the pricing-and-economics research and the buyer-demand ledger compiled September 2026; values in [BRACKETS] are yours to decide.*
