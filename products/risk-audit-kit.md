# The AI Agent Risk Audit Kit

**A self-audit workbook for teams already running AI agents. Find your exposure before it finds you.**

By GhostCorp · Kestrelattice · September 2026

---

## What this is

You already have agents running. This kit tells you, honestly, where you're exposed.

It has four parts:

1. **Risk-tier self-assessment quiz** — 18 questions that map what your agents actually do against the three risk tiers (Hard-gated, Bounded auto, Draft-only). Mismatches are findings.
2. **40-point audit checklist** — eight checks across each of five domains: agent identity, permissions, spend controls, data access, and logging. Every check demands evidence, not vibes.
3. **Red-flag catalog** — twelve failure patterns seen in real agent deployments, so you can recognize yours.
4. **Scoring worksheet + remediation priority matrix** — turn your results into an ordered fix list.

**What this is not.** This kit does not fix anything. It evaluates. The fix templates — the six policies, the plan-bound and audit-row schemas, the 14-day rollout — live in *The Playbook — Studio Edition*. Run this audit first; adopt the policies second. An audit without a fix plan is anxiety with extra steps.

**Evidence discipline.** Nothing in this kit is invented. Failure patterns reference documented practitioner cases (sourced in the Kestrelattice buyer-demand ledger, September 2026). Where a value is yours to decide, it appears as [BRACKETED CAPS]. Where a check asks for evidence, "we think so" is not evidence.

**How to run it.** Solo: budget 90 minutes with access to your repos, dashboards, and billing. Team: run it as a half-day workshop — one person per domain, then compare answers. Disagreement between two people's answers to the same question is itself a finding: it means the control isn't real enough to be visible.

**Who this is for.** Small teams and founders already running AI agents in production or near-production — cron jobs, support bots, scrapers, coding agents, multi-agent workflows — who need to check their exposure before scaling.

---

## Part 1 — Risk-tier self-assessment quiz

### The three tiers (read this first)

Every action your agents can take belongs in exactly one tier. Tier by consequence, not by frequency:

- **Hard-gated.** The action always requires a recorded human approval. No auto-grant path exists, ever. This covers: moving money or committing spend above your threshold, accepting contracts or terms, external outreach (emails, messages, posts, calls), accessing or transmitting credentials or secrets, changing agent permissions, and anything with legal consequences.
- **Bounded auto.** The action runs automatically inside a pre-approved plan — with a cost ceiling, an expiry date, and full audit logging — and blocks itself at any bound. Routine compute, nothing more.
- **Draft-only.** The action prepares output that is recorded but never executed and never contacts anyone: proposals, composed messages, plans. Sending or executing is a separate action in a higher tier.

### How to answer

For each question, pick the answer that describes what **actually happens today** — not what's documented, not what's planned:

- **(a)** A human approves each instance, and the approval is recorded → in practice: **Hard-gated**
- **(b)** It runs automatically within pre-set bounds, is fully logged, and blocks itself at any bound → in practice: **Bounded auto**
- **(c)** It is prepared but never executes or contacts anyone on its own → in practice: **Draft-only**
- **(d)** None of the above, or you're not sure → in practice: **No control**

If you answer (d), that is a finding. If you can't describe the control, you don't have the control.

### The questions

**Money & spend**

**Q1.** An agent needs to spend money — API calls, a purchase, a paid signup. What happens?
*Required tier: Hard-gated for the spend decision; Bounded auto is acceptable only for metered inference inside a plan with a ceiling.*

**Q2.** An agent's task starts costing more than expected mid-run. What stops it?
*Required tier: Bounded auto — a per-plan cost ceiling that blocks automatically. (a) is also acceptable.*

**Q3.** Who can raise a spend ceiling, and how?
*Required tier: Hard-gated — a human decision with a recorded reason.*

**External communication**

**Q4.** An agent sends an email, DM, or post to someone outside your team. What happens first?
*Required tier: Hard-gated.*

**Q5.** An agent drafts an outreach message. Where does the draft go?
*Required tier: Draft-only — recorded, never sent by the agent.*

**Q6.** A scheduled workflow posts content on a timer with no human in the loop. Which tier is that in?
*Required tier: Trick question — timer-based external posting with no approval is not a tier, it's a finding. Required: Hard-gated.*

**Credentials & secrets**

**Q7.** An agent needs an API key or password to do its job. How does it get it?
*Required tier: Hard-gated — grant record plus a time-bounded stated purpose.*

**Q8.** An agent reads from a credential store or secrets manager. What tier is that read in?
*Required tier: Hard-gated. Reads with write-grade consequences are tiered by consequence: a leaked credential is an account takeover.*

**Q9.** A former team member's credentials are still in an agent's config. How would you know?
*Required tier: Hard-gated processes around this (rotation, review). If you wouldn't know, that's the finding.*

**Permissions & grants**

**Q10.** A new agent needs access to a production database. Who decides, and where is it recorded?
*Required tier: Hard-gated — explicit issuance decision, recorded grant.*

**Q11.** An agent's permissions were widened six months ago for a one-off task. What narrowed them back?
*Required tier: Bounded auto at minimum (expiry on the grant); if nothing did, that's a finding.*

**Q12.** Can an agent change its own permissions or grant itself new capabilities?
*Required tier: Hard-gated — and the correct in-practice answer is (a) with "no auto-grant path exists," or the question exposes a critical finding.*

**Data access**

**Q13.** An agent exports a customer list or dumps a production database. What tier is that in?
*Required tier: Hard-gated. Like Q8: reads with write-grade consequences.*

**Q14.** Your agents touch customer data. Where is the data classification recorded — and what is the highest class any agent touches?
*Required tier: Bounded auto minimum (classification recorded per plan). If unrecorded: finding.*

**Q15.** An agent sends data to a third-party API. What constrains which domains it may call?
*Required tier: Bounded auto — an egress allowlist in the plan.*

**Planning & drafts**

**Q16.** An agent produces a plan for a multi-step task. What happens to the plan before execution?
*Required tier: Draft-only for the plan itself; execution is a separate tiered action.*

**Q17.** In the last 30 days, did any draft-only output — a composed message, a proposal, a plan — reach an external party or execute on its own?
*Required tier: This must be answerable from your logs. "We don't know" is a finding.*

**Q18.** When a control blocks an agent's action, what does the team see?
*Required tier: Bounded auto minimum — a recorded block with the exact reason. A silent skip or a warning nobody reads is a finding.*

### Quiz scoring worksheet

Copy this table and fill it in. Tier rank for comparison: No control = 0, Draft-only = 1, Bounded auto = 2, Hard-gated = 3. A finding is any row where your in-practice tier ranks **below** the required tier — or where you answered (d).

| Q | Required tier | Your answer (a/b/c/d) | In-practice tier | Match? (Y/N) | Finding # |
|---|---|---|---|---|---|
| 1 | Hard-gated | | | | |
| 2 | Bounded auto | | | | |
| 3 | Hard-gated | | | | |
| 4 | Hard-gated | | | | |
| 5 | Draft-only | | | | |
| 6 | Hard-gated | | | | |
| 7 | Hard-gated | | | | |
| 8 | Hard-gated | | | | |
| 9 | Hard-gated | | | | |
| 10 | Hard-gated | | | | |
| 11 | Bounded auto | | | | |
| 12 | Hard-gated | | | | |
| 13 | Hard-gated | | | | |
| 14 | Bounded auto | | | | |
| 15 | Bounded auto | | | | |
| 16 | Draft-only | | | | |
| 17 | (answerable from logs) | | | | |
| 18 | Bounded auto | | | | |

**Tier-alignment score:** [18 minus findings] / 18 aligned.

- **16–18 aligned:** Your tiering is largely honest. The checklist will confirm or embarrass you.
- **12–15 aligned:** Real gaps. The findings list is your fix backlog's first draft.
- **Below 12:** You are running agents on trust. Do the checklist, then treat the remediation matrix as urgent.

Carry every finding number forward to Part 4. A finding without a number gets lost.

---

## Part 2 — 40-point audit checklist

Eight checks per domain, five domains. For each check, mark **Pass**, **Fail**, or **N/A** — and write down the evidence. A check passes only if you can point to the proof: a file, a log query, a dashboard, a config. "The engineer who set it up remembers doing it" is not evidence.

Convention: checks are numbered by domain — **ID** (identity), **PM** (permissions), **SP** (spend), **DA** (data access), **LG** (logging).

### Domain 1 — Agent identity

- [ ] **ID-1.** Every agent, script, cron job, and scheduled workflow that can take an action holds a stable, owner-scoped identity (e.g. `agent:[OWNER]/[NAME]`). → Evidence: ______ · ☐ Pass ☐ Fail ☐ N/A
- [ ] **ID-2.** No two actors share an identity, and no identity is shared across owners. → Evidence: ______ · ☐ Pass ☐ Fail ☐ N/A
- [ ] **ID-3.** An identity registry exists (file, table, or system) recording identity, owner, date issued, and status for each actor. → Evidence: ______ · ☐ Pass ☐ Fail ☐ N/A
- [ ] **ID-4.** The dispatch path rejects anonymous or unregistered actors outright — a block, not a warning. → Evidence: ______ · ☐ Pass ☐ Fail ☐ N/A
- [ ] **ID-5.** Every action call path attaches the acting identity, and you can trace one real workflow end to end. → Evidence: ______ · ☐ Pass ☐ Fail ☐ N/A
- [ ] **ID-6.** Decommissioned agents have their identities revoked; a revoked identity is never reissued to a different agent. → Evidence: ______ · ☐ Pass ☐ Fail ☐ N/A
- [ ] **ID-7.** No hardcoded superuser, "admin," or shared service identity exists that bypasses attribution. → Evidence: ______ · ☐ Pass ☐ Fail ☐ N/A
- [ ] **ID-8.** A capability request arriving with no recorded identity parks visibly (e.g. `REQUIRES_OWNER_ACTION`) instead of running or failing silently. → Evidence: ______ · ☐ Pass ☐ Fail ☐ N/A

### Domain 2 — Permissions & grants

- [ ] **PM-1.** No action runs without an explicit grant; every grant records capability, scope, issuing owner, dates, and the identity it is issued to. → Evidence: ______ · ☐ Pass ☐ Fail ☐ N/A
- [ ] **PM-2.** Grants follow least privilege: each covers the minimum capability and scope the agent has demonstrated it needs. → Evidence: ______ · ☐ Pass ☐ Fail ☐ N/A
- [ ] **PM-3.** Every grant has an expiry date. Permanent grants do not exist. → Evidence: ______ · ☐ Pass ☐ Fail ☐ N/A
- [ ] **PM-4.** Auto-grant is prohibited: every grant required an explicit issuance decision by a named authority. → Evidence: ______ · ☐ Pass ☐ Fail ☐ N/A
- [ ] **PM-5.** Changing a grant (any permission change) requires human approval — it is treated as a hard-gated action. → Evidence: ______ · ☐ Pass ☐ Fail ☐ N/A
- [ ] **PM-6.** Grant reviews happen on a schedule: stale or over-broad grants are shrunk or removed, not left in place. → Evidence: ______ · ☐ Pass ☐ Fail ☐ N/A
- [ ] **PM-7.** "Compose" and "send" are separate actions: drafting a message never confers the ability to send it. → Evidence: ______ · ☐ Pass ☐ Fail ☐ N/A
- [ ] **PM-8.** No agent can approve its own action, and no agent holds an approval role over itself. → Evidence: ______ · ☐ Pass ☐ Fail ☐ N/A

### Domain 3 — Spend controls

- [ ] **SP-1.** Every unit of agent work carries a cost ceiling, set per plan — never one shared ceiling per account. → Evidence: ______ · ☐ Pass ☐ Fail ☐ N/A
- [ ] **SP-2.** Every plan has an expiry date or expiry rule. No workload runs open-ended. → Evidence: ______ · ☐ Pass ☐ Fail ☐ N/A
- [ ] **SP-3.** Spend is counted against the ceiling in real time (or via a meter you reconcile), not estimated after the fact. → Evidence: ______ · ☐ Pass ☐ Fail ☐ N/A
- [ ] **SP-4.** The owner is alerted at defined thresholds (e.g. 50% and 80% of ceiling) before the ceiling is hit. → Evidence: ______ · ☐ Pass ☐ Fail ☐ N/A
- [ ] **SP-5.** Hitting a ceiling fails closed: the action is blocked and recorded as blocked — never warned, never retried automatically. → Evidence: ______ · ☐ Pass ☐ Fail ☐ N/A
- [ ] **SP-6.** Raising a ceiling requires human approval and a recorded reason. → Evidence: ______ · ☐ Pass ☐ Fail ☐ N/A
- [ ] **SP-7.** Frameworks with no native budget controls run behind a meter (e.g. a proxy with request logging on a free tier). Unmetered execution is prohibited. → Evidence: ______ · ☐ Pass ☐ Fail ☐ N/A
- [ ] **SP-8.** You have replayed a runaway-loop scenario in a sandbox and confirmed it terminates at its plan ceiling. → Evidence: ______ · ☐ Pass ☐ Fail ☐ N/A

### Domain 4 — Data access

- [ ] **DA-1.** Data your agents touch is classified (e.g. public / internal / confidential / restricted), and the highest class per workload is recorded. → Evidence: ______ · ☐ Pass ☐ Fail ☐ N/A
- [ ] **DA-2.** Reads with write-grade consequences — credential stores, customer lists, production database dumps — are tiered as hard-gated, not "read-only." → Evidence: ______ · ☐ Pass ☐ Fail ☐ N/A
- [ ] **DA-3.** Agent access to credentials or secrets requires a grant record plus a time-bounded stated purpose. → Evidence: ______ · ☐ Pass ☐ Fail ☐ N/A
- [ ] **DA-4.** No secrets or credentials appear in logs, configs in version control, or prompt histories. → Evidence: ______ · ☐ Pass ☐ Fail ☐ N/A
- [ ] **DA-5.** Egress is constrained: agents may only call an allowlist of domains recorded in the plan. → Evidence: ______ · ☐ Pass ☐ Fail ☐ N/A
- [ ] **DA-6.** Data sent to third-party APIs is limited to what the task needs; bulk exports require human approval. → Evidence: ______ · ☐ Pass ☐ Fail ☐ N/A
- [ ] **DA-7.** Storage writes are scoped: agents write only to their plan's designated storage scope, with a size cap. → Evidence: ______ · ☐ Pass ☐ Fail ☐ N/A
- [ ] **DA-8.** A former team member's access — keys, grants, identities — would be found and revoked within a defined time window. → Evidence: ______ · ☐ Pass ☐ Fail ☐ N/A

### Domain 5 — Logging & audit

- [ ] **LG-1.** Every request, approval, block, and outcome writes an audit row with actor, action, target, outcome, and timestamp. → Evidence: ______ · ☐ Pass ☐ Fail ☐ N/A
- [ ] **LG-2.** Audit rows are tamper-evident (e.g. hash-chained: each row links to the previous). A broken chain is investigated, never ignored. → Evidence: ______ · ☐ Pass ☐ Fail ☐ N/A
- [ ] **LG-3.** Every block persists with the exact reason — no silent skips, no empty "failed" entries. → Evidence: ______ · ☐ Pass ☐ Fail ☐ N/A
- [ ] **LG-4.** Every approval records the approver's identity, the timestamp, and the decision. → Evidence: ______ · ☐ Pass ☐ Fail ☐ N/A
- [ ] **LG-5.** A retention period is defined; early deletion or modification itself requires approval and is recorded. → Evidence: ______ · ☐ Pass ☐ Fail ☐ N/A
- [ ] **LG-6.** Synthetic or demo rows are labeled as such. Unlabeled fake telemetry is prohibited. → Evidence: ______ · ☐ Pass ☐ Fail ☐ N/A
- [ ] **LG-7.** Zero warning-only paths remain on actions with external or financial side effects — every warning was converted to a block with a recorded reason. → Evidence: ______ · ☐ Pass ☐ Fail ☐ N/A
- [ ] **LG-8.** Chain/log verification runs on a schedule (daily is sane), and you have seen it fail visibly on a tampered test row. → Evidence: ______ · ☐ Pass ☐ Fail ☐ N/A

### Checklist scoring

Count Pass as 1, Fail as 0, and exclude N/A from the denominator.

**Your score: [PASSES] / [40 minus N/As]**

| Band | Meaning | What to do |
|---|---|---|
| 35–40 | Governed. Your exposure is mostly residual. | Fix the fails, then re-audit quarterly. |
| 28–34 | Gaps. You have controls, but named ones are missing. | The fails are your backlog — prioritize with Part 4. |
| 20–27 | Exposed. Whole domains are unguarded. | Treat the matrix as urgent; don't scale agent usage until the critical fails are fixed. |
| Below 20 | Critical. You are running on trust and luck. | Stop adding agent capabilities until identity, spend, and hard gates are real. |

Record your per-domain sub-scores — the weakest domain is where the red flags live:

| Domain | Passes / 8 (minus N/A) |
|---|---|
| ID — Agent identity | / |
| PM — Permissions | / |
| SP — Spend controls | / |
| DA — Data access | / |
| LG — Logging & audit | / |

---

## Part 3 — Red-flag catalog

Twelve failure patterns from real agent deployments. Each one names what it looks like in the wild, why it hurts, which checklist checks it violates, and how bad it is. If you recognize yours, write the number down — it goes into the scoring worksheet in Part 4.

Severity scale: **Critical** = can cause unrecoverable loss (money, data, legal) on its own. **High** = reliably causes incidents given time. **Medium** = degrades control and hides other problems.

### RF-1 — The Runaway Loop

**Looks like:** An agent retries a failing task, or loops over paginated results, with no cost ceiling — and the meter only gets read at the end of the month. The documented case: one developer's agent burned over $700 in 72 hours on an infinite loop with no budget control and no watchdog.
**Why it hurts:** Cloud and API spend is the one incident class that bills you while you sleep. There is no "undo" on a provider invoice.
**Maps to:** SP-1, SP-3, SP-5, SP-7, SP-8.
**Severity:** Critical.

### RF-2 — The Shared API Key

**Looks like:** Three agents, two cron jobs, and one contractor all use the same production API key. When something odd happens, nobody can say which actor did it.
**Why it hurts:** Attribution is the foundation every other control stands on. Without per-actor identity, approvals, grants, and audit rows are theater — you can't gate or blame what you can't name.
**Maps to:** ID-1, ID-2, ID-5, ID-7.
**Severity:** High.

### RF-3 — The Silent Approver

**Looks like:** An approval step exists in the workflow diagram, but in practice the agent approves its own action, or approvals auto-resolve after a timeout, or "approval" is a Slack message nobody reads before the action proceeds.
**Why it hurts:** A gate that cannot say no is decoration. The incident it was supposed to prevent still happens; now it happens with a false record of oversight.
**Maps to:** PM-8, LG-4, quiz Q12.
**Severity:** Critical.

### RF-4 — The Warning Nobody Reads

**Looks like:** Missing-identity warnings, soft budget alerts, unlogged rejections — the system "warns" and the action proceeds anyway. The team muted the channel months ago.
**Why it hurts:** Warnings decay into ignored banners; that decay is predictable and documented. Every warning-only path on a side-effecting action is a control you pretend to have.
**Maps to:** LG-7, ID-4, SP-5.
**Severity:** High.

### RF-5 — The Immortal Grant

**Looks like:** A grant issued for a one-off migration in March still lets an agent read the production database in September. Nobody remembers issuing it. There is no expiry, no review, no owner.
**Why it hurts:** Permissions only ever widen unless something actively narrows them. Every immortal grant is a future incident with a head start.
**Maps to:** PM-3, PM-6, DA-8.
**Severity:** High.

### RF-6 — The Draft That Sent Itself

**Looks like:** The agent that "only drafts" messages shares a code path, a tool, or a config flag with the sending action — and one bad afternoon, a draft goes out. Or scheduled posting runs with no human review because "it's just the newsletter."
**Why it hurts:** External outreach is reputation and legal exposure. Compose and send must be separate actions with separate gates, or they are one action with no gate.
**Maps to:** PM-7, quiz Q5, Q6, Q17.
**Severity:** Critical.

### RF-7 — The Read That Writes

**Looks like:** "It's read-only" — said about an agent that can read the credential store, export the customer table, or dump the production database. The team tiered it as low-risk because nothing gets modified.
**Why it hurts:** Tier by consequence, not by frequency, and not by read-vs-write. A leaked credential is an account takeover; an exported customer list is a breach notification. Reads with write-grade consequences are hard-gated.
**Maps to:** DA-2, DA-3, quiz Q8, Q13.
**Severity:** Critical.

### RF-8 — The Unlogged Tuesday

**Looks like:** The audit log covers last week beautifully — and has a gap on Tuesday nobody can explain. Or blocks aren't recorded, so you can't distinguish "the agent chose not to act" from "the control failed open."
**Why it hurts:** An audit trail with gaps is worse than none: it gives you confidence the evidence doesn't support. "We don't know what happened Tuesday" is the sentence that ends incident reviews.
**Maps to:** LG-1, LG-2, LG-3, LG-8.
**Severity:** High.

### RF-9 — The Mystery Agent

**Looks like:** A cron job fires at 2 AM. Nobody on the current team knows who set it up, what it does, or what it can touch. It has production credentials because it always has.
**Why it hurts:** You cannot govern actors you haven't inventoried. Shadow workflows are where every other red flag goes to hide.
**Maps to:** ID-1, ID-3, ID-6.
**Severity:** High.

### RF-10 — The Spreadsheet of Secrets

**Looks like:** API keys in a shared doc, credentials in environment files committed to the repo, secrets pasted into prompt histories or logged in plaintext "for debugging."
**Why it hurts:** Secrets in the wrong place are secrets already shared — with every repo reader, every log viewer, and, via training-data pipelines, potentially everyone. Rotation after the fact doesn't unshare them.
**Maps to:** DA-4, DA-3.
**Severity:** Critical.

### RF-11 — The Unreconciled Meter

**Looks like:** A usage dashboard exists, but nobody has ever checked whether its numbers match the provider's actual bill. The meter and the money disagree, and the money is always right.
**Why it hurts:** A meter you don't reconcile is a placebo. Spend controls built on untrusted numbers fail exactly when you need them — during the incident.
**Maps to:** SP-3, SP-7.
**Severity:** Medium (escalates to Critical during any cost incident).

### RF-12 — The Permission Creep

**Looks like:** Every agent started with least privilege. Then came the demo, the deadline, the "just give it admin for today." None of it was ever rolled back. Today's effective permissions are whatever was convenient last quarter.
**Why it hurts:** This is the slow version of RF-5, and it's the default outcome of every team without scheduled grant reviews. Convenience compounds; least privilege decays.
**Maps to:** PM-2, PM-6.
**Severity:** Medium (escalates as blast radius grows).

### Red-flag tally

Count how many you recognized — including "maybe" and "we're not sure." Unsure counts: uncertainty about a red flag is evidence for it.

**Red flags recognized: [N] / 12 — numbers: [list them]**

---

## Part 4 — Scoring worksheet & remediation priority matrix

### Consolidated scorecard

Bring the three results together in one place.

| Result | Your number | Where it came from |
|---|---|---|
| Quiz: tier-alignment findings | [N] / 18 questions | Part 1 worksheet |
| Checklist: failed checks | [N] / [40 minus N/A] | Part 2 scoring |
| Red flags recognized | [N] / 12 | Part 3 tally |
| Weakest checklist domain | [ID / PM / SP / DA / LG] | Part 2 sub-scores |

### Overall risk rating

Find your row. Use the worst of the three numbers — a clean checklist doesn't cancel a critical red flag.

| Rating | Criteria (any one qualifies) | Meaning |
|---|---|---|
| **Critical** | Checklist below 20, or any Critical red flag (RF-1, RF-3, RF-6, RF-7, RF-10) confirmed, or 7+ quiz findings | Unrecoverable-loss exposure exists today. Fix before scaling anything. |
| **High** | Checklist 20–27, or 2+ High red flags, or 4–6 quiz findings | Incidents are a matter of time, not chance. Urgent backlog. |
| **Medium** | Checklist 28–34, or 1 High red flag, or 2–3 quiz findings | Controls exist but named ones are missing. Scheduled backlog. |
| **Low** | Checklist 35–40, no red flags above Medium, 0–1 quiz findings | Residual exposure only. Re-audit quarterly. |

**Your overall rating: [Critical / High / Medium / Low]**

Write it down. This is the number you report to whoever owns the risk — your co-founder, your lead, yourself in the mirror.

### Remediation priority matrix

List every failed check and every finding as its own row. Then place each in the matrix by two questions:

- **Impact:** if this control stays missing, what's the blast radius? (Money lost, data leaked, legal exposure = high.)
- **Effort:** how hard is the fix — hours, days, or a project?

| | Low effort (hours–days) | High effort (weeks / project) |
|---|---|---|
| **High impact** | **DO FIRST.** Example: put a ceiling on the runaway-prone plan; revoke the immortal grant. | **PLAN NEXT.** Example: build the identity registry; stand up the grant store. |
| **Low impact** | **DO SOON.** Example: label synthetic rows; define the retention period. | **SCHEDULE.** Example: full egress allowlisting; scheduled chain verification. |

**Placement rules — when in doubt:**

1. **Hard-gated gaps outrank everything.** Anything that should require human approval and doesn't goes in the top row, no matter the effort. RF-3, RF-6, RF-7, RF-10 live here.
2. **Spend fail-closed comes second.** An unmetered, unceilinged workload is a ticking invoice. RF-1 lives here.
3. **Identity comes third.** You can't gate what you can't name. RF-2, RF-9 live here.
4. **Logging comes fourth — but "fourth" doesn't mean optional.** Without it you can't prove any of the above worked. RF-8 lives here.

Copy this ordering into your fix list: for each failed check or finding, write the fix in one sentence, the owner, and the due date.

| # | Failed check / finding | Fix (one sentence) | Owner | Due |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |
| 6 | | | | |
| 7 | | | | |
| 8 | | | | |
| 9 | | | | |
| 10 | | | | |
| 11 | | | | |
| 12 | | | | |

*(Add rows as needed. If you have more than 12 rows, your rating is telling you something — believe it.)*

### 30-day remediation plan

Four weeks. Fill the blanks with rows from your fix list, in matrix order.

**Week 1 — Stop the bleeding (high impact, low effort).**
Target: every Critical red flag has an owner and a started fix.
- [ ] Fix: ______ — Owner: ______ — Done by: ______
- [ ] Fix: ______ — Owner: ______ — Done by: ______
- [ ] Fix: ______ — Owner: ______ — Done by: ______

**Week 2 — Build the missing controls (high impact, high effort — started).**
Target: identity registry exists, grant expiries set, spend ceilings on every plan.
- [ ] Fix: ______ — Owner: ______ — Done by: ______
- [ ] Fix: ______ — Owner: ______ — Done by: ______
- [ ] Fix: ______ — Owner: ______ — Done by: ______

**Week 3 — Close the evidence gaps (logging, data access).**
Target: every action writes an audit row; no secrets in logs; egress allowlisted.
- [ ] Fix: ______ — Owner: ______ — Done by: ______
- [ ] Fix: ______ — Owner: ______ — Done by: ______
- [ ] Fix: ______ — Owner: ______ — Done by: ______

**Week 4 — Verify and re-audit.**
Target: re-run the 40-point checklist; confirm the Critical and High items now pass.
- [ ] Re-ran checklist. New score: ______ / ______
- [ ] All Critical red flags cleared: ☐ Yes ☐ No (if no, list what's left: ______)
- [ ] Next audit date set: ______

### Sign-off

The audit isn't done until someone signs it. Unsigned audits get filed and forgotten; signed ones get fixed.

- Team: [TEAM NAME]
- Auditor(s): [NAMES]
- Date completed: [DATE]
- Overall risk rating: [Critical / High / Medium / Low]
- Weakest domain: [ID / PM / SP / DA / LG]
- Committed fix-list owner: [NAME]
- Next audit date: [DATE — no more than 90 days out, 30 if rated Critical]

Signed: ______

---

### What pairs with this kit

This kit finds the exposure. *The Playbook — Studio Edition* contains the fix templates: the six fill-in-the-brackets policies (identity, grants, hard gates, spend limits, fail-closed blocks, retention), the plan-bound and audit-row schemas, and the 14-day rollout that installs them in order. Audit with this kit; adopt with the Studio Edition.

---

*The AI Agent Risk Audit Kit. An original GhostCorp work. Failure patterns reference documented practitioner cases compiled in the Kestrelattice buyer-demand ledger, September 2026. Values in [BRACKETS] are yours to decide. No statistics in this kit are invented; where a number appears, it is a count from your own audit.*
