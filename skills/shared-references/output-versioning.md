# Output Versioning Protocol

Every artifact this skill writes must follow the timestamped-then-aliased pattern.

## Rule

Write a timestamped file FIRST, then copy to a fixed-name alias. Never overwrite the timestamped file.

## Pattern

```bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
TIMESTAMPED="review-stage/blog_approved_${TIMESTAMP}.md"
ALIAS="review-stage/blog_approved.md"

# Write timestamped first
cp draft.md "$TIMESTAMPED"

# Then update alias
cp "$TIMESTAMPED" "$ALIAS"
```

## Why

- `_approved.md` always points to the latest approved version (convenient)
- `_approved_{ts}.md` files are an audit trail (never lost)
- Recovery: if `_approved.md` is corrupted, the most recent `_approved_*.md` is the source of truth

## Files this protocol applies to

- `{format}_approved_{ts}.md` ↔ `{format}_approved.md`
- `AUTO_REVIEW_round{N}_{ts}.md` ↔ `AUTO_REVIEW.md` (the cumulative log appends; rounds don't get timestamped aliases)
- `REVIEWER_MEMORY_{ts}.md` ↔ `REVIEWER_MEMORY.md` (snapshot at end of run only)

## Files this does NOT apply to

- `REVIEW_STATE.json` — overwrite each round; only latest matters (recovery is from latest, not history)
- Trace files — already timestamped by directory structure
