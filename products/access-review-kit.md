# Quarterly Access Review Kit

**The companion that keeps the governance you installed from quietly expiring: a complete quarterly access-review ceremony for agent permissions — inventory worksheets, re-certification sign-offs, a leaver's checklist, automation hooks, and a 90-day calendar that folds the review into your ongoing governance rhythm.**

By GhostCorp · Kestrelattice · September 2026

Companion to *The Playbook — Studio Edition* and the three sibling kits (*Risk Audit Kit*, *Incident Response Runbook*, *Use Case Library*). This kit assumes the three risk tiers and the grant-store model from the Studio Edition. It does not re-explain them — it operates them, once a quarter, forever.

---

## What this is

Grants don't quit when people do. Agents don't resign, agents don't hand in their notice, and a grant issued in March for a one-off migration still lets an agent read your production database in September. Nobody remembers issuing it. That's not a bug in your team — it's the default state of every permissions system ever built. Permissions widen; they never narrow on their own.

This kit is the machinery that narrows them back. It has seven parts:

1. **Why access reviews matter for agents specifically** — the five ways agent grants decay faster than human ones.
2. **The quarterly ceremony** — five steps, in order: inventory every grant, re-certify or revoke, rotate credentials, re-tier changed capabilities, record the review.
3. **Grant inventory worksheet** — one row per grant, in [BRACKETED] fill-in format.
4. **Re-certification sign-off sheet** — the document that makes the review real.
5. **The leaver's checklist** — what to revoke the day a human leaves, and the day an agent is retired.
6. **Automation hooks** — exactly what to script, and what stays a human decision.
7. **The 90-day calendar** — the quarterly review mapped into your weekly and monthly governance rhythm.

**What this is not.** This is not a fix for broken governance — if you don't have an identity registry, a grant store, and recorded grants, adopt the Studio Edition first. This kit is also not an audit: the *Risk Audit Kit* evaluates whether your controls exist. This kit *operates* one specific control — the scheduled grant review that the audit kit's PM-6 check asks for — and keeps it running forever.

**Convention.** [BRACKETED CAPS] are your inputs. Suggested defaults appear in prose where a sane starting value exists. Change them deliberately, not accidentally.

**Who this is for.** Teams that already issue grants to agents — or are about to — and need those grants to stay as tight six months from now as they are on day one.

---

## Part 1 — Why access reviews matter for agents specifically

Human access reviews exist because employees change jobs, projects end, and contractors' contracts expire. Agent grants decay all of those ways, plus five that have no human equivalent:

**1. Agents accumulate; they never self-report.** An employee whose access is wrong will eventually complain, request more, or ask a question that reveals the problem. An agent never does. A grant that's too wide sits silently until it's used — by which point it's an incident, not a review finding.

**2. Grants are invisible by default.** A human with admin access to a system you can see them log into. An agent's grants live in a grant store, a config file, or (worst case) an environment variable — places nobody looks unless the review makes them look. The *Risk Audit Kit* calls this out as RF-5 (The Immortal Grant) and RF-9 (The Mystery Agent); this kit is the scheduled activity that kills both.

**3. Permissions creep without any single decision.** "Just give it admin for the demo." "Widen the scope so the cron stops failing." Each change was reasonable in the moment. None was ever rolled back. Human permission creep gets caught at promotion, transfer, or termination — inflection points agents don't have. The review ceremony *is* the inflection point.

**4. The grant holder and the grant user diverge.** A human leaver triggers offboarding. An agent built by a leaver keeps running with the leaver's credentials and access — nobody revoked anything because nobody thought of the agent as someone who could leave. Part 5 exists because this one is the most common and the most embarrassing.

**5. Capabilities re-tier themselves when nobody's watching.** A bounded-auto agent gets a new integration; now it touches customer data it never touched before. A draft-only agent gets a send tool "for testing"; now it can reach the outside world. The consequence column changed, but the tier label didn't — because nothing forced a re-tier. Step 4 of the ceremony forces it.

**The rule.** Every grant is guilty until re-certified. Not suspected — guilty. The default outcome of a quarterly review is revocation or narrowing, and keeping a grant as-is requires a named owner to say, on record, "this is still correct." That default is the entire kit.

---

## Part 2 — The quarterly review ceremony

Five steps, in order, once per quarter. Budget a half day for a small stack, a full day for a large one. The review owner runs it; grant owners answer for their grants.

**Roles:**

- **[REVIEW OWNER]** — one named human, runs the ceremony, holds the sign-off sheet, and reports the outcome. Not optional. An ownerless review becomes a skipped review.
- **[GRANT OWNERS]** — the humans who requested or issued each grant. Every grant has exactly one. "The team" is not an owner.

### Step 1 — Inventory every grant

Pull the full grant list from your grant store. Every grant — active, expired-but-unrevoked, and suspended. If any agent can act on a capability that isn't in the store, stop: you have a shadow grant, and it goes on the inventory as its own row marked **[SHADOW — no record found]**.

For each grant, fill one row of the inventory worksheet (Part 3). The row demands: the acting identity, the capability and scope, who issued it and when, when it expires, its tier, and the evidence that the capability is still needed.

**Completion rule:** the inventory is complete when every identity in your identity registry maps to at least one row, and every row maps to a real identity. Orphans in either direction are findings, not gaps — a grant with no identity is a shadow grant; an identity with no grants is either retired (revoke it) or undocumented (inventory it).

### Step 2 — Re-certify or revoke

The review owner walks the inventory with each grant owner, grant by grant. For every grant, the owner answers three questions on the record:

1. **Is this capability still needed?** If the answer is no, or "I'm not sure," or "I don't know what this does" — revoke. Uncertainty is not a reason to keep a grant; it's the reason the default is revocation.
2. **Is the scope still the minimum?** The grant that needed the whole customer table in March might need three columns now. Shrink it.
3. **Is the tier still correct?** See Step 4.

The answer is recorded on the sign-off sheet (Part 4) as one of: **re-certified as-is**, **re-certified narrowed**, or **revoked**. There is no fourth option. "Re-certified, will fix later" is a revoked grant with extra words — the fix happens now or the grant dies now.

### Step 3 — Rotate credentials

During the review, rotate every credential an agent holds — API keys, tokens, database passwords — regardless of whether anything looks wrong. Rotation is scheduled, not incident-driven. The cadence is quarterly for routine credentials; the leaver's checklist (Part 5) handles the emergency case.

**Rotation discipline:**

- New credentials go to the vault. They never appear in the audit rows, the grant store, or this worksheet.
- The old credential is revoked, not just replaced — verify revocation by confirming the old credential fails.
- The rotation itself is recorded as an audit row: who rotated, what was rotated (by identifier, never the secret), when, and for which identity.
- If rotation breaks an agent, the breakage is information: it means a credential was hardcoded somewhere it shouldn't be. Fix the wiring, don't roll back the rotation.

### Step 4 — Re-tier changed capabilities

For every grant that survived Step 2, check whether the capability changed since the last review — or since issuance. A new integration, a new data class, a wider blast radius, a bigger spend ceiling: any of these changes the consequence column, and the tier follows the consequence.

**Re-tiering rules (from the Studio Edition's tiering logic):**

- If the capability now moves money, accepts terms, contacts anyone outside the team, touches credentials, changes permissions, or carries legal weight → **Hard-gated**, no exceptions.
- If it now reads data it didn't read before, check for reads with write-grade consequences (customer lists, credential stores, production dumps) → those tier as **Hard-gated**, not "read-only."
- If it only gained internal, reversible, bounded behavior → **Bounded auto**, with the plan's cost ceiling and expiry re-confirmed.
- Tiering down — from Hard-gated to anything lower — is itself a hard-gated decision: named owner, recorded reason, stated bounds. The quarterly review is a fine place to make it; "we've been fine so far" is not a reason.

### Step 5 — Record the review

The review isn't done until the paperwork exists. Archive, in your audit log or alongside it:

- The completed inventory worksheet (Part 3), dated.
- The completed sign-off sheet (Part 4), signed.
- The list of revoked grants, with revocation recorded as audit rows.
- The rotation record: what was rotated, for which identities, old credentials verified revoked.
- Every re-tiering decision, with the reason.

**Completion rule:** the review is complete when the sign-off sheet is signed by the review owner and every grant owner, and the archive exists where the next review's owner can find it in under five minutes. If the next owner can't find it, it doesn't exist.

---

## Part 3 — Grant inventory worksheet

Copy this table once per review. One row per grant. Fill every column — a blank cell is an unanswered question, and unanswered questions are findings.

| Grant ID | Acting identity | Capability + scope | Issued by | Issued | Expires | Tier | Still needed? (Y/N/unsure) | Evidence of need |
|---|---|---|---|---|---|---|---|---|
| [G-001] | agent:[OWNER]/[NAME] | [e.g. read orders table, last 90 days] | [NAME] | [DATE] | [DATE] | [H/B/D] | | [e.g. "powers the weekly ops report; owner confirmed 2026-09"] |
| [G-002] | | | | | | | | |
| [G-003] | | | | | | | | |
| [G-004] | | | | | | | | |
| [G-005] | | | | | | | | |

*(Add rows. Number them sequentially; never reuse a retired grant ID — the ID space is append-only so the archive stays unambiguous.)*

**Shadow-grant rows** — capabilities with no recorded grant. Mark Grant ID as [SHADOW-n] and fill what you can:

| Grant ID | Acting identity | Capability + scope | How it was found | Tier it should be | Owner assigned |
|---|---|---|---|---|---|
| [SHADOW-1] | agent:[OWNER]/[NAME] | [e.g. writes to prod logs dir] | [e.g. found during inventory] | [H/B/D] | [NAME] |

Every shadow grant gets a real grant issued (hard-gated decision, recorded) or the capability gets removed. Shadow grants do not survive the review.

**Tier key:** H = Hard-gated · B = Bounded auto · D = Draft-only.

**Row-level rules:**

- "Expires" must be a real date. "Never" is not a date; "never" means the grant is revoked in Step 2.
- "Evidence of need" must name something checkable: a plan ID, a report it powers, a workflow that breaks without it. "We use it" is not evidence.
- Any row where the grant owner is no longer with the team goes straight to the leaver's checklist (Part 5) before Step 2.

---

## Part 4 — Re-certification sign-off sheet

One sheet per review. The review owner fills it; every grant owner signs it. Copy and fill.

```
ACCESS REVIEW SIGN-OFF — [TEAM NAME]
Review period: [QUARTER, e.g. Q3 2026] · Review date: [DATE]
Review owner: [NAME]

INVENTORY SUMMARY
- Grants inventoried: [N]
- Shadow grants found: [N]
- Identities with no grants (retired / documented): [N] / [N]

DECISIONS
| Grant ID | Decision (as-is / narrowed / revoked) | New scope (if narrowed) | New tier (if changed) | Grant owner sign |
|---|---|---|---|---|
| [G-001] | | | | |
| [G-002] | | | | |
...

TOTALS
- Re-certified as-is: [N]
- Re-certified narrowed: [N]
- Revoked: [N]

CREDENTIAL ROTATION
- Credentials rotated: [N] — identities: [LIST]
- Old credentials verified revoked: ☐ Yes ☐ No (if no, explain: ______)
- Rotation recorded as audit rows: ☐ Yes

RE-TIERING
- Capabilities re-tiered this review: [N]
- Tiered down (with recorded reason + bounds): [N]

SHADOW GRANTS
- Shadow grants found: [N] — disposition: [issued proper grants / capability removed]
- All shadow grants resolved: ☐ Yes ☐ No (if no, list unresolved: ______)

SIGNATURES
- Review owner: ______ Date: ______
- Grant owners: [NAME] ______ Date: ______  (one line per owner)

NEXT REVIEW
- Next review date: [DATE — no more than 90 days out]
- Next review owner: [NAME — named now, not later]

ARCHIVE LOCATION: [WHERE THE COMPLETED WORKSHEET + THIS SHEET LIVE]
```

**The signatures are the control.** An unsigned sign-off sheet is a draft. A signed one is evidence — the kind the audit kit's checklist asks for and the kind a postmortem cites.

---

## Part 5 — The leaver's checklist

Two versions: a human leaves, or an agent is retired. Both are revocation events. The difference is that humans announce their departure; agents don't.

### When a human leaves

Run this on the departure date — not the week after, not "when we get to it." The day.

- [ ] **List every agent the person owned, built, or issued grants for.** Check the identity registry by owner, the grant store by issuer, and the schedule/cron list. Ask the team: "what did [NAME] set up that still runs?" People remember agents the registry forgot.
- [ ] **Revoke the person's own credentials.** API keys, tokens, passwords, SSO access — the standard human offboarding, assumed done. The rest of this list is what standard offboarding misses.
- [ ] **For each agent they owned: reassign ownership or retire it.** An agent with no living owner is an orphan, and orphans don't get to keep grants. Either a named owner adopts it (recorded, with the grants re-certified on the spot) or the agent is retired per the checklist below.
- [ ] **Rotate every credential the person's agents used.** Not just the person's credentials — the agents'. If [NAME] could see the API key in a config file, assume it's known. Rotate it.
- [ ] **Revoke grants the person issued that no current owner will defend.** A grant whose only advocate was the leaver dies with the departure. This is not harsh; it's the default rule from Part 1 applied to a specific event.
- [ ] **Check for personal accounts in agent wiring.** The agent that sends "from" the leaver's personal Gmail, the cron authenticated as their user, the webhook registered under their login. Rewire to team-owned identities or retire the agent.
- [ ] **Verify.** After revocation: confirm the identity shows no new audit rows, the meter shows no new billable calls, and scheduled runs stop firing. "We revoked it" is a claim; the audit log is the evidence.
- [ ] **Record it all as audit rows** — the departure, the revocations, the rotations, the reassignments. The next quarterly review inherits this record.

### When an agent is retired

- [ ] **Revoke the identity** in the identity registry. A revoked identity is never reissued to a different agent — the Studio Edition's identity policy is absolute on this, and retirement is exactly the case it was written for.
- [ ] **Revoke all its grants** in the grant store. Revoke, don't delete — the rows stay in the archive as history.
- [ ] **Cancel its scheduled work:** cron entries, scheduled workflows, queued retries, webhook handlers registered under the identity. The incident runbook's kill-switch checklist is the reference procedure; retirement is the non-urgent version of the same steps.
- [ ] **Rotate the credentials it held.** A retired agent's old key in a backup config is a future shadow credential.
- [ ] **Remove or reassign its outputs:** dashboards it fed, files it wrote, channels it posted to. Decide per output — archive or hand to a successor — and record the decision.
- [ ] **Verify silence:** no audit rows, no meter activity, no scheduled fires for [7] days after retirement. Then close it out.

### The contractor variant

Contractors are leavers with a known end date, which makes them easier — if you use the date. When a contractor starts, set every grant they issue or own to expire on the contract end date. The quarterly review then becomes a formality for contractor grants; the expiry does the work automatically. If you didn't set the expiry at the start, run the human-leaver checklist on the end date anyway.

---

## Part 6 — Automation hooks

The ceremony has mechanical parts and judgment parts. Automate the mechanical ones aggressively — that's what makes the quarterly review cheap enough to actually happen. Never automate the judgment ones; a scripted "re-certify" is a rubber stamp with extra steps.

### Script these

| Hook | What it does | Why it's safe to automate |
|---|---|---|
| **Grant-expiry sweep** | Lists every grant expiring before the next review; flags grants with no expiry at all. | Pure inventory. No decisions. |
| **Orphan detector** | Finds identities with no grants, grants with no identity, grants whose owner is no longer on the team roster. | Pure inventory. The findings go to humans. |
| **Stale-grant report** | For each grant, shows last-used timestamp from audit rows. Grants unused for [90] days get flagged for Step 2. | "Unused" is a fact from the logs. "Unneeded" is still a human call. |
| **Scope-drift diff** | Compares current effective permissions against the grant store's recorded scope. Differences are drift. | Diffing is mechanical. Deciding whether drift was legitimate is Step 4. |
| **Rotation scheduler** | Generates the rotation list for Step 3, executes rotations against the vault, verifies old credentials fail. | The schedule is policy; the vault does the work. Human confirms the verification step. |
| **Review reminder** | 14 days before the review date: notifies the review owner and all grant owners with their grant lists. 3 days before: escalates to [TEAM LEAD] if unacknowledged. | A review nobody remembers is a review that doesn't happen. |
| **Archive check** | Verifies the last review's worksheet and sign-off sheet exist at the archive location and are complete (every row has a decision, every owner signed). | The next review's Step 1 depends on the last review's archive. |

### Keep these human

| Decision | Why a human decides |
|---|---|
| Re-certify vs. revoke vs. narrow | Requires knowing whether the capability is still needed — a business judgment, not a log query. |
| Re-tiering | Requires assessing whether the consequence column changed — new integrations, new data classes, new blast radius. |
| Shadow-grant disposition | Requires deciding whether an undocumented capability should exist at all. |
| Leaver grant triage | Requires knowing what the departed person's agents were actually for. |
| Signing the sign-off sheet | A signature is a person taking responsibility. A script cannot take responsibility. |
| Tiering down (Hard-gated → lower) | Always a hard-gated decision: named owner, recorded reason, stated bounds. |

**The line, stated once:** scripts find and prepare; humans decide and sign. If a proposed automation would let a grant survive the review without a human looking at it, it's not automation — it's the permission creep, automated.

### Minimum viable automation

If you automate nothing else, automate two hooks: the **grant-expiry sweep** and the **review reminder**. Expiries are the cheapest control in the whole system — a grant that dies on its own never becomes an immortal one — and the reminder is what turns "quarterly" from an aspiration into a calendar event. Everything else can be manual at first; the ceremony works on paper. It just works better with the sweep and the reminder running.

---

## Part 7 — The 90-day calendar

The quarterly review is the peak of an ongoing rhythm, not a standalone event. Map it onto the weekly and monthly cadence your governance already runs — or should run:

**Weekly (ongoing):**

- **Chain/log verification** — confirm the audit hash chain is intact (the runbook's standing practice). A broken chain found during the quarterly review means three months of unverifiable history.
- **SEV4 / near-miss review** — scan the near-miss log for patterns. Three near-misses with the same shape escalate before the quarter ends.
- **Spend-ceiling alerts** — the thresholds fire on their own; the weekly job is confirming someone actually looked at them.

**Monthly (ongoing):**

- **Permission spot-check** — the review owner picks [5] grants at random and verifies scope, owner, and tier against the grant store. This is the quarterly review in miniature; it keeps the full ceremony from being a surprise.
- **Leaver/contractor sweep** — anyone left this month? Any contract ended? Run the relevant Part 5 checklist immediately, not at quarter's end.
- **Drill one control** — kill switch, rotation, or re-tiering, on a non-production identity. The runbook's quarterly drill guidance applies; monthly is better if you can afford it.

**Quarterly (the ceremony — this kit):**

- **Week 1 — Prepare.** Run the automation hooks: expiry sweep, orphan detector, stale-grant report, scope-drift diff. Send the review reminder with grant lists to every grant owner. Assemble last quarter's archive as the starting point.
- **Week 2 — Review.** Run Steps 1–5 of the ceremony (Part 2). Walk the inventory with grant owners. Decide every grant. Rotate credentials. Re-tier. This is the half-day or full-day session.
- **Week 3 — Record and follow through.** Sign-off sheet signed. Archive stored. Revocations verified (silence confirmed per Part 5's verification step). Any shadow grants resolved — issued properly or removed.
- **Week 4 — Report.** Review owner reports the totals to [TEAM LEAD / FOUNDER]: grants inventoried, revoked, narrowed, re-tiered; credentials rotated; shadow grants found and resolved. Next review owner named. Next review date on the calendar — the reminder hook picks it up from there.

**The first quarter is the hardest.** The first review will find the most shadow grants, the most immortal grants, the most "I don't know what this does." That's the point — you're paying down the backlog every previous quarter accrued. The second review is half the work. By the third, the monthly spot-checks and expiring grants have done most of the narrowing for you, and the ceremony is mostly confirmation. Governance compounds, same as the creep did — in the other direction.

---

## Appendix — Adopting this kit

- [ ] Review owner named for the next four quarters: [Q1 OWNER], [Q2 OWNER], [Q3 OWNER], [Q4 OWNER]. The owner can rotate; the role cannot be vacant.
- [ ] Grant store and identity registry exist and are current (Studio Edition, Parts 1–2). If not, adopt those first — this kit operates them.
- [ ] Every existing grant has an owner, an expiry, and a tier. Grants missing any of the three get all three before the first review.
- [ ] Archive location chosen: [LOCATION]. Last review's materials must be findable in under five minutes.
- [ ] At minimum, the grant-expiry sweep and review reminder hooks are running (Part 6).
- [ ] First review date set: [DATE]. Reminder sent to all grant owners with their grant lists.
- [ ] Leaver's checklist (Part 5) posted where offboarding happens — HR doc, ops runbook, wherever departures are processed. It must be reachable on the day, not discoverable the week after.
- [ ] The 90-day calendar (Part 7) merged with your existing weekly/monthly rhythm: chain verification, near-miss review, spot-checks, drills.

---

*Quarterly Access Review Kit. An original GhostCorp work. Companion to The Governed Agent Mesh Playbook — Studio Edition. No statistics, testimonials, customer stories, or revenue claims appear in this kit — every worksheet is written to be executed during a real review.*
