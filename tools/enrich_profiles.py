#!/usr/bin/env python3
"""
enrich_profiles.py — Apify wrapper for the LinkedIn outbound workflow.

Calls the `dev_fusion/Linkedin-Profile-Scraper` actor (or a user-supplied
alternative) via the `run-sync-get-dataset-items` endpoint, normalizes the
returned records into the schema documented in
`skills/auto-linkedin-outbound-loop/SKILL.md`, and writes the raw and
normalized payloads to the run's output directory.

Stdlib-only — urllib + json + ssl. Cross-platform. The Apify token comes
from `$APIFY_TOKEN`; the tool refuses to read it from disk.

Usage:
    bash tools/run.sh enrich_profiles.py <campaign.json> [--out-dir=...] [--actor=...]

Emits a JSON object to stdout matching the verification-protocols schema:
  {tool, schema_version, timestamp, passed, checks[], flags[], summary, ...}

Exit code: 0 on success (token present, all chunks completed), 1 if
anything failed (token missing, all chunks failed, no valid URLs). The
JSON is the contract; the loop reads checks[] to decide whether to halt.

Defense-in-depth: `email` and `phone` fields are stripped from the
normalized output unless `campaign.channels.email = true` or
`campaign.channels.phone = true`. The persona compliance reviewer catches
misuse downstream too, but pre-stripping removes the temptation entirely.
"""
from __future__ import annotations

import json
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

TOOL_NAME = "enrich_profiles"
SCHEMA_VERSION = 1

DEFAULT_ACTOR = "dev_fusion/Linkedin-Profile-Scraper"
DEFAULT_OUT_DIR = "review-stage/outbound"
DEFAULT_CHUNK_SIZE = 10
DEFAULT_BACKOFF_SECONDS = (1, 4, 16)
DEFAULT_TIMEOUT_SECONDS = 120

# LinkedIn profile URL: https://(www.)linkedin.com/in/<slug>(/)
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


def slugify(s: str) -> str:
    """Conservative slug for filenames + state rows. ASCII-only, lowercased."""
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-") or "unknown"


def actor_to_url_path(actor: str) -> str:
    """Apify accepts both `username/actor` and `username~actor` in paths.

    Normalize to the tilde form because the slash form requires URL-encoding
    and the tilde form is the canonical run-sync path documented at
    https://docs.apify.com/api/v2#tag/Actor-runs/operation/actorRun_runSync.
    """
    return actor.replace("/", "~", 1)


def load_json(path: Path) -> dict:
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


def validate_urls(urls: list[str]) -> tuple[list[str], list[str]]:
    """Return (valid_urls, invalid_urls). Dedupes valid URLs preserving order."""
    seen = set()
    valid: list[str] = []
    invalid: list[str] = []
    for raw in urls:
        if not isinstance(raw, str):
            invalid.append(repr(raw))
            continue
        u = raw.strip()
        if not PROFILE_URL_RE.match(u):
            invalid.append(u)
            continue
        if u in seen:
            continue
        seen.add(u)
        valid.append(u)
    return valid, invalid


def chunk(items: list, size: int) -> list[list]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def call_apify(
    *,
    actor: str,
    token: str,
    profile_urls: list[str],
    timeout_seconds: int,
) -> tuple[list[dict] | None, str | None, int | None]:
    """Single POST to run-sync-get-dataset-items.

    Returns (records, error_message, http_status). On HTTP success, records
    is the parsed JSON list and error_message is None. On failure, records
    is None and error_message describes the problem.

    The Apify token is sent as `Authorization: Bearer <token>` rather than
    as a `?token=` query parameter. Both are accepted by the Apify API, but
    the header form keeps tokens out of access logs, proxy logs, and
    referer chains.
    """
    url = (
        f"https://api.apify.com/v2/acts/{actor_to_url_path(actor)}"
        f"/run-sync-get-dataset-items"
    )
    body = json.dumps({"profileUrls": profile_urls}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "auto-essay-review-loop/enrich_profiles",
        },
        method="POST",
    )
    ctx = create_ssl_context()
    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds, context=ctx) as resp:
            raw = resp.read().decode("utf-8")
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError as e:
                return None, f"apify returned non-JSON ({e})", resp.status
            if not isinstance(parsed, list):
                return None, (
                    f"apify returned {type(parsed).__name__}, expected list"
                ), resp.status
            return parsed, None, resp.status
    except urllib.error.HTTPError as e:
        body = read_http_error(e)
        detail = f"HTTP {e.code} {e.reason}"
        if body:
            detail += f": {body}"
        return None, detail, e.code
    except urllib.error.URLError as e:
        return None, f"URLError: {e.reason}", None
    except TimeoutError:
        return None, f"timeout after {timeout_seconds}s", None
    except Exception as e:  # noqa: BLE001
        return None, f"{type(e).__name__}: {e}", None


def call_apify_with_retry(
    *,
    actor: str,
    token: str,
    profile_urls: list[str],
    timeout_seconds: int,
    backoff: tuple[int, ...] = DEFAULT_BACKOFF_SECONDS,
    sleep_fn=time.sleep,
) -> tuple[list[dict] | None, list[str]]:
    """Retries on 429 / 5xx using the given backoff sequence.

    Returns (records, attempt_errors). attempt_errors is empty on success
    AFTER retry; it contains every error encountered across attempts when
    the call ultimately fails. The skill logs these into AUTO_REVIEW.md.
    """
    attempt_errors: list[str] = []
    for attempt, delay in enumerate([0] + list(backoff)):
        if delay > 0:
            sleep_fn(delay)
        records, err, status = call_apify(
            actor=actor,
            token=token,
            profile_urls=profile_urls,
            timeout_seconds=timeout_seconds,
        )
        if records is not None:
            return records, attempt_errors
        attempt_errors.append(f"attempt {attempt + 1}: {err}")
        # Only retry on 429 / 5xx / transport errors. 4xx other than 429
        # mean the request itself is wrong and retrying won't help.
        if status is not None and status not in (429,) and status < 500:
            break
    return None, attempt_errors


def normalize_record(rec: dict, *, profile_url: str, channels: dict, actor: str) -> dict:
    """Apify schemas vary. Be permissive — read multiple plausible keys,
    fall back to None. The shape of the output matches the documented
    target schema in skills/auto-linkedin-outbound-loop/SKILL.md.

    Stripping rule: `email` and `phone` are removed unless the campaign
    explicitly authorizes those channels. Done here, in code, so a
    misbehaving downstream consumer cannot accidentally surface them.
    """

    def first(*keys, default=None):
        for k in keys:
            v = rec.get(k)
            if v not in (None, "", []):
                return v
        return default

    first_name = first("firstName", "first_name", "givenName")
    last_name = first("lastName", "last_name", "familyName")
    full_name = first("fullName", "name") or (
        f"{first_name} {last_name}".strip() if (first_name or last_name) else None
    )
    headline = first("headline", "currentTitle", "title")
    about = first("about", "summary", "description")
    location = first("location", "geoLocationName", "addressWithCountry", "city")

    experience = first("experience", "experiences", default=[]) or []
    # Apify returns dicts; some shapes have nested companyName / position.
    recent_experience = []
    for item in experience[:5] if isinstance(experience, list) else []:
        if not isinstance(item, dict):
            continue
        recent_experience.append(
            {
                "title": item.get("title") or item.get("position"),
                "company": item.get("companyName") or item.get("company"),
                "duration": item.get("duration") or item.get("dateRange"),
                "description": item.get("description"),
            }
        )

    education = first("education", "educations", default=[]) or []
    edu_records = []
    for item in education[:3] if isinstance(education, list) else []:
        if not isinstance(item, dict):
            continue
        edu_records.append(
            {
                "school": item.get("school") or item.get("institution"),
                "degree": item.get("degree"),
                "field": item.get("fieldOfStudy") or item.get("field"),
            }
        )

    current_role = None
    current_company = first("company", "companyName")
    if recent_experience:
        current_role = recent_experience[0].get("title") or current_role
        current_company = recent_experience[0].get("company") or current_company

    email_authorized = bool(channels.get("email"))
    phone_authorized = bool(channels.get("phone"))
    email_val = first("email", "publicEmail") if email_authorized else None
    phone_val = first("phone", "publicPhone") if phone_authorized else None

    slug_basis = full_name or (first_name and f"{first_name} {last_name or ''}") or profile_url
    profile_slug = slugify(str(slug_basis))

    return {
        "profileUrl": profile_url,
        "profile_slug": profile_slug,
        "firstName": first_name,
        "fullName": full_name,
        "headline": headline,
        "currentRole": current_role,
        "company": current_company,
        "location": location,
        "about": about,
        "recentExperience": recent_experience,
        "education": edu_records,
        "email": email_val,
        "phone": phone_val,
        "source": f"apify:{actor}",
    }


def parse_args(argv: list[str]) -> dict:
    if len(argv) < 2:
        raise SystemExit(
            "usage: enrich_profiles.py <campaign.json> [--out-dir=...] [--actor=...]"
        )
    args = {
        "campaign_path": argv[1],
        "out_dir": DEFAULT_OUT_DIR,
        "actor": None,  # resolved from campaign or default
        "timeout_seconds": DEFAULT_TIMEOUT_SECONDS,
        "chunk_size": DEFAULT_CHUNK_SIZE,
    }
    for a in argv[2:]:
        if a.startswith("--out-dir="):
            args["out_dir"] = a.split("=", 1)[1]
        elif a.startswith("--actor="):
            args["actor"] = a.split("=", 1)[1]
        elif a.startswith("--timeout="):
            args["timeout_seconds"] = int(a.split("=", 1)[1])
        elif a.startswith("--chunk-size="):
            args["chunk_size"] = max(1, int(a.split("=", 1)[1]))
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


def main(argv: list[str]) -> int:
    try:
        args = parse_args(argv)
    except SystemExit as exc:
        sys.stdout.write(
            json.dumps(
                error_result("", str(exc), "ArgumentError", ["argument_error"]),
                ensure_ascii=False,
                indent=2,
            )
            + "\n"
        )
        return 2

    campaign_path = Path(args["campaign_path"])
    if not campaign_path.exists():
        sys.stdout.write(
            json.dumps(
                error_result(
                    str(campaign_path),
                    f"campaign file not found: {campaign_path}",
                    "FileNotFoundError",
                    ["campaign_missing"],
                ),
                ensure_ascii=False,
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
                ensure_ascii=False,
                indent=2,
            )
            + "\n"
        )
        return 2

    raw_urls = campaign.get("profileUrls") or []
    channels = campaign.get("channels") or {}
    actor = args["actor"] or campaign.get("apify_actor") or DEFAULT_ACTOR
    out_dir = Path(args["out_dir"])

    checks: list[dict] = []
    flags: list[str] = []

    # Check 1: $APIFY_TOKEN present.
    token = os.environ.get("APIFY_TOKEN", "").strip()
    token_present = bool(token)
    checks.append(
        {
            "name": "apify_token_present",
            "passed": token_present,
            "detail": (
                "APIFY_TOKEN is set in environment"
                if token_present
                else "APIFY_TOKEN missing — export it before running the loop"
            ),
        }
    )
    if not token_present:
        flags.append("missing_apify_token")

    # Check 2: profileUrls present + well-formed.
    valid_urls, invalid_urls = validate_urls(raw_urls)
    urls_valid = bool(valid_urls) and not invalid_urls
    checks.append(
        {
            "name": "urls_valid",
            "passed": urls_valid,
            "detail": (
                f"{len(valid_urls)} valid LinkedIn profile URL(s)"
                + (
                    f"; {len(invalid_urls)} invalid: {invalid_urls[:3]}"
                    + ("…" if len(invalid_urls) > 3 else "")
                    if invalid_urls
                    else ""
                )
            ),
            "value": len(valid_urls),
            "invalid": invalid_urls,
        }
    )
    if invalid_urls:
        flags.append("invalid_profile_url")
    if not valid_urls:
        flags.append("no_profile_urls")

    # Short-circuit: cannot enrich without token or valid URLs.
    if not token_present or not valid_urls:
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
            "enriched_count": 0,
            "failed_chunks": [],
            "summary": (
                "missing APIFY_TOKEN — cannot enrich"
                if not token_present
                else "no valid LinkedIn profile URLs to enrich"
            ),
        }
        sys.stdout.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        return 1

    # Phase: enrichment loop, chunked + retried.
    chunks = chunk(valid_urls, args["chunk_size"])
    raw_records: list[dict] = []
    failed_chunks: list[dict] = []

    for idx, urls in enumerate(chunks):
        records, errs = call_apify_with_retry(
            actor=actor,
            token=token,
            profile_urls=urls,
            timeout_seconds=args["timeout_seconds"],
        )
        if records is None:
            failed_chunks.append(
                {
                    "chunk_index": idx,
                    "profile_urls": urls,
                    "errors": errs,
                }
            )
            continue
        raw_records.extend(records)

    # Check 3: enrichment completed (at least one chunk succeeded; treat
    # partial success as passed-but-flagged so the loop can keep going on
    # the qualified subset).
    enrichment_ok = bool(raw_records)
    checks.append(
        {
            "name": "enrichment_completed",
            "passed": enrichment_ok,
            "detail": (
                f"{len(raw_records)} profile(s) enriched across "
                f"{len(chunks) - len(failed_chunks)}/{len(chunks)} chunks"
                + (
                    f"; {len(failed_chunks)} chunk(s) failed permanently"
                    if failed_chunks
                    else ""
                )
            ),
            "value": len(raw_records),
        }
    )
    if failed_chunks:
        flags.append("chunk_failed")
    if not enrichment_ok:
        flags.append("enrichment_empty")

    # Save raw.
    raw_path = out_dir / "enriched_profiles.raw.json"
    if enrichment_ok:
        write_json(raw_path, raw_records)

    # Normalize. Map by profileUrl since Apify may reorder.
    normalized: list[dict] = []
    by_url: dict[str, dict] = {}
    for rec in raw_records:
        if not isinstance(rec, dict):
            continue
        url = (
            rec.get("profileUrl")
            or rec.get("url")
            or rec.get("publicIdentifier")
            or ""
        )
        if url and url.startswith("http"):
            by_url[url.rstrip("/")] = rec
    for url in valid_urls:
        rec = by_url.get(url.rstrip("/"))
        if rec is None:
            continue
        normalized.append(
            normalize_record(rec, profile_url=url, channels=channels, actor=actor)
        )

    fields_ok = all(
        n.get("profileUrl") and (n.get("fullName") or n.get("firstName"))
        for n in normalized
    )
    checks.append(
        {
            "name": "per_profile_fields_present",
            "passed": fields_ok,
            "detail": (
                f"{len(normalized)} normalized record(s); "
                + ("all have name + url" if fields_ok else "some missing name or url")
            ),
            "value": len(normalized),
        }
    )
    if not fields_ok:
        flags.append("normalized_field_missing")

    if normalized:
        write_json(out_dir / "enriched_profiles.normalized.json", normalized)

    passed = all(c["passed"] for c in checks)
    summary = (
        f"enriched {len(normalized)} of {len(valid_urls)} profile(s) via {actor}"
        if passed
        else "; ".join(c["detail"] for c in checks if not c["passed"])
    )

    result = {
        "tool": TOOL_NAME,
        "schema_version": SCHEMA_VERSION,
        "timestamp": now_iso(),
        "input_file": str(campaign_path),
        "out_dir": str(out_dir),
        "actor": actor,
        "passed": passed,
        "checks": checks,
        "flags": flags,
        "enriched_count": len(normalized),
        "failed_chunks": failed_chunks,
        "summary": summary,
    }
    sys.stdout.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
