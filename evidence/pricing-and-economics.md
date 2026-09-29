# Pricing, Willingness-to-Pay & $0-Stack Unit Economics

**Compiled:** September 29, 2026 · All figures from verified public sources.
> Full research: [docs/research_pricing_econ.md](../docs/research_pricing_econ.md)

## 1. Comparable pricing benchmarks (verified Sept 2026)

| Tool | Model | Tiers |
|------|-------|-------|
| LangSmith | Seat + usage | Free (5k traces) · **$39/seat/mo** Plus · Enterprise custom |
| CrewAI AMP | Open source + executions | Free (50/mo) · **$25–$99/mo** · $225/mo at 500 executions |
| AgentOps | Tiered SaaS | Free (5–10k traces) · **$49/mo** · **$199/mo** · Enterprise custom |
| LangWatch | Usage events | Free (200k events) · **$29/mo + $6/100k** · Enterprise custom |
| Arize Phoenix | OSS + managed | OSS free · **$199/mo** Cloud Starter · Enterprise custom |
| Helicone | Proxy logging | Free (10k req) · **$29–$79/mo** · $799/mo Team |
| Braintrust | Platform fee | Free Starter · **$249/mo** Pro |
| OpenRouter | Credit metering | Free models tier · PAYG, $0 minimum |

## 2. Willingness-to-pay for small teams

- Per-developer WTP for core AI/dev tooling: **$20–$50/developer/mo** (Copilot $20, ChatGPT Team $25–$30, Claude Code $20–$50).
- Aggregate AI stack spend runs **$50–$200/developer/mo**.
- A 5-person studio's total tooling budget: **$250–$1,000/mo** across all software.
- Single-tool ceiling for <10 FTE teams: strong resistance above **$100–$200/mo** unless the tool directly offsets compute or headcount.
- Sources: OpenView Product Benchmarks, Boldstart DevTool Report (2023–2026).

## 3. Conversion benchmarks (plan from the bottom of each range)

| Metric | Benchmark |
|--------|-----------|
| Cold email reply rate (general B2B) | 3.43%–5.10% |
| Cold email reply rate (technical audiences) | 1.00%–3.50% |
| Cold email → demo booking | 0.50%–1.50% of contacts |
| LinkedIn connection acceptance | 20%–30% |
| LinkedIn DM response | 10%–15% |
| Landing page visitor → signup (median) | 2.35%–3.50% |
| Top-quartile SaaS/dev-tool pages | 6.60%–11.45% |
| Dev-tool visitor → free signup (median) | 10% |
| Free → paid within 6 months (median) | 5% |
| Hybrid seat+usage pricing among high-growth SaaS | 61%–86% |

## 4. The $0 distribution stack and its hard limits

| Channel | Free limits | Notes |
|---------|-------------|-------|
| Gmail (personal) | 500 emails/24 hrs | Keep 1:1 personal, not blasts |
| Google Workspace | 2,000 emails/24 hrs | 1,500/day for mail merges |
| Google Analytics 4 | Unlimited standard events; 1M events/day BigQuery export | Covers all analytics needs at this scale |
| Dub.co | 25 links/mo, 1,000 clicks | Custom domain support, API |
| Short.io | 1,000 branded links/mo, 5 domains, 50k clicks | Best free link volume |
| Bitly | 5 links/mo | Too restricted; avoid |
| LinkedIn | ~100 connection requests/week | Free accounts get 0 cold InMails |
| Reddit | 1 post/10 min; 9:1 non-promo ratio; 50–100 karma gates | Build karma before posting |
| Discord | 50 req/sec bot limit; 2,000 chars/message | Community channel |

## 5. What this means for Kestrelattice's offer

1. **Under-$100/mo is the honest early ceiling** for small-team adoption; the comparables that scale ($199–$2,499/mo) sell to funded studios and enterprises, which matches our venture-studio segment (1,000+ studios, $1.36M–$2.49M median budgets, 40–60% into shared tooling).
2. **Lead with the downloadable playbook at $0** (10% median visitor→signup for dev tools; 5% free→paid within 6 months gives a realistic upgrade path once a paid tier exists).
3. **Free channels are sufficient for the first 1,000 signups**: GA4 for analytics, Short.io for links, Gmail 1:1s and LinkedIn within quotas, Reddit after building 9:1 karma.
4. **Set funnel expectations from the bottom of the benchmark ranges** and let recorded evidence revise them upward — the same fail-closed, claim-evidenced discipline as the product itself.
