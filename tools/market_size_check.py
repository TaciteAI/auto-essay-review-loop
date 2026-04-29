#!/usr/bin/env python3
"""
market_size_check.py — TAM/SAM/SOM sanity checker for business plans.

Part of the auto-essay-review-loop framework, v0.1. Pure stdlib, no external
dependencies (no `requests`; we use `urllib.request` for the future
--web-search=on path).

Usage:
    python market_size_check.py path/to/plan.md [--web-search=on|off]

Default: --web-search=off (v0.1 ships without a WebSearch MCP integration).
With --web-search=on, the tool prints a stub message and falls through to the
same structural checks. Phase 2 will wire this into a real verification path.

Output: JSON document on stdout, conforming to the schema in
shared-references/verification-protocols.md:

    {
      "tool": "market_size_check",
      "timestamp": "2026-04-28T10:00:00",
      "input_file": "path/to/plan.md",
      "passed": true|false,
      "checks": [{"name": "...", "passed": true|false, "detail": "..."}, ...],
      "flags": ["fantasy_tam", ...],   # personas may veto on these
      "extracted": {
          "tam_value_usd": 50000000000,
          "sam_value_usd": 5000000000,
          "som_value_usd": 50000000,
          "tam_raw": "$50B",
          "sam_raw": "$5B",
          "som_raw": "$50M"
      },
      "summary": "Human-readable one-liner"
    }

Exit code: 0 always (the JSON is the contract; the consuming skill decides
whether to block on flags). Non-zero only on actual tool errors (bad file
path, malformed CLI args).
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from typing import Any

# Currency suffix → multiplier in USD.
_SUFFIXES: dict[str, int] = {
    "K":   1_000,
    "M":   1_000_000,
    "MM":  1_000_000,
    "B":   1_000_000_000,
    "BN":  1_000_000_000,
    "T":   1_000_000_000_000,
    "TN":  1_000_000_000_000,
}

# Match patterns like:
#   $50B TAM        $50 billion TAM         TAM: $50B           TAM of $50 billion
#   $5B SAM         5B SAM                  SAM = $5,000,000,000
#
# We keep the regex deliberately permissive on order; named-group `label`
# captures the market term, `amt` captures the numeric+suffix.
_LABELS = ("TAM", "SAM", "SOM")

# Explicit-suffix form: "$50B" / "$50.5MM" / "50 billion"
# Numeric+suffix unit. Named groups appear ONCE in the inner regex used after
# locating a label-vs-amount neighborhood; the locator regex below uses the
# same shape but with non-capturing groups to avoid duplicate-name errors when
# we OR the two orderings together.
_AMT = (
    r"\$?\s*"
    r"(?P<num>\d{1,3}(?:[,\d]{0,12})?(?:\.\d+)?)"
    r"\s*"
    r"(?P<suf>"
    r"(?:K|M|MM|B|BN|T|TN)\b"
    r"|(?:thousand|million|billion|trillion)\b"
    r")"
)

# Same shape, no named groups — used in the locator that ORs both orderings.
_AMT_NONCAPTURING = (
    r"\$?\s*"
    r"\d{1,3}(?:[,\d]{0,12})?(?:\.\d+)?"
    r"\s*"
    r"(?:(?:K|M|MM|B|BN|T|TN)\b|(?:thousand|million|billion|trillion)\b)"
)


# "TAM" close to amount, in either order, allowing "of", ":", "=", "is",
# up to ~40 chars between. Locator only — extraction uses _AMT separately.
def _build_label_amt_pattern(label: str) -> re.Pattern[str]:
    return re.compile(
        rf"(?:\b{label}\b[^\n]{{0,80}}?{_AMT_NONCAPTURING})"
        rf"|(?:{_AMT_NONCAPTURING}[^\n]{{0,40}}?\b{label}\b)",
        re.IGNORECASE,
    )

_WORD_TO_SUFFIX: dict[str, str] = {
    "thousand": "K",
    "million":  "M",
    "billion":  "B",
    "trillion": "T",
}


def _to_usd(num_raw: str, suf_raw: str) -> int | None:
    """Convert (numeric string, suffix string) to integer USD value."""
    num_clean = num_raw.replace(",", "").strip()
    try:
        num = float(num_clean)
    except ValueError:
        return None
    suf_norm = _WORD_TO_SUFFIX.get(suf_raw.strip().lower(), suf_raw.strip().upper())
    mult = _SUFFIXES.get(suf_norm)
    if mult is None:
        return None
    return int(num * mult)


def _extract(text: str, label: str) -> tuple[int | None, str | None]:
    """Return (usd_value, raw_match_string) for the FIRST occurrence of label."""
    pat = _build_label_amt_pattern(label)
    m = pat.search(text)
    if not m:
        return None, None
    # The pattern has two alternatives; one of them populated num/suf.
    # Because `re` only keeps the LAST captured value for repeated names,
    # we re-extract from the matched span using a simpler local regex.
    span = m.group(0)
    inner = re.search(_AMT, span, re.IGNORECASE)
    if not inner:
        return None, span.strip()
    val = _to_usd(inner.group("num"), inner.group("suf"))
    return val, span.strip()


def _humanize(usd: int | None) -> str:
    if usd is None:
        return "—"
    if usd >= 1_000_000_000_000:
        return f"${usd / 1_000_000_000_000:.2f}T"
    if usd >= 1_000_000_000:
        return f"${usd / 1_000_000_000:.2f}B"
    if usd >= 1_000_000:
        return f"${usd / 1_000_000:.2f}M"
    return f"${usd:,}"


def check(text: str, web_search: bool) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    flags: list[str] = []

    tam_val, tam_raw = _extract(text, "TAM")
    sam_val, sam_raw = _extract(text, "SAM")
    som_val, som_raw = _extract(text, "SOM")

    # Check 1: presence
    for label, val in (("TAM", tam_val), ("SAM", sam_val), ("SOM", som_val)):
        present = val is not None
        checks.append({
            "name": f"{label.lower()}_present",
            "passed": present,
            "detail": f"{label} stated" if present else f"{label} missing or unparseable",
        })
        if not present:
            flags.append(f"missing_{label.lower()}")

    # Check 2: nesting (SOM < SAM < TAM)
    nesting_ok = True
    if all(v is not None for v in (tam_val, sam_val, som_val)):
        if not (som_val < sam_val < tam_val):
            nesting_ok = False
            flags.append("nesting_violation")
        checks.append({
            "name": "nesting_correct",
            "passed": nesting_ok,
            "detail": (
                f"SOM ({_humanize(som_val)}) < SAM ({_humanize(sam_val)}) < TAM ({_humanize(tam_val)})"
                if nesting_ok else
                f"violation: SOM={_humanize(som_val)}, SAM={_humanize(sam_val)}, TAM={_humanize(tam_val)} — expected SOM < SAM < TAM"
            ),
        })
    else:
        checks.append({
            "name": "nesting_correct",
            "passed": False,
            "detail": "cannot evaluate — at least one of TAM/SAM/SOM missing",
        })

    # Check 3: TAM absurdity
    if tam_val is not None:
        if tam_val >= 10_000_000_000_000:  # $10T+
            flags.append("fantasy_tam")
            checks.append({
                "name": "tam_realistic",
                "passed": False,
                "detail": f"TAM = {_humanize(tam_val)} — fantasy_tam (≥$10T; for reference global advertising is ~$700B)",
            })
        elif tam_val > 5_000_000_000_000:  # $5T < x < $10T
            flags.append("tam_suspicious")
            checks.append({
                "name": "tam_realistic",
                "passed": False,
                "detail": f"TAM = {_humanize(tam_val)} — suspicious (>$5T; very few real markets are this large)",
            })
        else:
            checks.append({
                "name": "tam_realistic",
                "passed": True,
                "detail": f"TAM = {_humanize(tam_val)} within plausible market sizes",
            })

    # Check 4: SOM realism (SOM ≤ 10% of SAM is the heuristic for <5yr capture)
    if sam_val is not None and som_val is not None and sam_val > 0:
        ratio = som_val / sam_val
        if ratio > 0.10:
            flags.append("som_unrealistic")
            checks.append({
                "name": "som_realistic_capture",
                "passed": False,
                "detail": (
                    f"SOM ({_humanize(som_val)}) is {ratio*100:.1f}% of SAM ({_humanize(sam_val)}); "
                    f"realistic <5yr capture is 1–5%, >10% is fantasy"
                ),
            })
        else:
            checks.append({
                "name": "som_realistic_capture",
                "passed": True,
                "detail": f"SOM is {ratio*100:.1f}% of SAM (within 1–10% realistic band)",
            })

    # Check 5: web search (Phase 2 stub)
    if web_search:
        checks.append({
            "name": "web_verified_market_size",
            "passed": True,
            "detail": "STUB — --web-search=on requires future WebSearch MCP integration (Phase 2). Skipping real verification; only structural checks ran.",
        })

    passed = not flags or all(f not in flags for f in (
        "fantasy_tam", "nesting_violation", "missing_tam", "missing_sam", "missing_som"
    ))

    return {
        "tool": "market_size_check",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).isoformat(timespec="seconds"),
        "passed": passed,
        "checks": checks,
        "flags": flags,
        "extracted": {
            "tam_value_usd": tam_val,
            "sam_value_usd": sam_val,
            "som_value_usd": som_val,
            "tam_raw": tam_raw,
            "sam_raw": sam_raw,
            "som_raw": som_raw,
        },
        "summary": _summarize(tam_val, sam_val, som_val, flags),
    }


def _summarize(tam: int | None, sam: int | None, som: int | None, flags: list[str]) -> str:
    parts: list[str] = []
    parts.append(f"TAM={_humanize(tam)} SAM={_humanize(sam)} SOM={_humanize(som)}")
    if not flags:
        parts.append("structural checks pass")
    else:
        parts.append("flags: " + ", ".join(flags))
    return "; ".join(parts)


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="TAM/SAM/SOM sanity checker for business plans")
    p.add_argument("input_file", help="Path to the business plan markdown file")
    p.add_argument(
        "--web-search",
        choices=["on", "off"],
        default="off",
        help="(v0.1: stub) When 'on', emit a placeholder note. Real verification ships in Phase 2.",
    )
    args = p.parse_args(argv[1:])

    try:
        with open(args.input_file, "r", encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        print(json.dumps({
            "tool": "market_size_check",
            "passed": False,
            "error": f"could not read file: {e}",
            "input_file": args.input_file,
        }), flush=True)
        return 2

    result = check(text, web_search=(args.web_search == "on"))
    result["input_file"] = args.input_file
    print(json.dumps(result, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
