#!/usr/bin/env python3
"""
verify_cv.py - verification tool for CV / resume markdown drafts.

Stdlib-only. Cross-platform (Windows + Unix). No external deps.

Usage (from a skill):
    bash tools/run.sh verify_cv.py <draft_path> [--target-pages=1|2]

Direct invocation:
    py  tools/verify_cv.py <draft_path> [--target-pages=1|2]
    python3 tools/verify_cv.py <draft_path> [--target-pages=1|2]

Emits a JSON object to stdout matching the schema in
shared-references/verification-protocols.md.

Checks (all enforced; CV is "passed" only if all pass):
    1. page_estimate          - words/500 within target +/- 20%
    2. action_verb_first      - >=80% of Experience bullets start with strong action verb
    3. quantified_bullets_pct - >=50% of Experience bullets contain a digit
    4. cliche_density         - <=2 cliches per 1000 words
    5. date_format_consistent - all role headers use the same date-range format
    6. tense_consistency      - past roles use past-tense; current role can be present
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

TOOL_NAME = "verify_cv"
SCHEMA_VERSION = 1

# Strong action verbs allowed at the start of an Experience bullet (case-insensitive match
# on the first whitespace-delimited token, with optional trailing punctuation stripped).
ACTION_VERBS = {
    "built", "build", "shipped", "ship", "drove", "drive", "designed", "design",
    "scaled", "scale", "reduced", "reduce", "grew", "grow", "founded", "found",
    "led", "lead", "owned", "own", "launched", "launch", "migrated", "migrate",
    "refactored", "refactor", "automated", "automate", "mentored", "mentor",
    "hired", "hire", "delivered", "deliver", "created", "create", "developed",
    "develop", "implemented", "implement", "improved", "improve", "increased",
    "increase", "decreased", "decrease", "reorganized", "reorganize",
    "rearchitected", "rearchitect", "architected", "architect", "negotiated",
    "negotiate", "won", "win", "wrote", "write", "presented", "present",
    "trained", "train", "taught", "teach", "coached", "coach", "introduced",
    "introduce", "established", "establish", "founded", "spearheaded",
    "spearhead", "championed", "champion", "deployed", "deploy", "rolled",
    "roll", "ran", "run", "managed", "manage", "directed", "direct",
    "supervised", "supervise", "engineered", "engineer", "optimized",
    "optimize", "rewrote", "rewrite", "investigated", "investigate",
    "diagnosed", "diagnose", "secured", "secure", "saved", "save",
    "earned", "earn", "drafted", "draft", "produced", "produce",
    "released", "release", "tested", "test", "debugged", "debug",
    "instrumented", "instrument", "consolidated", "consolidate",
    "streamlined", "streamline", "expanded", "expand", "supported",
    "support", "fixed", "fix", "resolved", "resolve",
}

# Weak openers that disqualify a bullet from "starts with strong action verb".
# Tracked separately so the JSON output can name the offending pattern.
WEAK_OPENERS = {
    "responsible", "helped", "worked", "involved", "assisted", "participated",
    "collaborated",  # collaborated alone is weak; "collaborated with X to ship Y" still gets flagged here
    "tasked", "assigned",
}

# Cliches counted toward density. Lowercase exact-phrase match against the body text.
CLICHES = [
    "results-driven",
    "results driven",
    "passionate about",
    "passionate",
    "team player",
    "self-starter",
    "self starter",
    "go-getter",
    "go getter",
    "synergy",
    "transformational",
    "thought leader",
    "wear many hats",
    "wears many hats",
    "wearing many hats",
    "hit the ground running",
    "hits the ground running",
    "hitting the ground running",
    "out-of-the-box thinking",
    "out of the box thinking",
    "outside the box",
    "outside-the-box",
    "track record of success",
    "proven track record",
    "dynamic professional",
    "highly motivated",
    "detail-oriented",
    "detail oriented",
]

# "leverage" / "leveraging" / "leveraged" used as a verb. We look for the bare token;
# the noun "leverage" is uncommon enough in CVs that this is a fair approximation.
LEVERAGE_VERB_RE = re.compile(r"\b(leverag(?:e|es|ed|ing))\b", re.IGNORECASE)

# Markdown structure
H2_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
H3_RE = re.compile(r"^###\s+(.+?)\s*$", re.MULTILINE)
BULLET_RE = re.compile(r"^[\-\*\+]\s+(.+?)\s*$", re.MULTILINE)

# Date-range patterns we recognize. Each matches a range; we classify by which one wins.
# We deliberately include the "till" / "to" / dash variants because they are common ATS killers.
MONTH_NAMES = (
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|"
    r"Dec(?:ember)?)"
)
SEPARATORS = r"(?:\s*(?:[-–—]|to|till|until|through|thru)\s*)"
DATE_FMT_PATTERNS = [
    # MMM YYYY - MMM YYYY (with hyphen, en-dash, em-dash, "to", or "till"); allows "present" / "current"
    (
        "MMM_YYYY",
        re.compile(
            rf"\b{MONTH_NAMES}\.?\s+\d{{4}}{SEPARATORS}(?:{MONTH_NAMES}\.?\s+\d{{4}}|present|current|now)\b",
            re.IGNORECASE,
        ),
    ),
    # MM/YYYY - MM/YYYY
    (
        "MM_YYYY",
        re.compile(
            rf"\b\d{{1,2}}/\d{{4}}{SEPARATORS}(?:\d{{1,2}}/\d{{4}}|present|current|now)\b",
            re.IGNORECASE,
        ),
    ),
    # YYYY - YYYY
    (
        "YYYY",
        re.compile(
            rf"\b\d{{4}}{SEPARATORS}(?:\d{{4}}|present|current|now)\b",
            re.IGNORECASE,
        ),
    ),
]

# A pattern we explicitly call out as ATS-hostile: the word "till" or "until" inside a date range.
TILL_RE = re.compile(rf"\b\d{{4}}\s*(?:till|until)\s*\d{{4}}\b", re.IGNORECASE)

# Past-tense detection (best-effort). We look at the first word of each bullet; if it ends in "ing"
# or "s" (third person singular present) inside what's marked as a past role, that's a flag.
ING_RE = re.compile(r"^[A-Za-z]+ing\b")
THIRD_PERSON_S_RE = re.compile(r"^[A-Za-z]+s\b")  # leads, ships, manages — present tense for current roles


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_token(tok: str) -> str:
    """Lowercase, strip trailing punctuation; used for action-verb lookup."""
    return tok.lower().rstrip(".,;:!?\"')")


def parse_sections(text: str) -> dict[str, str]:
    """Split markdown text into sections keyed by H2 heading (lowercased)."""
    sections: dict[str, str] = {}
    matches = list(H2_RE.finditer(text))
    for i, m in enumerate(matches):
        name = m.group(1).strip().lower()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections[name] = text[start:end]
    return sections


def find_experience_section(sections: dict[str, str]) -> str:
    """Find the Experience section by common alias (returns empty string if absent)."""
    for key in ("experience", "work experience", "professional experience", "employment"):
        if key in sections:
            return sections[key]
    return ""


def find_role_headers(experience_text: str) -> list[tuple[str, int]]:
    """Return (header_text, start_offset) for each ### heading inside Experience."""
    return [(m.group(1).strip(), m.start()) for m in H3_RE.finditer(experience_text)]


def split_role_blocks(experience_text: str) -> list[tuple[str, str]]:
    """Return list of (header, body) for each role inside Experience."""
    headers = find_role_headers(experience_text)
    blocks: list[tuple[str, str]] = []
    for i, (header, start) in enumerate(headers):
        body_start = experience_text.find("\n", start) + 1 if experience_text.find("\n", start) != -1 else start
        body_end = headers[i + 1][1] if i + 1 < len(headers) else len(experience_text)
        blocks.append((header, experience_text[body_start:body_end]))
    return blocks


def extract_bullets(block: str) -> list[str]:
    """Pull out the bullet bodies (without leading - / *)."""
    return [m.group(1).strip() for m in BULLET_RE.finditer(block)]


def starts_with_action_verb(bullet: str) -> tuple[bool, str]:
    """Return (passes, first_token_lowercased)."""
    bullet_clean = bullet.lstrip()
    # Strip leading bold/italic markers
    bullet_clean = re.sub(r"^[*_`]+", "", bullet_clean)
    if not bullet_clean:
        return False, ""
    first = normalize_token(bullet_clean.split()[0])
    if first in WEAK_OPENERS:
        return False, first
    if first in ACTION_VERBS:
        return True, first
    return False, first


def has_digit(text: str) -> bool:
    return any(c.isdigit() for c in text)


def count_words(text: str) -> int:
    """Word count; collapses whitespace; ignores markdown markers."""
    cleaned = re.sub(r"[`*_#>\-\[\]\(\)]", " ", text)
    return len([t for t in cleaned.split() if t])


def count_cliches(text: str) -> tuple[int, list[str]]:
    """Count distinct cliche occurrences. Returns (count, list of phrases found)."""
    lower = text.lower()
    found: list[str] = []
    for phrase in CLICHES:
        idx = 0
        while True:
            idx = lower.find(phrase, idx)
            if idx == -1:
                break
            # Word-boundary check on both sides
            left_ok = idx == 0 or not lower[idx - 1].isalnum()
            right_idx = idx + len(phrase)
            right_ok = right_idx >= len(lower) or not lower[right_idx].isalnum()
            if left_ok and right_ok:
                found.append(phrase)
            idx = right_idx
    # leverage-as-verb counted separately
    for m in LEVERAGE_VERB_RE.finditer(text):
        found.append(m.group(1).lower())
    return len(found), found


def detect_date_format(header: str) -> str | None:
    """Return the format-tag of the FIRST matching date pattern in this header, or None."""
    for tag, pattern in DATE_FMT_PATTERNS:
        if pattern.search(header):
            return tag
    return None


def header_uses_till(header: str) -> bool:
    return bool(TILL_RE.search(header))


def is_current_role(header: str) -> bool:
    return bool(re.search(r"\b(present|current|now)\b", header, re.IGNORECASE))


def check_tense(blocks: list[tuple[str, str]]) -> tuple[bool, list[str]]:
    """
    Best-effort tense check. For non-current roles, flag bullets whose first verb
    looks present-tense (ends -s or -ing). For the current role, allow either,
    but flag mixed within the same role.

    Returns (passed, list of flagged headers).
    """
    flagged: list[str] = []
    for header, body in blocks:
        bullets = extract_bullets(body)
        if not bullets:
            continue
        present_count = 0
        past_count = 0
        for b in bullets:
            b_clean = re.sub(r"^[*_`]+", "", b.lstrip())
            if not b_clean:
                continue
            first = normalize_token(b_clean.split()[0])
            if not first:
                continue
            if ING_RE.match(b_clean) or THIRD_PERSON_S_RE.match(b_clean):
                # Crude present-tense signal
                if first not in ACTION_VERBS:
                    present_count += 1
                    continue
            # Anything else, treat as past-tense if it's a recognized action verb in past form
            if first.endswith("ed") or first in {"led", "ran", "built", "shipped", "drove", "grew", "won", "wrote", "found", "founded", "owned", "made", "set", "took", "gave", "saved"}:
                past_count += 1
        if not is_current_role(header):
            # Past role; flag if mostly present-tense
            if present_count > past_count and present_count >= 2:
                flagged.append(header)
    return (len(flagged) == 0, flagged)


def build_result(*, input_file: str, text: str, target_pages: float) -> dict:
    word_count = count_words(text)
    estimated_pages = round(word_count / 500.0, 2)
    sections = parse_sections(text)
    exp_section = find_experience_section(sections)
    role_blocks = split_role_blocks(exp_section) if exp_section else []
    all_bullets: list[str] = []
    for _, body in role_blocks:
        all_bullets.extend(extract_bullets(body))
    bullet_count = len(all_bullets)

    # 1. page_estimate (target +/- 20%)
    if target_pages <= 0:
        target_pages = 1.0
    lower_bound = target_pages * 0.8
    upper_bound = target_pages * 1.2
    pages_passed = lower_bound <= estimated_pages <= upper_bound
    pages_check = {
        "name": "page_estimate",
        "passed": pages_passed,
        "value": estimated_pages,
        "target": target_pages,
        "detail": (
            f"{word_count} words ~ {estimated_pages} pages "
            f"(target {target_pages} +/- 20%, allowed {lower_bound:.2f}-{upper_bound:.2f})"
        ),
    }

    # 2. action_verb_first (>=80%)
    action_pass_count = 0
    weak_opener_examples: list[str] = []
    for b in all_bullets:
        ok, first = starts_with_action_verb(b)
        if ok:
            action_pass_count += 1
        else:
            if first in WEAK_OPENERS and len(weak_opener_examples) < 5:
                weak_opener_examples.append(b[:80])
    action_pct = round(100.0 * action_pass_count / bullet_count, 1) if bullet_count else 0.0
    action_check = {
        "name": "action_verb_first",
        "passed": action_pct >= 80.0 and bullet_count > 0,
        "value": action_pct,
        "target": 80.0,
        "detail": (
            f"{action_pass_count} of {bullet_count} bullets start with a strong action verb "
            f"({action_pct}%); target >=80%"
            + (f". Weak-opener examples: {weak_opener_examples}" if weak_opener_examples else "")
        ),
    }

    # 3. quantified_bullets_pct (>=50%)
    quantified_count = sum(1 for b in all_bullets if has_digit(b))
    quantified_pct = round(100.0 * quantified_count / bullet_count, 1) if bullet_count else 0.0
    quantified_check = {
        "name": "quantified_bullets_pct",
        "passed": quantified_pct >= 50.0 and bullet_count > 0,
        "value": quantified_pct,
        "target": 50.0,
        "detail": (
            f"{quantified_count} of {bullet_count} bullets contain a digit "
            f"({quantified_pct}%); target >=50%"
        ),
    }

    # 4. cliche_density (<=2 per 1000 words)
    cliche_count, cliche_list = count_cliches(text)
    density = round(1000.0 * cliche_count / word_count, 2) if word_count else 0.0
    cliche_check = {
        "name": "cliche_density",
        "passed": density <= 2.0,
        "value": density,
        "target": 2.0,
        "detail": (
            f"{cliche_count} cliche(s) detected per {word_count} words = {density} per 1000; target <=2"
            + (f". Cliches found: {sorted(set(cliche_list))}" if cliche_list else "")
        ),
    }

    # 5. date_format_consistent
    formats_seen: list[tuple[str, str]] = []  # (header, format-tag-or-NONE)
    till_violations: list[str] = []
    for header, _ in role_blocks:
        tag = detect_date_format(header)
        formats_seen.append((header, tag or "UNKNOWN"))
        if header_uses_till(header):
            till_violations.append(header)
    distinct_formats = {tag for _, tag in formats_seen if tag != "UNKNOWN"}
    has_unknown = any(tag == "UNKNOWN" for _, tag in formats_seen)
    consistent = (len(distinct_formats) <= 1) and (not has_unknown) and (not till_violations)
    date_check = {
        "name": "date_format_consistent",
        "passed": consistent and len(role_blocks) > 0,
        "value": consistent,
        "detail": (
            f"{len(role_blocks)} role header(s); "
            f"distinct date formats: {sorted(distinct_formats) or '[]'}; "
            f"unrecognized: {[h for h, t in formats_seen if t == 'UNKNOWN']}; "
            f"'till'/'until' usage: {till_violations}"
        ),
    }

    # 6. tense_consistency
    tense_passed, tense_flagged = check_tense(role_blocks)
    tense_check = {
        "name": "tense_consistency",
        "passed": tense_passed,
        "value": tense_passed,
        "detail": (
            "past roles use past tense; current role can use present"
            if tense_passed
            else f"flagged role headers (likely present-tense in a past role): {tense_flagged}"
        ),
    }

    checks = [
        pages_check,
        action_check,
        quantified_check,
        cliche_check,
        date_check,
        tense_check,
    ]
    passed = all(c["passed"] for c in checks)
    failed_names = [c["name"] for c in checks if not c["passed"]]
    summary = (
        "all checks passed"
        if passed
        else f"{len(failed_names)} of {len(checks)} checks failed: {', '.join(failed_names)}"
    )

    return {
        "tool": TOOL_NAME,
        "schema_version": SCHEMA_VERSION,
        "timestamp": now_iso(),
        "input_file": input_file,
        "passed": passed,
        "checks": checks,
        "summary": summary,
        "metrics": {
            "word_count": word_count,
            "estimated_pages": estimated_pages,
            "experience_bullets": bullet_count,
            "quantified_pct": quantified_pct,
            "cliche_count": cliche_count,
        },
    }


def parse_args(argv: list[str]) -> tuple[str, float]:
    if len(argv) < 2:
        raise SystemExit(
            "usage: verify_cv.py <draft_path> [--target-pages=1|2]"
        )
    draft_path = argv[1]
    target_pages = 1.0
    for arg in argv[2:]:
        if arg.startswith("--target-pages="):
            try:
                target_pages = float(arg.split("=", 1)[1])
            except ValueError:
                raise SystemExit(f"invalid --target-pages value: {arg}")
        elif arg.startswith("--"):
            raise SystemExit(f"unknown flag: {arg}")
        else:
            # Allow positional fallback for target pages
            try:
                target_pages = float(arg)
            except ValueError:
                raise SystemExit(f"unknown positional argument: {arg}")
    return draft_path, target_pages


def emit_error(input_file: str, summary: str, exc_name: str) -> None:
    err = {
        "tool": TOOL_NAME,
        "schema_version": SCHEMA_VERSION,
        "timestamp": now_iso(),
        "input_file": input_file,
        "passed": False,
        "checks": [],
        "summary": summary,
        "error": exc_name,
    }
    sys.stdout.write(json.dumps(err, ensure_ascii=False, indent=2))
    sys.stdout.write("\n")


def main(argv: list[str]) -> int:
    try:
        draft_path, target_pages = parse_args(argv)
    except (ValueError, SystemExit) as exc:
        emit_error(argv[1] if len(argv) > 1 else "", str(exc).strip() or "argument error", type(exc).__name__)
        return 2

    p = Path(draft_path)
    if not p.exists():
        emit_error(draft_path, f"input file not found: {draft_path}", "FileNotFoundError")
        return 2

    try:
        text = p.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as exc:
        emit_error(draft_path, f"could not read draft: {exc}", type(exc).__name__)
        return 2

    try:
        result = build_result(input_file=str(p), text=text, target_pages=target_pages)
    except Exception as exc:  # defensive: never traceback to stdout
        emit_error(draft_path, f"unexpected error during verification: {exc}", type(exc).__name__)
        return 2

    sys.stdout.write(json.dumps(result, ensure_ascii=False, indent=2))
    sys.stdout.write("\n")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
