# 100 Agent Use Cases, Pre-Tiered

**The governance thinking, done for you: 100 concrete things small teams actually do with AI agents, each one assigned to a tier — with the rationale and the key control to put in place.**

By GhostCorp · Kestrelattice · September 2026

Companion to *The Playbook — Studio Edition*. This library assumes the three-tier system from that edition. Nothing here re-explains the policies or schemas — it applies them, one hundred times.

---

## The three tiers, in thirty seconds

Every use case in this catalog lands in exactly one tier. Tier by **consequence, not frequency** — how bad it is if the action is wrong, not how often you run it.

- **Hard-gated.** A recorded human approves every single time. No auto-grant path, ever. This is where money moves, contracts get accepted, messages leave the building, credentials get touched, permissions change, or the law gets involved.
- **Bounded auto.** Runs on its own inside an approved plan — with a cost ceiling, an expiry date, a scoped grant, and full audit. It auto-blocks the moment any bound is hit.
- **Draft-only.** Prepares, composes, plans. Recorded, never executed, never contacts anyone. Sending, publishing, or acting on a draft is always a separate hard-gated action.

**The shape of this catalog:** 41 hard-gated · 48 bounded auto · 11 draft-only. That ratio is the point — most of what agents do all day is safe to automate inside bounds, and the dangerous minority always goes through a human.

## How to use this library

1. **Find your use case.** If it's here, adopt the tier as written — the argument for it is in the Rationale column.
2. **Install the key control.** The Key control column names the single most important mechanism for that item. It is the minimum, not the menu.
3. **When in doubt, tier up.** A bounded-auto action that should have been hard-gated is an incident; a hard-gated action that could have been bounded auto is just a slow afternoon.
4. **You can earn a lower tier.** Downgrading a tier is itself a hard-gated decision: a named owner approves it, records the reason, and sets the bounds the lower tier will run inside. Several rows below name the exact path.
5. **Re-tier when the blast radius changes.** A new integration, a new data class, or a bigger spend ceiling changes the consequence column — and the tier follows the consequence.
6. **Watch the reads.** The most commonly mis-tiered actions look read-only: exporting a customer list, dumping a production database, reading a credential store. Reads with write-grade consequences get write-grade tiers.

If your use case isn't in the catalog, tier it yourself with the blank worksheet at the end.

---

## Operations

| # | Use case | Tier | Rationale | Key control |
|---|----------|------|-----------|-------------|
| 1 | Triage the shared inbox into categories (billing, bug, praise, spam) | Bounded auto | Read-and-classify only; nothing leaves the inbox. | Scope the grant to inbox labels; log every classification. |
| 2 | Draft replies to routine vendor inquiries | Draft-only | Composing is safe; sending is a separate action. | Drafts are watermarked internal-only; send requires its own hard-gated approval. |
| 3 | Summarize the weekly ops meeting transcript | Bounded auto | Internal text transform with no external effect. | Data-class the output "internal"; apply your retention policy. |
| 4 | Extract action items from meeting notes | Bounded auto | Read-only transform of text you already own. | Write output to plan-scoped storage only. |
| 5 | Generate a daily standup digest from ticket updates | Bounded auto | Internal reporting; reversible and low-stakes. | Read-only grant on the ticket system — no write grant issued. |
| 6 | Reorder office supplies when stock runs low | Hard-gated | Commits spend to an outside vendor. | Recorded human approval against a per-order spend threshold. |
| 7 | Book travel for team members | Hard-gated | Commits spend and creates external bookings. | Approval records the itinerary and the cost ceiling together. |
| 8 | Schedule internal meetings from team availability | Bounded auto | Internal calendar writes; reversible in one click. | Calendar scope limited to the team; external guests need approval. |
| 9 | Send meeting invites to external guests | Hard-gated | A message leaving the building under your name. | Recorded approval of the guest list before anything sends. |
| 10 | File expense reports from photographed receipts | Bounded auto | Creates internal records; pays nobody. | Finance reviews the report; the reimbursement itself stays hard-gated. |
| 11 | Approve expense reimbursements | Hard-gated | Moves money out of the company. | Recorded human approval plus policy amount caps per category. |
| 12 | Update the internal wiki from release notes | Bounded auto | Internal docs; every edit is reversible. | Write scope limited to the wiki space; keep full change history. |
| 13 | Watch SLA dashboards and page the on-call human | Bounded auto | Alerting is information, not action. | Read-only dashboard grant; the agent pages — it never auto-remediates. |
| 14 | Restart a failed staging service | Bounded auto | Non-production; blast radius is contained. | Staging-only grant, max restarts per window, owner alerted each time. |
| 15 | Restart a failed production service | Hard-gated | Production state change with customer impact. | Approve each restart — or pre-approve the runbook once as a bounded-auto plan with a max-restart budget and owner alerts. |
| 16 | Rotate API keys on a schedule | Hard-gated | Touches credential material directly. | Human-approved rotation window; new key goes to the vault, never the logs. |
| 17 | Read secrets from the vault for a deployment | Hard-gated | Accessing credentials is always gated. | Grant record with a time-bounded stated purpose; no secret ever lands in an audit row. |
| 18 | Generate the weekly ops report for leadership | Bounded auto | Internal reporting from data you own. | Label the data class; no grant for external distribution. |

---

## Sales & marketing

| # | Use case | Tier | Rationale | Key control |
|---|----------|------|-----------|-------------|
| 19 | Score inbound leads from form fills | Bounded auto | Internal scoring; contacts nobody. | Version the scoring criteria; issue no outreach grant. |
| 20 | Enrich lead records with public company data | Bounded auto | Read-only enrichment of records you hold. | Egress allowlist for the data providers; handle PII per its data class. |
| 21 | Draft personalized first-touch emails | Draft-only | Composing is safe; sending is the gated action. | Sending requires a separate hard-gated approval with a reviewed list. |
| 22 | Send cold outreach emails | Hard-gated | External outreach to strangers; reputation and spam risk. | Recorded approval plus a reviewed recipient list, every batch. |
| 23 | Send follow-ups to warm prospects | Hard-gated | Still external outreach — "warm" doesn't change the tier. | Approval per campaign; honor unsubscribes automatically. |
| 24 | Post to the company social accounts | Hard-gated | Public speech under the company name. | Recorded approval of the exact copy and schedule. |
| 25 | Draft social post copy | Draft-only | Words on a page until someone publishes them. | Publishing is a separate hard-gated action. |
| 26 | Reply to comments on company posts | Hard-gated | Public, external, and attributable to you. | Recorded approval — or a pre-approved response playbook with human spot-checks. |
| 27 | Summarize call transcripts into the CRM | Bounded auto | Internal record-keeping. | Verify recording consent before processing; data-class the output. |
| 28 | Update CRM fields from call notes | Bounded auto | Internal system of record; edits are reversible. | Field-level write scope; retain the change log. |
| 29 | Generate the weekly pipeline report | Bounded auto | Internal reporting. | No external distribution grant on the report. |
| 30 | Build a target account list from ICP criteria | Bounded auto | Internal research; contacts nobody. | Egress allowlist for sources; contacting anyone is a separate hard-gated action. |
| 31 | Draft a proposal for a prospect | Draft-only | A proposal is a plan until it's sent. | Sending — and any terms it commits — stays hard-gated. |
| 32 | Send a proposal to a prospect | Hard-gated | External, and it commits commercial terms. | Recorded approval of the final terms, not just the draft. |
| 33 | Apply a discount to a quote | Hard-gated | Commits revenue terms. | Approval inside a written discount-authority matrix. |
| 34 | Publish a blog post to the CMS | Hard-gated | Public-facing content under your brand. | Recorded editorial approval of the final post. |
| 35 | A/B test email subject lines on the list | Hard-gated | Real emails to real people, even as a test. | Approval of the test plan and the exact list segment. |

---

## Support

| # | Use case | Tier | Rationale | Key control |
|---|----------|------|-----------|-------------|
| 36 | Classify incoming tickets by topic and urgency | Bounded auto | Read-and-classify; replies are a separate action. | No auto-reply grant; log every classification. |
| 37 | Draft replies to common questions | Draft-only | Composing is safe; the customer never sees a draft. | Sending requires its own hard-gated approval. |
| 38 | Send replies to customers | Hard-gated | External communication under your brand. | Recorded approval — or approved macros with regular human spot-checks. |
| 39 | Summarize long ticket threads for handoff | Bounded auto | Internal transform of your own records. | Data-class internal; never expose the summary externally. |
| 40 | Look up order status for a customer inquiry | Bounded auto | Read-only lookup. | Read grant on orders only; pull the minimum PII needed. |
| 41 | Issue a refund | Hard-gated | Moves money, and it's hard to un-move. | Recorded approval plus per-agent refund policy caps. |
| 42 | Apply account credit | Hard-gated | A financial commitment by another name. | Approval plus written credit limits. |
| 43 | Reset a customer's password | Hard-gated | Account-security action; abuse vector if wrong. | Verify the requester's identity first; log the reset. |
| 44 | Change a customer's plan or subscription | Hard-gated | A billing change is a money movement. | Recorded approval plus the customer's own confirmation. |
| 45 | Export a customer's data for a portability request | Hard-gated | Bulk PII export — a read with write-grade consequences. | Verified requester identity, encrypted transfer, full logging. |
| 46 | Delete customer data on request | Hard-gated | Irreversible, with legal consequences if wrong. | Verified identity plus legal sign-off; log everything. |
| 47 | Update the help-center article from a resolved ticket | Bounded auto | Internal docs; reversible. | Docs-only write scope; route through a review queue. |
| 48 | Detect sentiment spikes and alert the team | Bounded auto | Detection is information, not action. | Read-only; alert the humans — never auto-act on the finding. |
| 49 | Close inactive tickets after 14 days (no message sent) | Bounded auto | Internal state change; reopen restores everything. | Reopen path preserved; every closure logged. |
| 50 | Draft a status-page update during an incident | Draft-only | Wording under pressure needs a human eye. | Publishing the update is a separate hard-gated action. |
| 51 | Publish the status-page update | Hard-gated | Public incident communication. | Recorded approval of the exact wording. |

---

## Finance

| # | Use case | Tier | Rationale | Key control |
|---|----------|------|-----------|-------------|
| 52 | Categorize transactions for bookkeeping | Bounded auto | Internal classification; touches no money. | Read-only bank feed — never issue a transfer grant to this agent. |
| 53 | Reconcile accounts against statements | Bounded auto | Read-and-compare; changes nothing. | Discrepancies get flagged to a human — never auto-adjusted. |
| 54 | Draft invoices from time entries | Draft-only | An invoice is a plan until it's sent. | Sending the invoice is a separate hard-gated action. |
| 55 | Send invoices to clients | Hard-gated | External demand for payment. | Recorded approval of the amounts on each invoice. |
| 56 | Send payment reminders | Hard-gated | External outreach about money owed. | Approval per reminder batch; review the tone. |
| 57 | Initiate vendor payments | Hard-gated | Moves money out, full stop. | Recorded approval with the invoice matched to the payment. |
| 58 | Run payroll | Hard-gated | Moves money with tax and legal consequences. | Multi-person approval; reconcile every amount first. |
| 59 | File tax documents | Hard-gated | Regulatory filing; errors compound. | Human (CPA) review and signature; never auto-filed. |
| 60 | Generate the monthly P&L | Bounded auto | Internal reporting from your own books. | Source data read-only; no external distribution grant. |
| 61 | Forecast cash flow from pipeline data | Bounded auto | Internal analysis; a model, not a decision. | Document the assumptions; external sharing needs review. |
| 62 | Flag anomalous transactions for review | Bounded auto | Detection only. | Alert the human — blocking or reversing is a separate hard-gated action. |
| 63 | Reverse a transaction | Hard-gated | Moves money back; audit-sensitive. | Recorded approval with a reason code on every reversal. |
| 64 | Export financial reports for the accountant | Bounded auto | Routine transfer to a contracted counterparty. | Standing recipient allowlist (approved once, as a hard-gated decision), encrypted channel, per-export audit row. |
| 65 | Monitor budget vs. actuals and alert on variance | Bounded auto | Alerting is information. | Read-only; alerts at 50%/80% inform — the block is the control. |
| 66 | Draft the board financial summary | Draft-only | Numbers for directors need human judgment. | Distribution of the summary is hard-gated. |

---

## Engineering

| # | Use case | Tier | Rationale | Key control |
|---|----------|------|-----------|-------------|
| 67 | Generate code from a spec | Bounded auto | An internal artifact; reviewed before it lands. | No direct push to main — human review is the gate before merge. |
| 68 | Push code directly to main | Hard-gated | Production state change with no review trail. | Recorded approval plus passing checks — or require a pull request instead. |
| 69 | Open a pull request with generated changes | Bounded auto | Proposes; merges nothing. | Merging is a separate hard-gated action. |
| 70 | Merge a pull request | Hard-gated | The moment code becomes the product. | Recorded approval with CI green. |
| 71 | Run the test suite | Bounded auto | No side effects by design. | Test-environment-only grant. |
| 72 | Deploy to staging | Bounded auto | Non-production; mistakes are cheap. | Staging-only scope; log every deploy. |
| 73 | Deploy to production | Hard-gated | Customer-facing state change. | Recorded approval inside the change window. |
| 74 | Roll back a production deploy | Hard-gated | Still a production state change, even in the safe direction. | Recorded approval — or a pre-approved rollback runbook running bounded-auto with owner alerts. |
| 75 | Triage CI failures and suggest fixes | Bounded auto | Analysis only; changes nothing. | No grant to auto-commit the suggested fixes. |
| 76 | Scan dependencies for vulnerabilities | Bounded auto | Read-only analysis. | Log the findings; auto-upgrading is a separate decision. |
| 77 | Auto-merge dependency updates | Hard-gated | Any merge to a deployable branch is a production change. | Recorded approval per merge — or a standing auto-merge policy (approved as a hard-gated decision) limited to semver-patch, CI-green, with auto-revert on failure. |
| 78 | Dump the production database for debugging | Hard-gated | Bulk sensitive data — a read with write-grade consequences. | Approval plus data-class handling and time-bounded access. |
| 79 | Query the production read-replica for analytics | Bounded auto | Read-only by construction. | Replica-only grant; mask PII columns. |
| 80 | Read application logs for incident triage | Bounded auto | Read-only. | Log scope in the grant; confirm secrets are redacted from logs. |
| 81 | Rotate database credentials | Hard-gated | Credential material. | Approved rotation window; new credential to the vault, never the logs. |
| 82 | Provision cloud infrastructure from IaC | Hard-gated | Commits spend and creates real state. | Recorded approval of the reviewed plan output before apply. |
| 83 | Tear down idle dev environments | Bounded auto | Low consequence; work is reproducible. | Define the idle threshold; notify the owner before teardown. |
| 84 | Generate API documentation from code | Bounded auto | Internal artifact. | Docs scope; scan the output for leaked secrets before publishing. |

---

## Research

| # | Use case | Tier | Rationale | Key control |
|---|----------|------|-----------|-------------|
| 85 | Summarize a batch of papers or articles | Bounded auto | Internal transform of text you can already read. | Source allowlist; data-class the output internal. |
| 86 | Monitor competitor pricing pages and summarize changes | Bounded auto | Read-only web access. | Egress allowlist; respect robots.txt and terms of service; log the runs. |
| 87 | Scrape a site whose terms prohibit bots | Hard-gated | Terms-of-service and legal exposure. | Legal review first; proceed only with documented permission. |
| 88 | Build a dataset from public web data | Bounded auto | Collection, not publication. | License check per source; record provenance for every row. |
| 89 | Draft a research report | Draft-only | A draft makes no claims in public. | External publication is a separate hard-gated action. |
| 90 | Publish research externally | Hard-gated | Public claims under your name. | Recorded approval plus a fact-check pass. |
| 91 | Transcribe interviews | Bounded auto | Mechanical transform of your own recordings. | Record consent before processing; data-class the transcripts. |
| 92 | Analyze survey responses for themes | Bounded auto | Internal analysis. | Anonymize before analysis where the data allows it. |
| 93 | Generate synthetic test data | Bounded auto | Fake data for safe testing. | Label it "synthetic demo" everywhere; never let it mix with real data unlabeled. |
| 94 | Run a literature review with cited sources | Bounded auto | Research with receipts. | Every claim traceable to a cited source — no invented citations, ever. |
| 95 | Draft survey questions | Draft-only | Questions are harmless until sent. | Sending the survey is a separate hard-gated action. |
| 96 | Send a survey to participants | Hard-gated | External outreach to real people. | Approval of the questions and the recipient list; handle consent properly. |
| 97 | Monitor news and mentions, then alert | Bounded auto | Read-only monitoring. | Alert the humans — never auto-respond to what it finds. |
| 98 | Draft responses to press inquiries | Draft-only | High-stakes wording needs a human. | Sending is hard-gated; add legal review for sensitive topics. |
| 99 | Summarize user feedback from app stores | Bounded auto | Public data, internal use. | No grant to auto-reply to reviewers. |
| 100 | Reply to public reviews | Hard-gated | Public speech under your brand. | Recorded approval — or an approved response playbook with spot-checks. |

---

## Tier your next 10 — blank worksheet

Your stack has use cases this catalog doesn't. Run each through this table. A row is done when all five columns are filled and the owner has signed off.

| Use case | Consequence if wrong | Tier | Key control | Owner |
|---|---|---|---|---|
| 1. | | | | |
| 2. | | | | |
| 3. | | | | |
| 4. | | | | |
| 5. | | | | |
| 6. | | | | |
| 7. | | | | |
| 8. | | | | |
| 9. | | | | |
| 10. | | | | |

**Decision checklist** — answer honestly before you tier:

- [ ] Can I name the consequence if this action is wrong? If not, it starts Hard-gated.
- [ ] Does it move money, accept terms, contact anyone outside the team, touch credentials, change permissions, or carry legal weight? If yes to any: Hard-gated.
- [ ] Does it only read, classify, summarize, or alert inside bounds I can state? If yes: Bounded auto — and state the bounds (cost ceiling, expiry, scope).
- [ ] Does it only prepare something a human will review before anything happens? If yes: Draft-only — and confirm the "send" step is separately gated.
- [ ] Am I calling it "read-only" while it exports, dumps, or copies sensitive data? Reads with write-grade consequences tier up.
- [ ] If two owners disagree on the tier, the higher tier wins.

---

## Adopt it this week

Pick the ten use cases your team runs most often. Tier them — using this catalog where they appear, the worksheet where they don't. Install the key control for each. Put cost ceilings and expiries on every bounded-auto plan, separate every draft-only "compose" from its hard-gated "send," and make sure no hard-gated action has an auto-grant path hiding anywhere.

That is the whole adoption motion: ten rows, ten controls, ten owners. Everything else in your agent operations is the same exercise at larger scale.

*100 Agent Use Cases, Pre-Tiered. An original GhostCorp work. No statistics, testimonials, or customer stories appear in this library — every tier follows from the consequence of the action being wrong.*
