# Agent Incident Response Runbook

**The incident-response companion to the Studio Edition: severity levels, triage procedures, kill-switch and rollback checklists, a blameless postmortem template, and an escalation policy — ready to adopt.**

By GhostCorp · Kestrelattice · September 2026

---

## How to use this runbook

This runbook assumes the Studio Edition's six policies are adopted — identity, grants, hard gates, spend limits, fail-closed blocks, audit retention. If they aren't, this document still works, but several steps will say "revoke the grant" or "verify the audit chain," and without those systems you'll be improvising. Adopt the policies first; keep this runbook next to them.

**Convention:** [BRACKETED CAPS] are your inputs. Fill every bracket before you call this runbook adopted. Suggested defaults appear in prose where a sane starting value exists — change them deliberately, not accidentally.

One rule governs everything below: **when in doubt, contain first.** You can always un-kill an agent. You cannot unsend its outputs.

---

## Part 1 — Severity levels

Severity is assigned by blast radius and reversibility, not by how embarrassed anyone feels. Assign the highest severity whose criteria match. When two people disagree, the higher severity wins — downgrading is a decision you make deliberately in the postmortem, never in the moment.

### The four levels

**SEV1 — Critical.** External or financial impact is happening or has happened.

- Money moved, committed, or accepted without a recorded human approval.
- External outreach (email, message, post, call) sent without approval.
- Credentials or secrets accessed, read, or transmitted outside their grant.
- Data of class confidential or restricted (your scale, from the plan bound) left your control.
- Any Hard-gated action executed without a recorded human approval — automatically SEV1, no debate.

**SEV2 — Major.** A bound was breached or a control failed, but no external or financial impact yet.

- A spend ceiling was hit and the action did not fail closed — it retried, warned, or kept billing.
- An agent acted outside its grant scope with no external side effect yet.
- The audit hash chain is broken or rows are missing.
- A permission or grant change took effect without approval.

**SEV3 — Minor.** A control degraded; nothing escaped.

- Draft-only output was one step from sending (caught in review or by a gate).
- A warning-only path was found on an action with external or financial side effects.
- A grant expired mid-run and produced a cascade of blocks — noisy, not dangerous.

**SEV4 — Near miss.** Something looked wrong; no bound breached, no impact.

- A spike in blocked attempts from one identity.
- Meter counts don't reconcile with provider billing.
- An unknown or unregistered actor appeared in the logs.
- Anything that made someone say "that's odd" about agent behavior.

### Response table

| Severity | Acknowledge within | Who responds | Updates every |
|---|---|---|---|
| SEV1 | 15 minutes | Incident commander + all responders | 30 minutes until contained |
| SEV2 | 1 hour | Commander + owning team | 2 hours until contained |
| SEV3 | Same business day | Owning team | Daily until resolved |
| SEV4 | Next weekly review | Whoever noticed it | Logged; reviewed weekly |

Suggested defaults. Tighten them as you grow; never loosen them after an incident teaches you otherwise.

---

## Part 2 — Triage procedures

Every severity follows the same three phases: **contain, assess, recover.** Contain stops the bleeding. Assess finds the blast radius. Recover restores service without reintroducing the failure. Never skip contain to "quickly assess" — assessment on a still-running incident is just watching the damage grow.

### SEV1 triage

**Phase 1 — Contain (first 15 minutes)**

- [ ] First responder declares the incident and assumes incident commander, or hands command explicitly: "I am IC, [NAME] is scribe."
- [ ] Start the incident log (Appendix A). From here on, every action gets a timestamp.
- [ ] Identify the acting identity: `agent:[OWNER]/[NAME]` and the `plan_id` from the audit log or alert. If you cannot identify the actor, treat every agent as suspect and run the global kill switch (Part 3).
- [ ] Run the kill-switch checklist (Part 3) for the implicated identity. Do not wait for full understanding.
- [ ] Freeze spend: confirm the meter shows no new billable calls from the identity; if the framework has no kill path, rotate or disable the provider API key the agent uses.
- [ ] If credentials or customer data may be involved, rotate the credentials now. Rotation is cheap; exposure is not.
- [ ] Preserve evidence: export the audit rows for the incident window and verify the chain (Studio Edition, Part 2). Snapshot the grant store and identity registry as they are right now — do not "clean up" before the postmortem.

**Phase 2 — Assess (15–60 minutes)**

- [ ] Reconstruct the timeline from audit rows: first anomalous row (`row_id`, `seq`, timestamp), what the agent did, which bounds it crossed.
- [ ] Name the control that should have stopped it: identity check, grant scope, hard gate, spend ceiling, fail-closed block, or audit. Be specific — "the gate" is not specific; "the hard-gated approval on external outreach for plan_9f2c" is.
- [ ] Determine reversibility for each affected action (Part 4): which outputs can be recalled or reverted, which cannot.
- [ ] Scope the blast radius: money (amount, direction, counterparty), messages (recipients, content), data (classes, volume, destination), permissions (what changed, for whom).
- [ ] Notify per the escalation policy (Part 6): SEV1 pages the full chain immediately, including [FOUNDER/CEO].

**Phase 3 — Recover (after assessment, not before)**

- [ ] Execute the rollback checklist (Part 4) for reversible actions; execute the mitigation plan for irreversible ones.
- [ ] Fix the failed control and test it before anything runs again: replay the exact failure in a sandbox and confirm the block. The agent does not run again until the control that should have stopped it is fixed and proven.
- [ ] Re-enable in stages: identity re-issued (never reuse a revoked identity for a different agent), fresh grants with tightened scope, a new plan with a lower ceiling for the first runs back.
- [ ] Keep the incident open until the postmortem (Part 5) is complete and its action items have owners and dates. "Recovered" means service restored; "closed" means the control gap is fixed.

### SEV2 triage

- [ ] Acknowledge within 1 hour; assign a commander (can be the owning team's lead).
- [ ] Contain: revoke or narrow the implicated grants; pause the plan. Full kill switch only if the agent is still acting outside scope.
- [ ] Preserve evidence: export audit rows for the window; verify the chain — a SEV2 with a broken chain is a SEV1 until proven otherwise.
- [ ] Assess: which bound failed and why the fail-closed behavior didn't engage. If a ceiling existed but didn't block, that's a bug in your enforcement path, not a policy gap — treat it as one.
- [ ] Recover: fix the enforcement, test with a replay, re-enable with tighter bounds.
- [ ] Postmortem required (Part 5); the lightweight version in the template's notes is acceptable.

### SEV3 triage

- [ ] Log it the same business day with the incident log template (Appendix A).
- [ ] Fix the degraded control: convert the warning-only path to a block, renew the grant, tighten the review step.
- [ ] No full postmortem required, but record the cause and the fix — SEV3s are where SEV1s come from.

### SEV4 triage

- [ ] Log it. That's the whole procedure.
- [ ] Review the SEV4 log weekly. Three near-misses with the same shape are a SEV3 wearing a disguise — escalate the pattern, not just the incidents.

---

## Part 3 — Kill-switch checklist

Two scopes: **targeted** (one identity) and **global** (everything stops). Use targeted when you know the actor; use global when you don't, or when the actor might have siblings — same owner, same plan family, duplicated identity.

### Targeted kill switch

Run in order. Check each box as it completes — during an incident, memory is unreliable and the checklist is the memory.

- [ ] 1. Pause the dispatcher/scheduler so no new runs start for `agent:[OWNER]/[NAME]`.
- [ ] 2. Revoke the identity's grants in the grant store. Record the revocation as an audit row.
- [ ] 3. Terminate in-flight runs: cancel at the provider/framework level, kill local processes. Confirm termination — "sent the cancel" is not "it stopped."
- [ ] 4. Confirm the meter shows zero new billable calls from the identity over the next [5] minutes.
- [ ] 5. Check for scheduled work the kill didn't reach: cron entries, scheduled workflows, queued retries, webhook handlers registered under the identity. Kill those too.
- [ ] 6. Check for identity duplication: any other identity with the same owner/name pattern or the same API key. A kill that misses the twin is theater.
- [ ] 7. Verify the kill in the audit log: no new rows with the identity as actor after the kill timestamp. If rows keep appearing, you haven't killed it — go back to step 1 and widen to global.

### Global kill switch

- [ ] 1. Stop the dispatch path entirely: pause the scheduler, disable the dispatcher, or take the runner hosts out of rotation — whichever stops new agent actions fastest in your stack.
- [ ] 2. Revoke all non-human grants, or set the grant store to deny-by-default if your implementation supports it. Record the change as an audit row.
- [ ] 3. Disable or rotate the provider API keys the agents use. This is the backstop that works even when your own control plane is the thing that's broken.
- [ ] 4. Confirm zero new agent-attributed audit rows for [10] minutes.
- [ ] 5. Notify per the escalation policy — a global kill is automatically at least a SEV2.

### Re-enable checklist

Never re-enable from the incident state. Re-enable from a known-good state:

- [ ] The failed control is fixed and has passed a replay test (Part 2, SEV1 Phase 3).
- [ ] The identity is re-issued fresh if it was revoked — a revoked identity is never reissued to a different agent (Identity Policy, Studio Edition Part 1).
- [ ] Grants are re-issued at least-privilege, with expiries, for the specific recovery plan.
- [ ] The first runs back use a new `plan_id` with a reduced cost ceiling and a short expiry.
- [ ] The incident commander signs off on re-enable. Not the agent owner alone — the commander.

**Test this quarterly.** A kill switch you've never pulled is a hope, not a control. Schedule a drill: pick a non-production identity, run the targeted checklist, time it, fix what was slow or missing. Record the drill in the audit log with a `drill` label so drill rows never mix with incident history.

---

## Part 4 — Rollback checklists

"Rollback" means different things for different actions. Before you touch anything, classify every affected action into one of two buckets. This classification decides your whole recovery.

### Step 0 — Classify: reversible vs irreversible

| Reversible (can be undone) | Irreversible (can only be mitigated) |
|---|---|
| Grant or permission changes | Money sent or committed |
| Configuration and policy edits | Messages, emails, posts sent |
| Drafts and internal artifacts | Data exfiltrated or published |
| Feature flags, routing rules | Contracts or terms accepted |
| Cached or derived data | Credentials seen by an unauthorized party |

Be honest about the bucket. Treating an irreversible action as reversible is how a SEV1 becomes a SEV1 with a cover-up attached.

### Rollback: reversible actions

- [ ] Identify the last-known-good state: versioned policy files, grant store snapshots, config history. If you don't have versioned state, your first postmortem action item is to get it.
- [ ] Revert to last-known-good. Revert, don't hand-edit forward — hand edits during recovery are how you introduce the next incident.
- [ ] Verify the revert: the reverted state matches the snapshot exactly (diff it), and a test action behaves as the policy requires.
- [ ] Record the revert as an audit row with a reference to the incident ID.

### Mitigation: irreversible actions

For each irreversible action, work the list:

- [ ] **Money:** contact the counterparty or payment provider immediately about reversal options; record amounts, timestamps, and transaction references; notify [FINANCE OWNER]. Assume it is not coming back and plan accordingly.
- [ ] **Messages sent:** do not send a "correction" blast without approval — a second unapproved outreach is a second incident. Draft the correction and route it through the hard-gated approval path like any other external outreach.
- [ ] **Data exfiltrated:** determine exactly what classes and volumes left; rotate any exposed credentials; notify affected parties per your legal obligations in [JURISDICTION]. This is a legal-involved incident (Part 6).
- [ ] **Contracts accepted:** involve [LEGAL OWNER] before any further action. Do not attempt to "un-accept" by having the agent take more actions.
- [ ] **Credentials seen:** rotate them, then check access logs for use of the old credentials between exposure and rotation.

### Data restore

- [ ] Restore from backup only after confirming the backup predates the incident window and is clean of the incident's effects.
- [ ] Verify the restore in an isolated environment before pointing production at it.
- [ ] If no clean backup exists, say so in the postmortem and make backups the highest-priority action item. Do not improvise a "mostly clean" restore.

---

## Part 5 — Blameless postmortem template

Run the postmortem within [5] business days of containment. The goal is a stronger control plane, not a culprit. If the document starts assigning fault to a person, it's broken — rewrite it around the control that failed.

Copy this template per incident.

```
POSTMORTEM — [INCIDENT ID]
Severity: [SEV1–SEV4] · Date: [DATE] · Commander: [NAME]
Responders: [NAMES]
Status: [OPEN / ACTION ITEMS PENDING / CLOSED]

1. SUMMARY (three sentences)
[What happened, what the impact was, what stopped it.]

2. TIMELINE (from audit rows — cite row_id / seq)
[HH:MM] [EVENT] (row_[id], seq [n])
[HH:MM] [EVENT]
…first anomalous row, containment actions, notifications, recovery steps.

3. IMPACT
- Money: [amount / none]
- External communications: [count and recipients / none]
- Data: [classes and volumes / none]
- Duration of exposure: [window]
- Customers affected: [count / none]

4. THE CONTROL THAT SHOULD HAVE STOPPED IT
[Name the specific control: e.g. "hard-gated approval on external outreach
for plan_9f2c-…". Then answer: did the control exist and fail, or did it
never exist? These are different failures with different fixes.]

5. FIVE WHYS (control-focused — no person's name in the root cause)
Why 1: [e.g. The agent sent the messages.]
Why 2: [e.g. The send action executed without a recorded approval.]
Why 3: [e.g. The approval gate checked a stale grant cache.]
Why 4: [e.g. The cache had no invalidation on grant revocation.]
Why 5: [e.g. Invalidation was documented as a requirement but never
         implemented.]

6. CONTRIBUTING FACTORS (blameless — systems, not people)
- [e.g. No alert fired at 80% of the plan ceiling — the threshold was
  configured but the notification path was never tested.]
- ["The on-call didn't notice" is not a factor.
  "The spend view took five clicks to reach" is.]

7. WHAT WENT WELL
- [e.g. Kill switch executed promptly; audit chain intact and complete.]

8. ACTION ITEMS
| # | Action | Owner | Due | How we verify it |
|---|--------|-------|-----|------------------|
| 1 | [e.g. Add cache invalidation on grant revocation] | [NAME] | [DATE] | [Replay test blocks the unapproved send] |
| 2 | | | | |

Every action item needs an owner, a date, and a verification method.
"Be more careful" is not an action item.

9. FOLLOW-UP
Review date: [DATE — within 30 days]. Reopen if any action item misses
its date. An incident with overdue action items is still open.
```

**Blamelessness, enforced.** Review the draft postmortem for names attached to failures. "The deploy script had a bug" is fine. "[NAME] broke the deploy" gets rewritten. People hide incidents when postmortems punish; hidden incidents are the ones that become SEV1s.

---

## Part 6 — Escalation policy template

Fill every bracket. Post this where the team can find it at 3 a.m. — a policy nobody can locate during an incident doesn't exist.

```
ESCALATION POLICY — [TEAM NAME]
Version [VERSION] · Effective [DATE] · Owner: [POLICY OWNER]

1. SEVERITY → RESPONSE
   - SEV1: page immediately. [PRIMARY ON-CALL] and [SECONDARY ON-CALL]
     via [PAGER — e.g. PagerDuty, Opsgenie, or phone tree]. Notify
     [FOUNDER/CEO] within 30 minutes. All-hands until contained.
   - SEV2: notify [PRIMARY ON-CALL] and [TEAM LEAD] within 1 hour via
     [CHANNEL]. Founder notified if customer impact is confirmed.
   - SEV3: ticket to [OWNING TEAM] the same business day via [TRACKER].
   - SEV4: log it; reviewed at the weekly ops review.

2. ON-CALL ROTATION
   - Primary: [NAME / ROTATION SCHEDULE]; Secondary: [NAME / SCHEDULE].
   - Handoff requires explicit acknowledgment. A page nobody acknowledges
     escalates to secondary after [15] minutes, then to [FOUNDER/CEO].
   - The rotation lives in [LOCATION — calendar, pager schedule, doc].

3. INCIDENT COMMANDER AUTHORITY
   During an active SEV1/SEV2, the commander may, without further approval:
   - Take any agent, plan, or integration offline.
   - Spend up to [AMOUNT] on mitigation (provider overages, emergency
     vendor support, forensics help).
   - Page anyone in [TEAM NAME], including the founder.
   The commander may NOT: change policy unilaterally, re-enable a killed
   agent without the fixed control passing its replay test (Part 3), or
   communicate externally beyond the holding statement below.

4. LEGAL INVOLVEMENT — notify [LEGAL OWNER / CONTACT] immediately when:
   - Any data of class confidential or restricted left your control.
   - A contract or terms of service was accepted by an agent.
   - A regulator, customer, or counterparty asks about the incident
     in writing.

5. CUSTOMER COMMUNICATION
   - Only [COMMS OWNER] speaks externally. Engineers do not freelance
     updates.
   - Holding statement (fill once, reuse): "[TEAM NAME] experienced an
     automated-systems issue on [DATE]. We contained it at [TIME]. We're
     investigating and will share findings by [DATE]."
   - Post the holding statement within [2] hours of SEV1 containment.
     Silence reads as concealment; a holding statement buys honest time.

6. REVIEW
   This policy is reviewed quarterly and after every SEV1/SEV2. An
   escalation path that didn't fire during a real incident is a failed
   drill — fix the path, then re-test it.
```

---

## Part 7 — First 30 minutes card

Print this. One page. Tape it where the on-call sits. When the alert fires, you won't be thinking clearly — that's what the card is for.

```
┌─ FIRST 30 MINUTES — AGENT INCIDENT ─────────────────────────────
│ MINUTES 0–5: DECLARE
│ □ Say it out loud: "I'm declaring a [SEV] incident. I'm IC."
│ □ Open the incident log (Appendix A). Timestamp everything from here.
│ □ Assign a scribe if anyone else is present.
│
│ MINUTES 5–10: IDENTIFY + KILL
│ □ Acting identity? agent:_____/_____   plan_id: _______________
│ □ Can't identify it → GLOBAL kill switch (Part 3).
│ □ Can identify it → TARGETED kill switch (Part 3), steps 1–7.
│ □ Confirm the meter: zero new billable calls from the identity.
│
│ MINUTES 10–20: FREEZE + PRESERVE
│ □ Spend frozen? (meter flat / API key rotated or disabled)
│ □ Credentials possibly exposed? → ROTATE NOW, don't deliberate.
│ □ Export audit rows for the incident window. Verify the chain.
│ □ Snapshot grant store + identity registry as-is. Don't clean up.
│
│ MINUTES 20–30: ASSESS + NOTIFY
│ □ Blast radius: money $_____  messages _____  data classes _____
│ □ Notify per escalation policy (Part 6). SEV1 → page everyone now.
│ □ Set next check-in: _____ (SEV1: every 30 min). Don't end the call
│   without a next check-in time.
│
│ REMEMBER: contain first. You can un-kill an agent.
│ You cannot unsend its outputs.
└─────────────────────────────────────────────────────────────────
```

---

## Appendix A — Incident log template

One log per incident. The scribe owns it during the event; the commander reviews it after.

```
INCIDENT LOG — [INCIDENT ID]
Severity: [SEV]   Declared at: [HH:MM]   Commander: [NAME]   Scribe: [NAME]
Suspected identity: agent:[OWNER]/[NAME]    plan_id: [ID]

[HH:MM] [EVENT / ACTION / DECISION]
[HH:MM] [EVENT / ACTION / DECISION]
…

Contained at: [HH:MM]   Method: [kill-switch scope / grant revoke / …]
Notifications sent: [who, when, how]
Re-enable approved by: [COMMANDER] at [HH:MM]
Postmortem scheduled: [DATE]
```

---

## Appendix B — Adopting this runbook

- [ ] Severity levels (Part 1) reviewed; response-time defaults accepted or changed deliberately.
- [ ] Triage procedures (Part 2) walked through in a tabletop exercise: narrate a SEV1 start to finish and confirm everyone knows their role.
- [ ] Kill-switch checklist (Part 3) tested quarterly on a non-production identity; drill timed and gaps fixed.
- [ ] Rollback classification (Part 4) completed in advance for your three highest-risk capabilities — don't classify for the first time mid-incident.
- [ ] Postmortem template (Part 5) copied to [LOCATION]; first postmortem reviewed for blamelessness.
- [ ] Escalation policy (Part 6) filled, posted where on-call can find it at 3 a.m., contact paths tested.
- [ ] First-30-minutes card (Part 7) printed and posted.
- [ ] All brackets in this document filled. An unfilled bracket is a decision deferred to the worst possible moment.

---

*Agent Incident Response Runbook. An original GhostCorp work. Companion to The Governed Agent Mesh Playbook — Studio Edition. No statistics, testimonials, or customer stories appear in this document; every checklist is written to be executed during a real incident.*
