# Troubleshooting

Common failure modes and what to do. If your symptom is not here, open an
issue with: the format, the round it failed at, the relevant slice of
`AUTO_REVIEW.md`, and the offending `traces/.../*.response.txt`.

## Reviewer returns malformed JSON

**Symptom:** `traces/.../persona-X-round-N.response.txt` contains prose,
markdown fences around the JSON, or a partial object. Skill logs say
`INCONCLUSIVE` for that persona.

**Why:** GPT-5.4 occasionally adds a preamble ("Here's my review...") or
wraps the JSON in ```` ```json ```` fences. Long persona system prompts
sometimes blow past the model's "JSON only" instruction.

**What the skill does automatically:** retries the persona once with a
stricter format instruction injected ("OUTPUT ONLY JSON. NO PROSE. NO
FENCES. NO PREAMBLE.").

**What to do if it persists:**

1. Read the actual response file. If you see prose at all, the persona's
   system prompt has too much going on — trim. Move secondary instructions
   to the user prompt.
2. If the response is truncated mid-JSON, the prompt + draft is too long
   for the reviewer's context window. Trim the persona's "what they look
   for" section, or if the draft itself is huge, run with
   `--summarize-draft=true` (planned, not in v0.1).
3. Check Codex MCP connectivity: `claude mcp list`. If `codex` is not
   listed as `running`, restart it.

If 2+ personas malformat in the same round, suspect a Codex-side issue
(rate limit, model rollover, etc.) and re-run.

## Score divergence between personas

**Symptom:** in the same round, `vc-partner` scores 8/10 and
`unit-economics-skeptic` scores 3/10. Or `growth-hacker` says 9/10 but
`cynical-scroller` says 2/10.

**This is not a bug.** It's the entire point.

**Why:** persona disagreement IS the signal. The personas are calibrated to
different bars. A draft that delights `growth-hacker` (engagement bait
quality) will sometimes offend `cynical-scroller` (sees through engagement
bait). That's a real tension in the draft — the loop surfaced it.

**What to do:**

1. **Read both raw responses.** Often the disagreement is locatable to a
   specific paragraph. The `growth-hacker` likes the hook; the
   `cynical-scroller` thinks the hook is a tell. Decide which audience
   matters more and write to them.
2. **The conflict-resolution rule (Phase C, loop-contract.md) breaks ties
   in favor of the format's primary success metric.** For LinkedIn, that's
   engagement → growth-hacker tends to win. For business plans, that's
   rigor → unit-economics-skeptic tends to win.
3. **If the spread is consistent across rounds (e.g., always 8 vs 3), your
   draft has an unresolved core tension.** Two audiences want different
   posts. Either commit to one or split into two drafts.

The loop won't terminate while ANY persona scores below the format's bar
(see termination criteria in loop-contract.md). If round 4 ends with
divergence, the per-persona blocker list in the final `AUTO_REVIEW.md`
section tells you exactly who's holding you up.

## Loop doesn't terminate at MAX_ROUNDS

**Symptom:** round 4 ends, the skill writes a "stopped at MAX_ROUNDS without
consensus" footer, one or two personas keep rejecting.

**Diagnosis path:**

1. **Read the persistent rejector's `REVIEWER_MEMORY.md` entries** (only
   present if you ran `--difficulty=hard` or `nightmare`). The memory file
   shows what the persona has been suspicious of across rounds. Often the
   pattern is something the author didn't address — they fixed the surface
   issue but not the underlying one.
2. **Read the persona's last few raw responses.** Look for a phrase that
   recurs. "The wedge is still unclear." "The CAC math still doesn't
   close." "The hook is better but the payoff is still buried." That
   recurrence is the actual unresolved problem.
3. **Check whether the persona's bar is reasonable for this format.**
   Sometimes a persona designed for one shape of content gets applied to
   the wrong shape (e.g., `unit-economics-skeptic` applied to a Series A
   product launch where rigor is appropriate, vs. an angel teaser where
   it's overkill). The per-format roster shouldn't have this issue, but
   custom configs can.
4. **Consider whether the persona is right.** If `unit-economics-skeptic`
   keeps saying the math doesn't close, the math probably doesn't close.
   The persona is doing its job. Fix the math or accept that the draft
   isn't ready.

**Escape hatches:**

- Re-run with `--difficulty=medium` to drop reviewer memory. Lighter bar.
  Use only when you've decided the persona is overcalibrated for this
  draft, not when you're trying to dodge a real problem.
- Edit the persona — make its bar appropriate for your actual audience.
- Drop the persona for this run (skills accept `--exclude-persona=name`).
  Document why in the manifest.

The skill exits gracefully at MAX_ROUNDS — your draft + AUTO_REVIEW.md
+ MANIFEST.md are intact. Nothing was destroyed. You can resume manually.

## Verification false positives

**Symptom:** `verify_links.sh` reports a link as broken, but you can open
it in a browser. Or `market_size_check.py` flags a TAM you've grounded
correctly.

### Broken-link false positives

The most common cause is transient 5xx from rate limits, cloudflare
challenges, or the target site being briefly down. The link is real;
the check fired during a hiccup.

**Fixes:**

1. **Re-run.** Easiest. The check passes the second time in ~80% of cases.
2. **Add to allowlist.** Create or edit `.linkcheck-allowlist` in the
   project root with one URL pattern per line. The skill's verification
   reads this and skips matched URLs. Use sparingly — every allowlisted
   URL is one you've decided not to check.
3. **Check the response code in the JSON output.** 503 / 429 / 500 are
   transient; 404 / 410 / 301-loop are real. The skill marks them
   differently in `verify_links.json`.

### Market-size false positives

If `market_size_check.py` flags `fantasy_tam` on a real TAM, the issue is
usually one of:

- TAM stated without source (the script wants a citation or a methodology
  paragraph nearby)
- TAM > $5T (the script's hard cap; override with `--max-tam=10T` if you
  have actual reason)
- TAM, SAM, SOM not in decreasing order (e.g., SAM > TAM is a reasoning bug)

The script outputs `flags` in its JSON. Each flag tells you specifically
what triggered. If you disagree, you can:

1. Re-write the section so the script picks up the citation.
2. Use `--skip-verification=market_size` (planned for v0.2; in v0.1, edit
   the verification config in the format skill).

## Skill says "draft hash mismatch" on resume

**Symptom:** you re-invoke the skill on the same draft, expecting it to
resume from round 3, but it warns:
`draft has been modified since last round. Restart from round 1?`

**Why:** the loop contract requires that the draft NOT change between
rounds without the loop's knowledge. If you edited the draft manually
between round 2 and the resume attempt, the hash check catches it.

**What to do:**

1. **If you intentionally edited the draft**, accept the restart. The prior
   rounds were against a different artifact; resuming doesn't make sense.
2. **If you didn't intentionally edit it**, check whether your editor
   re-saved the file with different line endings or trailing whitespace.
   Run `git diff` on the draft. If the diff is whitespace-only, the loop
   is being overly strict — you can override with `--ignore-draft-hash`
   (planned v0.2) or just accept the restart.

## Loop runs but no fixes are applied (Phase C is empty)

**Symptom:** round completes, scores were low, weaknesses were identified,
but the draft is unchanged after Phase C. Round N+1 starts with the same
draft.

**Why:** Phase C skips fixes that "require external data we don't have."
This includes:

- Fixes that ask for new statistics, citations, or quotes the loop can't
  source.
- Fixes that ask for content the author needs to provide (e.g., "add a
  case study from your most recent client").
- Fixes flagged as out-of-scope by Phase C's safety check.

These get logged in `AUTO_REVIEW.md` under "skipped fixes — manual
follow-up." The skill is supposed to mention this in the round summary.

**What to do:**

1. **Check the AUTO_REVIEW.md round entry's "skipped fixes" section.**
2. **Hand-edit the draft to address those.** Then re-run; the loop will
   pick up.
3. **If Phase C is skipping fixes it shouldn't**, the persona's `fix`
   field is too vague. Personas should write fixes as specific edits, not
   "add more depth here."

## Reviewer memory is stale across runs

**Symptom:** running `--difficulty=hard` on a fresh draft pulls in
suspicions from a different document.

**Why:** `REVIEWER_MEMORY.md` is per-project. If you switch drafts in the
same `review-stage/` directory without cleaning up, memory leaks across.

**Fix:** delete `review-stage/REVIEWER_MEMORY.md` (and `REVIEW_STATE.json`)
before the new run, OR run from a different working directory.

## Brand-voice false positive

**Symptom:** persona reports `voice_drift: true` for a phrase that's
actually in your `BRAND_VOICE.md` allowed list.

**Why:** `BRAND_VOICE.md` parsing is loose in v0.1. The "allowed phrases"
section is hint-text for the persona; it's not a strict regex match.

**Fix:** edit `BRAND_VOICE.md` to make the allowed phrases more prominent
(under a clearer heading), or add an "Examples that ARE this voice" block
showing the phrase in context.

## Loop is way too slow

**Symptom:** a single round takes 30+ minutes.

**Why:** GPT-5.4 xhigh is slow. Long drafts (>3000 words) compound.
Parallel persona dispatch helps but doesn't change per-call latency.

**Mitigations:**

1. Use `--parallel-personas=true` (default in v0.1) — this is already on.
2. Use `--difficulty=medium` (default) — `hard`/`nightmare` add memory and
   debate phases that double round time.
3. Trim the draft. If it's 4500 words and you're doing a tight blog
   review, the draft itself is over the format's word target.
4. Wait for v0.2 — `--reviewer=deepseek` will be ~3x faster.

## Backend not responding

**Symptom:** Phase A hangs. No `traces/.../*.response.txt` files appear.

**Diagnosis:**

```bash
claude mcp list
# Should show: codex   codex mcp-server   running
```

If Codex isn't running:

```bash
# Restart it
claude mcp remove codex
claude mcp add codex -s user -- codex mcp-server
claude mcp list   # verify
```

If Codex is running but calls hang, check `~/.codex/logs/` for errors
(Codex CLI logs there). Common causes: OpenAI rate limit, expired API
credential, network blip.

## Manifest missing rows

**Symptom:** `MANIFEST.md` has rows for rounds 1-2 but not round 3, even
though round 3 wrote files.

**Why:** the skill is supposed to append a manifest row immediately after
writing a file. If the loop crashed between writing a file and writing
its manifest row, you'll see this drift.

**Recovery:** the files exist; only the bookkeeping is stale. Re-run the
skill — the recovery logic resumes from `REVIEW_STATE.json` and rebuilds
the manifest from `traces/` and `review-stage/` contents.
