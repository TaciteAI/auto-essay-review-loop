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

# --- Business plan: market sizing ---
assert_passed "market_size_check fantasy TAM" "false" \
  "$PYTHON" tools/market_size_check.py tests/fixtures/business-plan/fantasy_tam.md
assert_flag_contains "market_size_check fantasy TAM flag" "fantasy_tam" \
  "$PYTHON" tools/market_size_check.py tests/fixtures/business-plan/fantasy_tam.md
assert_passed "market_size_check strong plan" "true" \
  "$PYTHON" tools/market_size_check.py tests/fixtures/business-plan/strong.md

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
