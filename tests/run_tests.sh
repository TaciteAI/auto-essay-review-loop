#!/usr/bin/env bash
# auto-essay-review-loop v0.1 smoke tests
#
# Verifies that the verification tools in tools/ correctly pass good
# fixtures and reject bad ones. Does NOT run the full skill loops —
# that requires Codex MCP and a live Claude Code session.
#
# Run from repo root:
#   bash tests/run_tests.sh
#
# Designed to work on Git Bash on Windows. No GNU-specific flags.

set -uo pipefail

# Resolve repo root (this script is at <repo>/tests/run_tests.sh)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

PASS=0
FAIL=0
RESULTS=()

# Pick a python invocation that works on Windows (py launcher) or Unix (python3/python)
PYTHON=""
for candidate in python3 python py; do
  if command -v "$candidate" >/dev/null 2>&1; then
    PYTHON="$candidate"
    break
  fi
done
if [ -z "$PYTHON" ]; then
  echo "ERROR: no python interpreter found on PATH (tried python3, python, py)"
  exit 2
fi

# Parse the top-level "passed" field from a tool's JSON output via Python.
# We can't use grep — nested per-check "passed":true/false inside the
# checks[] array would false-match a top-level grep.
extract_passed() {
  local out="$1"
  "$PYTHON" -c '
import sys, json
try:
    data = json.loads(sys.stdin.read())
    print("true" if data.get("passed") else "false")
except Exception:
    print("error")
' <<< "$out"
}

# assert_passed <name> <expected_passed_true_or_false> <command...>
assert_passed() {
  local name="$1"; shift
  local expected="$1"; shift
  local out
  out="$("$@" 2>&1)" || true
  local got
  got="$(extract_passed "$out")"
  if [ "$got" = "error" ]; then
    RESULTS+=("FAIL  $name  (could not parse JSON top-level 'passed')")
    FAIL=$((FAIL+1))
    return
  fi
  if [ "$got" = "$expected" ]; then
    RESULTS+=("PASS  $name")
    PASS=$((PASS+1))
  else
    RESULTS+=("FAIL  $name  (expected passed=$expected, got passed=$got)")
    FAIL=$((FAIL+1))
  fi
}

# assert_flag_contains <name> <flag> <command...>
# Parses the top-level "flags" array via Python.
assert_flag_contains() {
  local name="$1"; shift
  local flag="$1"; shift
  local out
  out="$("$@" 2>&1)" || true
  local has
  has="$("$PYTHON" -c "
import sys, json
try:
    data = json.loads(sys.stdin.read())
    flags = data.get('flags', [])
    # Also search nested checks[].flag in case schema differs across tools
    for c in data.get('checks', []):
        if isinstance(c, dict) and c.get('flag'):
            flags.append(c['flag'])
    print('yes' if '$flag' in flags else 'no')
except Exception:
    print('error')
" <<< "$out")"
  if [ "$has" = "yes" ]; then
    RESULTS+=("PASS  $name  (flag '$flag' present)")
    PASS=$((PASS+1))
  elif [ "$has" = "error" ]; then
    RESULTS+=("FAIL  $name  (could not parse JSON for flag check)")
    FAIL=$((FAIL+1))
  else
    RESULTS+=("FAIL  $name  (expected flag '$flag' in output.flags)")
    FAIL=$((FAIL+1))
  fi
}

# assert_metric <name> <metric.dot.path> <expected_value> <command...>
# Pulls a numeric/string metric out of the tool's JSON. Supports dotted paths like
# "metrics.slide_count", "checks.2.value" (int index into list), or top-level keys.
assert_metric() {
  local name="$1"; shift
  local path="$1"; shift
  local expected="$1"; shift
  local out
  out="$("$@" 2>&1)" || true
  local got
  got="$("$PYTHON" -c "
import sys, json
try:
    data = json.loads(sys.stdin.read())
    cur = data
    for part in '$path'.split('.'):
        if isinstance(cur, list):
            cur = cur[int(part)]
        else:
            cur = cur[part]
    print(cur)
except Exception as e:
    print('error:'+str(e))
" <<< "$out")"
  if [ "$got" = "$expected" ]; then
    RESULTS+=("PASS  $name  ($path=$expected)")
    PASS=$((PASS+1))
  else
    RESULTS+=("FAIL  $name  (expected $path=$expected, got $got)")
    FAIL=$((FAIL+1))
  fi
}

echo "Running auto-essay-review-loop v0.1 smoke tests"
echo "================================================"
echo

# --- Blog: link verification ---
assert_passed "verify_links good draft" "true" \
  bash tools/verify_links.sh tests/fixtures/blog/good_draft.md
assert_passed "verify_links bad draft" "false" \
  bash tools/verify_links.sh tests/fixtures/blog/bad_draft.md

# --- Social: char count ---
assert_passed "count_chars good X post" "true" \
  "$PYTHON" tools/count_chars.py tests/fixtures/social/good_x_post.txt --format=x
assert_passed "count_chars over-limit X post" "false" \
  "$PYTHON" tools/count_chars.py tests/fixtures/social/over_limit_x.txt --format=x
assert_passed "count_chars good Threads post" "true" \
  "$PYTHON" tools/count_chars.py tests/fixtures/social/good_threads_post.txt --format=threads

# --- LinkedIn: char/link/hashtag count ---
assert_passed "count_chars good LinkedIn post (3 hashtags, 0 links)" "true" \
  "$PYTHON" tools/count_chars.py tests/fixtures/linkedin/good_post.md --format=linkedin
assert_passed "count_chars LinkedIn broetry slop (8 hashtags, 2 links)" "false" \
  "$PYTHON" tools/count_chars.py tests/fixtures/linkedin/broetry_slop.md --format=linkedin
# Surface the specific failures so a regression that drops one check still trips.
assert_metric "broetry slop hashtag_count value" "checks.2.value" "8" \
  "$PYTHON" tools/count_chars.py tests/fixtures/linkedin/broetry_slop.md --format=linkedin
assert_metric "broetry slop link_count value" "checks.1.value" "2" \
  "$PYTHON" tools/count_chars.py tests/fixtures/linkedin/broetry_slop.md --format=linkedin

# --- Business plan: market sizing ---
assert_passed "market_size_check fantasy TAM" "false" \
  "$PYTHON" tools/market_size_check.py tests/fixtures/business-plan/fantasy_tam.md
assert_flag_contains "market_size_check fantasy TAM flag" "fantasy_tam" \
  "$PYTHON" tools/market_size_check.py tests/fixtures/business-plan/fantasy_tam.md
assert_passed "market_size_check strong plan" "true" \
  "$PYTHON" tools/market_size_check.py tests/fixtures/business-plan/strong.md

# --- Market research: plan + validate ---
# `plan` always exits 0 with no top-level `passed` field. Assert the JSON shape
# instead so a regression that breaks subcommand wiring trips the test.
assert_metric "market_research_fetch plan emits tool name" "tool" "market_research_fetch" \
  bash tools/run.sh market_research_fetch.py plan --input "AI code review for startups" --depth=lite
assert_metric "market_research_fetch plan emits phase=plan" "phase" "plan" \
  bash tools/run.sh market_research_fetch.py plan --input "AI code review for startups" --depth=lite
# `validate` against a fixture missing 7 of 8 required sections must fail
# with the canonical `missing_section` flag.
assert_passed "market_research_fetch validate thin doc" "false" \
  bash tools/run.sh market_research_fetch.py validate --input tests/fixtures/market-research/thin.md
assert_flag_contains "market_research_fetch validate thin doc flag" "missing_section" \
  bash tools/run.sh market_research_fetch.py validate --input tests/fixtures/market-research/thin.md

# --- Application: per-answer verification ---
assert_passed "verify_application strong draft" "true" \
  "$PYTHON" tools/verify_application.py tests/fixtures/application/strong.md
assert_passed "verify_application weak draft" "false" \
  "$PYTHON" tools/verify_application.py tests/fixtures/application/weak.md

# --- Regression: count_chars must not crash on unknown platform.
# Before the fix, --format=mastodon raised ValueError and produced a
# Python traceback (no JSON), breaking Phase B verification when a
# typo'd platform reached the tool. Should now produce passed:false JSON.
assert_passed "count_chars bad platform yields JSON error (not traceback)" "false" \
  "$PYTHON" tools/count_chars.py tests/fixtures/social/good_x_post.txt --format=mastodon

# --- Regression: tools/run.sh wrapper picks the right interpreter and
# forwards arguments. Before this wrapper, SKILL.md hardcoded
# `python tools/...` and broke on Windows boxes where only `py` is on
# PATH. Verify the wrapper produces equivalent JSON for a known-good
# input — same fixture as the count_chars test above.
assert_passed "tools/run.sh wraps count_chars correctly" "true" \
  bash tools/run.sh count_chars.py tests/fixtures/social/good_x_post.txt --format=x

# --- CV: structural verification ---
assert_passed "verify_cv strong CV" "true" \
  bash tools/run.sh verify_cv.py tests/fixtures/cv/strong.md --target-pages=1
assert_passed "verify_cv weak CV (cliches, weak verbs, no numbers, mixed dates)" "false" \
  bash tools/run.sh verify_cv.py tests/fixtures/cv/weak.md --target-pages=1

# --- Slides: structural verification ---
assert_passed "verify_slides strong deck (Marp markdown)" "true" \
  bash tools/run.sh verify_slides.py tests/fixtures/slides/strong.md
assert_passed "verify_slides weak deck (walls of text, dup titles, no notes, no close)" "false" \
  bash tools/run.sh verify_slides.py tests/fixtures/slides/weak.md
assert_passed "verify_slides weak deck fails under pitch tighter limits" "false" \
  bash tools/run.sh verify_slides.py tests/fixtures/slides/weak.md --max-words-per-slide=40 --slide-count-max=15 --claim-title-target=40

# Regression: pitch deck with positioning-style titles ("Stripe for X", "From X to Y",
# "X: Y" colon claims) should pass under pitch-tightened thresholds. Before
# expanding is_claim_title(), this fixture would fail claim_title_ratio.
assert_passed "verify_slides good pitch deck under pitch limits" "true" \
  bash tools/run.sh verify_slides.py tests/fixtures/slides/pitch_strong.md --max-words-per-slide=40 --slide-count-max=15 --claim-title-target=40

# Regression: code-fence-aware splitting. The fixture has 3 `---` lines inside
# fenced YAML/python blocks AND 4 real slide separators (5 slides total). Without
# fence masking, the parser would have produced 8 slides.
assert_metric "verify_slides ignores fenced-block --- lines (code_fence fixture)" "metrics.slide_count" "5" \
  bash tools/run.sh verify_slides.py tests/fixtures/slides/code_fence.md

# Regression: a deck whose first content is a slide separator (no real frontmatter)
# must NOT have its first slide consumed as YAML frontmatter. Before the fix,
# strip_frontmatter() ate any opening `---...---` block; now it requires a YAML
# key:value line inside.
assert_metric "verify_slides preserves first slide when no real frontmatter" "metrics.slide_count" "5" \
  bash tools/run.sh verify_slides.py tests/fixtures/slides/no_frontmatter.md

# Regression: verify_slides handles non-UTF8 markdown gracefully.
_BAD_ENC_SLIDES="$(mktemp -t auto-essay-bad-slides-enc.XXXXXX 2>/dev/null || mktemp)"
printf '\xff\xfe\x00garbage\xff' > "$_BAD_ENC_SLIDES"
assert_passed "verify_slides handles non-UTF8 input gracefully" "false" \
  bash tools/run.sh verify_slides.py "$_BAD_ENC_SLIDES"
rm -f "$_BAD_ENC_SLIDES" 2>/dev/null || true

# --- Slides: edit_pptx round-trip (v0.2 writer) ---
# Builds a tiny .pptx fixture, applies a fix list, and checks that the
# expected text/notes changes landed. Skipped if python-pptx is missing.
HAS_PPTX="$("$PYTHON" -c 'import pptx; print("yes")' 2>/dev/null || true)"
if [ "$HAS_PPTX" = "yes" ]; then
  _ROUND_TRIP_DIR="$(mktemp -d -t auto-essay-pptx-rt.XXXXXX 2>/dev/null || mktemp -d)"
  _RT_INPUT="$_ROUND_TRIP_DIR/round_trip_input.pptx"
  _RT_OUTPUT="$_ROUND_TRIP_DIR/round_trip_output.pptx"

  "$PYTHON" tests/fixtures/slides/build_pptx_fixture.py "$_RT_INPUT" >/dev/null 2>&1
  if [ ! -f "$_RT_INPUT" ]; then
    RESULTS+=("FAIL  edit_pptx round-trip  (fixture builder did not produce input deck)")
    FAIL=$((FAIL+1))
  else
    assert_passed "edit_pptx applies fix list and reports passed" "false" \
      bash tools/run.sh edit_pptx.py --input "$_RT_INPUT" --output "$_RT_OUTPUT" --fixes tests/fixtures/slides/round_trip_fixes.json

    # The fix list intentionally includes one warning case (target text not
    # found) and one unsupported action. We assert specific outcomes by
    # inspecting the output deck rather than the writer's own report.
    _RT_CHECK="$("$PYTHON" - "$_RT_OUTPUT" <<'PYEOF'
import sys
from pptx import Presentation
prs = Presentation(sys.argv[1])
slides = list(prs.slides)
errors = []

# Slide 1: notes set
n1 = slides[0].notes_slide.notes_text_frame.text
if "30 seconds" not in n1:
    errors.append("slide 1 notes missing the new content")

# Slide 2: wordy line replaced, redundant line deleted
text2 = "\n".join(
    sh.text_frame.text for sh in slides[1].shapes if sh.has_text_frame
)
if "$432K wasted per year" not in text2:
    errors.append("slide 2 replacement text not present")
if "$432K per year on duplicated work and abandoned projects" in text2:
    errors.append("slide 2 original wordy text was not replaced")
if "wordy descriptor we plan to cut" in text2:
    errors.append("slide 2 deletion did not happen")

# Slide 3: title replaced + notes appended
title3 = slides[2].shapes.title.text
if title3 != "We are raising $1.5M":
    errors.append(f"slide 3 title not replaced (got: {title3!r})")
n3 = slides[2].notes_slide.notes_text_frame.text
if "Close on the ask" not in n3:
    errors.append("slide 3 appended notes missing")

print("OK" if not errors else "; ".join(errors))
PYEOF
)"
    if [ "$_RT_CHECK" = "OK" ]; then
      RESULTS+=("PASS  edit_pptx round-trip applies all 5 supported actions")
      PASS=$((PASS+1))
    else
      RESULTS+=("FAIL  edit_pptx round-trip  ($_RT_CHECK)")
      FAIL=$((FAIL+1))
    fi

    # Verify the writer's own report classifies the unsupported + missing-target
    # fixes correctly: the unsupported action should be skipped (not warning),
    # and the missing-target fix should be a warning (not crash).
    _RT_REPORT="$(bash tools/run.sh edit_pptx.py --input "$_RT_INPUT" --output "$_RT_OUTPUT" --fixes tests/fixtures/slides/round_trip_fixes.json --dry-run 2>/dev/null || true)"
    _RT_SKIP_COUNT="$("$PYTHON" -c "import sys, json; d=json.loads(sys.stdin.read()); print(len(d['skipped']))" <<<"$_RT_REPORT" 2>/dev/null || echo error)"
    _RT_WARN_COUNT="$("$PYTHON" -c "import sys, json; d=json.loads(sys.stdin.read()); print(len(d['warnings']))" <<<"$_RT_REPORT" 2>/dev/null || echo error)"
    if [ "$_RT_SKIP_COUNT" = "1" ] && [ "$_RT_WARN_COUNT" = "1" ]; then
      RESULTS+=("PASS  edit_pptx classifies unsupported as skipped, missing target as warning")
      PASS=$((PASS+1))
    else
      RESULTS+=("FAIL  edit_pptx classification  (skipped=$_RT_SKIP_COUNT expected 1, warnings=$_RT_WARN_COUNT expected 1)")
      FAIL=$((FAIL+1))
    fi
  fi
  rm -rf "$_ROUND_TRIP_DIR" 2>/dev/null || true
else
  RESULTS+=("SKIP  edit_pptx round-trip  (python-pptx not installed)")
fi

# Regression: edit_pptx fails fast with a JSON error if python-pptx missing.
# We can't easily simulate "missing" here without uninstalling, so instead
# assert that calling without --input produces a JSON error (not a traceback).
assert_passed "edit_pptx errors cleanly on missing args" "false" \
  bash tools/run.sh edit_pptx.py --output /tmp/x.pptx --fixes /tmp/x.json

# --- Skill-shape linter ---
# Cross-refs from SKILL.md files resolve, the umbrella dispatcher table
# matches the on-disk format skills, every persona file is referenced by
# at least one SKILL.md (or persona-library.md), and every SKILL.md has
# the name+description frontmatter the harness needs.
assert_passed "lint_skills clean run" "true" \
  bash tools/run.sh lint_skills.py

# Negative test: drop an unreferenced persona file into personas/blog/ and
# verify the linter catches it. Without this, the linter could silently
# regress to "always passed=true" and the green-path test alone wouldn't
# notice. Cleanup is unconditional via trap so a mid-test crash doesn't
# leave the fake persona behind.
_LINT_ORPHAN="personas/blog/_lint_test_orphan.md"
trap 'rm -f "$_LINT_ORPHAN" 2>/dev/null || true' EXIT
cat > "$_LINT_ORPHAN" <<'EOF'
---
name: _lint_test_orphan
role: temporary fixture; should never be referenced by any SKILL.md
---
This file exists only while tests/run_tests.sh is running.
EOF
assert_passed "lint_skills detects orphan persona" "false" \
  bash tools/run.sh lint_skills.py
assert_flag_contains "lint_skills orphan flag" "orphan_persona" \
  bash tools/run.sh lint_skills.py
rm -f "$_LINT_ORPHAN" 2>/dev/null || true
trap - EXIT

# --- Regression: verification tools must not crash on non-UTF8 input.
# Before this fix, count_chars.py and verify_application.py raised
# UnicodeDecodeError and printed a Python traceback when handed a cp1252
# or otherwise non-UTF8 draft. Should now produce passed:false JSON like
# verify_cv.py already did.
_BAD_ENC_FILE="$(mktemp -t auto-essay-bad-enc.XXXXXX 2>/dev/null || mktemp)"
printf '\xff\xfe\x00garbage\xff' > "$_BAD_ENC_FILE"
assert_passed "count_chars handles non-UTF8 input gracefully" "false" \
  "$PYTHON" tools/count_chars.py "$_BAD_ENC_FILE" --format=x
assert_passed "verify_application handles non-UTF8 input gracefully" "false" \
  "$PYTHON" tools/verify_application.py "$_BAD_ENC_FILE"
assert_passed "verify_cv handles non-UTF8 input gracefully" "false" \
  "$PYTHON" tools/verify_cv.py "$_BAD_ENC_FILE" --target-pages=1
rm -f "$_BAD_ENC_FILE" 2>/dev/null || true

# --- Summary ---
echo
echo "Results:"
echo "--------"
for line in "${RESULTS[@]}"; do
  echo "  $line"
done
echo
echo "Total: $((PASS+FAIL))   PASSED: $PASS   FAILED: $FAIL"
echo

if [ "$FAIL" -gt 0 ]; then
  exit 1
fi
exit 0
