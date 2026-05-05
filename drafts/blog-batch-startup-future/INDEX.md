# 20-Blog Batch — AI Startup Future (2026-05-05)

40 drafts (20 topics × English + Chinese). Drafted by Codex MCP (`gpt-5.4`, `medium` reasoning, `workspace-write` / `danger-full-access` sandbox). Reviewed by 4 personas via Codex MCP per the auto-blog-review-loop skill spec (single round, Phase A + B + B.7 equivalent).

Sources for the topic plan:
- a16z, "The Empty Promise of Data Moats" — https://a16z.com/the-empty-promise-of-data-moats/
- AgentMarketCap, "Agentic Funding Shift 2026" — https://agentmarketcap.ai/blog/2026/04/08/agentic-ai-funding-velocity-2026-sector-map-vertical-distribution
- AgentMarketCap, "AI Captured 61% of Global VC" — https://agentmarketcap.ai/blog/2026/04/10/ai-captures-50-percent-global-venture-capital-2025
- Foundation Capital, "Where AI is headed in 2026" — https://foundationcapital.com/ideas/where-ai-is-headed-in-2026
- NFX, "How AI Companies Will Build Real Defensibility" — https://www.nfx.com/post/ai-defensibility
- Linas Beliūnas, "Sequoia's Services-as-Software Thesis" — https://linas.substack.com/p/sequoiathesis

All 40 drafts pass blog hard verification (word count, H-tag structure, ≥2 inline links, no emojis/hashtags/code-fences). **29 of 40 pass single-round persona termination** (≥3 of 4 personas ≥6, no CRITICAL).

## Score table (M = mobile, S = SEO, H = H2-skim, I = ICP)

| # | Topic | EN avg / term | CN avg / term |
|---|-------|---------------|---------------|
| 01 | wrapper-era-over | 6.8 / **NO** | 6.2 / **NO** |
| 02 | service-as-software | 6.8 / yes | 6.7 / yes |
| 03 | distribution-is-the-moat | 6.7 / yes | 5.9 / **NO** |
| 04 | data-flywheel-vs-hoard | 6.7 / yes | 6.2 / yes |
| 05 | workflow-lockin | 6.5 / **NO** | 5.5 / **NO** |
| 06 | vertical-beats-horizontal | **7.8** / yes | 7.5 / yes |
| 07 | trust-and-compliance | 6.8 / **NO** | 6.8 / **NO** |
| 08 | multiplayer-agent-network-effects | 6.8 / **NO** | 7.0 / **NO** |
| 09 | system-of-action | 7.5 / yes | 7.5 / **NO** |
| 10 | brand-and-ux-when-capability-is-rented | 7.2 / yes | 7.2 / **NO** |
| 11 | death-of-prompt-box | 7.2 / yes | 7.5 / yes |
| 12 | outcome-pricing | 7.5 / yes | 7.5 / yes |
| 13 | vendor-consolidation | 7.2 / yes | 7.5 / yes |
| 14 | 155M-series-a | 7.0 / yes | 7.2 / yes |
| 15 | foundation-models-as-competitors | 7.5 / yes | 7.5 / yes |
| 16 | ai-native-hedge-fund | 7.2 / yes | **7.8** / yes |
| 17 | ai-native-agency | **7.8** / yes | **7.8** / yes |
| 18 | open-vs-closed-cost-curve | 7.2 / yes | **8.0** / yes |
| 19 | vertical-saas-rebundling | **7.8** / yes | **8.0** / yes |
| 20 | micro-saas-corner | 7.2 / yes | **7.8** / yes |

**Average across 40 drafts:** Mobile 6.6 · SEO 7.5 · H2-skim 7.2 · ICP 7.3
**Termination rate:** 29 / 40

## My editorial pass (read 4 samples directly)

I read [en/02-service-as-software](en/02-service-as-software.en.md), [en/09-system-of-action](en/09-system-of-action.en.md), [cn/14-155M-series-a](cn/14-155M-series-a.cn.md), and [en/17-ai-native-agency](en/17-ai-native-agency.en.md) in full before the persona reviews returned. My read agrees with the personas on shape but is more lenient on score:

- **en/02** is solid (I'd give 7.5; personas gave 6.8). Quotable: "If the agency cannot own the outcome, it should not price the outcome." Closing flip lands.
- **en/09** is solid (I'd give 7.5; personas gave 7.5 — agreement). Quotable: "The system of record answered what happened. The system of action answers what should happen next."
- **cn/14** is one of the strongest CN drafts in the batch (I'd give 8; personas gave 7.2). Native phrasing throughout, localizes to 百度/阿里/腾讯/月之暗面/智谱/DeepSeek without losing the load-bearing US numbers. The closing line — "找到一个小团队能先成为权威、而资本重玩家还没注意到的工作流" — is the kind of forward-looking sting the brief asked for.
- **en/17** is the standout of the batch (I'd give 8.5; personas gave 7.8 — agreement). "More economically violent than the AI-native hedge fund" earns the scroll. "The billable hour was a tax on coordination" is a quotable closer that survives platform stripping.

The personas caught two things my read glossed over: (1) generic H2s tank h2-skimmer scores even when the body is good — "Trust and Compliance", "System of Action" read as chapter headings; (2) Codex used the AgentMarketCap URL whose slug says `50-percent` while the body says 61%, which is a credibility risk on close inspection.

## Why 11 failed termination

Three patterns explain every failure:

1. **Generic abstract H2s.** Topics 07 (Trust and Compliance), 08 (Network Effects), 09-CN, 10-CN all use chapter-heading-style H2s. H2-skimmer drops to 4-6 because the H2 list alone doesn't tell the post's argument — the persona literally only reads the H2s and bounces if they read like a TOC.
2. **AgentMarketCap URL/body mismatch.** The article URL slug is `ai-captures-50-percent-global-venture-capital-2025` but the article body — and our drafts — use the updated 61% number. Personas flag this as a credibility hit. **Fix:** either change the in-text number to "50–61%" with both URL contexts, or replace that link with a different source for the same datum.
3. **CN drafts in batch A specifically.** Drafts 01-CN, 03-CN, 05-CN read as 中英夹杂 / 翻译 VC memo to mobile-first-reader and target-icp. Native phrasing got partially lost when Codex was rendering the same essay across two languages back-to-back. Topics 11–20 in CN scored notably better (avg ~7.6) — the technique tightened.

## Cross-cutting weaknesses (raised by ≥3 batches)

1. **VC-memo register.** "Control plane", "data gravity", "operational memory", "operational density" — they recur across drafts and read as 投研腔 / VC template. Replace with concrete operator vocabulary.
2. **Citation-as-confetti.** NFX, a16z, Foundation, AgentMarketCap, Menlo, Bessemer get name-dropped without zoomed-in detail. One quoted sentence per source beats five drive-by citations.
3. **No named company casualty.** Drafts argue "the wrapper era is over" / "vendors will consolidate" without naming a specific failed wrapper or a specific consolidating buyer. Adding 1 named example per draft would lift target-icp scores by 1+ point.
4. **Three-part-symmetry triads.** "First, second, third constraint" — every draft has at least one. Mobile-first-reader and target-icp flag this as AI/LinkedIn template.
5. **Mobile paragraph walls in CN.** EN drafts sit around 70-word paragraphs; CN drafts repeatedly hit 200–300 char walls. Easiest mechanical fix: split at the first natural transition.

## Strongest drafts (avg ≥ 7.8) — ship as-is

- en/06-vertical-beats-horizontal.en.md (7.8)
- en/17-ai-native-agency.en.md (7.8)
- en/19-vertical-saas-rebundling.en.md (7.8)
- cn/16-ai-native-hedge-fund.cn.md (7.8)
- cn/17-ai-native-agency.cn.md (7.8)
- cn/18-open-vs-closed-cost-curve.cn.md (8.0)
- cn/19-vertical-saas-rebundling.cn.md (8.0)
- cn/20-micro-saas-corner.cn.md (7.8)

## Drafts that need a Phase C fix pass before shipping

The 11 that failed termination plus a couple borderline cases:

- en/01-wrapper-era-over.en.md
- cn/01-wrapper-era-over.cn.md
- cn/03-distribution-is-the-moat.cn.md
- en/05-workflow-lockin.en.md
- cn/05-workflow-lockin.cn.md
- en/07-trust-and-compliance.en.md (generic H2s)
- cn/07-trust-and-compliance.cn.md
- en/08-multiplayer-agent-network-effects.en.md
- cn/08-multiplayer-agent-network-effects.cn.md
- cn/09-system-of-action.cn.md
- cn/10-brand-and-ux-when-capability-is-rented.cn.md

To re-loop a single draft with the full 4-round skill machinery:

```
/auto-blog-review-loop drafts/blog-batch-startup-future/en/07-trust-and-compliance.en.md --rounds=3
```

Or to do a focused Codex fix-pass on a single weakness without invoking the full loop, ask me to "fix the H2s on en/07-trust-and-compliance".

## Files in this batch

- [TOPICS.md](TOPICS.md) — locked 20-topic plan with derivation
- [SOURCE_NOTES.md](SOURCE_NOTES.md) — every fact, every URL, the style rules subagents had access to
- [en/](en/) — 20 English drafts
- [cn/](cn/) — 20 Chinese drafts (native phrasing, not translated)
- [review-state/](review-state/) — 40 per-draft persona JSONs + `_aggregate.json` + `verify_all.json`
- [verify_all.json](review-state/verify_all.json) — hard-check snapshot

## Reviewer model + sandbox notes

- Drafting: Codex MCP `gpt-5.4` at `medium` reasoning. Two of four parallel sessions hit a Windows sandbox login error (`CreateProcessWithLogonW failed: 1326/1909`); retried with `danger-full-access` and completed.
- Reviewing: 4 reviewer subagents in parallel, each handling 10 drafts × 4 personas via `mcp__codex__codex` at `medium` reasoning. ~160 Codex calls total.

## Comparison to the previous (cyberpunk) batch

| | Cyberpunk batch (2026-05-05) | Startup-future batch |
|---|---|---|
| Drafts | 40 | 40 |
| Hard checks pass | 40/40 | 40/40 |
| Persona termination | **40/40** | 29/40 |
| Avg Mobile | 7.0 | 6.6 |
| Avg SEO | 7.5 | 7.5 |
| Avg H2-skim | 7.5 | 7.2 |
| Avg ICP | 7.2 | 7.3 |
| Drafting agent | general-purpose subagents | Codex MCP |

Codex with focused source notes produced sharper individual sentences but underperformed on H2 specificity (more abstract / chapter-heading H2s) than subagents working from inline brief text. Both batches scored similarly on ICP.
