#!/usr/bin/env python3
"""
qualify_prospect.py — heuristic ICP-fit scoring for enriched profiles.

Reads the normalized profile output from `enrich_profiles.py` and the
campaign's ICP definition; emits a 0–10 fit score per profile with the
exact evidence substrings that matched. Scoring is intentionally cheap
and explainable — the persona reviewers do the hard judgment downstream.
This tool gates which prospects merit a Codex call at all.

Stdlib-only. Usage:

    bash tools/run.sh qualify_prospect.py \\
        <normalized.json> <campaign.json> [--min-score=6] [--out-dir=...]

Writes:
  {out-dir}/qualified_prospects.json  — profiles with score >= min_score
  {out-dir}/rejected_prospects.json   — everything else, with reasons

Stdout: JSON summary matching the verification-protocols schema.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

TOOL_NAME = "qualify_prospect"
SCHEMA_VERSION = 1
DEFAULT_OUT_DIR = "review-stage/outbound"
DEFAULT_MIN_SCORE = 6


def now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def normalize_text(*parts) -> str:
    return " ".join(p for p in parts if p).lower()


def find_substring(needle: str, haystack: str) -> str | None:
    """Case-insensitive substring match. Returns the matched span (in haystack
    casing) if found; None otherwise. Uses word-boundary matching for short
    needles so "VP" doesn't match "VPN"."""
    if not needle or not haystack:
        return None
    needle = needle.strip()
    if not needle:
        return None
    # Build a regex that allows hyphen/space variation ("head of growth" vs
    # "head-of-growth") but anchors on word boundaries.
    parts = re.split(r"\s+", needle)
    pattern = r"\b" + r"[\s\-]+".join(re.escape(p) for p in parts) + r"\b"
    m = re.search(pattern, haystack, flags=re.IGNORECASE)
    return m.group(0) if m else None


def score_profile(profile: dict, icp: dict) -> dict:
    """Return a scored prospect dict with evidence + missingEvidence arrays."""
    headline = profile.get("headline") or ""
    role = profile.get("currentRole") or ""
    company = profile.get("company") or ""
    about = profile.get("about") or ""
    location = profile.get("location") or ""
    blob = normalize_text(headline, role, about, company, location)

    evidence: list[str] = []
    missing: list[str] = []
    disqualifiers: list[str] = []

    # Hard disqualifiers first.
    if not headline and not role:
        disqualifiers.append("no_headline_or_role")
    if not company:
        disqualifiers.append("no_current_company")

    score = 0

    # 1. Title overlap: up to 5 points. Strongest single signal.
    titles = icp.get("titles") or []
    title_hits = []
    for t in titles:
        hit = find_substring(t, headline) or find_substring(t, role)
        if hit:
            title_hits.append(hit)
    if title_hits:
        score += 5
        evidence.append(f"title matches ICP: {sorted(set(title_hits))}")
    else:
        missing.append(f"none of icp.titles {titles} found in headline/role")

    # 2. Industry keyword: up to 3 points. Looser match against headline+about.
    industry = (icp.get("industry") or "").strip()
    if industry:
        # Try the whole phrase first; then each word ≥4 chars (skip "and"/"the").
        whole = find_substring(industry, blob)
        if whole:
            score += 3
            evidence.append(f"industry '{industry}' present in profile text")
        else:
            words = [w for w in re.split(r"\W+", industry) if len(w) >= 4]
            partial_hits = [w for w in words if find_substring(w, blob)]
            if partial_hits:
                score += 1
                evidence.append(f"industry partial: {partial_hits}")
            else:
                missing.append(f"industry '{industry}' not detected")

    # 3. Buying trigger / pain keyword in about: up to 2 points.
    for field, weight in (("buying_trigger", 1), ("pain", 1)):
        val = (icp.get(field) or "").strip()
        if not val:
            continue
        if find_substring(val, about):
            score += weight
            evidence.append(f"icp.{field} signal in about: '{val}'")
        else:
            # Split on commas/and; require any meaningful phrase.
            phrases = [p.strip() for p in re.split(r"[,/]| and ", val) if p.strip()]
            hit_any = next((p for p in phrases if p and find_substring(p, about)), None)
            if hit_any:
                score += weight
                evidence.append(f"icp.{field} phrase '{hit_any}' in about")
            else:
                missing.append(f"icp.{field} '{val}' not detected in about/headline")

    # Cap at 10.
    if score > 10:
        score = 10

    reason_matched = (
        ("; ".join(evidence)) if evidence else "no positive ICP signals matched"
    )

    # Note: there is intentionally no `qualified` boolean on the per-row
    # record. The decision is single-gate (`not disqualifiers and fitScore
    # >= min_score`), and it's applied at the file level — the row's
    # presence in `qualified_prospects.json` IS the boolean. Having both
    # confuses readers who land on a `qualified: true` row inside
    # `rejected_prospects.json`.
    return {
        "profileUrl": profile.get("profileUrl"),
        "profile_slug": profile.get("profile_slug"),
        "firstName": profile.get("firstName"),
        "fullName": profile.get("fullName"),
        "company": profile.get("company"),
        "currentRole": profile.get("currentRole"),
        "headline": profile.get("headline"),
        "fitScore": score,
        "reasonMatchedIcp": reason_matched,
        "evidence": evidence,
        "missingEvidence": missing,
        "disqualifiers": disqualifiers,
    }


def parse_args(argv: list[str]) -> dict:
    if len(argv) < 3:
        raise SystemExit(
            "usage: qualify_prospect.py <normalized.json> <campaign.json> "
            "[--min-score=6] [--out-dir=...]"
        )
    args = {
        "normalized_path": argv[1],
        "campaign_path": argv[2],
        "min_score": DEFAULT_MIN_SCORE,
        "out_dir": DEFAULT_OUT_DIR,
    }
    for a in argv[3:]:
        if a.startswith("--min-score="):
            args["min_score"] = int(a.split("=", 1)[1])
        elif a.startswith("--out-dir="):
            args["out_dir"] = a.split("=", 1)[1]
        else:
            raise SystemExit(f"unknown flag: {a}")
    return args


def error_result(summary: str, error: str, flags: list[str]) -> dict:
    return {
        "tool": TOOL_NAME,
        "schema_version": SCHEMA_VERSION,
        "timestamp": now_iso(),
        "passed": False,
        "checks": [],
        "flags": flags,
        "summary": summary,
        "error": error,
    }


def main(argv: list[str]) -> int:
    try:
        args = parse_args(argv)
    except SystemExit as exc:
        sys.stdout.write(
            json.dumps(
                error_result(str(exc), "ArgumentError", ["argument_error"]),
                ensure_ascii=False,
                indent=2,
            )
            + "\n"
        )
        return 2

    norm_path = Path(args["normalized_path"])
    camp_path = Path(args["campaign_path"])
    out_dir = Path(args["out_dir"])
    min_score = int(args["min_score"])

    for label, p in (("normalized", norm_path), ("campaign", camp_path)):
        if not p.exists():
            sys.stdout.write(
                json.dumps(
                    error_result(
                        f"{label} file not found: {p}",
                        "FileNotFoundError",
                        [f"{label}_missing"],
                    ),
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n"
            )
            return 2

    try:
        profiles = load_json(norm_path)
        campaign = load_json(camp_path)
    except (json.JSONDecodeError, OSError, UnicodeDecodeError) as exc:
        sys.stdout.write(
            json.dumps(
                error_result(
                    f"could not parse input: {exc}",
                    type(exc).__name__,
                    ["input_invalid"],
                ),
                ensure_ascii=False,
                indent=2,
            )
            + "\n"
        )
        return 2

    if not isinstance(profiles, list):
        sys.stdout.write(
            json.dumps(
                error_result(
                    "normalized.json must be a list",
                    "TypeError",
                    ["input_invalid"],
                ),
                ensure_ascii=False,
                indent=2,
            )
            + "\n"
        )
        return 2

    icp = campaign.get("icp") or {}
    if not icp:
        sys.stdout.write(
            json.dumps(
                error_result(
                    "campaign.icp is empty — cannot score fit",
                    "ValueError",
                    ["missing_icp"],
                ),
                ensure_ascii=False,
                indent=2,
            )
            + "\n"
        )
        return 1

    scored = [score_profile(p, icp) for p in profiles if isinstance(p, dict)]

    def admitted(s: dict) -> bool:
        # Single gate: no hard disqualifiers AND meets the score floor.
        return (not s["disqualifiers"]) and (s["fitScore"] >= min_score)

    qualified = [s for s in scored if admitted(s)]
    rejected = [s for s in scored if not admitted(s)]

    write_json(out_dir / "qualified_prospects.json", qualified)
    write_json(out_dir / "rejected_prospects.json", rejected)

    checks = [
        {
            "name": "input_loaded",
            "passed": True,
            "detail": f"{len(scored)} normalized profile(s) scored",
            "value": len(scored),
        },
        {
            "name": "any_qualified",
            "passed": bool(qualified),
            "detail": (
                f"{len(qualified)} qualified at score >= {min_score}"
                if qualified
                else f"no profile met threshold {min_score}"
            ),
            "value": len(qualified),
        },
    ]
    flags: list[str] = []
    if not qualified:
        flags.append("no_qualified_prospects")

    rejection_reasons: list[str] = []
    for r in rejected[:5]:
        why = "; ".join(r["disqualifiers"]) if r["disqualifiers"] else (
            f"score {r['fitScore']} < {min_score}"
        )
        rejection_reasons.append(f"{r['profile_slug']}: {why}")

    passed = all(c["passed"] for c in checks)
    summary = (
        f"{len(qualified)} of {len(scored)} prospects qualified at score >= {min_score}"
    )

    result = {
        "tool": TOOL_NAME,
        "schema_version": SCHEMA_VERSION,
        "timestamp": now_iso(),
        "input_file": str(norm_path),
        "campaign_file": str(camp_path),
        "out_dir": str(out_dir),
        "min_score": min_score,
        "qualified_count": len(qualified),
        "rejected_count": len(rejected),
        "rejection_examples": rejection_reasons,
        "passed": passed,
        "checks": checks,
        "flags": flags,
        "summary": summary,
    }
    sys.stdout.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
