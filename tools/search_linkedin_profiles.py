#!/usr/bin/env python3
"""
search_linkedin_profiles.py — optional Apify lead discovery pre-step.

Reads campaign.lead_search, runs an Apify people-search Actor, extracts
LinkedIn profile URLs, and writes a campaign copy with profileUrls filled.

Usage:
    bash tools/run.sh search_linkedin_profiles.py campaigns/name.json \
        --out-dir=review-stage/outbound \
        --update-campaign

The Apify token must be provided via APIFY_TOKEN. The token is never written
to disk.
"""
from __future__ import annotations

import json
import os
import re
import ssl
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

TOOL_NAME = "search_linkedin_profiles"
SCHEMA_VERSION = 1
DEFAULT_OUT_DIR = "review-stage/outbound"
DEFAULT_ACTOR = "harvestapi/linkedin-profile-search"
DEFAULT_TIMEOUT_SECONDS = 180

PROFILE_URL_RE = re.compile(
    r"^https://(?:[a-z]{2,3}\.)?linkedin\.com/in/[A-Za-z0-9\-_%]+/?$",
    re.IGNORECASE,
)


def now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def actor_to_url_path(actor: str) -> str:
    return actor.replace("/", "~", 1)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def parse_args(argv: list[str]) -> dict:
    if len(argv) < 2:
        raise SystemExit(
            "usage: search_linkedin_profiles.py <campaign.json> "
            "[--out-dir=...] [--update-campaign] [--timeout=180]"
        )
    args = {
        "campaign_path": argv[1],
        "out_dir": DEFAULT_OUT_DIR,
        "update_campaign": False,
        "timeout_seconds": DEFAULT_TIMEOUT_SECONDS,
    }
    for a in argv[2:]:
        if a.startswith("--out-dir="):
            args["out_dir"] = a.split("=", 1)[1]
        elif a == "--update-campaign":
            args["update_campaign"] = True
        elif a.startswith("--timeout="):
            args["timeout_seconds"] = int(a.split("=", 1)[1])
        else:
            raise SystemExit(f"unknown flag: {a}")
    return args


def error_result(input_file: str, summary: str, error: str, flags: list[str]) -> dict:
    return {
        "tool": TOOL_NAME,
        "schema_version": SCHEMA_VERSION,
        "timestamp": now_iso(),
        "input_file": input_file,
        "passed": False,
        "checks": [],
        "flags": flags,
        "summary": summary,
        "error": error,
    }


def call_apify_actor(
    *,
    actor: str,
    token: str,
    actor_input: dict,
    timeout_seconds: int,
) -> tuple[list[dict] | None, str | None, int | None]:
    url = (
        f"https://api.apify.com/v2/acts/{actor_to_url_path(actor)}"
        f"/run-sync-get-dataset-items"
    )
    body = json.dumps(actor_input).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "auto-essay-review-loop/search_linkedin_profiles",
        },
        method="POST",
    )
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds, context=ctx) as resp:
            raw = resp.read().decode("utf-8")
            parsed = json.loads(raw)
            if not isinstance(parsed, list):
                return None, f"apify returned {type(parsed).__name__}, expected list", resp.status
            return parsed, None, resp.status
    except json.JSONDecodeError as exc:
        return None, f"apify returned non-JSON: {exc}", None
    except urllib.error.HTTPError as exc:
        return None, f"HTTP {exc.code} {exc.reason}", exc.code
    except urllib.error.URLError as exc:
        return None, f"URLError: {exc.reason}", None
    except TimeoutError:
        return None, f"timeout after {timeout_seconds}s", None
    except Exception as exc:  # noqa: BLE001
        return None, f"{type(exc).__name__}: {exc}", None


def iter_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for nested in value.values():
            yield from iter_strings(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from iter_strings(nested)


def extract_profile_urls(records: list[dict]) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()
    candidate_keys = (
        "url",
        "profileUrl",
        "profile_url",
        "linkedinUrl",
        "linkedin_url",
        "linkedinProfileUrl",
        "linkedin_profile_url",
        "profileLink",
        "profile_link",
    )
    for rec in records:
        if not isinstance(rec, dict):
            continue
        found_for_record = False
        for key in candidate_keys:
            raw = rec.get(key)
            if not isinstance(raw, str):
                continue
            url = raw.strip()
            if not PROFILE_URL_RE.match(url):
                continue
            normalized = url.rstrip("/") + "/"
            if normalized in seen:
                continue
            seen.add(normalized)
            urls.append(normalized)
            found_for_record = True
            break
        if found_for_record:
            continue
        for raw in iter_strings(rec):
            url = raw.strip()
            if not PROFILE_URL_RE.match(url):
                continue
            normalized = url.rstrip("/") + "/"
            if normalized in seen:
                continue
            seen.add(normalized)
            urls.append(normalized)
            break
    return urls


def main(argv: list[str]) -> int:
    try:
        args = parse_args(argv)
    except SystemExit as exc:
        sys.stdout.write(
            json.dumps(error_result("", str(exc), "ArgumentError", ["argument_error"]), indent=2)
            + "\n"
        )
        return 2

    campaign_path = Path(args["campaign_path"])
    out_dir = Path(args["out_dir"])
    if not campaign_path.exists():
        sys.stdout.write(
            json.dumps(
                error_result(
                    str(campaign_path),
                    f"campaign file not found: {campaign_path}",
                    "FileNotFoundError",
                    ["campaign_missing"],
                ),
                indent=2,
            )
            + "\n"
        )
        return 2

    try:
        campaign = load_json(campaign_path)
    except (json.JSONDecodeError, OSError, UnicodeDecodeError) as exc:
        sys.stdout.write(
            json.dumps(
                error_result(
                    str(campaign_path),
                    f"could not parse campaign JSON: {exc}",
                    type(exc).__name__,
                    ["campaign_invalid"],
                ),
                indent=2,
            )
            + "\n"
        )
        return 2

    lead_search = campaign.get("lead_search") or {}
    actor = lead_search.get("actor") or DEFAULT_ACTOR
    actor_input = lead_search.get("input") or {}
    token = os.environ.get("APIFY_TOKEN", "").strip()

    checks = [
        {
            "name": "lead_search_present",
            "passed": bool(actor_input),
            "detail": "campaign.lead_search.input present"
            if actor_input
            else "campaign.lead_search.input missing",
        },
        {
            "name": "apify_token_present",
            "passed": bool(token),
            "detail": "APIFY_TOKEN is set"
            if token
            else "APIFY_TOKEN missing — export it before running discovery",
        },
    ]
    flags: list[str] = []
    if not actor_input:
        flags.append("lead_search_missing")
    if not token:
        flags.append("missing_apify_token")
    if flags:
        result = {
            "tool": TOOL_NAME,
            "schema_version": SCHEMA_VERSION,
            "timestamp": now_iso(),
            "input_file": str(campaign_path),
            "out_dir": str(out_dir),
            "actor": actor,
            "passed": False,
            "checks": checks,
            "flags": flags,
            "summary": "; ".join(c["detail"] for c in checks if not c["passed"]),
        }
        sys.stdout.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        return 1

    records, error, status = call_apify_actor(
        actor=actor,
        token=token,
        actor_input=actor_input,
        timeout_seconds=args["timeout_seconds"],
    )
    if records is None:
        result = {
            "tool": TOOL_NAME,
            "schema_version": SCHEMA_VERSION,
            "timestamp": now_iso(),
            "input_file": str(campaign_path),
            "out_dir": str(out_dir),
            "actor": actor,
            "passed": False,
            "checks": checks
            + [
                {
                    "name": "actor_run_completed",
                    "passed": False,
                    "detail": error,
                    "http_status": status,
                }
            ],
            "flags": ["actor_run_failed"],
            "summary": f"Apify actor failed: {error}",
        }
        sys.stdout.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        return 1

    urls = extract_profile_urls(records)
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_path = out_dir / "searched_profiles.raw.json"
    urls_path = out_dir / "discovered_profile_urls.json"
    generated_campaign_path = out_dir / f"{campaign_path.stem}.discovered.json"
    write_json(raw_path, records)
    write_json(urls_path, urls)

    generated = dict(campaign)
    existing = [
        u.rstrip("/") + "/"
        for u in (campaign.get("profileUrls") or [])
        if isinstance(u, str) and PROFILE_URL_RE.match(u.strip())
    ]
    merged = list(dict.fromkeys(existing + urls))
    generated["profileUrls"] = merged[: int(campaign.get("max_prospects") or len(merged))]
    write_json(generated_campaign_path, generated)
    if args["update_campaign"]:
        write_json(campaign_path, generated)

    checks.extend(
        [
            {
                "name": "actor_run_completed",
                "passed": True,
                "detail": f"{len(records)} record(s) returned by {actor}",
                "value": len(records),
            },
            {
                "name": "profile_urls_found",
                "passed": bool(urls),
                "detail": f"{len(urls)} LinkedIn profile URL(s) extracted",
                "value": len(urls),
            },
        ]
    )
    passed = bool(urls)
    result = {
        "tool": TOOL_NAME,
        "schema_version": SCHEMA_VERSION,
        "timestamp": now_iso(),
        "input_file": str(campaign_path),
        "out_dir": str(out_dir),
        "actor": actor,
        "passed": passed,
        "checks": checks,
        "flags": [] if passed else ["no_profile_urls_found"],
        "raw_output": str(raw_path),
        "urls_output": str(urls_path),
        "generated_campaign": str(generated_campaign_path),
        "updated_campaign": str(campaign_path) if args["update_campaign"] else None,
        "profile_url_count": len(urls),
        "summary": f"found {len(urls)} profile URL(s)",
    }
    sys.stdout.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
