#!/usr/bin/env python3
"""
verify_outbound_message.py — Phase B.7 verification for outbound messages.

Per-message hard checks that bypass persona consensus. A draft message
cannot be APPROVED with a sensitive-trait reference, a surveillance
phrase, a channel that the campaign hasn't authorized, or a length over
the platform cap — no matter how the personas score it.

Stdlib-only. Usage:

    bash tools/run.sh verify_outbound_message.py <message.json> <campaign.json>

`message.json` is a single JSONL record from `candidate_messages.jsonl`
(or any file with the same shape):

    {
      "profileUrl": "...",
      "firstName": "...",
      "channel": "linkedin_connection",
      "personalizationEvidence": ["headline says Founder"],
      "message": "Hi Dana, I saw you ..."
    }

Emits JSON to stdout matching the verification-protocols schema. Failure
on any check → loop generates a CRITICAL fix item.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

TOOL_NAME = "verify_outbound_message"
SCHEMA_VERSION = 1

# Channel caps. linkedin_connection note is hard-capped at 300 by LinkedIn.
# DM and email are softer — picked at a length where personalization survives
# but pitch-slap doesn't.
CHANNEL_LIMITS = {
    "linkedin_connection": 300,
    "linkedin_dm": 900,
    "email": 1500,
}

# Sensitive-trait words to avoid in cold outbound. These are not legal
# advice — they are conservative campaign-safety defaults. The compliance
# persona enforces the same idea downstream; this layer is the
# deterministic backstop.
#
# Design tradeoff. v0.1 used bare-adjective alternations
# (`\b(?:black|white|asian|...)\b`) which caught many real false positives
# in business prose: "black-box testing", "white paper", "race condition",
# "single source of truth", "the age of AI", "religious about test
# coverage". v0.2 tightens each pattern to require *demographic context* —
# the word has to appear in a phrase that's clearly about a person's
# identity, not as a domain term. We accept some false negatives ("you're
# black" without leading "as a" still slips through) in exchange for far
# fewer false-positive CRITICAL fix items wasting persona rounds.
SENSITIVE_TRAIT_PATTERNS = [
    # Age: numeric-anchored or possessive only.
    (r"\b(?:you'?re|you are|aged?)\s+\d+\b", "age"),
    (r"\b\d+\s+years?\s+old\b", "age"),
    (r"\byour age\b", "age"),
    # Family / pregnancy: specific stems.
    (r"\b(?:pregnan|maternity|paternity)\w*", "family_status"),
    (r"\byour (?:wife|husband|spouse|partner|kids?|children|family)\b",
     "family_status"),
    # Disability: specific phrases (not bare "disabled" which appears in
    # "disabled feature flag" etc).
    (r"\b(?:disabled person|disability|wheelchair)\b", "disability"),
    # Health / medical: specific phrases. Drops bare "condition" which
    # collided with "race condition" / "edge condition".
    (r"\b(?:health (?:issue|problem|condition)|medical condition|"
     r"chronic illness|diagnosed with|your health)\b", "health"),
    # Religion: explicit demographic markers. Drops bare "religious" (FP:
    # "religious about test coverage").
    (r"\b(?:christian|muslim|jewish|hindu|buddhist|catholic|atheist)\s+"
     r"(?:faith|background|family|community|values|beliefs|identity)\b",
     "religion"),
    (r"\byour (?:faith|religion)\b", "religion"),
    # Politics: explicit identity markers. Drops bare "liberal" /
    # "conservative" which collide with "liberal arts", "conservative
    # estimate".
    (r"\b(?:democrat|republican|maga|trump|biden|harris)\s+"
     r"(?:supporter|voter|donor|values|policies|administration|years?)\b",
     "politics"),
    (r"\b(?:left|right)[- ]?wing (?:politics|voter|supporter)\b", "politics"),
    # Orientation: explicit identity reference.
    (r"\b(?:gay|lesbian|lgbt|lgbtq|queer|transgender)\s+"
     r"(?:person|community|identity|individual|founder|leader|woman|man)\b",
     "sexual_orientation"),
    (r"\bsexual orientation\b", "sexual_orientation"),
    # Ethnicity: demographic context required. Drops bare adjectives that
    # produced "black box", "white paper", "racial bias" (test-set jargon),
    # "Asian markets" false positives. The multi-word phrases below are
    # demographically anchored on their own — no optional-suffix group,
    # which previously degenerated to matching bare "race".
    (r"\bas (?:a |an )?(?:black|white|asian|hispanic|latino|latina|"
     r"indigenous|asian[- ]american|african[- ]american)\b", "ethnicity"),
    (r"\b(?:your )?(?:ethnic background|ethnicity|racial background)\b",
     "ethnicity"),
    # Marital: demographic context required. Drops bare "single" which
    # produced "single source of truth", "single tenant", "single page
    # application" false positives.
    (r"\b(?:as a |since you'?re |because you'?re )"
     r"(?:married|single|divorced|widowed)\b", "marital_status"),
    (r"\b(?:married|single|divorced|widowed)\s+"
     r"(?:woman|man|mom|dad|mother|father|parent)\b", "marital_status"),
]

# Surveillance / creepy phrasing that prospects flag as stalker-y.
SURVEILLANCE_PATTERNS = [
    (r"i (?:saw|noticed|see|saw that) you (?:viewed|visited|looked at|checked out)",
     "saw_you_viewed"),
    (r"i noticed you are probably", "i_noticed_you_are_probably"),
    (r"based on your (?:personal|private) life", "personal_life_reference"),
    (r"i'?ve been (?:watching|following|tracking) you", "watching_you"),
    (r"your (?:wife|husband|spouse|kids?|children)", "family_reference"),
]

# Fake-familiarity / pitch-slap tells that frequently produce auto-decline.
FAKE_CLAIMS_PATTERNS = [
    (r"\bas (?:you|we) discussed\b", "fabricated_prior_conversation"),
    (r"\bfollowing up on our (?:call|chat|meeting)\b", "fabricated_prior_meeting"),
    (r"\b(?:per|as per) our (?:last )?(?:call|chat|conversation)\b",
     "fabricated_prior_conversation"),
    (r"\bnice to (?:meet|see) you again\b", "fabricated_prior_meeting"),
]


def now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def find_pattern_hits(text: str, patterns: list[tuple[str, str]]) -> list[dict]:
    """Return a list of {pattern, label, match} dicts for every pattern that fires."""
    if not text:
        return []
    hits: list[dict] = []
    for pat, label in patterns:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            hits.append({"pattern": pat, "label": label, "match": m.group(0)})
    return hits


def check_message_length(message: str, channel: str) -> dict:
    limit = CHANNEL_LIMITS.get(channel)
    if limit is None:
        return {
            "name": "message_length",
            "passed": False,
            "detail": f"unknown channel '{channel}'; expected one of {sorted(CHANNEL_LIMITS)}",
            "value": len(message or ""),
            "limit": None,
        }
    n = len(message or "")
    return {
        "name": "message_length",
        "passed": n <= limit,
        "detail": f"{n}/{limit} chars on channel '{channel}'",
        "value": n,
        "limit": limit,
    }


def check_evidence_count(evidence) -> dict:
    items = [e for e in (evidence or []) if isinstance(e, str) and e.strip()]
    return {
        "name": "evidence_count",
        "passed": len(items) >= 1,
        "detail": (
            f"{len(items)} personalization evidence item(s)"
            if items
            else "no personalizationEvidence items — message is generic"
        ),
        "value": len(items),
    }


def check_forbidden_claims(message: str) -> dict:
    sens = find_pattern_hits(message, SENSITIVE_TRAIT_PATTERNS)
    surv = find_pattern_hits(message, SURVEILLANCE_PATTERNS)
    fake = find_pattern_hits(message, FAKE_CLAIMS_PATTERNS)
    all_hits = sens + surv + fake
    return {
        "name": "forbidden_claims",
        "passed": not all_hits,
        "detail": (
            "no sensitive-trait, surveillance, or fake-familiarity phrasing detected"
            if not all_hits
            else "found: "
            + ", ".join(
                f"{h['label']}('{h['match']}')" for h in all_hits[:5]
            )
            + ("…" if len(all_hits) > 5 else "")
        ),
        "sensitive_traits": [h["label"] for h in sens],
        "surveillance": [h["label"] for h in surv],
        "fake_claims": [h["label"] for h in fake],
    }


def check_channel_authorized(channel: str, campaign: dict) -> dict:
    channels = campaign.get("channels") or {}
    # linkedin_* channels are always allowed (LinkedIn is the platform the
    # workflow targets). email/phone require explicit opt-in in the
    # campaign config.
    if channel in ("linkedin_connection", "linkedin_dm"):
        return {
            "name": "channel_authorized",
            "passed": True,
            "detail": f"linkedin channel '{channel}' allowed by default",
        }
    if channel == "email":
        ok = bool(channels.get("email"))
        return {
            "name": "channel_authorized",
            "passed": ok,
            "detail": (
                "campaign.channels.email = true"
                if ok
                else "channel=email but campaign.channels.email is not set to true"
            ),
        }
    if channel == "phone":
        ok = bool(channels.get("phone"))
        return {
            "name": "channel_authorized",
            "passed": ok,
            "detail": (
                "campaign.channels.phone = true"
                if ok
                else "channel=phone but campaign.channels.phone is not set to true"
            ),
        }
    return {
        "name": "channel_authorized",
        "passed": False,
        "detail": f"unknown channel '{channel}'",
    }


def parse_args(argv: list[str]) -> dict:
    if len(argv) < 3:
        raise SystemExit(
            "usage: verify_outbound_message.py <message.json> <campaign.json>"
        )
    return {"message_path": argv[1], "campaign_path": argv[2]}


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

    msg_path = Path(args["message_path"])
    camp_path = Path(args["campaign_path"])
    for label, p in (("message", msg_path), ("campaign", camp_path)):
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
        message_obj = load_json(msg_path)
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

    if not isinstance(message_obj, dict):
        sys.stdout.write(
            json.dumps(
                error_result(
                    "message.json must be a JSON object (one candidate message)",
                    "TypeError",
                    ["input_invalid"],
                ),
                ensure_ascii=False,
                indent=2,
            )
            + "\n"
        )
        return 2

    message_text = message_obj.get("message") or ""
    channel = message_obj.get("channel") or ""
    evidence = message_obj.get("personalizationEvidence") or []

    checks = [
        check_message_length(message_text, channel),
        check_evidence_count(evidence),
        check_forbidden_claims(message_text),
        check_channel_authorized(channel, campaign),
    ]

    flags: list[str] = []
    for c in checks:
        if c["passed"]:
            continue
        if c["name"] == "message_length":
            flags.append("message_too_long")
        elif c["name"] == "evidence_count":
            flags.append("no_personalization_evidence")
        elif c["name"] == "forbidden_claims":
            if c.get("sensitive_traits"):
                flags.append("sensitive_trait")
            if c.get("surveillance"):
                flags.append("surveillance_phrasing")
            if c.get("fake_claims"):
                flags.append("fake_familiarity")
        elif c["name"] == "channel_authorized":
            flags.append("channel_unauthorized")

    passed = all(c["passed"] for c in checks)
    summary = (
        f"all {len(checks)} checks passed"
        if passed
        else "; ".join(f"{c['name']} FAIL" for c in checks if not c["passed"])
    )

    result = {
        "tool": TOOL_NAME,
        "schema_version": SCHEMA_VERSION,
        "timestamp": now_iso(),
        "input_file": str(msg_path),
        "campaign_file": str(camp_path),
        "profile_slug": message_obj.get("profile_slug") or message_obj.get("profileUrl"),
        "channel": channel,
        "passed": passed,
        "checks": checks,
        "flags": flags,
        "summary": summary,
    }
    sys.stdout.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
