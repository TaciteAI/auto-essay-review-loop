#!/usr/bin/env python3
"""
search_linkedin_profiles.py — optional Apify lead discovery pre-step.

Reads campaign.lead_search, runs an Apify people-search Actor, extracts
LinkedIn profile URLs, and writes a campaign copy with profileUrls filled.

Usage:
    bash tools/run.sh search_linkedin_profiles.py campaigns/name.json \
        --out-dir=review-stage/outbound \
        --campaign-out-dir=review-stage/outbound \
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
import urllib.parse
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


def create_ssl_context() -> ssl.SSLContext:
    try:
        import certifi  # type: ignore
    except Exception:  # noqa: BLE001
        return ssl.create_default_context()
    return ssl.create_default_context(cafile=certifi.where())


def read_http_error(exc: urllib.error.HTTPError) -> str:
    try:
        body = exc.read().decode("utf-8", errors="replace").strip()
    except Exception:  # noqa: BLE001
        return ""
    if len(body) > 600:
        return body[:600] + "..."
    return body


def parse_args(argv: list[str]) -> dict:
    if len(argv) < 2:
        raise SystemExit(
            "usage: search_linkedin_profiles.py <campaign.json> "
            "[--out-dir=...] [--campaign-out-dir=...] "
            "[--update-campaign] [--timeout=180]"
        )
    args = {
        "campaign_path": argv[1],
        "out_dir": DEFAULT_OUT_DIR,
        "campaign_out_dir": None,
        "update_campaign": False,
        "timeout_seconds": DEFAULT_TIMEOUT_SECONDS,
    }
    for a in argv[2:]:
        if a.startswith("--out-dir="):
            args["out_dir"] = a.split("=", 1)[1]
        elif a.startswith("--campaign-out-dir="):
            args["campaign_out_dir"] = a.split("=", 1)[1]
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
    ctx = create_ssl_context()
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
        body = read_http_error(exc)
        detail = f"HTTP {exc.code} {exc.reason}"
        if body:
            detail += f": {body}"
        return None, detail, exc.code
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


def canonical_profile_url(raw: str) -> str | None:
    raw = raw.strip()
    if not raw:
        return None
    parsed = urllib.parse.urlparse(raw)
    if parsed.scheme not in ("http", "https"):
        return None
    host = parsed.netloc.lower()
    if host not in ("linkedin.com", "www.linkedin.com") and not host.endswith(".linkedin.com"):
        return None
    path = parsed.path.rstrip("/")
    if not re.match(r"^/in/[A-Za-z0-9\-_%]+$", path, flags=re.IGNORECASE):
        return None
    return f"https://www.linkedin.com{path}/"


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
            normalized = canonical_profile_url(raw)
            if not normalized:
                continue
            if normalized in seen:
                continue
            seen.add(normalized)
            urls.append(normalized)
            found_for_record = True
            break
        if found_for_record:
            continue
        for raw in iter_strings(rec):
            normalized = canonical_profile_url(raw)
            if not normalized:
                continue
            if normalized in seen:
                continue
            seen.add(normalized)
            urls.append(normalized)
            break
    return urls


def normalize_keywords(value) -> list[str]:
    if isinstance(value, list):
        return [str(v).strip().lower() for v in value if str(v).strip()]
    if isinstance(value, str):
        parts = re.split(r"\s+\bOR\b\s+|[,|]", value, flags=re.IGNORECASE)
        return [p.strip().lower() for p in parts if p.strip()]
    return []


def author_profile_blob(rec: dict) -> str:
    parts: list[str] = []
    author = rec.get("author")
    if isinstance(author, dict):
        parts.extend(iter_strings(author))

    # Profile-search actors do not always nest identity fields under author.
    for key in (
        "name",
        "fullName",
        "full_name",
        "headline",
        "summary",
        "title",
        "currentRole",
        "currentPositions",
        "currentPosition",
        "positions",
        "experience",
        "linkedinUrl",
        "url",
        "profileUrl",
    ):
        value = rec.get(key)
        if value is not None:
            parts.extend(iter_strings(value))
    return " | ".join(parts)


def filter_records(records: list[dict], exclude_keywords: list[str]) -> tuple[list[dict], list[dict]]:
    if not exclude_keywords:
        return records, []

    kept: list[dict] = []
    excluded: list[dict] = []
    for rec in records:
        if not isinstance(rec, dict):
            kept.append(rec)
            continue
        blob = author_profile_blob(rec)
        lowered = blob.lower()
        hit = next((kw for kw in exclude_keywords if kw in lowered), None)
        if not hit:
            kept.append(rec)
            continue
        author = rec.get("author") if isinstance(rec.get("author"), dict) else {}
        excluded.append(
            {
                "excluded_keyword": hit,
                "author_name": author.get("name") if isinstance(author, dict) else rec.get("name"),
                "profile_url": extract_profile_urls([rec])[:1],
                "author_profile_text": blob[:500],
            }
        )
    return kept, excluded


def resolve_campaign_out_dir(discovery_dir: Path, explicit: str | None) -> Path:
    if explicit:
        return Path(explicit)
    # Phase-aware default for run folders:
    #   runs/<id>/01_discovery -> runs/<id>/00_campaign
    if discovery_dir.name == "01_discovery":
        sibling = discovery_dir.parent / "00_campaign"
        if sibling.exists() or discovery_dir.parent.name:
            return sibling
    return discovery_dir


def generated_campaign_path(campaign_path: Path, discovery_dir: Path, campaign_dir: Path) -> Path:
    if campaign_dir != discovery_dir:
        return campaign_dir / "campaign.discovered.json"
    return discovery_dir / f"{campaign_path.stem}.discovered.json"


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
    campaign_out_dir = resolve_campaign_out_dir(out_dir, args["campaign_out_dir"])
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
    exclude_keywords = normalize_keywords(lead_search.get("exclude_author_keywords"))
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
            "campaign_out_dir": str(campaign_out_dir),
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
            "campaign_out_dir": str(campaign_out_dir),
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

    filtered_records, excluded_records = filter_records(records, exclude_keywords)
    urls = extract_profile_urls(filtered_records)
    out_dir.mkdir(parents=True, exist_ok=True)
    campaign_out_dir.mkdir(parents=True, exist_ok=True)
    raw_path = out_dir / "searched_profiles.raw.json"
    filtered_path = out_dir / "searched_profiles.filtered.json"
    excluded_path = out_dir / "excluded_search_records.json"
    urls_path = out_dir / "discovered_profile_urls.json"
    generated_campaign = generated_campaign_path(campaign_path, out_dir, campaign_out_dir)
    write_json(raw_path, records)
    write_json(filtered_path, filtered_records)
    write_json(excluded_path, excluded_records)
    write_json(urls_path, urls)

    generated = dict(campaign)
    existing = [
        normalized
        for u in (campaign.get("profileUrls") or [])
        if isinstance(u, str)
        for normalized in [canonical_profile_url(u)]
        if normalized
    ]
    merged = list(dict.fromkeys(existing + urls))
    generated["profileUrls"] = merged[: int(campaign.get("max_prospects") or len(merged))]
    write_json(generated_campaign, generated)
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
            {
                "name": "exclude_author_keywords",
                "passed": True,
                "detail": (
                    f"{len(excluded_records)} record(s) excluded by "
                    f"{len(exclude_keywords)} author keyword(s)"
                ),
                "value": len(excluded_records),
                "keywords": exclude_keywords,
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
        "campaign_out_dir": str(campaign_out_dir),
        "actor": actor,
        "passed": passed,
        "checks": checks,
        "flags": [] if passed else ["no_profile_urls_found"],
        "raw_output": str(raw_path),
        "filtered_output": str(filtered_path),
        "excluded_output": str(excluded_path),
        "urls_output": str(urls_path),
        "generated_campaign": str(generated_campaign),
        "updated_campaign": str(campaign_path) if args["update_campaign"] else None,
        "profile_url_count": len(urls),
        "summary": f"found {len(urls)} profile URL(s)",
    }
    sys.stdout.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
