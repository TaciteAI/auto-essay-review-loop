#!/usr/bin/env bash
# verify_links.sh — Phase B.7 hard check for the blog format.
#
# Input:  $1 = path to a markdown file
# Output: JSON to stdout matching shared-references/verification-protocols.md schema
#
# Behavior:
#   - Extracts every http(s):// URL from the markdown
#     (handles [text](url), <url>, and bare URLs in body text)
#   - For each unique URL, runs a HEAD request via curl with a 10s timeout
#   - Treats 200 and 301/302 chains that resolve to 200 as PASS
#   - Treats 4xx, 5xx, network errors, and timeouts as FAIL
#   - Emits a single JSON object to stdout
#
# Designed to work on Git Bash for Windows (msys/mingw curl + GNU coreutils).

set -uo pipefail

INPUT_FILE="${1:-}"

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

iso_timestamp() {
    # Portable ISO-8601 down to seconds, no fractional/TZ noise.
    date -u +"%Y-%m-%dT%H:%M:%SZ"
}

json_escape() {
    # Minimal JSON string escape. Reads from stdin, writes to stdout.
    # Handles: \  "  newline  carriage-return  tab.
    sed \
        -e 's/\\/\\\\/g' \
        -e 's/"/\\"/g' \
        -e ':a;N;$!ba;s/\n/\\n/g' \
        -e 's/\r/\\r/g' \
        -e 's/\t/\\t/g'
}

slugify_url() {
    # Make a stable, JSON-safe identifier from a URL.
    # Strip protocol, replace non-alnum with underscore, collapse repeats, trim.
    printf '%s' "$1" \
        | sed -e 's|^https\{0,1\}://||' \
              -e 's|[^A-Za-z0-9]|_|g' \
              -e 's|__\+|_|g' \
              -e 's|^_||' -e 's|_$||' \
        | cut -c1-80
}

emit_error_json() {
    # $1 = summary string
    local ts summary_escaped input_escaped
    ts="$(iso_timestamp)"
    summary_escaped=$(printf '%s' "$1" | json_escape)
    input_escaped=$(printf '%s' "${INPUT_FILE}" | json_escape)
    cat <<EOF
{"tool":"verify_links","timestamp":"${ts}","input_file":"${input_escaped}","passed":false,"checks":[],"summary":"${summary_escaped}"}
EOF
}

# ------------------------------------------------------------------
# Pre-flight
# ------------------------------------------------------------------

if [[ -z "${INPUT_FILE}" ]]; then
    emit_error_json "verify_links: no input file provided (usage: verify_links.sh <markdown-file>)"
    exit 0
fi

if [[ ! -f "${INPUT_FILE}" ]]; then
    emit_error_json "verify_links: input file not found: ${INPUT_FILE}"
    exit 0
fi

if ! command -v curl >/dev/null 2>&1; then
    emit_error_json "verify_links: curl not available in PATH"
    exit 0
fi

# ------------------------------------------------------------------
# Extract URLs
# ------------------------------------------------------------------
# Strategy: pull every http(s):// URL out of the file, regardless of
# whether it's wrapped in [text](url), <url>, or appears bare.
# grep -oE pulls all matches per line. We then trim trailing punctuation
# that's commonly attached to URLs in prose: ) ] > , . ; ! ? "

RAW_URLS=$(grep -oE 'https?://[^[:space:]]+' "${INPUT_FILE}" 2>/dev/null || true)

# Trim trailing punctuation that is usually NOT part of the URL
# (closing paren/bracket/angle, comma, period, semicolon, colon,
# bang, question, quote, backtick).
CLEAN_URLS=$(printf '%s\n' "${RAW_URLS}" \
    | sed -E 's/[][)>.,;:!?"`]+$//' \
    | sed -E 's/[][)>.,;:!?"`]+$//' \
    | grep -E '^https?://' \
    | sort -u)

# Drop empty lines from the unique list.
URL_LIST=()
while IFS= read -r line; do
    [[ -n "${line}" ]] && URL_LIST+=("${line}")
done <<< "${CLEAN_URLS}"

TOTAL=${#URL_LIST[@]}

# ------------------------------------------------------------------
# Zero-URL case: pass with informational summary
# ------------------------------------------------------------------

if [[ "${TOTAL}" -eq 0 ]]; then
    TS="$(iso_timestamp)"
    INPUT_ESCAPED=$(printf '%s' "${INPUT_FILE}" | json_escape)
    cat <<EOF
{"tool":"verify_links","timestamp":"${TS}","input_file":"${INPUT_ESCAPED}","passed":true,"checks":[],"summary":"0 of 0 links broken (no http(s) URLs found)"}
EOF
    exit 0
fi

# ------------------------------------------------------------------
# Check each URL
# ------------------------------------------------------------------

CHECKS_JSON=""
BROKEN=0

for url in "${URL_LIST[@]}"; do
    # HEAD request first, follow redirects, 10s total timeout.
    # -L follows redirects; -o discards body; -w prints final HTTP code.
    # -s silent; -I HEAD method.
    # Some servers reject HEAD with 405 — fall back to GET in that case.
    CODE=$(curl -sI -L --max-time 10 -o /dev/null -w "%{http_code}" "${url}" 2>/dev/null || echo "000")

    # Take only the LAST 3 chars in case curl emitted a redirect chain or
    # extra characters (e.g., "302200" → "200").
    CODE="${CODE: -3}"

    if [[ "${CODE}" == "405" || "${CODE}" == "000" || -z "${CODE}" ]]; then
        # Retry with GET (range trick to minimize bytes)
        CODE2=$(curl -sL --max-time 10 -o /dev/null -r 0-0 -w "%{http_code}" "${url}" 2>/dev/null || echo "000")
        CODE="${CODE2: -3}"
    fi

    if [[ "${CODE}" =~ ^2[0-9][0-9]$ ]]; then
        PASS=true
        DETAIL="${CODE} OK"
    elif [[ "${CODE}" == "000" || -z "${CODE}" ]]; then
        PASS=false
        DETAIL="network error or timeout"
        BROKEN=$((BROKEN + 1))
    else
        PASS=false
        DETAIL="HTTP ${CODE}"
        BROKEN=$((BROKEN + 1))
    fi

    SLUG="url_$(slugify_url "${url}")"
    URL_ESCAPED=$(printf '%s' "${url}" | json_escape)
    DETAIL_ESCAPED=$(printf '%s' "${DETAIL} (${URL_ESCAPED})" | json_escape)

    CHECK_OBJ="{\"name\":\"${SLUG}\",\"passed\":${PASS},\"detail\":\"${DETAIL_ESCAPED}\"}"

    if [[ -z "${CHECKS_JSON}" ]]; then
        CHECKS_JSON="${CHECK_OBJ}"
    else
        CHECKS_JSON="${CHECKS_JSON},${CHECK_OBJ}"
    fi
done

# ------------------------------------------------------------------
# Emit final JSON
# ------------------------------------------------------------------

if [[ "${BROKEN}" -eq 0 ]]; then
    PASSED=true
else
    PASSED=false
fi

TS="$(iso_timestamp)"
INPUT_ESCAPED=$(printf '%s' "${INPUT_FILE}" | json_escape)
SUMMARY="${BROKEN} of ${TOTAL} links broken"

cat <<EOF
{"tool":"verify_links","timestamp":"${TS}","input_file":"${INPUT_ESCAPED}","passed":${PASSED},"checks":[${CHECKS_JSON}],"summary":"${SUMMARY}"}
EOF
