# Reviewer Independence Protocol

The reviewer must be context-naive on every round. Prior-round summaries,
fix lists, and author explanations are not evidence; they are a source of
confirmation bias. If the reviewer is told what changed, scores tend to
drift upward even when the artifact has not materially improved.

This protocol is adapted from ARIS, where empirical evidence (April 2026)
showed running the same paper with `codex-reply` + "since last round we
did X" prompts inflated scores from real 3/10 → fake 8/10 across 5 rounds.
Switching to fresh threads recovered the true 3/10 assessment.

## Rules

1. Every round starts with `mcp__codex__codex` (NOT `mcp__codex__codex-reply`).
2. Never pass a prior-round threadId into the next review prompt.
3. Never include "since last round", "we fixed", "after applying", or any
   fix summary in the reviewer prompt.
4. The only acceptable evidence of improvement is the current draft itself.
5. If a fix cannot be observed in the draft, the reviewer should not be told it happened.
6. Save threadIds only for crash recovery — never to preserve review context.

## Exception: Reviewer Memory (`hard` / `nightmare` difficulty)

When `REVIEWER_DIFFICULTY = hard` or `nightmare`, the persona DOES carry
memory across rounds — but only its OWN memory of suspicions, not the
author's narrative of fixes. The memory file is the persona's audit trail,
not a summary of what the author claims to have done.

Pattern:
- Persona writes its own memory at end of each round (Phase B.5)
- Memory is prepended to the next round's prompt as "Your prior suspicions"
- The author CANNOT edit persona memory
- The author's claims about fixes are NEVER in the prompt — only the new draft

This preserves independence (no author narrative bias) while letting the
persona track patterns of weakness ("the author keeps glossing over the
unit economics question").

## Override

Set `REVIEWER_BIAS_GUARD = false` in skill constants only for deliberate
debugging of the legacy context-carrying behavior. Default is `true`.
