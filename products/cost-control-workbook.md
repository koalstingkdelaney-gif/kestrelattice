# Agent Cost Control Workbook

**The money companion to the Studio Edition: cost anatomy, budget worksheets, metering setup, tiered alert and kill rules, and a monthly review ritual — so your agents never bill you while you sleep.**

By GhostCorp · Kestrelattice · September 2026

---

## What this is

Every agent action costs money. Most teams discover this the way the practitioner in the buyer-demand ledger did: one runaway agent, $700 in 72 hours, no budget control, no watchdog. That incident wasn't a model-pricing problem. It was a governance problem — and governance is cheaper than invoices.

This workbook has six parts:

1. **Cost anatomy** — where agent money actually goes: plans, tool calls, context windows, retries.
2. **Budget-design worksheet** — per-plan, per-workload, per-window ceilings, with worked examples.
3. **Metering setup guide** — the ten fields to log per request so every dollar is attributable.
4. **Alert thresholds & kill-on-overspend rules** — wired into the three risk tiers.
5. **Monthly cost-review ritual** — a 30-minute template.
6. **Ten cost leaks** — each with the exact control that stops it.

**What this is not.** This workbook does not reprint the spend policies. The Spend-Limit & Expiry Policy, the plan-bound `cost_ceiling`, the fail-closed budget rule, and the day 6–8 rollout steps live in *The Playbook — Studio Edition* — this book shows you how to *use* them, with numbers. It is not the audit, either: the Risk Audit Kit's SP-1–SP-8 checks tell you whether spend controls exist; this workbook tells you what to set them to.

**Evidence discipline.** Every number in your budgets comes from two places: your meter, and your provider's rate card. Never from this book. Where a value is yours to decide, it appears as [BRACKETED CAPS]. Worked examples use [BRACKETED] numbers throughout — they are arithmetic illustrations, not benchmarks.

**Who this is for.** Founders and teams whose agents burn API money — or who are about to scale agent usage and want the ceilings in place before the bill arrives.

---

## Part 1 — Where agent money actually goes

You cannot budget what you cannot decompose. If the only number you see is the monthly total on the provider invoice, you see nothing actionable. Agent spend decomposes into five drivers. Learn them, because your meter (Part 3) is organized around them.

### The five cost drivers

**1. Inference tokens.** Every model call pays for input tokens and output tokens against the provider's rate card. Two structural facts matter more than any rate: cost scales with tokens, not with "requests" — a 200-token classification and a 20,000-token document synthesis are not the same purchase — and output-heavy workloads cost more per unit of work than input-heavy ones at the same rates, because generation is the expensive direction.

**2. Context growth.** Multi-turn agents re-send the conversation history with every turn. A 40-turn session doesn't cost 40 single-turn calls — it costs roughly the sum of 40 growing contexts, because turn 40 carries turns 1–39 along with it. Long sessions are where input-token spend quietly compounds. If you run research agents, coding agents, or anything with extended tool-use loops, context is probably your largest line item and the one you look at least.

**3. Tool and API calls.** Each search query, embedding batch, scrape, or third-party API call is billed separately — by the tool provider, the model provider, or both. Agents are enthusiastic tool users: the same lookup run six times "to be sure," a search per paragraph, an embedding batch per document. None of these are expensive alone. That is exactly why they add up unnoticed.

**4. Retries and loops.** The biggest bills come from volume, not unit price. A cheap call times ten thousand iterations is not a cheap call. Retry-on-failure with no cap, pagination loops with no bound, "try again with a different prompt" loops — every one of them multiplies the other four drivers. The $700/72h case was this driver, alone, with no ceiling.

**5. Always-on and auxiliary.** Schedulers that poll every minute, embeddings recomputed on every run, vector-database hosting, the framework's own compute. This driver is the hardest to see because it never appears as "an agent doing something" — it's the cost of the agent *existing*.

### The cost formula

Per request, approximately:

```
cost ≈ (input_tokens  × [INPUT RATE])
     + (output_tokens × [OUTPUT RATE])
     + Σ (tool_calls  × [TOOL RATE])
```

Per plan, per window: sum that over every request the plan made. That sum is the number your ceiling (Part 2) is set against, your meter (Part 3) records, and your monthly review (Part 5) reconciles.

**Worked example.** A nightly research agent, measured over [7] days: [38] requests per night, averaging [9,500] input tokens and [1,400] output tokens, plus [7] tool calls per request. At rate-card rates of [$INPUT]/1M input tokens, [$OUTPUT]/1M output tokens, and [$TOOL] per tool call, one night costs roughly [$NIGHTLY]. Times [30] nights: [$MONTHLY]. Every bracket in that paragraph is yours to fill from your meter and your rate card — the arithmetic is the point, not the numbers.

### The two rules

**Volume beats unit price.** When the bill surprises you, the cause is almost always call counts — retries, loops, context re-sends, polling — not the model you chose. Optimize counts first, rates second.

**Decompose or don't bother.** A budget set against "AI spend" as one lump is a wish. Budgets work when they're set per plan against the five drivers, because then a spike tells you *which driver moved* — and each driver has its own control (Part 6).

---

## Part 2 — Budget-design worksheet

Three ceiling levels, smallest to largest. The per-plan ceiling is required by the Studio Edition's Spend-Limit & Expiry Policy — ceilings apply per plan, never per account. The other two levels are this workbook's contribution: they catch what a single plan ceiling misses.

- **Per-plan ceiling.** The maximum one plan may spend. This is the fail-closed boundary: hit it and the action blocks.
- **Per-workload budget.** The aggregate across all plans serving one workload in a window (e.g. "nightly research, per month"). Catches the failure mode where each plan stays under its ceiling but the workload spawns too many plans.
- **Per-window backstop.** One account-level cap per [DAY/WEEK/MONTH]. This is the circuit breaker: if everything else fails, this number is the most you can lose in a window. Set it, then hope you never meet it.

### How to size a ceiling

Meter first (Part 3) for [7] days of normal operation. Take the measured run rate per plan. Add [50]% headroom. That is your starting ceiling. Never size a ceiling from vibes, from the provider's suggested limits, or from what "feels safe" — those numbers have no relationship to your workloads.

**Worked example.** The nightly research agent measured [$12.40]/night over [7] days. Per-plan ceiling: [$12.40] × [1.5] headroom = [$18.60], rounded to [$20]/night. Per-workload monthly budget: [$20] × [30] = [$600]/month. Per-window backstop for the account: [$1,000]/month — high enough to never trip during normal operation, low enough to bound the worst case. Alert thresholds (Part 4) at [50]% and [80]% of each: the plan pages its owner at [$10] and [$16] in a night.

Revisit every ceiling in the monthly review (Part 5). A ceiling set once and never revisited is how leak #10 happens.

### The worksheet

One row per workload. Fill the worked row as your template, then add your own. A row is done when every column has a number and an owner.

| Workload | Plans | Requests / window | Cost / request | Window total | Ceiling | Alert 50% | Alert 80% | Owner |
|---|---|---|---|---|---|---|---|---|
| Nightly research agent | [1]/night | [38]/night | [$0.33] | [$12.40]/night | [$20]/night | [$10] | [$16] | [NAME] |
| | | | | | | | | |
| | | | | | | | | |
| | | | | | | | | |
| | | | | | | | | |
| | | | | | | | | |

### The rules these ceilings live under

Stated here once, enforced by the policies — not reprinted, just referenced so the worksheet is honest about what backs it:

- Every plan carries its ceiling in the plan bound (`cost_ceiling`); a plan without one doesn't run.
- Hitting a ceiling fails closed: blocked, recorded as blocked, never retried automatically.
- Raising a ceiling is a Hard-gated action: human approval, recorded reason — and per this workbook, every raise carries an expiry (see leak #10).
- Frameworks with no native budget controls run behind a meter. Unmetered execution is prohibited.

---

## Part 3 — Metering setup guide

The meter sits at the dispatch path, in front of the framework: every billable call passes through it. The Studio Edition's day 7 covers the $0 tooling options for this (proxy free tiers) — this section covers what the meter must *record*, because a meter that logs the wrong fields is a dashboard, not a control.

### The ten fields to log per request

| # | Field | Why it exists |
|---|---|---|
| 1 | `ts` (UTC) | Windows, trends, and incident timelines need real timestamps. |
| 2 | `plan_id` | Every dollar attributes to exactly one plan. No plan_id, no spend. |
| 3 | `agent_identity` | `agent:[OWNER]/[NAME]` — which actor burned it. |
| 4 | `model` | The exact model string. Your rate card keys off this. |
| 5 | `input_tokens` | Driver #1 and #2 live here. |
| 6 | `output_tokens` | The expensive direction, tracked separately. |
| 7 | `tool_calls` | Count, plus which tools. Driver #3. |
| 8 | `retries` | Retry count for this request. Driver #4's early-warning signal. |
| 9 | `estimated_cost` | Tokens × your rate card + tool rates. Attribution, not billing. |
| 10 | `outcome` | `executed` / `blocked` / `failed`. Blocked calls cost nothing but tell you the ceiling works. |

**Why log estimated cost when the provider bills you anyway?** Attribution. The invoice tells you the total; the meter tells you which plan and which identity earned it. When the bill spikes, you don't ask "what happened" — you query field 2 and field 3 and you already know.

### Reconciliation

Monthly (Part 5, minutes 0–5): meter total vs. provider invoice. If they disagree, the invoice is right — investigate the gap. Common causes: a stale rate card in the estimate, tool calls billed by a third party the meter doesn't see, or a code path that bypasses the meter entirely. That last one is the serious find: an unmetered path is prohibited, and the monthly reconciliation is how you catch it. The Risk Audit Kit names the unreconciled meter as red flag RF-11; this section is the standing fix.

### Metering checklist

- [ ] Every billable call path passes through the meter — including cron jobs, retries, and background workers.
- [ ] All ten fields are logged on every request; no field is optional.
- [ ] `estimated_cost` uses the current rate card; the card is re-checked when the provider announces changes.
- [ ] A dashboard (or a weekly query) shows spend by `plan_id` and by `agent_identity`.
- [ ] First reconciliation against the provider invoice is done; the gap is explained or fixed.

---

## Part 4 — Alert thresholds and kill-on-overspend rules

Alerts are information. Blocks are control. This section wires both into the three tiers — the same tiers from the Studio Edition, applied to money.

### Bounded auto — the default for most agents

- **Alert at [50]%** of the plan ceiling: notify [OWNER] via [CHANNEL]. Informational — "you're halfway through the night's budget."
- **Alert at [80]%**: page [OWNER] via [PAGER]. Still informational, but louder — the plan has [20]% left and the owner should decide whether that's fine.
- **At [100]%: fail closed.** Block new billable calls, record the block with the reason, pause the plan, page [OWNER]. The plan stays paused until the owner re-authorizes: either a Hard-gated ceiling raise with a recorded reason, or a narrowed workload in a new plan. Retry-after-block is prohibited — a retry is a new plan with a new `plan_id`, not a timer.

### Hard-gated — spend-commit actions

Money-moving actions already require per-instance human approval. Add a per-approval cap: the approval records [APPROVED AMOUNT], and if actual spend exceeds it by more than [10]%, the plan pauses and the owner is paged. Treat the breach as a SEV2 under the Incident Response Runbook — a bound existed and didn't hold, which is an enforcement failure, not a policy gap.

### Draft-only — the tier people forget to meter

Composing is cheap — until a planning agent loops for an hour generating and discarding drafts. The tier describes the *action's* consequence, not its *bill*. Put draft-only agents on the same bounded-auto meter with tighter ceilings (default draft ceiling: [DRAFT CEILING] per plan). A draft agent with no ceiling is leak #2 wearing a "but it's just drafting" excuse.

### Kill-on-overspend rule template

Adopt one per workload. Fill every bracket; post it with the plan.

```
KILL-ON-OVERSPEND RULE — [WORKLOAD] / plan [PLAN_ID]
Ceiling: [AMOUNT] [CURRENCY] per [WINDOW]
Alert:  [OWNER] at [50]% via [CHANNEL]; at [80]% via [PAGER]
At 100%: BLOCK new billable calls · record blocked rows ·
         PAUSE the plan · page [OWNER]
Resume requires: [owner re-authorization / Hard-gated ceiling raise]
Retry-after-block: PROHIBITED — new plan_id required
Reviewed: monthly cost review (Part 5)
Owner: [NAME] · Effective: [DATE]
```

### Alert discipline

Three alerts per plan per window: 50, 80, 100. No more. If you alert at every 10%, the team mutes the channel — and you've built the warning nobody reads (the audit kit's RF-4), except now it's about money. When an alert fires and the owner does nothing, that is data for the monthly review: either the threshold is wrong or the workload's budget is wrong. Fix one of them.

---

## Part 5 — Monthly cost-review ritual

Thirty minutes, same day each month, the owner present. Put it on the calendar now: [DAY OF MONTH], [TIME]. The agenda is fixed — the ritual works because it's the same every time.

**Minutes 0–5 — Reconcile.** Meter total vs. provider invoice for [MONTH]. Difference: [$X] ([Y]% ). If it doesn't reconcile, that's action item #1 and you don't move on until it has an owner.

**Minutes 5–12 — Top 5 plans by spend.** For each: is the workload still justified? Trend vs. last month — up, flat, down, and why? Any plan whose workload ended but whose ceiling is still live gets paused *today*, in the meeting.

**Minutes 12–18 — Leak scan.** Query the meter: retries per request trending up? Output tokens per plan growing? Input tokens per session growing (context bloat)? Any identity with spend but no active workload? Each "yes" becomes an action item tagged with its leak number from Part 6.

**Minutes 18–25 — Ceiling adjustments.** Lower every ceiling that's more than [3]× its measured run rate — a ceiling 10× the run rate is decoration, not control. Raise requests: each is a Hard-gated decision, recorded reason, and the raise itself carries an expiry (leak #10).

**Minutes 25–30 — Action items.** Every item gets an owner and a date. Unfinished items from last month get named out loud — "carried over" without discussion is how leaks become permanent.

### Review template

Copy per month.

```
COST REVIEW — [MONTH] [YEAR]
Attendees: [NAMES] · Owner present: ☐ Yes ☐ No (if no, reschedule — don't review without the owner)

Reconciliation: meter [$M] vs invoice [$I] · gap [$X] ([Y]%)
Top 5 plans:
 1. [plan_id] [$] — trend [up/flat/down] — justified? [Y/N]
 2. [plan_id] [$] — trend [up/flat/down] — justified? [Y/N]
 3. [plan_id] [$] — trend [up/flat/down] — justified? [Y/N]
 4. [plan_id] [$] — trend [up/flat/down] — justified? [Y/N]
 5. [plan_id] [$] — trend [up/flat/down] — justified? [Y/N]
Leaks found: [leak numbers, or "none"]
Ceilings changed: [plan_id]: [old] → [new] ([reason, approver])
Action items:
 1. [action] — [owner] — due [date]
 2. [action] — [owner] — due [date]
Next review: [DATE]
```

---

## Part 6 — Ten cost leaks and the exact control

Each leak: how it burns money, what your meter shows, and the exact control that stops it. These are cost problems specifically — the governance failures behind them (no ceiling, no meter, no identity) are covered in the Risk Audit Kit; here we assume the controls exist and show you where the money still escapes.

### Leak 1 — The retry storm

**Burns:** An agent retries a failing call with no cap — rate-limit retries, flaky-tool retries, "try a different prompt" retries. Each retry re-pays the full context. This is driver #4 at its purest.
**Meter shows:** `retries` field climbing on one `plan_id`; requests with identical `input_tokens` repeating.
**Control:** Cap retries per plan at [MAX RETRIES] with exponential backoff; alert the owner when any request exceeds [3] retries. The meter's `retries` field exists for exactly this — query it in every monthly review.

### Leak 2 — Context bloat

**Burns:** Long sessions re-send the full history every turn. Turn 40 carries turns 1–39. Input-token spend compounds while the agent appears to be "just chatting."
**Meter shows:** `input_tokens` per request growing steadily within one `plan_id`'s session; cost per request rising while output stays flat.
**Control:** Summarize-and-truncate at [N] turns — compress history into a summary and continue from it. Cap input tokens per request at [MAX INPUT TOKENS]; the cap blocks, the summary keeps the work going.

### Leak 3 — Premium model for trivial work

**Burns:** The flagship model classifies inbox mail, formats JSON, and writes commit messages — work a smaller model does identically for a fraction of the rate.
**Meter shows:** One expensive `model` string on `plan_id`s whose outputs are short, structured, and low-stakes.
**Control:** A model allowlist per plan (the plan bound's `resources.model_allowlist` — Studio Edition Part 2). Route routine work to the cheapest adequate model; reserve the flagship for judgments that need it. Review the allowlist when the monthly top-5 shows a costly model on a cheap workload.

### Leak 4 — The always-on poller

**Burns:** A cron job checks every [1] minute for something that changes twice a day. 1,440 checks, ~1,438 of them wasted — each one paying inference and context.
**Meter shows:** A `plan_id` with metronomic request counts and near-zero output variance — the agent equivalent of a dripping tap.
**Control:** Widen the interval to match the actual change rate; better, trigger on events instead of polling. The per-window ceiling catches this even before you notice — which is why the per-window backstop exists.

### Leak 5 — Duplicate tool calls

**Burns:** The agent runs the same search, the same lookup, the same API call multiple times per task because nothing remembered the first answer.
**Meter shows:** Identical `tool_calls` entries repeating within one `plan_id`; tool spend disproportionate to task complexity.
**Control:** Cache tool results keyed on (tool, arguments) with a [TTL] — [15] minutes is a sane default for volatile data, longer for reference data. Log the cache-hit rate; a plan with heavy tool use and a 0% hit rate is this leak.

### Leak 6 — Verbose outputs

**Burns:** The model writes 2,000 words when 200 would do — and output tokens are the expensive direction. Verbosity is a per-request tax on every plan.
**Meter shows:** `output_tokens` consistently high relative to task size; output/input token ratio climbing on a `plan_id`.
**Control:** Cap output tokens per request at [MAX OUTPUT TOKENS]; instruct brevity in the system prompt ("answer in under [150] words unless asked for detail"). Watch the ratio in the monthly leak scan — it's the cheapest query you'll run.

### Leak 7 — Embedding churn

**Burns:** Documents are re-embedded on every run whether they changed or not. Embedding batches are cheap per document and ruinous across thousands of unchanged documents, nightly.
**Meter shows:** Embedding tool calls at constant volume while the source corpus barely changes.
**Control:** Content-hash every document before embedding; only embed what changed. Store the hash alongside the vector. This is a one-time build that pays for itself in the first month — check it in the first review after adopting.

### Leak 8 — The shadow agent

**Burns:** Nobody owns it, nobody watches its meter — a leftover experiment, a contractor's script, a cron job from two teams ago. It spends a little, constantly, forever.
**Meter shows:** An `agent_identity` with steady spend and no active workload row in your Part 2 worksheet. If it's not in the worksheet, it's shadow.
**Control:** The worksheet *is* the control: every spending identity must map to a worksheet row with an owner. Monthly review, minutes 12–18: any metered identity missing from the worksheet gets paused that day. Unmetered execution is prohibited — the reconciliation in Part 3 is how you catch the ones that bypass the meter.

### Leak 9 — Test traffic on paid endpoints

**Burns:** Dev loops, load tests, and "let me just try this" sessions run against production API keys and paid models. Test traffic has the worst cost-to-value ratio in the building.
**Meter shows:** A `plan_id` or identity with bursty, irregular spend that maps to no production workload — especially outside business hours.
**Control:** A separate test identity with a tiny ceiling ([$5]/[DAY] is plenty for most dev loops); route tests to free or local models where they exist. Production keys never appear in dev configs — that's the audit kit's territory; the cost control is the separate identity with its own small ceiling.

### Leak 10 — The creeping ceiling

**Burns:** Nothing — at first. A ceiling raised "temporarily" for a launch, a migration, a demo, and never lowered. Six months later every ceiling is 5× the run rate and the fail-closed boundary is decorative.
**Meter shows:** Ceilings (Part 2 worksheet) drifting upward over successive monthly reviews with no matching run-rate increase.
**Control:** Every ceiling raise carries its own expiry: the raise reverts after [30] days unless re-approved through the Hard-gated path. The monthly review (minutes 18–25) lists every active raise and its expiry date. A raise with no expiry is not a raise — it's leak #10.

---

## Appendix — Adoption checklist

- [ ] Part 1 read: you can name your five cost drivers and estimate each one's share of last month's bill.
- [ ] Part 2 worksheet filled: every active workload has a row, every row has a ceiling and an owner.
- [ ] Kill-on-overspend rule (Part 4 template) adopted for every workload; alert paths tested — page yourself once to prove the pager works.
- [ ] Part 3 meter logging all ten fields on every billable path; first reconciliation against the provider invoice done.
- [ ] Draft-only agents metered with tight ceilings (Part 4) — the tier is not an exemption.
- [ ] First monthly cost review scheduled: [DATE].
- [ ] Part 6 leak scan run once against the meter; every found leak has an owner and a due date.
- [ ] Risk Audit Kit SP-1–SP-8 re-run after adoption — the kit verifies; this workbook sets.

---

### What pairs with this workbook

- *The Playbook — Studio Edition*: the Spend-Limit & Expiry Policy, the plan-bound `cost_ceiling`, the fail-closed budget rule, and the day 6–8 rollout that installs them.
- *AI Agent Risk Audit Kit*: checks SP-1–SP-8 and red flags RF-1 (runaway loop) and RF-11 (unreconciled meter) — run the audit after adopting this workbook to verify the controls are real.
- *Agent Incident Response Runbook*: an overspend that didn't block is a SEV2; the freeze-spend steps in SEV1 triage are the incident version of the kill-on-overspend rule.
- *100 Agent Use Cases, Pre-Tiered*: use case #65 (monitor budget vs. actuals) is the standing version of the monthly ritual — pre-tiered Bounded auto, with the reminder that alerts inform and the block controls.

---

*Agent Cost Control Workbook. An original GhostCorp work. Companion to The Governed Agent Mesh Playbook — Studio Edition. No statistics, testimonials, customer stories, or revenue claims appear in this workbook — every number in your budgets comes from your meter and your provider's rate card; worked examples use [BRACKETED] illustration numbers only.*
