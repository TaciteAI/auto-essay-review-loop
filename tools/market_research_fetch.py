#!/usr/bin/env python3
"""
market_research_fetch.py — helper for the /market-research skill.

Two subcommands:

    plan       Read a topic string OR a business-plan markdown file, extract
               category / ICP / geography / mentioned-competitor signals, and
               emit a structured JSON research plan (queries to run, URLs to
               fetch, validation rubric). The skill consumes this plan and
               drives Claude's WebSearch / WebFetch tools accordingly.

    validate   Read a finished MARKET_RESEARCH.md (plus the originating plan)
               and check it for: required sections, competitor count, sizing
               citation count, citation density on numeric claims, citation
               resolvability against the raw fetch directory, and source
               staleness. Emits JSON matching the verification-protocols.md
               schema.

Pure stdlib. Cross-platform. No external dependencies. Exit code 0 always
when the JSON is the contract; non-zero only on tool errors (bad CLI args,
unreadable input file).
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import sys
from typing import Any

TOOL_NAME = "market_research_fetch"
SCHEMA_VERSION = 1

# ---------- shared helpers ----------

def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(tzinfo=None).isoformat(timespec="seconds")


def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _emit(obj: dict[str, Any]) -> None:
    print(json.dumps(obj, indent=2, ensure_ascii=False), flush=True)


# ---------- PLAN subcommand ----------

# Heuristics for pulling a topic out of a markdown plan. `(?ims)` = case
# insensitive, multiline (^/$ per-line), DOTALL (`.` matches newlines).
# We capture greedily to the next H2 and then slice in Python; a bounded
# `.{0,400}?` would fail when the section body is longer than the cap.
_CATEGORY_HEADERS = (
    r"(?ims)^##\s+(?:solution|product|what\s+we'?re\s+building|executive\s+summary)\b\s*\n+"
    r"(.+?)(?=\n##\s|\Z)"
)
_ICP_HEADERS = (
    r"(?ims)^##\s+(?:target\s+customer|icp|market|who\s+(?:we\s+)?serve)\b\s*\n+"
    r"(.+?)(?=\n##\s|\Z)"
)
# Capitalized 1-3 word company-ish tokens (e.g., "Greptile", "CodeRabbit",
# "Linear App"), sitting near competitor language. Deliberately conservative
# — false negatives are cheaper than false positives here, since the synth
# step looks again.
_COMPETITOR_CONTEXT = re.compile(
    r"(?i)(?:competitors?|vs\.?|alternatives?|incumbents?|rivals?)[^\n]{0,180}",
)
_COMPANY_TOKEN = re.compile(
    r"\b([A-Z][A-Za-z0-9]{2,}(?:\s+[A-Z][A-Za-z0-9]{1,}){0,2})\b"
)

_DEPTH_BUDGETS = {
    "lite":     {"queries":  6, "fetches":  8},
    "balanced": {"queries": 12, "fetches": 20},
    "max":      {"queries": 24, "fetches": 40},
}

_REQUIRED_SECTIONS = [
    "Executive snapshot",
    "Market size evidence",
    "Competitor landscape",
    "Customer pain signals",
    "Pricing benchmarks",
    "Pre-mortem questions for the founder",
    "Sources",
    "Confidence",
]


def _slug(s: str, max_len: int = 60) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    return s[:max_len] or "untitled"


def _extract_first_match(pattern: str, text: str) -> str | None:
    m = re.search(pattern, text)
    if not m:
        return None
    body = m.group(1).strip()
    # Collapse whitespace and trim.
    return re.sub(r"\s+", " ", body)[:280]


def _extract_competitors(text: str) -> list[str]:
    """Best-effort competitor-mention extraction. Conservative on purpose."""
    found: list[str] = []
    seen: set[str] = set()
    for ctx in _COMPETITOR_CONTEXT.findall(text):
        for tok in _COMPANY_TOKEN.findall(ctx):
            t = tok.strip()
            # Filter common false positives — generic capitalized words.
            if t.lower() in {
                "We", "Our", "The", "This", "Their", "Such", "Other", "Some",
                "Many", "Most", "Any", "All", "These", "Those", "But", "And",
                "However", "While", "Unlike", "Whereas",
            }:
                continue
            key = t.lower()
            if key in seen:
                continue
            seen.add(key)
            found.append(t)
            if len(found) >= 8:
                return found
    return found


def _build_topic(input_arg: str, icp_override: str | None, geo: str) -> dict[str, Any]:
    is_file = input_arg.lower().endswith(".md") and os.path.isfile(input_arg)
    if is_file:
        text = _read_text(input_arg)
        category = (
            _extract_first_match(_CATEGORY_HEADERS, text)
            or os.path.splitext(os.path.basename(input_arg))[0].replace("_", " ")
        )
        icp = icp_override or _extract_first_match(_ICP_HEADERS, text) or "auto"
        competitors = _extract_competitors(text)
        source = {"kind": "file", "path": os.path.abspath(input_arg)}
    else:
        category = input_arg.strip()
        icp = icp_override or "auto"
        competitors = []
        source = {"kind": "topic_string", "value": category}

    return {
        "category": category,
        "icp": icp,
        "geo": geo,
        "extracted_competitor_mentions": competitors,
        "input_source": source,
    }


def _build_queries(topic: dict[str, Any], depth: str) -> list[dict[str, str]]:
    cat = topic["category"]
    geo = topic["geo"]
    year = _dt.datetime.now().year
    icp = topic["icp"]

    base: list[tuple[str, str]] = [
        ("market_size",   f"{cat} market size {year}"),
        ("market_size",   f"{cat} TAM Gartner OR Forrester OR IDC"),
        ("competitors",   f"{cat} top vendors {year}"),
        ("competitors",   f"{cat} alternatives comparison"),
        ("pricing",       f"{cat} pricing comparison"),
        ("pricing",       f"{cat} pricing per seat"),
        ("pain_signal",   f"site:reddit.com {cat} problem OR frustration"),
        ("pain_signal",   f"site:news.ycombinator.com {cat}"),
        ("pain_signal",   f"site:stackoverflow.com {cat} workaround"),
        ("growth_rate",   f"{cat} CAGR {year}"),
        ("recent_funding", f"{cat} startup funding {year}"),
        ("analyst_view",  f"{cat} analyst report 2025 OR 2026"),
    ]

    if geo and geo.lower() != "global":
        base.insert(2, ("market_size_geo", f"{cat} market size {geo} {year}"))

    if icp and icp != "auto":
        # ICP-targeted pain query — quoted to keep the buyer phrase intact.
        base.append(("pain_signal_icp", f'"{icp}" pain points {cat}'))

    # Per-named-competitor pricing lookup.
    for comp in topic["extracted_competitor_mentions"][:5]:
        base.append(("pricing", f"{comp} pricing"))
        base.append(("competitor_detail", f"{comp} ARR OR funding OR customers"))

    cap = _DEPTH_BUDGETS[depth]["queries"]
    queries: list[dict[str, str]] = []
    for i, (intent, q) in enumerate(base[:cap], start=1):
        queries.append({"id": f"q{i:02d}", "intent": intent, "query": q})
    return queries


def _build_fetch_targets(topic: dict[str, Any], depth: str) -> list[dict[str, Any]]:
    """Pre-listed fetch targets seeded from extracted competitors. The skill
    will discover more URLs from search results during Phase 2 — this is just
    the seed set."""
    cap = _DEPTH_BUDGETS[depth]["fetches"]
    targets: list[dict[str, Any]] = []
    for i, comp in enumerate(topic["extracted_competitor_mentions"][:cap], start=1):
        slug = _slug(comp)
        # We don't guess URLs — we surface the COMPANY for Phase 2 to look up.
        targets.append({
            "id": f"f{i:02d}",
            "intent": "competitor_homepage",
            "company": comp,
            "url": None,
            "discover_via_query": f"{comp} official site pricing",
            "what_to_extract": ["pricing_tiers", "positioning_tagline", "target_customer", "any_size_claim"],
        })
    return targets


def cmd_plan(args: argparse.Namespace) -> int:
    topic = _build_topic(args.input, args.icp, args.geo)
    queries = _build_queries(topic, args.depth)
    fetch_targets = _build_fetch_targets(topic, args.depth)

    plan = {
        "tool": TOOL_NAME,
        "schema_version": SCHEMA_VERSION,
        "phase": "plan",
        "timestamp": _now_iso(),
        "depth": args.depth,
        "topic": topic,
        "search_queries": queries,
        "fetch_targets": fetch_targets,
        "validation_rubric": {
            "required_sections": _REQUIRED_SECTIONS,
            "min_competitors": 5,
            "min_sizing_sources": 2,
            "staleness_budget_months": 24,
        },
        "summary": (
            f"category={topic['category'][:60]!r}; "
            f"icp={topic['icp'][:40]!r}; "
            f"geo={topic['geo']}; "
            f"queries={len(queries)}; "
            f"seed_fetch_targets={len(fetch_targets)}; "
            f"depth={args.depth}"
        ),
    }
    _emit(plan)
    return 0


# ---------- VALIDATE subcommand ----------

# A "numeric claim" is any of these tokens.
_NUMERIC_CLAIM = re.compile(
    r"\$\s?\d[\d,.]*\s?(?:[KMBT]|thousand|million|billion|trillion)\b"   # $5B, $5 million
    r"|\b\d{1,4}(?:[,.]\d{1,3})?\s?%\b"                                  # 23%, 1.5%
    r"|\b\d{2,}\s+(?:seats?|users?|customers?|engineers?)\b"             # 200 seats
    r"|\b\d{1,4}(?:[,.]\d{1,3})?x\b",                                    # 10x
    re.IGNORECASE,
)
_CITATION = re.compile(r"\[source:\s*([^\]\s]+?)\s*(?:#[^\]]+)?\]")
_YEAR_IN_PARENS = re.compile(r"\((\d{4})\)")
_TABLE_ROW = re.compile(r"^\s*\|.+\|\s*$", re.MULTILINE)


def _section_body(text: str, heading: str) -> str | None:
    """Return the body of a `## heading` section (case-insensitive), up to the
    next `## ` or end of file. Returns None if the section is absent."""
    pat = re.compile(
        rf"(?im)^##\s+{re.escape(heading)}\b\s*\n+(.*?)(?=\n##\s|\Z)",
        re.DOTALL,
    )
    m = pat.search(text)
    return m.group(1) if m else None


def _count_table_rows(body: str) -> int:
    """Count non-header non-separator rows in a markdown table inside `body`."""
    rows = _TABLE_ROW.findall(body)
    if len(rows) < 2:
        return 0
    # Subtract header + separator (the |---|---| line).
    return max(0, len(rows) - 2)


def _check_required_sections(text: str, required: list[str]) -> tuple[list[dict[str, Any]], list[str]]:
    checks: list[dict[str, Any]] = []
    flags: list[str] = []
    for section in required:
        present = _section_body(text, section) is not None
        checks.append({
            "name": f"section_present__{_slug(section)}",
            "passed": present,
            "detail": f"`## {section}` " + ("found" if present else "MISSING"),
        })
        if not present:
            flags.append("missing_section")
    return checks, flags


def _check_competitor_count(text: str, minimum: int) -> tuple[dict[str, Any], list[str], int]:
    body = _section_body(text, "Competitor landscape") or ""
    n = _count_table_rows(body)
    passed = n >= minimum
    return (
        {
            "name": "competitor_count",
            "passed": passed,
            "detail": f"{n} competitor rows (minimum {minimum})",
        },
        [] if passed else ["thin_competitor_set"],
        n,
    )


def _check_sizing_sources(text: str, minimum: int) -> tuple[dict[str, Any], list[str], int]:
    body = _section_body(text, "Market size evidence") or ""
    distinct = {m.group(1) for m in _CITATION.finditer(body)}
    n = len(distinct)
    passed = n >= minimum
    return (
        {
            "name": "sizing_source_count",
            "passed": passed,
            "detail": f"{n} distinct citations under `## Market size evidence` (minimum {minimum})",
        },
        [] if passed else ["single_source_sizing"],
        n,
    )


def _check_citation_density(text: str) -> tuple[dict[str, Any], list[str], list[str]]:
    """Walk the text line by line; flag any line with a numeric claim that
    has no citation on the same line OR the immediately following line.

    Whole sections that are pure narrative (no numbers) don't trigger this.
    """
    lines = text.splitlines()
    uncited: list[str] = []
    for i, line in enumerate(lines):
        if not _NUMERIC_CLAIM.search(line):
            continue
        joined = line + (lines[i + 1] if i + 1 < len(lines) else "")
        if _CITATION.search(joined):
            continue
        uncited.append(line.strip()[:160])
    passed = not uncited
    return (
        {
            "name": "citation_density",
            "passed": passed,
            "detail": (
                "every numeric claim is cited"
                if passed
                else f"{len(uncited)} numeric claim(s) without inline `[source: ...]`"
            ),
        },
        [] if passed else ["uncited_number"],
        uncited,
    )


def _check_citation_resolvability(text: str, raw_dir: str) -> tuple[dict[str, Any], list[str], list[str]]:
    """Every `[source: filename]` reference must point to a file that exists in
    the raw directory. We accept matches by basename — the synth output uses
    bare filenames, while raw_dir holds the actual files."""
    refs = {m.group(1) for m in _CITATION.finditer(text)}
    if not refs:
        # Nothing to check — citation density already flags missing-altogether.
        return (
            {"name": "citation_resolvability", "passed": True, "detail": "no citations to resolve"},
            [],
            [],
        )

    if not os.path.isdir(raw_dir):
        return (
            {
                "name": "citation_resolvability",
                "passed": False,
                "detail": f"raw directory `{raw_dir}` not found — cannot verify citations",
            },
            ["broken_citation"],
            sorted(refs),
        )

    available = set(os.listdir(raw_dir))
    broken = sorted(r for r in refs if r not in available and os.path.basename(r) not in available)
    passed = not broken
    return (
        {
            "name": "citation_resolvability",
            "passed": passed,
            "detail": (
                f"all {len(refs)} citations resolve to files in {raw_dir}"
                if passed
                else f"{len(broken)} broken citation(s): {broken[:5]}{' …' if len(broken) > 5 else ''}"
            ),
        },
        [] if passed else ["broken_citation"],
        broken,
    )


def _check_staleness(text: str, budget_months: int) -> tuple[dict[str, Any], list[str], list[int]]:
    """Find `(YYYY)` year tokens; if any is older than the budget AND there is
    no in-budget corroborating year, emit a warning (not a failure)."""
    years = sorted({int(y) for y in _YEAR_IN_PARENS.findall(text) if 1900 <= int(y) <= 2100})
    if not years:
        return (
            {"name": "citation_staleness", "passed": True, "detail": "no dated citations to check"},
            [],
            [],
        )
    now = _dt.datetime.now()
    cutoff = now.year - max(1, budget_months // 12)
    stale = [y for y in years if y < cutoff]
    fresh_present = any(y >= cutoff for y in years)
    if stale and not fresh_present:
        return (
            {
                "name": "citation_staleness",
                "passed": False,
                "detail": f"all dated citations older than {cutoff} (oldest {min(stale)}, newest {max(stale)}) — no recent corroboration",
            },
            ["stale_citation"],
            stale,
        )
    return (
        {
            "name": "citation_staleness",
            "passed": True,
            "detail": (
                f"newest dated citation is {max(years)}; "
                + (f"{len(stale)} stale citation(s) but corroborated by recent source"
                   if stale else "all citations within freshness budget")
            ),
        },
        [],
        stale,
    )


def cmd_validate(args: argparse.Namespace) -> int:
    try:
        text = _read_text(args.input)
    except OSError as e:
        _emit({
            "tool": TOOL_NAME,
            "phase": "validate",
            "passed": False,
            "error": f"could not read input: {e}",
            "input_file": args.input,
            "timestamp": _now_iso(),
        })
        return 2

    rubric: dict[str, Any] = {
        "required_sections": _REQUIRED_SECTIONS,
        "min_competitors": 5,
        "min_sizing_sources": 2,
        "staleness_budget_months": 24,
    }
    if args.plan and os.path.isfile(args.plan):
        try:
            with open(args.plan, "r", encoding="utf-8") as f:
                plan_obj = json.load(f)
            rubric.update(plan_obj.get("validation_rubric", {}))
        except (OSError, json.JSONDecodeError):
            pass  # Fall through with defaults.

    raw_dir = args.raw_dir or os.path.join(os.path.dirname(os.path.abspath(args.input)), "raw")

    checks: list[dict[str, Any]] = []
    flags: list[str] = []

    sec_checks, sec_flags = _check_required_sections(text, rubric["required_sections"])
    checks.extend(sec_checks)
    flags.extend(sec_flags)

    comp_check, comp_flags, comp_n = _check_competitor_count(text, rubric["min_competitors"])
    checks.append(comp_check)
    flags.extend(comp_flags)

    siz_check, siz_flags, siz_n = _check_sizing_sources(text, rubric["min_sizing_sources"])
    checks.append(siz_check)
    flags.extend(siz_flags)

    dens_check, dens_flags, uncited = _check_citation_density(text)
    checks.append(dens_check)
    flags.extend(dens_flags)

    res_check, res_flags, broken = _check_citation_resolvability(text, raw_dir)
    checks.append(res_check)
    flags.extend(res_flags)

    stale_check, stale_flags, stale_years = _check_staleness(text, rubric["staleness_budget_months"])
    checks.append(stale_check)
    flags.extend(stale_flags)

    # `passed` ignores warnings (stale_citation is a warning, not a failure).
    blocking = {"missing_section", "thin_competitor_set", "single_source_sizing",
                "uncited_number", "broken_citation"}
    passed = not (set(flags) & blocking)

    _emit({
        "tool": TOOL_NAME,
        "schema_version": SCHEMA_VERSION,
        "phase": "validate",
        "timestamp": _now_iso(),
        "input_file": args.input,
        "raw_dir": raw_dir,
        "passed": passed,
        "checks": checks,
        "flags": sorted(set(flags)),
        "extracted": {
            "competitor_row_count": comp_n,
            "sizing_citation_count": siz_n,
            "uncited_numeric_claims": uncited[:20],
            "broken_citations": broken[:20],
            "stale_years": stale_years,
        },
        "summary": (
            f"competitors={comp_n}; sizing_sources={siz_n}; "
            f"flags={sorted(set(flags)) or 'none'}"
        ),
    })
    return 0


# ---------- entry point ----------

def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Helper for the /market-research skill")
    sub = p.add_subparsers(dest="cmd", required=True)

    pp = sub.add_parser("plan", help="Emit a research plan (queries + seed fetch targets)")
    pp.add_argument("--input", required=True, help="Topic string OR path to a .md plan")
    pp.add_argument("--geo", default="global")
    pp.add_argument("--icp", default=None)
    pp.add_argument("--depth", choices=list(_DEPTH_BUDGETS), default="balanced")
    pp.set_defaults(func=cmd_plan)

    pv = sub.add_parser("validate", help="Validate a finished MARKET_RESEARCH.md")
    pv.add_argument("--input", required=True, help="Path to MARKET_RESEARCH.md")
    pv.add_argument("--plan", default=None, help="Path to RESEARCH_PLAN.json (for rubric)")
    pv.add_argument("--raw-dir", default=None,
                    help="Directory containing the cited raw fetch files (default: ./raw next to --input)")
    pv.set_defaults(func=cmd_validate)

    args = p.parse_args(argv[1:])
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
