# Kestrelattice — Governed Agent Mesh

**By GhostCorp.** A governed mesh of specialized AI agents that finds ventures, wins customers, and executes approved work — with identity, spend limits, approval gates, and hash-linked audit trails on every action.

This repository is the open-source home of the project:

- **The product site** (`index.html`) — live on GitHub Pages, free hosting
- **[The Governed Agent Mesh Playbook](playbook.md)** — our original downloadable guide: run multi-agent AI operations with identity, spend limits, approval gates, and audit trails
- **[Buyer-demand evidence ledger](evidence/buyer-demand-ledger.md)** — 25 verified public sources behind every demand claim
- **[Pricing & $0-stack economics](evidence/pricing-and-economics.md)** — willingness-to-pay benchmarks, conversion rates, and free-tier channel limits
- **[Full research reports](docs/)** — the complete demand and pricing research

## Why

AI swarms are useful until nobody can tell what they did, spent, or were allowed to do. Developers document runaway agents burning $700+ in 72 hours, frameworks with no audit trails or spend limits, and production deployments blocked by missing governance — while analysts project $206.5B of AI-agent software spend in 2026. Every number is cited in the [evidence ledger](evidence/buyer-demand-ledger.md).

## The 8-layer governance stack

1. Identity — every action attributable, no anonymous actors
2. Grants — explicit, least-privilege, time-bounded
3. Approval gates — risk-tiered human decisions
4. Spend limits — bounded workloads, hard ceilings, expiry
5. Fail-closed runtime — missing evidence blocks, never warns
6. Audit trails — hash-linked rows for every outcome
7. Telemetry — bounded, attributable, labeled
8. Owner control — secrets never stored, terms never auto-accepted

Read the playbook: [playbook.md](playbook.md)

## Run it locally

It's a plain static site. Clone and open `index.html` in a browser, or:

```bash
npx serve .
# or
python3 -m http.server 8000
```

## Deploy

It's already deployed on GitHub Pages (free). To redeploy yourself: fork the repo, enable **Settings → Pages → Deploy from branch → main / (root)**.

## The $0 stack

Hosting on GitHub Pages · analytics on GA4 · links on Short.io/Dub.co · outreach within Gmail/LinkedIn/Reddit free quotas. The plan and its limits: [evidence/pricing-and-economics.md](evidence/pricing-and-economics.md).

## License

MIT — see [LICENSE](LICENSE). Use the playbook, cite the evidence, govern your agents.
