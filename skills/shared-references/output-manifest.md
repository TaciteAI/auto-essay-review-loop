# Output Manifest Protocol

Every output file the skill writes must be logged to `review-stage/MANIFEST.md`
with one row per file. This is the audit log a reader uses to navigate the run.

## Format

```markdown
# Run Manifest

| Timestamp | File | Phase | Description |
|-----------|------|-------|-------------|
| 2026-04-28T10:00:00 | review-stage/REVIEW_STATE.json | Init | Initial state, round=1 |
| 2026-04-28T10:01:23 | traces/blog/20260428_100000_run01/persona-h2-skimmer-round-1.prompt.txt | A1 | Reviewer prompt to h2-skimmer |
| 2026-04-28T10:01:45 | traces/blog/20260428_100000_run01/persona-h2-skimmer-round-1.response.txt | A1 | Raw response from h2-skimmer |
| ... | ... | ... | ... |
| 2026-04-28T10:14:02 | review-stage/blog_approved_20260428_101400.md | Term | Final approved draft |
| 2026-04-28T10:14:02 | review-stage/blog_approved.md | Term | Alias to latest approved |
```

## Rule

Append a row IMMEDIATELY after writing the file, not at end of round. If the
loop is killed mid-round, the manifest still tells you what got written.

## Phase codes

- `Init` — initialization
- `A{N}` — Phase A round N (review)
- `B{N}` — Phase B round N (parse)
- `B5` / `B6` / `B7` — sub-phases
- `C{N}` — Phase C round N (fixes)
- `E{N}` — Phase E round N (document)
- `Term` — termination

## Recovery use

When resuming after compaction, read MANIFEST.md to reconstruct what was
already written without re-doing work.
