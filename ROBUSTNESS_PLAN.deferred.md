<!-- /autoplan restore point: ~/.gstack/projects/ycaophysics-auto-essay-review-loop/master-autoplan-restore-20260428-232540.md -->

# Robustness Improvement Plan — auto-essay-review-loop v0.2

**Source of inspiration:** `Auto-claude-code-research-in-sleep` — a sibling project that survives crashes, context compaction, and OOM by leaning on atomic writes, append-only event logs, watchdog daemons, and schema validation.

**Current state (v0.1.0):** The loop already has reviewer-independence, output versioning, hash-based resume, and hard verification gates. It is *correct* but *fragile* in three ways:

1. **State writes are not atomic.** A crash between "write `REVIEW_STATE.json`" and the OS flushing leaves a corrupted file. Recovery then crashes on `json.loads`.
2. **No structured event log.** When a 12-round run goes sideways at round 7, you get a `MANIFEST.md` table of file writes but no record of *why* — which persona timed out, which fix attempt failed, which score moved which way.
3. **No liveness signal.** A loop that hangs (Codex MCP stalls, Claude session dies mid-phase) leaves `REVIEW_STATE.json` in `status="in_progress"` forever. The 24h staleness check catches it eventually, but you can't *detect* the hang while it is happening.

This plan closes those gaps with surgical, low-blast-radius changes. No rewrites. No new infra.

---

## Goals

- **Crash safety:** every persisted file survives `kill -9` mid-write.
- **Forensics:** any past run can be reconstructed from its trace dir + an append-only `events.jsonl`.
- **Liveness:** an external observer (or the operator) can tell within ~5 minutes whether a loop is alive, stuck, or done.
- **Schema discipline:** state files validate on load. Old/corrupt → migrate or fresh start, never silent crash.
- **Failure-mode tests:** the test suite covers what happens when things go wrong, not just when they go right.

## Non-goals

- Distributed locking. Single-operator single-machine for now.
- Cross-format project atomicity (still a v0.3 roadmap item).
- Replacing the reviewer-independence protocol or the verification gates — those are working.

---

## Scope: what changes

### Tier 1 — Crash safety (must-ship)

**1.1 Atomic state writes.** Every write to `REVIEW_STATE.json`, `MANIFEST.md` table rows, and the timestamped approved-draft files goes through write-temp-then-rename. New helper script: `tools/atomic_write.py` (stdlib only, ~30 lines).

```python
# tools/atomic_write.py
import os, tempfile, pathlib, json

def atomic_write(path: str, content: str, mode: str = "w") -> None:
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=p.name + ".", suffix=".tmp", dir=p.parent)
    try:
        with os.fdopen(fd, mode) as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, p)  # atomic on POSIX and Windows NTFS
    except Exception:
        try: os.unlink(tmp)
        except OSError: pass
        raise

def atomic_write_json(path: str, obj) -> None:
    atomic_write(path, json.dumps(obj, indent=2, ensure_ascii=False))
```

Update `skills/shared-references/loop-contract.md` to mandate atomic writes for state and approved drafts. Update each format SKILL.md's Phase E section to call this helper instead of raw `>` redirection.

**1.2 State schema validation.** New file: `skills/shared-references/state-schema.md` defining the JSON schema for `REVIEW_STATE.json` (required fields, types, allowed values for `status` and `phase`). Loop preamble validates state on load — if invalid, log to `events.jsonl` and start fresh with a `state_corrupt_recovered` event.

Schema (v1):
```json
{
  "schema_version": 1,
  "format": "blog | social | linkedin | business-plan",
  "round": <int >= 0>,
  "phase": "A | B | C | D | E | Term",
  "status": "in_progress | completed | aborted",
  "draft_path": <string>,
  "draft_mtime_hash": <string, sha256 of mtime+size>,
  "thread_ids": { "<persona-name>": "<threadId>" },
  "started_at": <ISO8601>,
  "last_heartbeat_at": <ISO8601>,
  "last_event_id": <int>
}
```

### Tier 2 — Forensics (high-value)

**2.1 Append-only event log.** New file per run: `review-stage/events.jsonl`. One JSON object per line, timestamped, immutable once written. Captures every meaningful state transition.

Event schema:
```json
{"id": 42, "ts": "2026-04-28T23:14:02Z", "round": 3, "phase": "B",
 "kind": "persona_response_received | persona_retry | persona_inconclusive |
          verification_passed | verification_failed | round_consensus |
          state_corrupt_recovered | hash_mismatch | resumed | terminated",
 "actor": "<persona-name|system>",
 "data": { /* free-form, kind-specific */ }}
```

New helper: `tools/log_event.sh` (bash, ~15 lines) — appends one line, atomic via `>>` on a single line write (POSIX guarantees atomicity for writes ≤ PIPE_BUF=4096 bytes when O_APPEND is set).

Update each format SKILL.md to emit events at:
- Round start (`phase_start`)
- Persona response received (`persona_response_received` with score, verdict)
- Verification result (`verification_passed`/`verification_failed` with which check)
- Round consensus computed (`round_consensus` with delta)
- Termination (`terminated` with reason: positive | max_rounds | aborted | error)

**2.2 Heartbeat field.** Bump `last_heartbeat_at` and `last_event_id` in `REVIEW_STATE.json` on every phase transition. Atomic write makes this safe.

### Tier 3 — Liveness (nice-to-ship)

**3.1 Liveness check tool.** New script: `tools/check_liveness.sh`. Reads `REVIEW_STATE.json`, computes `now - last_heartbeat_at`, prints `ALIVE | STALE | DONE` and exit code (0 / 1 / 2). Operator can `watch -n 60 tools/check_liveness.sh ./review-stage`.

Thresholds (configurable via env):
- `< 5 min` → ALIVE
- `5–30 min` → SLOW (warn)
- `> 30 min` AND `status=in_progress` → STALE
- `status=completed` → DONE

**3.2 Document the liveness contract.** One section in `skills/shared-references/loop-contract.md` explaining when an operator should intervene.

### Tier 4 — Failure-mode tests (must-ship alongside Tier 1)

Extend `tests/run_tests.sh` and add new fixtures under `tests/fixtures/state/`:

- `corrupt_state.json` — truncated mid-object → loader rejects, returns "fresh start needed"
- `stale_state.json` — `last_heartbeat_at` 25h old → loader rejects, returns "fresh start"
- `wrong_schema_state.json` — `schema_version: 99` → loader rejects with migration message
- `valid_resume_state.json` — schema-valid + recent heartbeat + matching hash → loader returns "resume from round N"
- `hash_mismatch_state.json` — schema-valid + recent + draft hash differs → loader returns "warn + ask"

Plus a positive test for `atomic_write.py`: write 1MB through it, verify temp file is gone and final file is intact. A "kill mid-write" test is hard cross-platform; skip for v0.2.

---

## Scope: what does NOT change (deferred)

- **Watchdog daemon** (reference repo's `watchdog.py`): would need a long-running process, conflicts with Claude Code's session model. The liveness *check* (3.1) gives 80% of the value with 5% of the complexity. Reconsider in v0.3.
- **OOM-style retry with exponential backoff:** the loop is bounded by `MAX_ROUNDS`; persona retries are bounded to 1 by `loop-contract.md`. Adding backoff for transient Codex MCP errors is real but out of scope here — file as TODO.
- **GPU memory tracking:** N/A, this isn't a training loop.
- **Phase dependency formalism:** the current state machine is documented in `loop-contract.md` and works. Formalizing it as a parser-checked DAG is over-engineering for 5 phases.
- **Cross-format project atomicity:** roadmap v0.3.

## What already exists

| Reference repo pattern | Current repo equivalent | Action |
|---|---|---|
| Atomic writes (temp+rename) | None — raw `>` redirects | **Add** (1.1) |
| Idempotent job dedup by ID | N/A — single-loop scope | Skip |
| Phase dependencies | Informal in `loop-contract.md` | Keep informal |
| OOM retry + backoff | Single retry, then INCONCLUSIVE | Keep; add event log entry |
| Watchdog daemon | None | Skip; add liveness check (3.1) |
| Append-only `alerts.log` | `MANIFEST.md` (file writes only) | **Add** `events.jsonl` (2.1) |
| 24h state recovery | Already implemented | **Add** schema validation (1.2) |
| Schema validation | Persona YAML only | **Add** for REVIEW_STATE.json (1.2) |
| Output-as-convergence-oracle | Score-threshold-based | Keep; appropriate for review domain |
| No destructive retries on ambiguity | Already implemented (hash mismatch → ask) | Keep |
| Reviewer independence (fresh threads) | Already implemented; reference repo lacks this | Keep |
| Hard verification gates | Already implemented; reference repo lacks this | Keep |
| Output versioning (timestamp + alias) | Already implemented | Keep; route through atomic_write |

## NOT in scope

- Replacing bash tools with Python equivalents
- Adding a UI / dashboard
- Multi-user / multi-machine coordination
- Persona schema v2 (multi-axis scoring) — separate effort
- Replacing Codex MCP with a different backend

---

## Files touched

**New:**
- `tools/atomic_write.py` — atomic write helper (stdlib only)
- `tools/log_event.sh` — append-only event logger
- `tools/check_liveness.sh` — operator liveness probe
- `tools/validate_state.py` — schema validator for REVIEW_STATE.json
- `skills/shared-references/state-schema.md` — schema documentation
- `tests/fixtures/state/corrupt_state.json`
- `tests/fixtures/state/stale_state.json`
- `tests/fixtures/state/wrong_schema_state.json`
- `tests/fixtures/state/valid_resume_state.json`
- `tests/fixtures/state/hash_mismatch_state.json`

**Modified:**
- `skills/shared-references/loop-contract.md` — mandate atomic writes; document events.jsonl; document liveness
- `skills/auto-blog-review-loop/SKILL.md` — call `log_event.sh` at phase transitions; route state writes through atomic_write
- `skills/auto-social-review-loop/SKILL.md` — same
- `skills/auto-linkedin-review-loop/SKILL.md` — same
- `skills/auto-business-plan-review-loop/SKILL.md` — same
- `tests/run_tests.sh` — add state fixture tests + atomic_write test
- `VERSION` — bump to `0.2.0`
- `README.md` — short "Robustness" section pointing at new docs

**Lines:** estimated ~250 net new lines of code (helpers + tests), ~80 lines of doc updates, ~120 lines of SKILL.md edits across 4 format skills.

## Implementation order

1. Land Tier 1 first (atomic_write.py + state-schema.md + validate_state.py + their tests). Nothing in the loop changes yet — these are pure additions.
2. Wire Tier 1 into one format (blog) end-to-end. Verify a smoke run.
3. Roll out to social, linkedin, business-plan in parallel (mechanical edits).
4. Land Tier 2 (events.jsonl + log_event.sh) on top — same rollout pattern.
5. Land Tier 3 (check_liveness.sh) — orthogonal, ship anytime after Tier 2.
6. Bump VERSION to 0.2.0; update README; tag release.

## Test plan

**Pre-existing tests (must still pass):**
- `tests/run_tests.sh` validates all 5 verification tools against all 9 fixtures.

**New tests (this plan):**
- Atomic write round-trip on 1MB content; verify no temp file left behind.
- State validator on each of the 5 state fixtures; verify expected verdict (reject / fresh / resume / warn).
- Per-format smoke: synthesize a `REVIEW_STATE.json` mid-round with a fake `events.jsonl`, kill mid-flight, restart loop, verify it picks up at the documented resume point.
- Liveness check on three states: ALIVE (heartbeat 30s old), SLOW (10 min old), STALE (45 min old + status=in_progress).

## Risks

- **Atomic rename on Windows:** `os.replace` works on NTFS, but cross-volume renames fail. Helper uses same-dir tempfile to avoid this. Verified by `tempfile.mkstemp(dir=p.parent)`.
- **Bash event log atomicity:** POSIX guarantees atomic writes only ≤ `PIPE_BUF` (4096 bytes). Each event line is well under that. If we ever exceed it, switch to a small Python helper.
- **Schema migrations:** v0.2 introduces `schema_version: 1`. There is no v0 in the wild yet (v0.1 had no schema field). Loader treats missing `schema_version` as "fresh start" — safe.
- **Behavior change for in-flight loops:** users with a running v0.1 loop will see their state file rejected when they upgrade. Document this in CHANGELOG: "v0.2 requires a fresh loop start; v0.1 state files are not migratable."

## Dream state delta

CURRENT (v0.1): loop runs to completion most of the time; debugging a failure means reading scrollback and guessing.
THIS PLAN (v0.2): loop survives crashes mid-write; every run leaves an audit trail; an operator can answer "is it stuck?" in one command.
12-MONTH IDEAL (v1.0): loop is a daemon; multiple loops run in parallel against the same project; failures self-heal where safe and escalate where not; full timeline reconstruction from any past run.

The plan moves us ~40% toward the 12-month ideal with v0.2-sized effort.

---

## GSTACK REVIEW REPORT

Run via `/autoplan` on 2026-04-28. Three independent Claude subagent reviewers (CEO, Eng, DX) ran in parallel on the v1 plan. Codex voice skipped this round (timeout-budget tradeoff in auto mode).

### Consensus tables

**CEO — strategic challenge:**

| Dimension | Verdict |
|---|---|
| Right problem to solve? | **DISAGREE** — CEO says persona quality + adoption are the binding constraint, not durability |
| Premises evidenced? | **NO** — no incidents, bug reports, or user complaints cited |
| Scope calibration | DISAGREE — CEO wants Tier 1.1 only; would invest the rest in formats/integrations |
| Alternatives explored? | **PARTIAL** — cross-format atomicity and OOM retry deferred without strong rationale |
| Competitive risk | **HIGH** — "polish existing" play vs. format/integration race |

**Eng — technical correctness:**

| Dimension | Claude subagent verdict |
|---|---|
| 1. Architecture sound? | **NO** — `atomic_write.py` lacks CLI entrypoint; SKILL.md can't import Python |
| 2. Cross-platform claims | **NO** — `PIPE_BUF` atomicity is fake on Git Bash; `os.replace` can throw `PermissionError` on Windows |
| 3. Edge cases covered? | **PARTIAL** — corrupt last line, orphan tmp, concurrent loops, encoding, symlinks all unhandled |
| 4. Test coverage sufficient? | **NO** — missing concurrency, migration, and Windows-file-lock tests |
| 5. Security threats covered? | **NO** — no path-traversal guard on `atomic_write` paths derived from user-supplied draft paths |
| 6. Hidden complexity? | **YES** — heartbeat is theater (Phase A naturally exceeds STALE threshold; compaction kills heartbeats) |

**DX — developer experience:**

| Dimension | Claude subagent verdict |
|---|---|
| 1. Upgrade path clear? | **NO** — on-load error message text not specified |
| 2. SKILL.md instruction style? | **CRITICAL** — 4 format SKILL.md files getting duplicate bash blocks; will drift |
| 3. Error message format? | **NO** — validator UX format not specified |
| 4. Liveness ergonomics? | **NO** — operator-facing doc lives in `loop-contract.md` (Claude-facing) not `TROUBLESHOOTING.md` |
| 5. Source of truth? | **CRITICAL** — schema redefined in 5+ places (helper, validator, doc, fixtures, multiple SKILL.md, AGENT_GUIDE) |
| 6. `events.jsonl` discoverable? | **NO** — not mentioned in README, AGENT_GUIDE, or TROUBLESHOOTING |
| 7. CONTRIBUTING.md updated? | **NO** — omitted from "Files touched" |
| 8. Reverse-compat messaging? | **NO** — only in plan's Risks section, no on-load pointer to CHANGELOG |

### Cross-phase themes

**THEME 1 — Tier 3 (liveness) is wrong as currently shaped.** CEO calls it the wrong investment; Eng calls the heartbeat "theater" because Phase A and compaction both break the signal; DX says even if it stays, the docs are in the wrong file. This is the highest-confidence finding across the review. **Decision:** drop the liveness probe. Replace with `tools/why_stuck.py` — a *post-mortem* tool that reads the events.jsonl tail and prints last event + age + suggested next action. Operator runs it after the fact, not while the loop is hot.

**THEME 2 — SKILL.md instruction boundary is correctness-critical.** Eng (Architecture #1) and DX (#2 + #5) both flagged it. The fix is structural, not cosmetic. **Decision:** define one canonical fenced bash block per event-emit pattern in `loop-contract.md`. Each format SKILL.md links to it (`see loop-contract.md §Events`) rather than duplicating. `tools/validate_state.py` becomes the single source of truth for the schema; `state-schema.md` is generated from a docstring or removed. Inline schemas in `loop-contract.md`, `AGENT_GUIDE.md`, and the format SKILL.md files get replaced with one-line pointers.

**THEME 3 — The CEO challenge is real but not unanimous.** CEO says don't do this; Eng and DX accept the goal and critique the execution. The user explicitly invoked "make the current repo more robust" — the user has the context CEO lacks (their own pain points, roadmap intuition). Surface it at the gate, default to user's stated direction.

### Decision Audit Trail

| # | Phase | Decision | Class | Principle | Rationale | Rejected |
|---|---|---|---|---|---|---|
| 1 | Eng | Add stdin CLI to `atomic_write.py`; SKILL.md invokes via Bash heredoc | Auto | P5 explicit | Skills can only call Python via Bash; no CLI entry = unusable | Inline-write logic (DRY violation) |
| 2 | Eng | Wrap `os.replace` in PermissionError retry (3x, 100ms backoff) | Auto | P1 completeness | Windows file-sharing locks are real; silent failure = state loss | Single attempt |
| 3 | Eng | Replace `tools/log_event.sh` with `tools/log_event.py` | Auto | P1 completeness | Git Bash on Windows has no `O_APPEND` atomicity; bash claim is false | Keep bash |
| 4 | Eng | Init-time sweep of orphan `*.tmp` in `review-stage/` | Auto | P1 completeness | Crash between mkstemp and replace leaves litter | Ignore tmp files |
| 5 | Eng | Path-traversal guard in `atomic_write` (rooted at `review-stage/`) | Auto | P5 + security | Plan derives state paths from user draft paths | No guard |
| 6 | Eng | Migration registry pattern in `validate_state.py` from day one | Auto | P5 explicit | Schema versioning footgun ships on day one, not v3 | Defer migration logic |
| 7 | Eng | Document last-line `JSONDecodeError` rule for `events.jsonl` readers | Auto | P5 explicit | Crash-during-write is the common case | Strict reader (ignore corruption) |
| 8 | DX | Spec on-load error message text in `state-schema.md` | Auto | P5 explicit | "v0.1 detected → fresh start" must reference CHANGELOG | Generic error |
| 9 | DX | Single source of truth = `validate_state.py` with embedded JSONSchema | Auto | P4 DRY | Schema currently redefined in 5+ places | Multiple sources |
| 10 | DX | Add `events.jsonl` to README "What you get back", AGENT_GUIDE, TROUBLESHOOTING with 3 jq recipes | Auto | P5 explicit | New artifact must be discoverable on day one | Hide it |
| 11 | DX | Add CONTRIBUTING.md to modified files; document event emission pattern | Auto | P1 completeness | Persona/format contributors need to emit events | Skip |
| 12 | DX | Three-place coverage for breaking-change message: CHANGELOG, README "Upgrading", on-load error | Auto | P1 completeness | User sees pointer at moment of breakage | Single CHANGELOG line |
| 13 | CEO | Push event emission into one shared helper, not 5 calls per skill | Auto | P4 DRY + P5 explicit | Reduces SKILL.md edit blast radius from 4 files × 5 sites to 4 files × 1 line | 5 per skill |
| 14 | All | **DROP Tier 3 liveness probe.** Replace with `tools/why_stuck.py` (post-mortem reader of events.jsonl tail) | Auto | P3 pragmatic + P5 explicit | Three-voice consensus: heartbeat is theater on Phase A and compaction; post-mortem gives 80% of value | Keep liveness as planned |
| T1 | CEO | **Direction:** robustness investment vs. new formats/integrations | **TASTE / USER CHALLENGE** | P6 user has context | User explicitly invoked "make robust" — but CEO voice's case for diverting to formats is real. Surface at gate. | — |
| T2 | Eng | Concurrent-loop lockfile (`.loop.lock` via `O_EXCL`) | **TASTE** | — | Plan declared non-goal; Eng wants enforcement. ~20 LOC, low risk. | — |
| T3 | Eng | Heartbeat field in REVIEW_STATE.json | **TASTE** | — | If we drop liveness probe (#14), heartbeat becomes non-load-bearing. Keep as `last_event_at` purely for events.jsonl correlation, or drop entirely. | — |

### Pre-gate checklist

- [x] CEO completion: 6 dimensions evaluated, all findings logged
- [x] Eng completion: 7 dimensions evaluated, 8 specific file:line findings
- [x] DX completion: 8 dimensions evaluated, 8 findings with fix specs
- [x] Cross-phase themes: 3 themes identified, all from independent voices
- [x] Audit trail: 14 auto-decisions + 3 taste decisions logged
- [ ] Test plan artifact written to disk — deferred to implementation phase since the plan itself encodes it
- [x] "What already exists" table present
- [x] "NOT in scope" section present
- [x] Dream state delta present

