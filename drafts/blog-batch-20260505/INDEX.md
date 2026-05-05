# 20-Blog Batch — 2026-05-05

40 drafts (20 topics × English + Chinese), 500–800 words each. Sources:
- `drafts/cyberpunk-ai-essay.md` (high-tech / low-life thesis)
- Citrini Research, "The 2028 Global Intelligence Crisis" (https://www.citriniresearch.com/p/2028gic)

All 40 drafts pass blog hard verification (word count, H-tag structure, ≥2 inline links, no emojis/hashtags/code-fences). All 40 terminate single-round persona review (≥3 of 4 personas ≥6, no CRITICAL weaknesses).

For platform-specific posting recipes (LinkedIn / X / Facebook / WeChat / Redbook / Sina blog), see `PLATFORM_FIT.md`.

## Score table (M = mobile-first-reader, S = seo-skeptic, H = h2-skimmer, I = target-icp)

| # | Topic | EN avg | CN avg | EN file | CN file |
|---|-------|--------|--------|---------|---------|
| 01 | compute-moat | 7.8 | 7.5 | `en/01-compute-moat.en.md` | `cn/01-compute-moat.cn.md` |
| 02 | on-ramp-collapse | 7.2 | 7.0 | `en/02-on-ramp-collapse.en.md` | `cn/02-on-ramp-collapse.cn.md` |
| 03 | so-so-automation | 7.2 | 7.0 | `en/03-so-so-automation.en.md` | `cn/03-so-so-automation.cn.md` |
| 04 | algorithmic-management | **8.0** | 7.8 | `en/04-algorithmic-management.en.md` | `cn/04-algorithmic-management.cn.md` |
| 05 | surveillance-pricing | 7.8 | 7.0 | `en/05-surveillance-pricing.en.md` | `cn/05-surveillance-pricing.cn.md` |
| 06 | antitrust-lag | **8.0** | **8.0** | `en/06-antitrust-lag.en.md` | `cn/06-antitrust-lag.cn.md` |
| 07 | personal-ai-exit-ramp | 7.8 | 7.5 | `en/07-personal-ai-exit-ramp.en.md` | `cn/07-personal-ai-exit-ramp.cn.md` |
| 08 | deepseek-trajectory | 7.5 | 7.8 | `en/08-deepseek-trajectory.en.md` | `cn/08-deepseek-trajectory.cn.md` |
| 09 | context-ownership | 7.8 | 7.8 | `en/09-context-ownership.en.md` | `cn/09-context-ownership.cn.md` |
| 10 | composition-over-subscription | 7.2 | 7.8 | `en/10-composition-over-subscription.en.md` | `cn/10-composition-over-subscription.cn.md` |
| 11 | displacement-spiral | 7.5 | 7.0 | `en/11-displacement-spiral.en.md` | `cn/11-displacement-spiral.cn.md` |
| 12 | ghost-gdp | 7.2 | 7.5 | `en/12-ghost-gdp.en.md` | `cn/12-ghost-gdp.cn.md` |
| 13 | friction-elimination | 6.5 | 7.8 | `en/13-friction-elimination.en.md` | `cn/13-friction-elimination.cn.md` |
| 14 | top10-spending-collapse | 6.8 | 7.2 | `en/14-top10-spending-collapse.en.md` | `cn/14-top10-spending-collapse.cn.md` |
| 15 | daisy-chain | 7.0 | 7.8 | `en/15-daisy-chain.en.md` | `cn/15-daisy-chain.cn.md` |
| 16 | 2028-mortgage-crisis | 7.8 | 7.0 | `en/16-2028-mortgage-crisis.en.md` | `cn/16-2028-mortgage-crisis.cn.md` |
| 17 | interchange-pressure | 7.0 | 7.0 | `en/17-interchange-pressure.en.md` | `cn/17-interchange-pressure.cn.md` |
| 18 | zendesk-template | 6.5 | 6.5 | `en/18-zendesk-template.en.md` | `cn/18-zendesk-template.cn.md` |
| 19 | revenue-paradox | 7.0 | 7.0 | `en/19-revenue-paradox.en.md` | `cn/19-revenue-paradox.cn.md` |
| 20 | labor-share-46 | 6.5 | 6.8 | `en/20-labor-share-46.en.md` | `cn/20-labor-share-46.cn.md` |

**Average across 40 drafts:** Mobile 7.0 · SEO 7.5 · H2-skim 7.5 · ICP 7.2

**Strongest (avg ≥ 7.8):** 01-EN, 04-EN, 04-CN, 05-EN, 06-EN, 06-CN, 07-EN, 08-CN, 09-EN, 09-CN, 10-CN, 13-CN, 15-CN, 16-EN — these can ship as-is.

**Weakest (avg ≤ 6.8, still terminate):** 13-EN, 14-EN, 18-EN, 18-CN, 20-EN, 20-CN — recommended one more pass before posting; common cause is over-reliance on Citrini's specific dated forecasts read as fact.

## Cross-cutting weaknesses (raised by ≥3 batches)

These appear systematically and are the obvious targets if you want a round-2 pass on the batch:

1. **Speculative-as-fact framing of Citrini scenario.** Topics 11–20 cite Citrini's 2027/2028 numbers (487K jobless claims, $13T mortgages, Mastercard 3.4%, Zendesk default Sept-2027) as if observed. Hedge with "Citrini's projection" or "in the 2028-GIC scenario" to keep target-ICP scores from sliding.
2. **Long-paragraph mobile walls.** EN drafts have 1–2 paragraphs >80 words; CN drafts have paragraphs 200–300 chars. Easiest mechanical fix: split at the first natural transition.
3. **In-prose enumerations not surfaced as lists/H3s.** Multiple drafts say "four things" or "three steps" but render them as paragraph prose. Convert to bullet lists or H3s.
4. **Op-ed register drift.** Phrases like "the lesson of every infrastructure cycle", "刹车必须从环外来", "the political brake is weaker than it looks" — rhetorical tics that mobile-first-reader and target-icp flag as AI/think-piece template.
5. **Voice flips at endings into policy/legislative tone** (Transition Economy Act, Shared AI Prosperity Act mentions). Land on the strongest mechanism line, not the policy wrap-up.

## Files in this batch

- `TOPICS.md` — the locked 20-topic plan with derivation
- `SOURCE_NOTES.md` — every fact and quote subagents had access to
- `PLATFORM_FIT.md` — per-platform posting recipes + 8-week posting calendar
- `verify_one.py` — hard-check verifier (word count, H-tags, links, pollutants)
- `en/*.md` — 20 English drafts
- `cn/*.md` — 20 Chinese drafts (native phrasing, not translated)
- `review-state/*.review.json` — full per-draft persona review with weaknesses + fixes
- `review-state/_aggregate.json` — score aggregate
- `review-state/verify_all.json` — hard-check snapshot

## How to re-loop a specific draft

The single-round termination check passed for all 40, but if you want the full multi-round skill convergence on a specific draft, run:

```
/auto-blog-review-loop drafts/blog-batch-20260505/en/13-friction-elimination.en.md --rounds=3
```

That will resume from the existing review state if it's still fresh; otherwise it'll start over and run up to 3 rounds with full Phase A–E machinery (verification + persona memory if you pass `--difficulty=hard`).

## Reviewer model note

Reviews used `mcp__codex__codex` with `model_reasoning_effort: medium` per the project memory note that medium is the right cost-quality point (xhigh is too slow for this volume).
