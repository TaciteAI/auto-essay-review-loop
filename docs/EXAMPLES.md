# Examples

End-to-end walkthroughs for each format. Console output and artifact
contents are illustrative — your actual run will differ. Persona scores
reflect what the loop tends to produce on drafts of these shapes; they are
not guaranteed.

## Contents

1. [Blog post — "How I cut design review by 80%"](#blog-post)
2. [Social — X post](#social-x-post)
3. [LinkedIn — career-arc post](#linkedin-career-arc-post)
4. [Business plan — pre-seed memo](#business-plan-pre-seed-memo)

---

## Blog post

### Invocation

```
$ /auto-essay-review-loop drafts/shipping-fast.md
```

### Console output

```
Detected: blog (1842 words, 5 H2s, no business-plan markers) — dispatching to auto-blog-review-loop.

[auto-blog-review-loop] Round 1 of 4 starting (2026-04-28T10:03:00)
[auto-blog-review-loop] Loaded 4 personas: mobile-first-reader, seo-skeptic, h2-skimmer, target-icp
[auto-blog-review-loop] BRAND_VOICE.md detected — loading
[auto-blog-review-loop] Phase A: dispatching reviews (parallel)
  → mobile-first-reader: thread 019cd... started
  → seo-skeptic: thread 019ce... started
  → h2-skimmer: thread 019cf... started
  → target-icp: thread 019d0... started
[auto-blog-review-loop] Phase B: parsing responses
  ✓ mobile-first-reader: score 4/10, verdict "not ready"
  ✓ seo-skeptic: score 6/10, verdict "almost"
  ✓ h2-skimmer: score 3/10, verdict "not ready"
  ✓ target-icp: score 7/10, verdict "almost"
[auto-blog-review-loop] Phase B.7: verification
  ✓ verify_links.sh: 4/4 links resolve
  ✓ word count: 1842 (within 500-4000)
  ✓ H-tag structure: valid
[auto-blog-review-loop] Termination check: 1/4 personas at ≥6 with verdict ∈ {ready,almost} — 25%, need 75%. Continuing.
[auto-blog-review-loop] Phase C: implementing 8 fixes (3 CRITICAL, 4 MAJOR, 1 MINOR)
  → Rewrote 5 H2s as claim-bearing (h2-skimmer fix)
  → Cut first 3 paragraphs, opened with concrete claim (mobile-first-reader fix)
  → Retitled "How I cut design review by 80%" (seo-skeptic fix)
  → ... 5 more
[auto-blog-review-loop] Phase D: re-running link check (no link edits — skip re-render)
[auto-blog-review-loop] Phase E: appended round 1 to AUTO_REVIEW.md, state written

[auto-blog-review-loop] Round 2 of 4 starting (2026-04-28T10:11:24)
[auto-blog-review-loop] Phase A: dispatching reviews (parallel)
  → mobile-first-reader: thread 019d4... started (FRESH — no carryover)
  → seo-skeptic: thread 019d5... started (FRESH)
  → h2-skimmer: thread 019d6... started (FRESH)
  → target-icp: thread 019d7... started (FRESH)
[auto-blog-review-loop] Phase B: parsing
  ✓ mobile-first-reader: score 8/10, verdict "ready"
  ✓ seo-skeptic: score 7/10, verdict "ready"
  ✓ h2-skimmer: score 8/10, verdict "ready"
  ✓ target-icp: score 8/10, verdict "ready"
[auto-blog-review-loop] Phase B.7: verification PASS
[auto-blog-review-loop] Termination: 4/4 at ≥6, all "ready" — APPROVED.

→ review-stage/blog_approved_20260428_101400.md
→ review-stage/blog_approved.md (alias)
→ review-stage/AUTO_REVIEW.md (full log)
→ review-stage/MANIFEST.md (37 files written)

Total: 2 rounds, 11 minutes, 8 fixes, 8 reviewer calls.
```

### `review-stage/AUTO_REVIEW.md` excerpt

```markdown
# AUTO_REVIEW — drafts/shipping-fast.md

## Round 1 (2026-04-28T10:03:14)

### Per-persona scores

| Persona | Score | Verdict |
|---------|-------|---------|
| mobile-first-reader | 4/10 | not ready |
| seo-skeptic | 6/10 | almost |
| h2-skimmer | 3/10 | not ready |
| target-icp (indie hackers) | 7/10 | almost |

### Verification layer

- [x] All links resolve (4/4)
- [x] Word count: 1842 (target 500–4000)
- [x] H-tag structure valid
- [x] No unclosed code fences

### Top weaknesses (cross-persona, ranked)

1. **CRITICAL** — `h2-skimmer`: H2s read like a list of nouns ("The setup",
   "The approach", "The result"). I cannot reconstruct the argument from
   the H2s alone. Fix: rewrite each H2 as a claim or a concrete number.
2. **CRITICAL** — `mobile-first-reader`: opening 3 paragraphs are
   meta-preamble ("In this post I'll explain..."). First concrete claim
   is line 47. I bounced at line 12. Fix: cut the preamble, open with the
   claim.
3. **MAJOR** — `seo-skeptic`: title "On shipping fast" is generic. No
   keyword targeting. Fix: lead with the outcome ("How I cut design review
   by 80%").
4. **MAJOR** — `h2-skimmer`: section "The result" has no number in the H2.
   The whole post is about a number — put it in the H2.
5. **MAJOR** — `mobile-first-reader`: code blocks are 12 lines wide;
   horizontal scroll on mobile. Wrap or restructure.
6. **MINOR** — `target-icp`: "indie hacker" appears once in para 4; should
   appear in title or first paragraph.

### Reviewer raw responses

<details>
<summary>mobile-first-reader (score 4/10)</summary>

```json
{
  "score": 4,
  "verdict": "not ready",
  "would_scroll_past": true,
  "weaknesses": [
    {"severity": "CRITICAL", "issue": "Opening 3 paragraphs are
     meta-preamble. First concrete claim is line 47.",
     "fix": "Cut the preamble. Open with the claim from line 47."},
    ...
  ],
  "summary": "Bounced at line 12 on my phone. The hook is 'In this post
  I'll explain...' — that's not a hook, that's a table of contents. Open
  with the number."
}
```
</details>

<details>
<summary>h2-skimmer (score 3/10)</summary>
[verbatim response]
</details>

### Actions taken this round

1. Rewrote H2s:
   - "The setup" → "Cut design review from 2 days to 4 hours"
   - "The approach" → "Three rules: ship every Friday, no design crit, ..."
   - "The result" → "80% faster reviews, zero quality drop"
   - "The lessons" → "Why we'll keep doing this even when it scales"
   - "Wrapping up" → (cut entirely)
2. Cut paragraphs 1-3. New opener (line 47 promoted to line 1).
3. Retitled "How I cut design review by 80% (and why it scales)".
4. Wrapped 3 wide code blocks for mobile.
5. Added "indie hacker" to first paragraph.

### Status

→ continuing → round 2

---

## Round 2 (2026-04-28T10:14:02)

### Per-persona scores

| Persona | Score | Verdict |
|---------|-------|---------|
| mobile-first-reader | 8/10 | ready |
| seo-skeptic | 7/10 | ready |
| h2-skimmer | 8/10 | ready |
| target-icp (indie hackers) | 8/10 | ready |

### Verification layer

PASS (all checks).

### Top weaknesses (cross-persona)

- **MINOR** — `seo-skeptic`: meta description is 162 chars (target ≤155).
  Auto-trimmed.

### Status

→ APPROVED. 4/4 personas at ≥6, all verdicts "ready", verification clean.

→ review-stage/blog_approved_20260428_101400.md
```

### Approved-draft diff (excerpt)

```diff
- # On shipping fast
-
- In this post I'll explain how my team and I cut design review time. We
- went through several iterations and learned a lot along the way. I want
- to share what worked and what didn't so other indie hackers can avoid
- the same pitfalls.
-
- ## The setup
+ # How I cut design review by 80% (and why it scales)
+
+ As an indie hacker shipping weekly, design review was eating two full
+ days. We got it down to four hours without losing quality. Here's the
+ exact change.
+
+ ## Cut design review from 2 days to 4 hours
```

---

## Social — X post

### Invocation

```
$ /auto-essay-review-loop drafts/tweet.txt
```

### Console output

```
Detected: social/x (247 chars, no headings, no hashtags) — dispatching to auto-social-review-loop.

[auto-social-review-loop] Round 1 of 3 starting
[auto-social-review-loop] Personas: scroller-08s, reply-guy, algorithm-ranker, domain-expert
[auto-social-review-loop] Phase A: parallel reviews
  ✓ scroller-08s: 5/10 ("would scroll past")
  ✓ reply-guy: 7/10 ("nothing to dunk on, dry")
  ✓ algorithm-ranker: 4/10 ("low engagement signals")
  ✓ domain-expert: 8/10 ("technically correct")
[auto-social-review-loop] Phase B.7: verification
  ✓ count_chars: 247/280 — PASS
  ✓ hashtag count: 0/3 — PASS
  ✓ link count: 0/1 — PASS
[auto-social-review-loop] Termination: scroller-08s says "would scroll past" — fail.
[auto-social-review-loop] Phase C: implementing fixes (1 CRITICAL, 2 MAJOR)

Round 2:
  ✓ scroller-08s: 7/10 ("would not scroll past — hook lands")
  ✓ reply-guy: 7/10
  ✓ algorithm-ranker: 7/10 ("better hook + concrete number")
  ✓ domain-expert: 8/10
[auto-social-review-loop] Termination: APPROVED.

→ review-stage/social_approved_20260428_103201.txt
```

### `review-stage/AUTO_REVIEW.md`

```markdown
# AUTO_REVIEW — drafts/tweet.txt (X)

## Round 1

| Persona | Score | Verdict | Notes |
|---------|-------|---------|-------|
| scroller-08s | 5/10 | not ready | would scroll past |
| reply-guy | 7/10 | almost | "boring, no easy ratio" |
| algorithm-ranker | 4/10 | not ready | predicts low engagement |
| domain-expert | 8/10 | ready | technically correct |

### Verification: PASS (247/280 chars)

### Top weaknesses
1. CRITICAL — scroller-08s: opens with "I think...". Three words wasted.
   The thumb keeps moving.
2. MAJOR — algorithm-ranker: no question, no concrete number, no contrast.
   Engagement signal score 0.31. Replace with a hook that triggers a reply.
3. MAJOR — scroller-08s: 247 chars but the payoff is in the last 80. Move
   it.

### Actions
- Rewrote opening: "I think most people..." → "Most founders waste 4 hours/week..."
- Moved the punchline (a concrete contrast) to chars 1-80.
- Added a one-line provocation at the end.

## Round 2 — APPROVED
```

### Approved-draft diff

```diff
- I think most people who run startups don't realize that the way they
- handle their inbox actually compounds. If you spend 4 hours a week
- triaging email, that's 200 hours a year, which is basically a month of
- full-time work going to a low-leverage activity. Worth fixing.
+ Most founders burn 4 hrs/week on email triage.
+ That's 200 hrs/year. A full month of work. On inbox.
+ The fix takes 30 minutes and 3 filters.
+ Why isn't this taught?
```

---

## LinkedIn — career-arc post

### Invocation

```
$ /auto-essay-review-loop drafts/li_post.md
```

### Console output

```
Detected: linkedin (2841 chars, 2 hashtags, no H1/H2) — dispatching to auto-linkedin-review-loop.

[auto-linkedin-review-loop] Round 1 of 4 starting
[auto-linkedin-review-loop] Personas: executive-recruiter, cynical-scroller, growth-hacker, target-icp
[auto-linkedin-review-loop] Phase A: parallel reviews
  ✓ executive-recruiter: 6/10 ("would consider engaging")
  ✓ cynical-scroller: 3/10 ("classic broetry; humble-brag detected")
  ✓ growth-hacker: 7/10 ("hook is decent, story arc fine")
  ✓ target-icp (PMs): 5/10 ("relatable but not actionable")
[auto-linkedin-review-loop] Phase B.7: verification
  ✓ char count: 2841/3000 — PASS
  ✓ hook (first 2 lines): 187/210 chars — PASS
  ✓ hashtag count: 2/5 — PASS
  ✓ link count: 0/1 — PASS
[auto-linkedin-review-loop] Termination: executive-recruiter says "would engage" but cynical-scroller score <6. Fail.

Round 2:
  ✓ executive-recruiter: 8/10 ("would DM")
  ✓ cynical-scroller: 6/10 ("less broetry, accepts the framing")
  ✓ growth-hacker: 8/10
  ✓ target-icp: 7/10 ("now there's a takeaway")
[auto-linkedin-review-loop] Termination: APPROVED.
```

### `review-stage/AUTO_REVIEW.md` excerpt

```markdown
## Round 1

| Persona | Score | Verdict | would_engage |
|---------|-------|---------|--------------|
| executive-recruiter | 6/10 | almost | maybe |
| cynical-scroller | 3/10 | not ready | n/a |
| growth-hacker | 7/10 | almost | n/a |
| target-icp (PMs) | 5/10 | not ready | n/a |

### Top weaknesses
1. CRITICAL — cynical-scroller: line 4 ("I was humbled to learn...") is
   textbook humble-brag. I see this 12 times a day. Cut.
2. MAJOR — target-icp: post tells a story but the takeaway is "be
   curious." Not actionable. PMs need the actual heuristic.
3. MAJOR — cynical-scroller: paragraph 6 lists 5 things in single-line
   broetry format. Either commit to a list or write prose.
4. MAJOR — executive-recruiter: no hint of what kind of role you're open
   to. If I want to DM you, what role am I pitching?

### Actions
- Cut the "I was humbled" line. Replaced with the concrete lesson.
- Added explicit heuristic at the end: "Heuristic: if the spec has 5+
  must-haves, the PM hasn't picked yet."
- Reformatted broetry paragraph as a 3-item numbered list.
- Added one-line bio footer: "PM at <company>. Looking to talk to founders
  building tools for PMs."
```

### Approved-draft diff (excerpt)

```diff
- I was humbled to learn that the best PMs I've worked with all share
- one trait.
-
- Curiosity.
+ The best PMs I've worked with all share one trait: they reduce the
+ must-haves. Aggressively.
```

---

## Business plan — pre-seed memo

### Invocation

```
$ /auto-essay-review-loop drafts/preseed_memo.md --difficulty=hard
```

### Console output

```
Detected: business-plan ($2B TAM, exec-summary structure) — dispatching to auto-business-plan-review-loop.

[auto-business-plan-review-loop] Round 1 of 5 starting
[auto-business-plan-review-loop] Personas: vc-partner, unit-economics-skeptic, technical-cofounder, target-customer, competitor
[auto-business-plan-review-loop] Difficulty: hard (memory + debate enabled)
[auto-business-plan-review-loop] Phase A: parallel reviews
  ✓ vc-partner: 5/10 ("would not take meeting; wedge unclear")
  ✓ unit-economics-skeptic: 3/10 ("CAC unknown, payback unknown")
  ✓ technical-cofounder: 6/10 ("AI claims plausible but unverified")
  ✓ target-customer (mid-market HR lead): 4/10 ("buying process not addressed")
  ✓ competitor (Workday): 7/10 ("we'd ship this in a quarter; they have no moat")
[auto-business-plan-review-loop] Phase B.5: writing reviewer memory
[auto-business-plan-review-loop] Phase B.6: debate protocol — author may rebut
  [skipped — auto-mode, no rebuttals submitted]
[auto-business-plan-review-loop] Phase B.7: verification
  ✗ market_size_check: TAM=$2B PASS, but SAM=$2B (= TAM) — flag "sam_equals_tam"
  ✓ unit-economics-presence: 1 of 5 metrics mentioned (LTV) — flag "weak_unit_economics"
  ✓ section presence: all 8 required sections present
  ✓ financial completeness: 12-mo present, 3-yr missing — flag "no_long_term_projection"
[auto-business-plan-review-loop] Verification: 3 hard flags. Cannot approve.

Round 2 (after fixes): scores 6/4/7/5/7
Round 3 (after fixes): scores 7/6/7/6/6
[auto-business-plan-review-loop] Round 3 termination check:
  All personas ≥6: ✓
  vc-partner says "would take meeting": ✓
  unit-economics-skeptic says "math holds": ✓ (after CAC and payback added)
  Verification: PASS
  → APPROVED.
```

### `review-stage/AUTO_REVIEW.md` excerpt

```markdown
## Round 1

| Persona | Score | Verdict | would_take_meeting / math_holds |
|---------|-------|---------|----------------------------------|
| vc-partner | 5/10 | not ready | would_take_meeting: false |
| unit-economics-skeptic | 3/10 | not ready | math_holds: false |
| technical-cofounder | 6/10 | almost | n/a |
| target-customer | 4/10 | not ready | n/a |
| competitor (Workday) | 7/10 | almost | n/a |

### Verification (3 hard flags)
- ✗ sam_equals_tam (SAM=$2B = TAM=$2B; SAM should narrow)
- ✗ weak_unit_economics (only LTV mentioned; need ≥2 of {CAC, LTV, payback, gross margin, churn})
- ✗ no_long_term_projection (12-mo present; 3-yr missing)

### Top weaknesses (cross-persona)
1. CRITICAL — vc-partner: wedge is "HR for mid-market." That's not a
   wedge, that's a category. Pick one job for one user.
2. CRITICAL — unit-economics-skeptic: no CAC, no payback, no gross margin.
   "We expect LTV of $30K" is a wish, not a number.
3. CRITICAL — verification: SAM = TAM. Either the SAM is wrong or you
   don't understand TAM/SAM/SOM.
4. MAJOR — target-customer: I'm an HR lead at a 400-person company. How
   does this get into my org? RFP? Bottom-up? Not addressed.
5. MAJOR — competitor (Workday): you call us "legacy and slow." We have
   18,000 customers. What's your defense when we ship a feature in 90 days?

### Reviewer memory (round 1 → round 2)

#### vc-partner — Round 1 — Score: 5/10
- **Suspicion**: founder is selling a category, not a product.
- **Unresolved**: wedge undefined.
- **New patterns**: 3 different "primary" customers across the deck.

#### unit-economics-skeptic — Round 1 — Score: 3/10
- **Suspicion**: numbers are aspirational.
- **Unresolved**: no CAC, no payback.

[memory carried into round 2 prompts]

## Round 3 — APPROVED
```

### Approved-draft diff (executive summary section)

```diff
- ## Executive Summary
-
- WorkflowAI is an AI-powered HR automation platform for mid-market companies.
- We are targeting a $2B TAM with proprietary AI agents that automate
- repetitive HR workflows.
+ ## Executive Summary
+
+ WorkflowAI automates onboarding for HR teams at 100-500-person SaaS
+ companies. The wedge is the first-week new-hire checklist — currently
+ done in 4 disconnected tools. We charge $12/seat/mo. CAC is $640 (3
+ paid pilots), payback is 5.3 months, gross margin is 78%.
+
+ TAM (HR software, mid-market): $42B
+ SAM (workflow-automation segment): $4.1B
+ SOM (3-yr capture, 100-500 employee SaaS): $180M
```

---

## Cross-format observations

A few patterns to notice across these examples:

1. **Round 1 always finds something.** If round 1 returns scores ≥7
   across the board, your draft is either genuinely strong OR your
   personas are too soft. Tune them.
2. **Verification flags are hard.** No amount of persona praise overrides
   `sam_equals_tam`. The math has to be there.
3. **The fix in round N is usually the unblock for round N+1.** When
   `scroller-08s` says "would scroll past" and you rewrite the hook, the
   recovery is sharp. 5 → 7 in a single round is normal.
4. **Difficulty=hard adds memory + debate.** Personas track suspicions
   across rounds and become harder to trick. Use for high-stakes drafts
   (pitch decks, viral candidates).
5. **The audit trail is the artifact.** `AUTO_REVIEW.md` is what you read
   if 6 months later you want to know why a paragraph is the way it is.
   Keep it. Commit it.

For more, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
