#!/usr/bin/env python3
"""
verify_application.py - verification tool for application drafts (YC, fellowships,
grad school, grants).

Stdlib-only. Cross-platform (Windows + Unix). No external deps.

Usage (from a skill):
    bash tools/run.sh verify_application.py <draft_path>

Direct invocation:
    py tools/verify_application.py <draft_path>
    python3 tools/verify_application.py <draft_path>

Emits a JSON object to stdout matching the schema in
shared-references/verification-protocols.md.

Input format: a markdown file. Each application question is a level-2 heading
beginning with `## Q:` followed by the question text. An optional length
annotation `[max=N words]` or `[max=N chars]` may appear at the end of the
heading line. The body of the section is the applicant's answer.

Example:

    # YC W26 Application

    ## Q: What is your company going to make? [max=500 chars]
    We sell a CRM for solo lawyers...

    ## Q: Why did you pick this idea? [max=300 words]
    My co-founder spent three years...

Per-answer checks:
    1. Not empty (>=10 non-whitespace chars).
    2. Within length limit if specified.
    3. First sentence is not a generic restating of the question.

Exit code: 0 if all checks pass, 1 if any check fails, 2 on tool error.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

TOOL_NAME = "verify_application"
SCHEMA_VERSION = 1

MIN_ANSWER_CHARS = 10

# Heading line: "## Q: <question text> [optional max annotation]"
# The annotation is captured as a trailing bracketed group.
HEADING_RE = re.compile(
    r"^##\s*Q:\s*(?P<question>.+?)\s*$",
    re.MULTILINE,
)

# Inside a heading's question text, look for a trailing length spec.
# Examples: "[max=500 chars]" "[max=300 words]" (case-insensitive, flexible spacing).
MAX_ANNOTATION_RE = re.compile(
    r"\[\s*max\s*=\s*(?P<n>\d+)\s*(?P<unit>chars?|words?)\s*\]\s*$",
    re.IGNORECASE,
)

# A sentence terminator. Conservative: split on .!? followed by whitespace or end.
SENTENCE_END_RE = re.compile(r"[.!?](?:\s|$)")

# Word-boundary tokenizer for word counts. Treat sequences of [\w'] as a word.
WORD_RE = re.compile(r"[\w']+", re.UNICODE)


def now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def strip_max_annotation(question_text: str) -> tuple[str, int | None, str | None]:
    """
    Given the full heading text after `Q:`, return (clean_question,
    max_value, max_unit). max_unit is "chars" or "words" canonical, or None
    if no annotation was present.
    """
    m = MAX_ANNOTATION_RE.search(question_text)
    if not m:
        return question_text.strip(), None, None
    n = int(m.group("n"))
    unit_raw = m.group("unit").lower()
    unit = "words" if unit_raw.startswith("word") else "chars"
    clean = question_text[: m.start()].rstrip()
    return clean, n, unit


def parse_questions(text: str) -> list[dict]:
    """
    Parse the markdown into a list of {question, max_value, max_unit, body}.
    Bodies are everything between this heading and the next `## Q:` heading
    (or end of file).
    """
    matches = list(HEADING_RE.finditer(text))
    questions: list[dict] = []
    for i, m in enumerate(matches):
        raw_question = m.group("question")
        clean_q, max_value, max_unit = strip_max_annotation(raw_question)
        body_start = m.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[body_start:body_end].strip()
        questions.append(
            {
                "index": i + 1,
                "question": clean_q,
                "max_value": max_value,
                "max_unit": max_unit,
                "body": body,
            }
        )
    return questions


def first_sentence(body: str) -> str:
    """Return the first sentence of body, stripped. If no terminator, the
    first non-empty line."""
    if not body:
        return ""
    body_clean = body.strip()
    m = SENTENCE_END_RE.search(body_clean)
    if m:
        return body_clean[: m.end()].strip()
    # Fall back to first line.
    return body_clean.splitlines()[0].strip() if body_clean else ""


def normalize_for_match(s: str) -> str:
    """Lowercase, strip non-word chars, collapse whitespace."""
    s = s.lower()
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def is_question_restate(question: str, first_sent: str) -> bool:
    """
    Heuristic: the first sentence "restates the question" if it shares an
    unusually high fraction of content words with the question, OR begins
    with the question's interrogative phrase echoed back.

    Returns True when:
      - The first sentence's normalized form contains >=70% of the
        question's content tokens (length >=4 chars), AND the question
        has at least 4 such tokens, OR
      - The first sentence begins with a clear echo pattern like
        "<question phrase verbatim>" with minimal change.
    """
    if not first_sent or not question:
        return False

    q_norm = normalize_for_match(question)
    s_norm = normalize_for_match(first_sent)

    if not q_norm or not s_norm:
        return False

    # Echo-pattern: applicant restates the literal question with a small
    # transformation. Example: question "Why did you pick this idea?" answered
    # "I picked this idea because...", first sentence repeats the verb phrase.
    # Detect this by checking whether the first sentence shares >=60% of the
    # question's content tokens AND those tokens appear in the same order.
    q_tokens = [t for t in q_norm.split() if len(t) >= 4]
    s_tokens = s_norm.split()
    if len(q_tokens) < 3:
        # Question too short to reliably detect restatement.
        return False

    # Count how many of the question's content tokens appear in the first
    # sentence (regardless of order).
    s_set = set(s_tokens)
    overlap = sum(1 for t in q_tokens if t in s_set)
    fraction = overlap / max(1, len(q_tokens))

    if fraction >= 0.7:
        return True

    # Order check: are >=60% of the question's content tokens present in the
    # first sentence in the same order? This catches paraphrastic restatements.
    if fraction >= 0.6:
        # Greedy match: walk through s_tokens, advance through q_tokens.
        qi = 0
        for st in s_tokens:
            if qi < len(q_tokens) and st == q_tokens[qi]:
                qi += 1
        if qi / len(q_tokens) >= 0.6:
            return True

    return False


def char_count(body: str) -> int:
    return len(body)


def word_count(body: str) -> int:
    return len(WORD_RE.findall(body))


def check_answer(q: dict) -> dict:
    """Return a dict of per-answer check results."""
    body = q["body"]
    sub_checks: list[dict] = []

    # 1. Non-empty.
    non_ws_chars = len(re.sub(r"\s+", "", body))
    not_empty = non_ws_chars >= MIN_ANSWER_CHARS
    sub_checks.append(
        {
            "name": "answer_present",
            "passed": not_empty,
            "detail": (
                f"{non_ws_chars} non-whitespace chars (min {MIN_ANSWER_CHARS})"
                if not_empty
                else f"answer empty or near-empty ({non_ws_chars} non-whitespace chars; min {MIN_ANSWER_CHARS})"
            ),
        }
    )

    # 2. Within length limit (if any).
    if q["max_value"] is not None:
        if q["max_unit"] == "chars":
            actual = char_count(body)
            limit_passed = actual <= q["max_value"]
            sub_checks.append(
                {
                    "name": "within_length_limit",
                    "passed": limit_passed,
                    "detail": (
                        f"{actual}/{q['max_value']} chars"
                        if limit_passed
                        else f"OVER LIMIT: {actual}/{q['max_value']} chars (excess: {actual - q['max_value']})"
                    ),
                    "value": actual,
                    "limit": q["max_value"],
                    "unit": "chars",
                }
            )
        else:  # words
            actual = word_count(body)
            limit_passed = actual <= q["max_value"]
            sub_checks.append(
                {
                    "name": "within_length_limit",
                    "passed": limit_passed,
                    "detail": (
                        f"{actual}/{q['max_value']} words"
                        if limit_passed
                        else f"OVER LIMIT: {actual}/{q['max_value']} words (excess: {actual - q['max_value']})"
                    ),
                    "value": actual,
                    "limit": q["max_value"],
                    "unit": "words",
                }
            )
    else:
        sub_checks.append(
            {
                "name": "within_length_limit",
                "passed": True,
                "detail": "no length limit declared in heading",
            }
        )

    # 3. First sentence is not a generic restatement of the question.
    fs = first_sentence(body)
    if not_empty and fs:
        restate = is_question_restate(q["question"], fs)
        sub_checks.append(
            {
                "name": "first_sentence_not_question_restate",
                "passed": not restate,
                "detail": (
                    f"first sentence opens on substance: \"{fs[:80]}{'...' if len(fs) > 80 else ''}\""
                    if not restate
                    else f"first sentence appears to restate the question: \"{fs[:80]}{'...' if len(fs) > 80 else ''}\""
                ),
                "first_sentence": fs,
            }
        )
    else:
        sub_checks.append(
            {
                "name": "first_sentence_not_question_restate",
                "passed": False,
                "detail": "answer empty; cannot evaluate first sentence",
                "first_sentence": "",
            }
        )

    all_passed = all(c["passed"] for c in sub_checks)

    return {
        "question_index": q["index"],
        "question": q["question"],
        "passed": all_passed,
        "sub_checks": sub_checks,
    }


def build_result(*, input_file: str, text: str) -> dict:
    questions = parse_questions(text)

    if not questions:
        return {
            "tool": TOOL_NAME,
            "schema_version": SCHEMA_VERSION,
            "timestamp": now_iso(),
            "input_file": input_file,
            "passed": False,
            "checks": [
                {
                    "name": "questions_found",
                    "passed": False,
                    "detail": "no '## Q:' headings found in the input file",
                }
            ],
            "summary": "no application questions found; expected level-2 headings beginning with '## Q:'",
        }

    per_answer = [check_answer(q) for q in questions]

    # Aggregate top-level checks.
    all_present = all(
        any(
            sc["name"] == "answer_present" and sc["passed"]
            for sc in pa["sub_checks"]
        )
        for pa in per_answer
    )
    all_within_limits = all(
        any(
            sc["name"] == "within_length_limit" and sc["passed"]
            for sc in pa["sub_checks"]
        )
        for pa in per_answer
    )
    no_restates = all(
        any(
            sc["name"] == "first_sentence_not_question_restate" and sc["passed"]
            for sc in pa["sub_checks"]
        )
        for pa in per_answer
    )

    top_checks = [
        {
            "name": "questions_found",
            "passed": True,
            "detail": f"{len(questions)} question(s) parsed",
            "value": len(questions),
        },
        {
            "name": "all_answers_present",
            "passed": all_present,
            "detail": (
                "every question has an answer of at least 10 non-whitespace chars"
                if all_present
                else "one or more answers are empty or near-empty"
            ),
        },
        {
            "name": "within_length_limits",
            "passed": all_within_limits,
            "detail": (
                "every answer with a declared max is within its limit"
                if all_within_limits
                else "one or more answers exceed the declared max"
            ),
        },
        {
            "name": "first_sentence_not_question_restate",
            "passed": no_restates,
            "detail": (
                "no answer restates its question in the first sentence"
                if no_restates
                else "one or more answers restate the question in the first sentence"
            ),
        },
    ]

    passed = all(c["passed"] for c in top_checks)

    failed_top = [c["name"] for c in top_checks if not c["passed"]]
    failed_per_answer = [pa["question_index"] for pa in per_answer if not pa["passed"]]
    if passed:
        summary = f"all checks passed across {len(questions)} answer(s)"
    else:
        parts: list[str] = []
        if failed_top:
            parts.append(f"top-level failures: {', '.join(failed_top)}")
        if failed_per_answer:
            parts.append(
                f"answer(s) with failing sub-checks: {', '.join('Q' + str(i) for i in failed_per_answer)}"
            )
        summary = "; ".join(parts) if parts else "checks failed"

    return {
        "tool": TOOL_NAME,
        "schema_version": SCHEMA_VERSION,
        "timestamp": now_iso(),
        "input_file": input_file,
        "passed": passed,
        "checks": top_checks,
        "per_answer": per_answer,
        "summary": summary,
    }


def parse_args(argv: list[str]) -> str:
    if len(argv) < 2:
        raise SystemExit("usage: verify_application.py <draft_path>")
    if argv[1].startswith("--"):
        raise SystemExit(f"unknown flag: {argv[1]}")
    return argv[1]


def main(argv: list[str]) -> int:
    try:
        draft_path = parse_args(argv)
    except SystemExit as exc:
        err = {
            "tool": TOOL_NAME,
            "schema_version": SCHEMA_VERSION,
            "timestamp": now_iso(),
            "input_file": argv[1] if len(argv) > 1 else "",
            "passed": False,
            "checks": [],
            "summary": str(exc).strip() or "argument error",
            "error": "ArgumentError",
        }
        sys.stdout.write(json.dumps(err, ensure_ascii=False, indent=2))
        sys.stdout.write("\n")
        return 2

    p = Path(draft_path)
    if not p.exists():
        err = {
            "tool": TOOL_NAME,
            "schema_version": SCHEMA_VERSION,
            "timestamp": now_iso(),
            "input_file": draft_path,
            "passed": False,
            "checks": [],
            "summary": f"input file not found: {draft_path}",
            "error": "FileNotFoundError",
        }
        sys.stdout.write(json.dumps(err, ensure_ascii=False, indent=2))
        sys.stdout.write("\n")
        return 2

    # Use utf-8 explicitly for cross-platform consistency.
    text = p.read_text(encoding="utf-8")
    result = build_result(input_file=str(p), text=text)
    sys.stdout.write(json.dumps(result, ensure_ascii=False, indent=2))
    sys.stdout.write("\n")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
