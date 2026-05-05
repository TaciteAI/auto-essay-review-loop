---
name: market-research
description: Gather actual external market data — competitor list with URLs, market-size benchmarks with citations, customer pain signals, and pricing comparables — about a topic or business plan, then synthesize into a structured `MARKET_RESEARCH.md` artifact that downstream review skills can ground their critique against. Use when the user says "do market research on X", "research the competitive landscape", "find competitors", "size the market", or wants to enrich a business plan with real-world data before running `auto-business-plan-review-loop`.
argument-hint: [topic-or-path-to-plan.md] [-- geo: "US"] [-- icp: "VP Eng at 200-person SaaS"] [-- depth: lite|balanced|max]
allowed-tools: Bash(*), Read, Grep, Glob, Write, Edit, WebSearch, WebFetch, Skill, mcp__codex__codex
---

# Market Research

Gather real external evidence about a market — competitors, sizing benchmarks, pain signals, pricing — and synthesize it into a single auditable artifact. Unlike the `auto-{format}-review-loop` skills, this skill is **one-shot data-gathering**, not iterative review. Its output (`MARKET_RESEARCH.md`) is a fact base that downstream personas (especially `competitor` and `unit-economics-skeptic` in `auto-business-plan-review-loop`) can cite and contradict, instead of operating purely on the plan's own claims.

## Context: $ARGUMENTS

The first positional argument is either:

1. **A path to a markdown file** (e.g., `BUSINESS_PLAN.md`) — the skill extracts topic, ICP, and geography signals from the plan structure.
2. **A free-text topic string** (e.g., `"developer-facing AI code-review tools"`) — used as-is when no plan exists yet.

Optional flags:

- `-- geo: "US|EU|JP|global"` — restricts sourcing to that geography (default: `global`).
- `-- icp: "<one-line buyer description>"` — overrides the plan-extracted ICP.
- `-- depth: lite|balanced|max` — controls the source budget (see Constants).

## Constants

| Constant | Value | Notes |
|----------|-------|-------|
| `OUTPUT_DIR` | `market-research/` | Distinct from `review-stage/` so it survives across multiple review loops. |
| `OUTPUT_DOC` | `market-research/MARKET_RESEARCH.md` | Canonical artifact; consumed by reviewer skills. |
| `OUTPUT_JSON` | `market-research/MARKET_RESEARCH.json` | Machine-readable sidecar (same schema as verification tools). |
| `TIMESTAMPED_COPY` | `market-research/MARKET_RESEARCH_{YYYYMMDD_HHMMSS}.md` | Per [output-versioning.md](../shared-references/output-versioning.md) — never overwritten. |
| `RESEARCH_PLAN` | `market-research/RESEARCH_PLAN.json` | Query plan emitted by Phase 1, replayable for crash recovery. |
| `RAW_DIR` | `market-research/raw/` | One JSON file per fetched source (`websearch-{slug}.json`, `webfetch-{slug}.json`). Audit trail. |
| `SYNTHESIS_BACKEND` | `codex` | v0.1: Codex MCP only. |
| `SYNTHESIS_MODEL` | `gpt-5.4` | Via `mcp__codex__codex` with `model_reasoning_effort: medium`. |
| `MIN_COMPETITORS` | `5` | Fewer than 5 named competitors (with URLs) → emit `thin_competitor_set` flag. |
| `MIN_SIZING_SOURCES` | `2` | Fewer than 2 independent TAM/SAM citations → emit `single_source_sizing` flag. |
| `STALENESS_BUDGET_MONTHS` | `24` | Citations older than 24 months without a corroborating recent source → emit `stale_citation` warning. |

### Depth budget (`-- depth:`)

| Depth | Search queries | Pages fetched | Synthesis effort | Wall-clock target |
|-------|----------------|---------------|------------------|-------------------|
| `lite` | ≤6 | ≤8 | medium | ~2 min |
| `balanced` (default) | ≤12 | ≤20 | medium | ~5 min |
| `max` | ≤24 | ≤40 | medium | ~12 min |

Depth caps are advisory, not hard. The synthesis step still runs at `medium` regardless — depth controls breadth, not reasoning quality.

## Phase contract

This skill follows a five-phase contract: **Phase 0 (intake) → Phase 1 (plan) → Phase 2 (gather) → Phase 3 (synthesize) → Phase 4 (validate & write)**. It does NOT inherit the A–E loop contract — there are no personas and no rounds. Crash recovery is per-phase: if `RESEARCH_PLAN.json` exists, resume from Phase 2; if `RAW_DIR/` is non-empty, resume from Phase 3.

## Phase 0 — Intake

1. Resolve the first argument:
   - If it ends in `.md` and the file exists, treat it as a plan path. `cat` the first 8KB.
   - Otherwise treat the entire argument string (up to the first `--`) as a free-text topic.
2. Parse `-- geo:`, `-- icp:`, `-- depth:` flags. Defaults: `geo=global`, `icp=auto`, `depth=balanced`.
3. Create `OUTPUT_DIR` and `RAW_DIR` if missing (`mkdir -p`).
4. If `OUTPUT_DOC` already exists and is <24h old, ask the user once: "Existing `MARKET_RESEARCH.md` from {timestamp} — refresh, append, or abort?" Default to **abort**; the user must explicitly say `refresh` or `append`.

## Phase 1 — Build research plan

Invoke the helper to extract structured signals from the input and emit a query plan:

```bash
bash tools/run.sh market_research_fetch.py plan \
  --input "$INPUT" \
  --geo "$GEO" \
  --icp "$ICP" \
  --depth "$DEPTH" \
  > market-research/RESEARCH_PLAN.json
```

`RESEARCH_PLAN.json` schema (excerpt):

```json
{
  "tool": "market_research_fetch",
  "phase": "plan",
  "topic": {
    "category": "developer-facing AI code-review tools",
    "icp": "VP Eng at 50–500 person SaaS",
    "geo": "global",
    "extracted_competitor_mentions": ["Greptile", "CodeRabbit"]
  },
  "search_queries": [
    {"id": "q01", "intent": "market_size", "query": "AI code review market size 2026"},
    {"id": "q02", "intent": "competitors", "query": "AI code review tools list 2026"},
    {"id": "q03", "intent": "pricing", "query": "Greptile pricing"},
    {"id": "q04", "intent": "pain_signal", "query": "site:reddit.com/r/ExperiencedDevs code review pain"}
  ],
  "fetch_targets": [
    {"id": "f01", "intent": "competitor_homepage", "url": "https://greptile.com", "what_to_extract": ["pricing", "positioning", "team_size"]},
    {"id": "f02", "intent": "competitor_pricing", "url": "https://coderabbit.ai/pricing"}
  ],
  "validation_rubric": {
    "required_sections": ["Market Size", "Competitor Landscape", "Customer Pain Signals", "Pricing Benchmarks", "Sources"],
    "min_competitors": 5,
    "min_sizing_sources": 2
  }
}
```

The helper does NOT itself call WebSearch or WebFetch — those are Claude tools, not Python tools. It emits the plan; Phase 2 executes it.

## Phase 2 — Gather

Execute the plan from `RESEARCH_PLAN.json` in this order, writing each result to `RAW_DIR/`:

### 2a. Local prior art (free)

Before any external call, check the project for prior research:

- `MARKET_NOTES.md`, `competitive-analysis*.md`, `research-notes/`, `competitors.csv` in the project root
- Any file matching `(?i)(market|competitive|industry).*\.md` in the working tree

If found, copy verbatim into `RAW_DIR/local-{slug}.md`. The synthesizer treats these as primary sources (the user's own knowledge is more reliable than search results).

**Always copy the originating plan when present.** If `topic.input_source.kind == "file"`, also copy the input plan into `RAW_DIR/local-input-plan.md`. The synthesizer needs full plan context to ground citations in the founder's actual claims (not just the auto-extracted topic string), and category extraction is best-effort — having the plan in the raw bundle backstops weak Phase 1 extractions.

### 2b. WebSearch (parallel where possible)

For each entry in `search_queries`, dispatch one `WebSearch` call. Capture top 5 results per query as JSON:

```json
{
  "query_id": "q01",
  "query": "AI code review market size 2026",
  "intent": "market_size",
  "results": [
    {"title": "...", "url": "...", "snippet": "...", "fetched_at": "2026-04-28T..."}
  ]
}
```

Write to `RAW_DIR/websearch-{query_id}.json`.

**Failure handling:** if `WebSearch` is unavailable or returns no results for a given query, log it but continue. Mark the query `status: "no_results"` in the raw file. Do NOT halt the phase.

### 2c. WebFetch (sequential, throttled)

For each entry in `fetch_targets` AND for any high-signal URL surfaced in 2b that wasn't pre-listed (cap total fetches at the depth budget):

1. `WebFetch` the URL with a focused prompt: `"Extract: pricing tiers and prices, positioning tagline, target customer, any market-size or customer-count claim. Return as JSON."`
2. Save raw response to `RAW_DIR/webfetch-{slug}.json` where slug is a sanitized hostname+path.
3. Throttle: max 1 fetch per 2 seconds to be polite to upstream sites.

**Failure handling:** 4xx/5xx → log with status code, continue. Robots-blocked → log and skip. Never retry more than once.

### 2d. (Optional) Exa MCP, if present

If `mcp__exa__search` is in the tool list, run a single Exa query for the top 1–2 high-intent queries (the ones tagged `intent: market_size` or `intent: competitors`). Exa returns AI-extracted highlights, which often surface non-obvious sources. Write to `RAW_DIR/exa-{query_id}.json`. If Exa is not available, skip silently.

## Phase 3 — Synthesize via Codex MCP

Pass ALL files in `RAW_DIR/` as raw evidence to Codex. The synthesis prompt deliberately requires citation-grounding: every numeric claim in the output must reference a specific raw file.

```yaml
mcp__codex__codex:
  config:
    model_reasoning_effort: "medium"
  prompt: |
    SYSTEM:
    You are a senior market analyst building a fact base for a startup
    business plan. You are NOT writing prose for the founder. You are
    producing a structured artifact that adversarial reviewers (a VC
    partner, an incumbent CEO, a unit-economics skeptic) will use to
    cross-check the founder's claims.

    RULES:
    1. Every numeric claim (TAM, SAM, pricing, headcount, ARR, growth
       rate) must cite a specific source from RAW_DIR. Citations are
       inline as `[source: websearch-q01.json#result-3]` or
       `[source: webfetch-greptile-pricing.json]`.
    2. If the evidence does not support a number, say so explicitly:
       `TAM: not directly sourced; nearest analog is $X (adjacent market)`.
       Never invent.
    3. Distinguish vendor self-claims from third-party data. Mark vendor
       claims as `(self-reported)`.
    4. Flag staleness: any source >24 months old gets `(2024)` etc.
       appended.
    5. Output format is the markdown skeleton below — fill every section,
       even if to say "insufficient evidence".

    CONTEXT:
    Topic: {topic.category}
    ICP: {topic.icp}
    Geography: {topic.geo}
    Extracted competitor mentions from input: {topic.extracted_competitor_mentions}

    RAW EVIDENCE FILES (read each one — do not skim):
    {paste each file's contents inline, prefixed by its filename}

    OUTPUT (markdown — return verbatim, no prose before or after):

    # Market Research: {topic.category}
    _Generated {timestamp} · depth={depth} · geo={geo}_

    ## Executive snapshot
    Three sentences. Market size order-of-magnitude, competitor density,
    one non-obvious finding. No hedging language.

    ## Market size evidence
    | Layer | Value | Source | Year | Notes |
    |-------|-------|--------|------|-------|
    | TAM | $X | [source: ...] | 2026 | Methodology if stated |
    | SAM | $X | ... | ... | ... |
    | Realistic capture rate (analog) | X% over Y years | ... | ... | ... |

    ## Competitor landscape
    | Name | URL | Stage / ARR | Pricing | Positioning | Wedge against new entrants |
    |------|-----|-------------|---------|-------------|----------------------------|
    | ... | ... | ... | ... | ... | ... |

    Minimum {MIN_COMPETITORS} rows. If fewer real competitors exist, list
    adjacent / partial-overlap players and label them `(adjacent)`.

    ## Customer pain signals
    Bullet list. Each bullet: one observed pain quote or pattern, with
    source link. Prefer Reddit / HN / job postings / public Slack
    transcripts over vendor blogs.

    ## Pricing benchmarks
    Inline table. Median price, range, common packaging (per-seat,
    usage-based, freemium). Cite each.

    ## Pre-mortem questions for the founder
    Five sharp questions a VC would ask given this evidence. These are
    written FOR the reviewer personas to use as ammunition.

    ## Sources
    Numbered list of every URL/file cited above.

    ## Confidence
    One paragraph. What's well-evidenced, what's thin, what would need
    primary research (interviews, paid reports) to nail down.
```

Save Codex's threadId to `market-research/.codex_thread` for one optional follow-up turn (Phase 3.5) if Phase 4 validation surfaces gaps; do NOT carry it across re-runs.

### Phase 3.5 (conditional) — Patch missing sections

If Phase 4 validation flags missing sections or under-cited claims, send ONE follow-up via `mcp__codex__codex-reply` with the specific gap list. Cap at one follow-up; if it still fails, surface to the user.

## Phase 4 — Validate and write

Before publishing, run the validator:

```bash
bash tools/run.sh market_research_fetch.py validate \
  --input market-research/MARKET_RESEARCH.md \
  --plan market-research/RESEARCH_PLAN.json \
  > market-research/MARKET_RESEARCH.json
```

The validator checks:

| Check | Pass criteria | Flag on failure |
|-------|---------------|-----------------|
| Required sections present | All sections from `validation_rubric.required_sections` exist as `^## ` headings | `missing_section` |
| Competitor count | ≥ `MIN_COMPETITORS` rows in the competitor table | `thin_competitor_set` |
| Sizing source count | ≥ `MIN_SIZING_SOURCES` distinct citations under "Market size evidence" | `single_source_sizing` |
| Citation density | Every numeric value (`$XB`, `$XM`, `X%`, `X seats`) has an inline `[source: ...]` reference | `uncited_number` |
| Citation resolvability | Every `[source: filename]` reference matches a file in `RAW_DIR/` | `broken_citation` |
| Staleness | No citation older than `STALENESS_BUDGET_MONTHS` without a corroborating recent source | `stale_citation` (warning, not failure) |

If any non-warning flag fires AND Phase 3.5 has not been used yet, run Phase 3.5 with the flag list as the targeted gap report. Otherwise: write the artifact, surface flags in the final user message, and let the user decide whether to ship.

### Final write

1. Write `OUTPUT_DOC` (overwrite of canonical alias).
2. Copy to `TIMESTAMPED_COPY` (immutable archive — never overwritten, per [output-versioning.md](../shared-references/output-versioning.md)).
3. Append a row to [output-manifest.md](../shared-references/output-manifest.md) format manifest at `market-research/MANIFEST.md`: `{timestamp} | {topic_slug} | {depth} | {flags} | {output_path}`.
4. Print to the user:
   - One-line summary (`X competitors, $XB TAM range, N sources`).
   - The path to `OUTPUT_DOC`.
   - Any non-warning flags that fired.
   - The Phase 4 confidence paragraph verbatim.

## Integration with `auto-business-plan-review-loop`

When `MARKET_RESEARCH.md` exists in the project root or `market-research/`, the business-plan loop's reviewer prompt construction (Phase B in [loop-contract.md](../shared-references/loop-contract.md)) appends a second tagged block:

```text
<DRAFT>
{the user's plan}
</DRAFT>

<MARKET_DATA>
{contents of MARKET_RESEARCH.md}
</MARKET_DATA>
```

The system prompt is updated to: _"You may cross-reference claims in `<DRAFT>` against evidence in `<MARKET_DATA>`. Cite the latter in your `weaknesses` list when contradictions appear (e.g., `'plan claims $50B TAM; MARKET_DATA shows third-party estimate of $4B'`)."_

This is opt-in: if `MARKET_RESEARCH.md` is absent, the loop runs as before. If present, the `competitor` and `unit-economics-skeptic` personas in particular get sharply better at catching unsupported claims. See [auto-business-plan-review-loop/SKILL.md](../auto-business-plan-review-loop/SKILL.md) "Optional market-research enrichment".

## Anti-patterns this skill explicitly rejects

- **Synthesizing without raw files.** If `RAW_DIR/` is empty (because Phase 2 found nothing), do NOT proceed to Phase 3. Tell the user the topic returned no usable sources and suggest narrowing or broadening the query.
- **Fabricated competitors.** Every competitor row needs a URL that actually resolves. If Phase 4 finds a competitor row with no URL or with a 404 URL, treat as `broken_citation`.
- **Vendor-claim laundering.** A pricing page is a vendor self-claim. Crunchbase ARR is a vendor self-claim filtered through PR. Both are useful, but must be tagged `(self-reported)`.
- **TAM-by-multiplication.** "Global software is $X, our slice is 2%" is not a sourced TAM — it's a back-of-envelope. The synthesizer must say so explicitly.
- **Single-source sizing.** One Gartner blog with no methodology is not market sizing. Either find a corroborating source or flag `single_source_sizing` and let the reviewer downstream weigh it.

## Crash & resume

State files are the source of truth, in this order:

1. If `MARKET_RESEARCH.md` exists and `MARKET_RESEARCH.json` reports `passed: true` — done; ask before re-running.
2. Else if `RAW_DIR/` has files — skip to Phase 3.
3. Else if `RESEARCH_PLAN.json` exists — skip to Phase 2.
4. Else — start at Phase 0.

Phase 2 is idempotent per file: if `websearch-q01.json` already exists, skip that query. Re-runs only fetch what's missing. Use `--force` to invalidate `RAW_DIR/` and re-fetch everything.

## Trace logging

Per the trace convention used elsewhere in this repo, write to:

```
traces/market-research/{YYYYMMDD_HHMMSS}_run{NN}/
  ├── phase1-plan.json                     # copy of RESEARCH_PLAN.json
  ├── phase2-raw/                          # copy of RAW_DIR/
  ├── phase3-synthesis.prompt.txt          # full Codex prompt
  ├── phase3-synthesis.response.txt        # raw Codex response
  ├── phase3.5-patch.prompt.txt            # if Phase 3.5 ran
  ├── phase3.5-patch.response.txt
  └── phase4-validation.json               # copy of MARKET_RESEARCH.json
```

The trace is the audit answer to "why does this MARKET_RESEARCH.md make this claim?" — every number can be walked back to a raw fetch.

## Example invocations

```text
/market-research "developer-facing AI code review tools" -- icp: "VP Eng at 50–500 person SaaS"
```

```text
/market-research ./BUSINESS_PLAN.md -- depth: max
```

```text
/market-research ./pitches/seed_round.md -- geo: "EU" -- depth: balanced
```

## Out of scope (v0.1)

- **Paid data sources** (PitchBook, CB Insights, Gartner Magic Quadrant). v0.1 uses only public web. The validator surfaces this as `confidence: low` when sizing depends on free sources only.
- **Direct user interviews.** No survey orchestration. Pain signals come from public artifacts (Reddit, HN, job postings, Glassdoor reviews) only.
- **Image / chart extraction** from competitor sites. Text only in v0.1.
- **Continuous monitoring.** This is one-shot. For "alert me when a new competitor enters" use a recurring `/schedule` agent.
- **Patent / IP landscape.** Out of scope for v0.1; that's a different research workflow.

---

See also: [tools/market_research_fetch.py](../../tools/market_research_fetch.py), [auto-business-plan-review-loop/SKILL.md](../auto-business-plan-review-loop/SKILL.md), [shared-references/verification-protocols.md](../shared-references/verification-protocols.md), [shared-references/output-versioning.md](../shared-references/output-versioning.md).
