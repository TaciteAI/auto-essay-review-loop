# Verification Protocols

Verification is the objective layer. Persona reviews are subjective. Both
must pass before an artifact is APPROVED. A draft cannot ship with a broken
link, a 312-character tweet, or a $10T TAM fantasy — no matter how much
the personas like the prose.

## Rule

Verification runs in **Phase B.7** (after personas review, before termination
check). Failures are reported as hard rejections in the round's
`AUTO_REVIEW.md` entry and added to the fix list with `severity: CRITICAL`.

## Per-format checks

### Blog

| Check | Tool | Pass criteria |
|-------|------|---------------|
| Links resolve | `tools/verify_links.sh` | All `http(s)://` links return 200 OR 301→200; 4xx/5xx fail |
| H-tag structure | inline (count `^## ` / `^### `) | At least 2 H2s; no H4 without H3 above; no skipped levels |
| Word count | `wc -w` | Within 500–4000 (configurable per skill) |
| Code-block sanity | inline (regex) | Code blocks have language tags; no unclosed fences |

### Social (X / Threads / IG caption)

| Check | Tool | Pass criteria |
|-------|------|---------------|
| Char count | `tools/count_chars.py` | ≤280 (X), ≤500 (Threads), ≤2200 (IG) |
| Link count | inline | ≤1 link per post (link-in-bio convention) |
| Hashtag count | inline | ≤3 (X), ≤5 (Threads), ≤30 (IG) |
| Mention validity | inline | `@handle` is well-formed (no spaces, no emoji) |

### LinkedIn

| Check | Tool | Pass criteria |
|-------|------|---------------|
| Char count | `tools/count_chars.py` | ≤3000 (post limit) |
| Hook length | inline | First 2 lines ≤210 chars (mobile preview cutoff) |
| Hashtag count | inline | ≤5 (LinkedIn algorithmic preference) |
| Link count | inline | 0 or 1 (LinkedIn deprioritizes external links) |

### Business plan

| Check | Tool | Pass criteria |
|-------|------|---------------|
| Section presence | inline | All required sections exist (Executive Summary, Problem, Solution, Market, Business Model, Traction, Team, Financials) |
| Market sizing sanity | `tools/market_size_check.py` | TAM/SAM/SOM stated; SOM < SAM < TAM; TAM not absurd (>$5T flagged) |
| Unit economics presence | inline (regex for CAC/LTV/payback) | At least 2 of {CAC, LTV, payback, gross margin, churn} mentioned with numbers |
| Financial completeness | inline | 12-month and 3-year projections, named line items |

## Calling verification from a skill

```bash
# Phase B.7 in a format skill
bash tools/verify_links.sh review-stage/draft.md > review-stage/verify_links.json
python tools/count_chars.py review-stage/draft.md --format=social > review-stage/count_chars.json
python tools/market_size_check.py review-stage/draft.md > review-stage/market_size.json
```

Each tool emits JSON to stdout (or to a file if `>` is used). Skills parse
the JSON and merge results into the round's `AUTO_REVIEW.md` entry.

## JSON output schema (all tools)

```json
{
  "tool": "verify_links",
  "timestamp": "2026-04-28T10:00:00",
  "input_file": "review-stage/draft.md",
  "passed": false,
  "checks": [
    {"name": "url_https_example_com", "passed": true, "detail": "200 OK"},
    {"name": "url_dead_link_example_com", "passed": false, "detail": "404 Not Found"}
  ],
  "summary": "1 of 2 links broken"
}
```

## Verification failures are not opinions

If `verify_links.sh` says a link is broken, the link is broken. The persona
that says "looks great to me" doesn't override that. The fix list MUST
include the broken link before the round can pass.

## Enrichment artifacts (not gates)

Some tools produce evidence that is fed back to reviewers as ammunition,
not as a hard gate on the draft. They run BEFORE the loop, not inside
Phase B.7, and their failures don't block termination — they only weaken
the resulting fact base. Currently:

| Artifact | Producer | Validator | Consumed by |
|----------|----------|-----------|-------------|
| `MARKET_RESEARCH.md` | [/market-research](../market-research/SKILL.md) | `python tools/market_research_fetch.py validate ...` | `auto-business-plan-review-loop` Phase B (appended to reviewer prompt as `<MARKET_DATA>`) |

The validator emits the same JSON schema as the gate tools (above) so
that any future enrichment artifact can be checked uniformly. The
distinction is **where the result is used**: gate-tool failures block
round termination; enrichment-validator failures only mean "this
evidence base is thin — surface it to the user before they trust the
review."
