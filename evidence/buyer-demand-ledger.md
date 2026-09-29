# Buyer-Demand Evidence Ledger

**Product category:** Governed Agent Mesh Platform (multi-agent orchestration, human approval gates, identity & authorization controls, spend limits, audit trails)
**Buyer segments:** Venture studios, AI-native founders, accelerators, enterprise innovation teams
**Compiled:** September 29, 2026 · 25 verified public sources (2 items explicitly marked not-verified and excluded from claims)

> Full research narrative: [docs/research_buyer_demand.md](../docs/research_buyer_demand.md)

## 1. Capital allocation & valuation (demand proxy)

| Signal | Evidence | Source |
|--------|----------|--------|
| LangChain / LangSmith | $125M Series B at $1.25B valuation (after $25M Sequoia Series A), driven by enterprise LangSmith adoption | [JobRight profile](https://jobright.ai/jobs/info/68d20a38a54edb3bf3e18eb9), Oct 2025 |
| Arize AI | $70M Series C (total $131M+), AI observability & agent monitoring | [AI Pulse vendor profile](https://aipulse.nayaone.com/landscape/ai-risk-governance?subcat=grc-extension), Feb 2025 |
| AgentOps | $2.6M pre-seed (645 Ventures, Afore Capital) for agent session replay & cost tracking | [PR Newswire](https://www.prnewswire.com/news-releases/agency-ai-raises-2-6m-in-pre-seed-funding-to-revolutionize-ai-agent-development-302233294.html), Aug 2024 |
| Langfuse | $4M seed (Lightspeed, La Famiglia; YC W23) for open-source LLM observability | [Panshi profile](https://panshi.io/tools/compare/langfuse-vs-mlflow-tracing-genai.html), 2024 |
| Respan | $5M (Gradient, YC) for proactive agent observability | [Dealroom](https://app.dealroom.co/news/feed/respan-raises-5m-to-bring-proactive-observability-to-ai-agents), 2025 |
| CrewAI | $15M+ early-stage funding; launched CrewAI Enterprise for multi-agent VPC management | [Harmonic Hot 25](https://harmonic.ai/hot-25-startups/q1-2025), Dec 2024 |

## 2. Public pricing: proven willingness to pay

| Tool | Price points | Source |
|------|--------------|--------|
| LangSmith | Developer $0; Plus **$39/seat/mo**; Enterprise custom | [langchain.com/pricing](https://www.langchain.com/pricing) |
| CrewAI AMP | Free ~50 executions/mo; Pro **$25–$99/mo**; Enterprise custom | [crewai.com/pricing](https://www.crewai.com/pricing) |
| AgentOps | Free 5–10k traces; Starter **$49/mo**; Pro **$199/mo**; Enterprise from **$2,000/mo** | [agentops.ai](https://www.agentops.ai) |
| LangWatch | Free 200k events/mo; Growth **€29/seat/mo** + usage | [langwatch.ai/pricing](https://www.langwatch.ai/pricing) |
| Langfuse | Free 50k units; Core $29/mo; Pro $199/mo; Enterprise **$2,499/mo** | [budgetforge.dev](https://www.budgetforge.dev/tools/langfuse-pricing-2026) |
| Arize Phoenix | OSS $0; Cloud Starter **$199/mo**; Enterprise custom | [arize.com/pricing](https://www.arize.com/pricing) |
| Helicone | Hobby 10k req/mo; Pro $29–$79/mo; Team **$799/mo** | [helicone.ai/pricing](https://www.helicone.ai/pricing) |
| Braintrust | Starter $0; Pro **$249/mo** platform fee | [braintrust.dev/pricing](https://www.braintrust.dev/pricing) |

## 3. Analyst forecasts

| Signal | Evidence | Source |
|--------|----------|--------|
| Enterprise adoption | **40%** of enterprise apps embed task-specific AI agents by end-2026 (<5% in 2025) | [Gartner forecast coverage](https://www.linkedin.com/pulse/40-2026-gartners-ai-agent-forecast-what-means-bhr9c) |
| Agent software spend | **$86.4B (2025) → $206.5B (2026)** | [Gartner estimate](https://medium.com/@olikhatib/the-next-era-of-saas-the-enterprise-execution-fabric-97d3c8b7f123) |
| Direct enterprise agent spend | **$14B (2025) → $38B (2026)** | [IDC forecast](https://clawbot.ai/wiki/market/idc-ai-agent-expenditure-forecast.html) |
| Adoption now | **62%** of enterprises experimenting with agents; **23%** scaling in production | [BudEcosystem whitepaper](https://www.budecosystem.com/transforming-to-an-ai-native-enterprise.html) |

## 4. Venture studios as a funded buyer segment

| Signal | Evidence | Source |
|--------|----------|--------|
| Market size | 1,000+ active studios globally, doubled since 2018; fund targets $6.4M–$10M | [LinkedIn studio surge](https://www.linkedin.com/posts/jordandivecha_the-same-model-is-suddenly-winning-across-activity-7416977073480601600-o2sl) |
| Tooling budgets | Median studio budget $1.36M–$2.49M/yr; 40–60% of year-1 engineering burn into shared platform stacks | [Inniches research](https://inniches.com/startup-studios-research) |
| Multi-agent procurement | Studios procuring multi-agent execution stacks (e.g. €18,000/mo) | [AI of the Coast](https://aiofthecoast.dcxps.com/p/how-our-venture-studio-model-and) |

## 5. Practitioner pain (unmet need, in their words)

| Pain | Evidence | Source |
|------|----------|--------|
| Runaway agent costs | Infinite-loop agent burned **$700+ in 72 hours**; no budget controls or watchdog | [r/IndieDev](https://www.reddit.com/r/IndieDev/comments/1qv922m/trusting_my_ai_agent_cost_me_over_usd_700/) |
| Missing audit trails | "Why do agent frameworks let agents rack up costs without audit trails or spend limits?" | [r/AI_Agents](https://www.reddit.com/r/AI_Agents/comments/1rm6hj0/i_kept_asking_why_agent_frameworks_let_agents/) |
| Fear of ungoverned production | Orchestration manageable; governance/kill switches are what block production | [r/AgentsOfAI](https://www.reddit.com/r/AgentsOfAI/comments/1wdg3tu/practical_strategies_for_governing_multi_agent_ai/) |
| Identity & permissions crisis | "Who gave your AI agent authority?" — need PreToolUse/PostToolUse approval gates | [r/AI_Agents](https://www.reddit.com/r/AI_Agents/comments/1ujjd9t/who_gave_your_ai_agent_authority/); [HN 47064122](https://news.ycombinator.com/item?id=47064122) |
| Need for a safety mesh | Prompt engineering inadequate; systems need centralized safety mesh control plane | [HN 46683661](https://news.ycombinator.com/item?id=46683661) |
| Debugging swarms | Tracing/debugging multi-agent swarms "a nightmare" without dedicated tooling | [r/aiagents](https://www.reddit.com/r/aiagents/comments/1vzfwkc/debugging_multiagent_swarms_is_a_nightmare_i/) |

## Excluded as not verified

- Arahi funding/pricing details — no confirmable public press release.
- OpenAI Swarm enterprise pricing — Swarm is an open-source educational release with no commercial pricing.
