# Sieve — Business Plan

## Executive Summary

Sieve is an exception-tracking tool for backend engineers at Series B–D SaaS companies. Our customers spend 6+ hours a sprint chasing flaky production errors across multiple monorepos; we cut that to under 30 minutes by stitching deterministic root-cause graphs from OpenTelemetry traces.

**Why now:** OpenTelemetry context propagation finally became standard across major language runtimes in 2024. Pre-OTel, root-cause graphs were impossible without instrumenting every service by hand. Post-OTel, we can compute them deterministically.

**Wedge:** competitors (Datadog, Sentry, Honeycomb) sample traces, which means root-cause graphs are probabilistic and noisy. We index 100% of trace context using a bloom-filter approach that costs $0.0004 per million spans — 30x cheaper than full-trace storage. This wedge requires a custom indexing pipeline that took us 18 months to build; an incumbent would need to rewrite their core to match.

**Ask:** $8M Series A to grow from $1.2M to $5M ARR over 18 months.

## Problem

The on-call engineer at a B2B SaaS company hits a production exception roughly every 6 hours. The current workflow:

1. Pager goes off, error drops in Slack
2. Engineer copies the trace ID into Datadog
3. Datadog shows a sampled trace; root span is missing because the trace wasn't sampled at the entry point
4. Engineer manually queries logs across 4–8 services to reconstruct what happened
5. Average resolution time per incident: **47 minutes**, of which 41 minutes is reconstruction, not fixing

We measured this in three customer environments (Replit, Vercel-stage company, Linear-stage company). 8–12 incidents per week per backend team. At a $200/hr loaded engineering rate, that's $36K–$54K per team per quarter in pure reconstruction time. Most teams just absorb the cost as "the price of running production."

## Solution

Sieve ingests OpenTelemetry trace context (no app changes; we sit behind the existing OTel collector). For every incoming span, we index its parent/child relationship into a bloom-filter-backed graph in ClickHouse. Cost: $0.0004 per million spans, vs. ~$0.012 per million for full-trace storage in Honeycomb.

When an exception fires, we serve a deterministic root-cause graph in <300ms: the full ancestry of the failing span, including upstream services, the request payload (with PII scrubbing), and a diff against the most recent successful trace with the same shape.

**AI/ML claims, specified:**

- We use a fine-tuned `code-llama-3-7b` (open-weights, hosted on our own GPUs) to generate a one-paragraph plain-English summary of each root-cause graph.
- Training data: 14,000 anonymized incident postmortems contributed by our 3 design partners.
- Evaluation: blind A/B against engineer-written postmortems; current accuracy is 78% on an internal eval set of 500 incidents.
- Failure mode: when model confidence (top-1 logit ratio) is below 0.6, we suppress the summary and surface only the deterministic graph. The graph is correct by construction; the summary is the optional layer.

Inference cost: $0.003 per incident at our current scale, well below the ~$2/incident value to the customer.

We are NOT building: a metrics platform, a logs platform, a synthetic monitoring tool, or a full observability suite. Customers keep Datadog/Honeycomb for those.

## Market

### TAM (Total Addressable Market)

**TAM: $50B**

Derivation: 380,000 backend engineering teams globally (per Stack Overflow developer survey 2024 + StackShare data) × $130K average annual observability spend per team (Gartner 2024) = $49.4B. We round to $50B. Sources cited; we did not multiply revenue against a top-down "global IT budget."

### SAM (Serviceable Addressable Market)

**SAM: $5B**

Derivation: We focus on Series B–D SaaS companies with 20–500 backend engineers, English-speaking, US/EU/CA. That's ~38,000 companies × $130K avg observability spend = $4.94B. We round to $5B (10% of TAM, consistent with focused startup posture).

### SOM (Serviceable Obtainable Market)

**SOM (Year 3): $50M ARR**

Derivation: 200 customers × $250K ACV. 200 customers represents 0.5% of our 38,000-company SAM, equivalent to ~1% of SAM dollar value. Within the 1–5% realistic capture band per the verification heuristic. Pipeline math: with 8 AEs at $750K quota loaded, $6M new ARR/year per AE cohort, achievable by Year 3.

## Business Model

**Pricing:**
- Starter: $499/month flat, up to 50M spans/month
- Growth: $1,500/month + $0.20 per million spans above 200M, includes Slack/PagerDuty integrations
- Scale: $5,000/month + custom data retention, dedicated support, SOC 2 Type II report

ACV is the budget line item enterprise buyers currently spend on a "supplemental observability" SKU within their Datadog/Honeycomb contracts ($150K–$400K range). We price below that anchor.

**Unit economics (current, blended across 14 paying customers):**

- **CAC:** $1,200 blended. Channels: paid ads $1,800 (4 customers), organic/content $400 (8 customers), outbound $4,500 (2 customers).
- **LTV:** $4,500. Computed as `(ARPU × gross_margin) / monthly_churn` = `($156/mo × 0.78) / 0.027 = $4,506`.
- **LTV/CAC:** **3.75x**.
- **CAC payback:** 11 months.
- **Gross margin:** **78%** (cost: $0.0004/M spans on ClickHouse + $0.003/incident inference + 15% support load).
- **Monthly logo churn:** 2.7%. Revenue churn: 1.9% (a few customers downgraded but kept).
- **NRR:** 116% (3 customers expanded to higher tier in Q1).
- **Burn multiple:** 1.4 (acceptable at our stage).
- **Magic number:** 0.9 (early — we're under-hiring on sales).

## Traction

- **14 paying customers**, $1.2M ARR run rate as of April 2026
- **Pipeline:** $4.8M weighted, 31 opportunities in late stage
- **Cohort retention:** Q3-2025 cohort (5 customers) retains 100% logos at month 6, with 2 expansions; Q4-2025 cohort retains 4/5 at month 4
- **Named customers (with permission):** Replit, Cursor, Linear (Linear is a design partner — paying $1/year, but the case study is real)
- **GitHub stars on our open-source SDK:** 4,200

## Team

- **Priya Vasudevan, CEO** — formerly Eng Manager #2 at Honeycomb (2018–2023), built the trace-pipelining team there, owned the OpenTelemetry SDK contributions. Has personally written the on-call rotation she's now selling out of.
- **Marcus Chen, CTO** — formerly L7 staff engineer at Stripe payments infra (2019–2024), led the rewrite of Stripe's internal trace-context propagation. Knows ClickHouse at the byte level.
- **Engineer #3, hired Q1 2026** — Sasha Patel, ex-Datadog APM team, brings competitive intel + bloom-filter expertise.
- **Hire #4 (planned, $8M round funds):** GTM lead with Series A → Series B SaaS playbook (founding sales hire profile).

## Financials

### 12-Month Projection

| Line item ($K) | Month 1 | Month 2 | Month 3 | Month 4 | Month 5 | Month 6 | Month 7 | Month 8 | Month 9 | Month 10 | Month 11 | Month 12 |
|----------------|---------|---------|---------|---------|---------|---------|---------|---------|---------|----------|----------|----------|
| Revenue (MRR) | 100 | 115 | 132 | 152 | 175 | 201 | 231 | 266 | 305 | 351 | 404 | 464 |
| COGS | 22 | 25 | 29 | 33 | 39 | 44 | 51 | 59 | 67 | 77 | 89 | 102 |
| Gross profit | 78 | 90 | 103 | 119 | 137 | 157 | 180 | 207 | 238 | 274 | 315 | 362 |
| Sales & marketing | 220 | 240 | 260 | 280 | 300 | 320 | 340 | 360 | 380 | 400 | 420 | 440 |
| R&D | 380 | 380 | 400 | 400 | 420 | 420 | 440 | 440 | 460 | 460 | 480 | 480 |
| G&A | 80 | 80 | 90 | 90 | 100 | 100 | 110 | 110 | 120 | 120 | 130 | 130 |
| Operating loss | (602) | (610) | (647) | (651) | (683) | (683) | (710) | (703) | (722) | (706) | (715) | (688) |
| Cash | 7,398 | 6,788 | 6,141 | 5,490 | 4,807 | 4,124 | 3,414 | 2,711 | 1,989 | 1,283 | 568 | (120) |

### 3-Year Summary

| | Year 1 | Year 2 | Year 3 |
|--|--------|--------|--------|
| Revenue (ARR EOY) | $5.6M | $18M | $50M |
| Gross margin % | 78% | 80% | 81% |
| Operating margin % | -120% | -45% | -8% |
| Cash burn | $8.1M | $7.5M | $4.0M |
| Headcount EOY | 16 | 32 | 58 |

### Funding Ask

$8M Series A. Milestones funded: 14 → 80 paying customers, $1.2M → $5M ARR, hire founding sales lead + 4 AEs + 6 engineers. ~14 months of runway at planned burn; reach default-alive at $5M ARR (Series B raise window opens).
