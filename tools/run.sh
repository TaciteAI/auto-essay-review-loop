#!/usr/bin/env bash
# tools/run.sh — portable Python launcher for the auto-essay-review-loop verification tools.
#
# Why this exists: SKILL.md files invoke verification scripts during Phase B of the
# loop. Hardcoding `python tools/foo.py ...` in every SKILL.md breaks on Windows
# installs where only the `py` launcher is on PATH (no `python`/`python3`). This
# wrapper picks the first interpreter that exists and forwards arguments unchanged.
#
# Usage:
#     bash tools/run.sh count_chars.py review-stage/draft.txt --format=x
#     bash tools/run.sh market_size_check.py review-stage/draft.md
#
# Resolves the script under tools/ relative to this wrapper's location, so it
# works regardless of the caller's CWD as long as tools/ is intact.

set -uo pipefail

if [ "$#" -lt 1 ]; then
  echo '{"tool":"run.sh","passed":false,"summary":"usage: bash tools/run.sh <script.py> [args...]","error":"NoScriptArgument"}' >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="$SCRIPT_DIR/$1"
shift

if [ ! -f "$TARGET" ]; then
  printf '{"tool":"run.sh","passed":false,"summary":"script not found: %s","error":"FileNotFoundError"}\n' "$TARGET" >&2
  exit 2
fi

PYTHON=""
for candidate in python3 python py; do
  if command -v "$candidate" >/dev/null 2>&1; then
    PYTHON="$candidate"
    break
  fi
done

if [ -z "$PYTHON" ]; then
  echo '{"tool":"run.sh","passed":false,"summary":"no python interpreter found on PATH (tried python3, python, py)","error":"PythonNotFound"}' >&2
  exit 2
fi

exec "$PYTHON" "$TARGET" "$@"
