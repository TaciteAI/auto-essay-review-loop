# {Company Name} — Business Plan

> Replace `{Company Name}` and every `[bracketed placeholder]` below. Section
> headers (the `## ...` lines) are required — the auto-business-plan-review-loop
> skill checks for them by regex. Do not rename or remove headers.

## Executive Summary

[2–4 short paragraphs. Open with the one-line thesis: "We are {what} for {who} so they can {outcome}." Then the why-now in two sentences. Then the wedge: what specifically is different about your approach. End with the ask: round size, milestone, runway.]

[Bad version: "We are an AI-powered platform for enterprise observability." Good version: "We are an exception-tracking tool for backend engineers at series-B SaaS companies, who currently spend 6 hours a sprint chasing flaky errors across three monorepos. Why now: trace context is finally standardized via OpenTelemetry. Our wedge is a deterministic root-cause graph that competitors can't build on top of sampled traces."]

## Problem

[State the problem in the words your buyer uses, not the words an investor uses. Quote a real customer if you have one. Explain the size and frequency of the pain — how often does the buyer hit it, what does it cost them in time or dollars today, what do they currently do about it.]

[Avoid: "engineering teams struggle with observability." Prefer: "When a payment fails in production, the on-call engineer takes 47 minutes on average to identify the root cause across our three current target customers' infrastructure. They have 8–12 such incidents per week. Each incident costs ~$200 in engineering time and 0.4% of recovery-window revenue."]

## Solution

[Describe what you built or are building. Be specific. If AI/ML is involved, name the model class, the training/grounding data, the evaluation methodology, and the failure mode. If you are claiming horizontal scale, describe the bottleneck. Aim for: a senior engineer reading this should be able to estimate engineer-months to ship.]

[Include a 1–3 paragraph "how it works" block. Include a "what we don't do (yet)" block — investors and engineers both respect founders who name their constraints.]

## Market

> Required subsections: TAM, SAM, SOM. Required values format: `$XXB` /
> `$XX million` / etc. The `market_size_check.py` tool parses these values
> and flags fantasy TAMs, broken nesting, and unrealistic capture rates.

### TAM (Total Addressable Market)

[State TAM as a dollar amount with a clear derivation. Bottom-up is much stronger than top-down. Bottom-up: `# of accountable buyers × realistic ACV per buyer × annual frequency`. Cite the source for the buyer count.]

TAM: **$[XX]B**

Derivation: [show the math]

### SAM (Serviceable Addressable Market)

[The portion of TAM you can actually reach with your distribution model in the next 3–5 years. SAM is typically 5–20% of TAM for a focused startup.]

SAM: **$[X]B**

Derivation: [show the math — geography, segment, product fit]

### SOM (Serviceable Obtainable Market)

[The realistic 3-year capture. Typical realistic capture is 1–5% of SAM. Anything over 10% will be flagged by the verification tool. State your year-3 ARR target here and show how it lands inside SOM.]

SOM (Year 3): **$[XX]M ARR**

Derivation: [show the math — # of customers × ACV × win rate against pipeline]

## Business Model

[Describe pricing in concrete numbers. Replace "Contact us" with at least a published anchor. Walk through the unit economics:]

- **Pricing:** $[X]/seat/month or $[Y] flat or $[Z] per-event. Anchored against the [budget line item] buyers currently spend on [alternative].
- **CAC:** $[N], blended (paid + organic). Channel breakdown: [paid: $A, organic: $B, outbound: $C].
- **LTV:** $[N], computed as `(ARPU × gross_margin) / monthly_churn`. State your gross margin assumption explicitly.
- **LTV/CAC ratio:** [N]x. Target ≥3x for software.
- **CAC payback:** [N] months. Target ≤12 (SMB) / ≤18 (mid-market) / ≤24 (enterprise).
- **Gross margin:** [N]%. Target ≥70% for SaaS; if lower, explain the cost structure (heavy infra, services component).
- **Monthly churn:** [N]%. Logo and revenue. State separately.
- **Net revenue retention (NRR):** [N]%. Target ≥110%.

[If you do not yet have these numbers, state the hypothesis explicitly with the assumption set, e.g., "Hypothesis: CAC of $X, payback in Y months, derived from comparable companies at our stage. We will validate by month 6 of the seed runway." Do NOT fabricate numbers — investors will check.]

## Traction

[Concrete progress to date. Numbers, not adjectives. "100,000 signups" with no retention curve is vanity; "12 paying customers, $400K ARR run rate, 4-month average tenure, 1 lost in the last 6 months, NRR 118%" is real.]

- **Customers:** [N paying, M pilot, K waitlist]
- **ARR / revenue run rate:** [$N]
- **Cohort retention:** [show the curve, with axis values]
- **Logos:** [named where permission allows]
- **LOIs / pipeline:** [N opportunities, $[X]M weighted pipeline]

## Team

[Three to six paragraphs, one per founder/key hire. Each paragraph: name, prior role, why this person is the right person for this specific company. Founder-market fit is the question.]

[Avoid generic credentials. Prefer: "Sarah was the third PM at Stripe, owned Atlas, lived inside the company-formation pain for four years before starting this." over: "Sarah is a product leader from Stripe."]

[Include hiring plan: who's hire #1 post-funding, with a one-line rationale.]

## Financials

> Required: a 12-month month-by-month line-item projection AND a 3-year
> summary. The verification layer parses the headers/labels by regex.

### 12-Month Projection (Month 1 through Month 12)

| Line item | M1 | M2 | M3 | M4 | M5 | M6 | M7 | M8 | M9 | M10 | M11 | M12 |
|-----------|----|----|----|----|----|----|----|----|----|-----|-----|-----|
| Revenue | | | | | | | | | | | | |
| COGS | | | | | | | | | | | | |
| Gross profit | | | | | | | | | | | | |
| Sales & marketing | | | | | | | | | | | | |
| R&D | | | | | | | | | | | | |
| G&A | | | | | | | | | | | | |
| Operating loss | | | | | | | | | | | | |
| Cash | | | | | | | | | | | | |

### 3-Year Summary

| | Year 1 | Year 2 | Year 3 |
|--|--------|--------|--------|
| Revenue | | | |
| Gross margin % | | | |
| Operating margin % | | | |
| Cash burn | | | |
| Headcount EOY | | | |
| ARR EOY | | | |

### Funding Ask

[Round size, valuation if pre-marketed, milestones the round funds, runway implied.]

---

> Once you fill this in, run: `/auto-business-plan-review-loop ./BUSINESS_PLAN.md`
