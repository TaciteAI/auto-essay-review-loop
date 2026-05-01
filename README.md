# auto-essay-review-loop

> Persona-adversarial review for blog posts, social media, LinkedIn, and business plans.
> Paste a draft. Go to bed. Wake up to a better artifact and an audit trail of who said what.

[![Version](https://img.shields.io/badge/version-0.1.0-blue)](VERSION)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Backend](https://img.shields.io/badge/backend-Codex%20MCP%20(gpt--5.4%20xhigh)-orange)](docs/BACKEND_CONFIG.md)

A skill-based review loop for non-academic writing. Same doctrine as
[ARIS](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep)
(the research-paper version), generalized: cross-model adversarial review
beats single-model self-play, persona-adversarial review beats generic
critique, and verification beats vibes.

---

## Table of contents

1. [The problem](#the-problem)
2. [The doctrine](#the-doctrine)
3. [The workflow](#the-workflow)
4. [Quickstart](#quickstart)
5. [Formats and personas](#formats-and-personas)
6. [Example output](#example-output)
7. [Why personas?](#why-personas)
8. [Backends](#backends)
9. [Repo layout](#repo-layout)
10. [Roadmap](#roadmap)
11. [Credits and license](#credits-and-license)

---

## The problem

You write a blog post. You ask ChatGPT "is this good?" It says yes. You ship.
Three people read it. Two of them are bots.

The standard tooling for non-academic writers in 2026:

- **Grammarly** catches commas. Catches nothing else.
- **One-shot LLM critique** ("review my draft") gives bland, agreeable feedback.
  The model has no stake. It will not tell you the hook is dead. It will tell
  you the hook is "engaging" and offer five synonyms for "interesting."
- **You re-read it yourself.** You wrote it. You have already lost.

The gap is not "more feedback." The gap is **adversarial feedback from
specific personas with specific bars**, repeated until the artifact survives.
That is what an editor does. That is what a VC partner does in 30 seconds.
That is what a recruiter does on LinkedIn at 11pm scrolling on their phone.

Most writers iterate alone with Grammarly and one-shot ChatGPT and a Slack
DM to a friend who is too nice. This is a measurement gap, not a writing
gap. We are fixing the measurement gap.

## The doctrine

Three rules, taken from the ARIS playbook and ported to writing:

### 1. Cross-model > self-play

You are using Claude (or Codex, or whatever your agent harness is) to drive
the loop. The reviewer is a *different* model — Codex GPT-5.4 with
`model_reasoning_effort: xhigh` in v0.1. Same model reviewing its own output
is the **stochastic** case: predictable noise, blind spots compound. Different
models is the **adversarial** case: the reviewer probes weaknesses the
executor didn't anticipate. Adversarial bandits are fundamentally harder to
game than stochastic ones.

### 2. Persona-adversarial > generic critique

"Review this blog post" is useless. "You are a mobile reader on a phone in
bed at 11:47pm. You will scroll past anything that doesn't grab you in the
first 1.5 H2s. Read this and tell me when you would bounce." is a measurement.

Each format ships 4–5 named personas with concrete bars, dealbreakers, and
veto powers. You don't review against "is this good." You review against:
*would the H2-skimmer get the argument from H2s alone? Would the unit-economics
skeptic believe the CAC math? Would the 0.8-second scroller stop?*

### 3. Verification > vibes

If a link 404s, it 404s. The persona that says "looks great" doesn't override
that. If a tweet is 312 characters, it is 312 characters. If a TAM is $10
trillion, the market-size sanity check fails — no matter how the prose flows.

Every format ships a verification layer that runs hard checks (link resolution,
character count, market-size sanity, hashtag count). Verification failures are
hard rejections that bypass persona consensus.

## The workflow

```
draft → /auto-essay-review-loop draft.md
              │
              ▼
       format detected (blog/social/linkedin/biz-plan)
              │
              ▼
   ┌──────────────────── round N ────────────────────┐
   │ Phase A: each persona reviews the draft         │
   │          (parallel, fresh thread per persona)   │
   │ Phase B: parse JSON → score, verdict, fixes     │
   │ Phase B.5: reviewer memory (hard/nightmare)     │
   │ Phase B.6: debate protocol (hard/nightmare)     │
   │ Phase B.7: verification (links, char, etc.)     │
   │ termination check                                │
   │ Phase C: implement highest-priority fixes       │
   │ Phase D: re-render / re-verify                  │
   │ Phase E: append to AUTO_REVIEW.md, write state  │
   └──────────────────────┬──────────────────────────┘
                          │
                ┌─────────┴─────────┐
              APPROVED          round N+1
                │
                ▼
       review-stage/{format}_approved.md
       review-stage/AUTO_REVIEW.md   (full audit trail)
       review-stage/MANIFEST.md      (every file written)
```

You go to bed at round 1. You wake up at round 4. The artifact is approved
or you have a paper trail of exactly which persona kept rejecting and why —
and you can read its memory file to see what it learned to suspect about
your draft over time.

## Quickstart

### Prerequisites

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (or any agent
  harness that supports skills + MCP)
- Codex MCP set up — see [docs/BACKEND_CONFIG.md](docs/BACKEND_CONFIG.md)
- Codex configured for `gpt-5.4` with `model_reasoning_effort: xhigh`

### Install

```bash
git clone https://github.com/your-handle/auto-essay-review-loop.git
mkdir -p ~/.claude/skills/
cp -r auto-essay-review-loop/skills/* ~/.claude/skills/
```

### Use

```bash
claude

# auto-detect format
/auto-essay-review-loop drafts/my_post.md

# explicit format
/auto-essay-review-loop drafts/tweet.txt --format=social --platform=x

# adversarial difficulty
/auto-essay-review-loop drafts/pitch_memo.md --difficulty=hard

# pause after each round to give human input
/auto-essay-review-loop drafts/blog.md --human-checkpoint=true
```

### What you get back

```
review-stage/
├── blog_approved.md                  # alias to latest approved draft
├── blog_approved_20260428_103401.md  # timestamped audit version
├── AUTO_REVIEW.md                    # cumulative round-by-round log
├── REVIEWER_MEMORY.md                # per-persona suspicions (hard/nightmare)
├── REVIEW_STATE.json                 # state for crash recovery
└── MANIFEST.md                       # every file written this run

traces/blog/20260428_103000_run01/
├── persona-h2-skimmer-round-1.prompt.txt
├── persona-h2-skimmer-round-1.response.txt
├── persona-mobile-first-reader-round-1.prompt.txt
└── ...
```

## Formats and personas

Specificity is the moat. Every persona is a real, specific, opinionated
reader — not "a generic VC" or "an SEO expert."

### Blog (`personas/blog/`)

| Persona | What they do |
|---------|--------------|
| `mobile-first-reader` | Reads on a phone, 300×600 viewport. Will scroll. |
| `seo-skeptic` | Checks H-tag structure, keyword density, meta-description. |
| `h2-skimmer` | Only reads H2s. If H2s don't tell the story, fails. |
| `target-icp` | The actual reader for this post (configurable per run). |

**Termination:** ≥75% personas score ≥6/10 AND verdict ∈ {ready, almost} AND verification passes.

### Social (`personas/social/`)

| Persona | What they do |
|---------|--------------|
| `scroller-08s` | 0.8 seconds of attention. Would they stop? |
| `reply-guy` | Looking for ratios, contradictions, easy dunks. |
| `algorithm-ranker` | Predicts engagement signals (replies > likes > shares). |
| `domain-expert` | Knows the topic. Checks for cringe, errors, oversimplification. |

**Termination:** all personas score ≥6/10 AND `scroller-08s` says "would not scroll past" AND verification passes (char count, hashtag count, link count).

### LinkedIn (`personas/linkedin/`)

| Persona | What they do |
|---------|--------------|
| `executive-recruiter` | Hiring manager. Would they DM you? |
| `cynical-scroller` | Sees through "broetry" and humble-brags. |
| `growth-hacker` | Measures hook strength + engagement bait quality. |
| `target-icp` | Your actual audience (configurable). |

**Termination:** ≥75% personas score ≥6/10 AND `executive-recruiter` says "would engage" AND verification passes.

### Business plan (`personas/business-plan/`)

| Persona | What they do |
|---------|--------------|
| `vc-partner` | Sequoia/a16z partner voice. Pattern-matches to fundable. |
| `unit-economics-skeptic` | CAC, LTV, payback, gross margin. Math has to hold. |
| `technical-cofounder` | Devil's advocate on technical claims. |
| `target-customer` | Would they actually buy this? |
| `competitor` | Incumbent CEO. How do they kill this? |

**Termination:** all personas ≥6/10 AND `vc-partner` says "would take meeting" AND `unit-economics-skeptic` says "math holds" AND verification passes (market sanity, financials).

### Application (`personas/application/`)

For job, YC/accelerator, grant, fellowship, grad-school, MBA, undergrad, and scholarship applications. Input is a markdown file of `## Q: <question>` headings with the user's drafted answers in the body. The skill **requires** a `--target=<type>` flag so the personas calibrate to the right reviewer (a YC partner is not a graduate admissions committee is not a hiring manager).

| Persona | What they do |
|---------|--------------|
| `selection-committee-skeptic` | Partner reading 200 apps in a weekend. Would they shortlist this? |
| `domain-bar-raiser` | Knows the claimed domain (ex-founder for YC, faculty for grad school, hiring manager for jobs). Can this person actually do what they claim? |
| `narrative-coherence` | Reads ALL answers as one document. Catches contradictions across questions. Does the application have a thesis? |
| `red-flag-detector` | Pattern-matches AI-slop, cliches ("passionate about", "ever since I was a child"), unanchored numbers, manufactured story arcs. |

**Targets supported:** `job`, `yc`, `accelerator`, `grant`, `fellowship`, `grad-school`, `mba`, `undergrad`, `scholarship`. Without `--target`, the skill asks once and refuses to default — silent defaults produce miscalibrated reviews.

**Termination:** ≥75% personas score ≥7/10 AND `selection-committee-skeptic` says `would_shortlist=true` AND verification passes (all answers present, within length limits, first sentence does not restate the question).

**Verification tool:** [`tools/verify_application.py`](tools/verify_application.py) — parses `## Q: ...` headings, optional `[max=N chars]` or `[max=N words]` annotations, and runs three structural checks per answer.

### CV / resume (`personas/cv/`)

For markdown CVs and resumes. Standard sections (`## Summary`, `## Experience`, `## Education`, `## Skills`, optional `## Projects`, `## Publications`).

| Persona | What they do |
|---------|--------------|
| `recruiter-6sec-scan` | 6-second scan in a stack of 80. What's the one thing they remember? |
| `hiring-manager-domain` | Knows the role. Can this candidate do the job, or did the work happen around them? |
| `ats-parser` | Greenhouse/Lever/Workday-style parsing. Catches table layouts, missing keywords, broken date formats. |
| `interview-prep-thief` | Picks the strongest claim and asks "ok, prove it in interview." Catches over-claiming. |

**Termination:** ≥75% personas score ≥7/10 AND `recruiter-6sec-scan` says `would_shortlist=true` AND verification passes.

**Verification tool:** [`tools/verify_cv.py`](tools/verify_cv.py) — checks page-length estimate, action-verb-first bullets, quantified-bullet ratio, cliche density, date-format consistency, tense consistency.

### Slides (`personas/slides/`)

For slide decks. Two input formats: **markdown slides** (Marp / Slidev / reveal.js convention — slides separated by `---` thematic breaks or by H1/H2 headings, speaker notes inside `<!-- ... -->` comments) and **`.pptx`** (parsed directly via stdlib `zipfile` + XML; no `python-pptx` dependency).

Requires a `--scenario=pitch|academic|internal` flag — the persona panel and thresholds differ sharply by audience. Without `--scenario`, the skill asks once and refuses to default.

**Pitch panel** (`--scenario=pitch`, e.g. seed-stage startup deck for investors):

| Persona | What they do |
|---------|--------------|
| `vc-partner-skim` | Partner reading 100+ decks/week. 90-second skim. Veto: would they forward this internally? |
| `exec-30s-skim` | Reads only the slide titles in order. If the title sequence does not deliver the wedge + ask, fails. |
| `density-skeptic` | Death-by-PowerPoint detector. Catches walls of text, "(cont.)" titles, slide-to-minute mismatch. |
| `presenter-coach` | Live-pitch dry run. Hook on slide 1, arc, notes on load-bearing slides, clean close. |

**Academic panel** (`--scenario=academic`, e.g. NeurIPS/SOSP/CHI talk, qualifying exam, dissertation defense):

| Persona | What they do |
|---------|--------------|
| `program-committee-skim` | Senior researcher / PC member. Veto: contribution clear by slide 3 AND evidence supports claims AND limitations named. |
| `back-of-room-reader` | Audience member in row 14 of the conference hall. Can the room read each slide in the time it's up? |
| `density-skeptic` | Slide-to-minute ratio against `--talk-length`. Equation overload, baseline omission. |
| `presenter-coach` | Talk-quality dry run. Contribution-stating opener and a memorable close. |

**Internal panel** (`--scenario=internal`, e.g. exec status, all-hands, team review):

| Persona | What they do |
|---------|--------------|
| `exec-30s-skim` | VP skim. Veto: title sequence delivers the thesis. |
| `back-of-room-reader` | All-hands or conference-room readability. |
| `density-skeptic` | Death-by-PowerPoint detector. |
| `presenter-coach` | Live-meeting dry run. |

**Termination** (per scenario):
- Pitch: `>=75%` personas at `>=7/10` AND `vc-partner-skim` says `would_forward_internally=true` AND `exec-30s-skim` says `title_story_holds=true` AND verification passes.
- Academic: `>=75%` personas at `>=7/10` AND `program-committee-skim` says contribution+evidence+limitations all hold AND verification passes.
- Internal: `>=75%` personas at `>=7/10` AND `exec-30s-skim` says `title_story_holds=true` AND verification passes.

**Verification tool:** [`tools/verify_slides.py`](tools/verify_slides.py) — slide count, max words/bullets per slide, title length, title uniqueness (catches "Background (cont.)"), speaker-notes coverage, agenda-or-close presence, claim-title ratio (claim-titles like "Latency dropped 40%" vs noun-titles like "Latency Improvements"). Stdlib-only; supports `.md`/`.txt` and `.pptx`.

→ Full schema and authoring guide: [docs/PERSONA_AUTHORING.md](docs/PERSONA_AUTHORING.md)

## Example output

After 2 rounds on a blog post, `review-stage/AUTO_REVIEW.md` looks like:

```markdown
# AUTO_REVIEW — drafts/shipping-fast.md

## Round 1 (2026-04-28T10:03:14)

| Persona | Score | Verdict |
|---------|-------|---------|
| mobile-first-reader | 4/10 | not ready |
| seo-skeptic | 6/10 | almost |
| h2-skimmer | 3/10 | not ready |
| target-icp (indie hackers) | 7/10 | almost |

**Verification:** all 4 links resolve. 3 H2s. 1842 words. PASS.

**Top weaknesses (cross-persona):**
1. CRITICAL — h2-skimmer: H2s read like a list of nouns ("The setup", "The
   approach", "The result"). Cannot reconstruct argument from skim.
2. CRITICAL — mobile-first-reader: opening 3 paragraphs are a meta-preamble.
   First concrete claim is line 47. Phone reader bounced at line 12.
3. MAJOR — seo-skeptic: title is "On shipping fast" — generic. No keyword.

**Actions taken this round:**
- Rewrote H2s as claim-bearing ("Cut design review from 2 days to 4 hours", ...)
- Cut first 3 paragraphs. New opener is the concrete claim from line 47.
- Retitled "How I cut design review by 80%".

## Round 2 (2026-04-28T10:14:02)

| Persona | Score | Verdict |
|---------|-------|---------|
| mobile-first-reader | 8/10 | ready |
| seo-skeptic | 7/10 | ready |
| h2-skimmer | 8/10 | ready |
| target-icp (indie hackers) | 8/10 | ready |

**Verification:** PASS.

**Status:** APPROVED. ≥75% personas at ≥6/10 with ready verdict. Verification clean.

→ review-stage/blog_approved_20260428_101400.md
```

## Why personas?

Adapted from the ARIS doctrine, framed for writing:

> Using a single model to review its own writing is the stochastic case —
> predictable noise, compounding blind spots. Cross-model review with
> persona-shaped reviewers is the adversarial case — the reviewer actively
> probes weaknesses the writer didn't anticipate. Adversarial bandits are
> fundamentally harder to game.
>
> Generic critique averages opinions and converges on bland. A "VC partner
> who pattern-matches to fundable" disagrees with a "unit-economics
> skeptic who needs CAC math" — that disagreement IS the signal. The draft
> survives both, or it doesn't ship.
>
> Two-or-more is the minimum to break self-review blind spots. Adding
> personas past 5 has diminishing returns and increases coordination cost
> (and API spend). The biggest gain is going from 1 → 4, not 4 → 12.

This is the same argument as ARIS, but for writing. The reviewer model is
GPT-5.4 xhigh because it's slow and rigorous; you (Claude) are fast and
fluid. Speed × rigor produces better outcomes than either alone.

## Backends

### v0.1 — Codex MCP only

The reviewer model is GPT-5.4 via the Codex MCP server (`mcp__codex__codex`),
with `model_reasoning_effort: xhigh`. This is the only supported backend in
v0.1. Setup in [docs/BACKEND_CONFIG.md](docs/BACKEND_CONFIG.md).

### v0.2+ roadmap

Planned backends, in rough priority order:

| Backend | Status | Notes |
|---------|--------|-------|
| Codex MCP (gpt-5.4 xhigh) | shipped | v0.1 default |
| OpenAI direct (via `llm-chat` MCP) | planned v0.2 | port from ARIS |
| DeepSeek-V3.5 | planned v0.2 | cheap reviewer for long-tail formats |
| MiniMax-M3 | planned v0.2 | port from ARIS |
| Local Ollama (Llama-4, Qwen-3) | planned v0.3 | offline mode |
| Anthropic Claude (cross-family) | planned v0.3 | when reviewer-as-Claude is desired |

Per-skill backend override (planned syntax):

```
/auto-blog-review-loop my_post.md --reviewer=deepseek
/auto-business-plan-review-loop pitch.md --reviewer=oracle-pro
```

## Repo layout

```
auto-essay-review-loop/
├── README.md                       # this file
├── AGENT_GUIDE.md                  # LLM-consumption version
├── VERSION                         # 0.1.0
├── LICENSE                         # MIT
├── CONTRIBUTING.md
├── skills/
│   ├── auto-essay-review-loop/     # umbrella dispatcher
│   ├── auto-blog-review-loop/
│   ├── auto-social-review-loop/
│   ├── auto-linkedin-review-loop/
│   ├── auto-business-plan-review-loop/
│   ├── auto-application-review-loop/
│   ├── auto-cv-review-loop/
│   ├── auto-slides-review-loop/
│   └── shared-references/          # loop contract, persona schema, etc.
├── personas/
│   ├── blog/
│   ├── social/
│   ├── linkedin/
│   ├── business-plan/
│   ├── application/
│   ├── cv/
│   └── slides/
├── tools/                          # verification scripts
├── templates/
│   └── BRAND_VOICE.template.md
├── tests/
│   ├── fixtures/                   # known-good and known-bad drafts
│   └── run_tests.sh
└── docs/
    ├── PERSONA_AUTHORING.md
    ├── BACKEND_CONFIG.md
    ├── EXAMPLES.md
    └── TROUBLESHOOTING.md
```

## Roadmap

- **v0.1.0** (now) — Codex MCP backend. 7 formats (blog, social, linkedin, business-plan, application, cv, slides). 31 personas. Verification
  layer (incl. `.pptx` parser via stdlib zipfile/XML). State recovery. Brand voice protocol.
- **v0.2.0** — Multi-backend (DeepSeek, MiniMax, OpenAI direct). Reviewer
  difficulty modes (`hard`, `nightmare`).
- **v0.3.0** — Local Ollama backend. Offline mode. Persona contribution
  workflow. Cross-format projects (e.g., long-form post → tweet thread →
  LinkedIn version, all reviewed coherently).
- **v0.4.0** — Voice-fingerprint detection (your draft auto-loads
  `BRAND_VOICE.md` if your prior posts are in the repo).

## Credits and license

MIT. See [LICENSE](LICENSE).

Built on the [ARIS](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep)
pattern by Yuxuan Cao. ARIS is the parent project — it does this same loop
for academic research papers. This repo ports the doctrine to non-academic
writing.

If you ship something with this loop, drop a note in an issue. We are
collecting persona contributions and example output for v0.2.

---

> *The reviewer doesn't care about your feelings. That is the entire point.*
