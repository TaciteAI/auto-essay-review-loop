#!/usr/bin/env python3
"""
outbound_state.py — batch state manager for multi-prospect outbound runs.

The existing `REVIEW_STATE.json` recovery pattern (loop-contract.md) is
single-document. Outbound runs touch up to 25 prospects in one batch, each
with its own round count, scores, and message hash. A 300-Codex-call run
*will* fail mid-batch — this tool is the durable, testable layer that
lets the skill resume cleanly.

Stdlib-only. State lives in `{out-dir}/prospect_state.jsonl` (JSONL so
single-line atomic updates are trivial; the whole file is rewritten via
temp+rename on each `update`).

Subcommands:
    init <qualified.json> [--out-dir=...] [--max-prospects=25]
    update <profile_slug> <patch.json>  [--out-dir=...]
        # use `-` for patch.json to read from stdin
    resume [--out-dir=...] [--max-stale-hours=24]

All commands emit JSON to stdout matching the verification-protocols
schema. Exit 0 on success, 1 on logical failure, 2 on usage errors.
"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

TOOL_NAME = "outbound_state"
SCHEMA_VERSION = 1

DEFAULT_OUT_DIR = "review-stage/outbound"
STATE_FILENAME = "prospect_state.jsonl"
DEFAULT_MAX_STALE_HOURS = 24
DEFAULT_MAX_PROSPECTS = 25

TERMINAL_STATUSES = {"approved", "rejected"}
IN_FLIGHT_STATUSES = {"drafting", "reviewing", "inconclusive"}
INITIAL_STATUSES = {"qualified"}

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9\-]*$")


def now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def parse_iso(s: str) -> datetime | None:
    if not s:
        return None
    try:
        # Allow trailing Z; datetime.fromisoformat handles +00:00 only.
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def state_path(out_dir: Path) -> Path:
    return out_dir / STATE_FILENAME


def read_state(out_dir: Path) -> tuple[list[dict], list[int]]:
    """Return (rows, malformed_line_numbers).

    Malformed lines are skipped — a partial write must not crash the
    resume tool — but we return their line numbers so `cmd_resume` can
    surface them in its JSON output. Silent corruption that's invisible
    to callers was the v0.1 trap; v0.2 makes it observable.
    """
    p = state_path(out_dir)
    if not p.exists():
        return [], []
    rows: list[dict] = []
    malformed: list[int] = []
    for line_no, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            malformed.append(line_no)
    return rows, malformed


def write_state(out_dir: Path, rows: list[dict]) -> None:
    """Atomic write: temp file in the same dir, then rename."""
    out_dir.mkdir(parents=True, exist_ok=True)
    target = state_path(out_dir)
    fd, tmp_path = tempfile.mkstemp(
        prefix=".prospect_state.", suffix=".tmp", dir=str(out_dir)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        os.replace(tmp_path, target)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def make_initial_row(qualified: dict) -> dict:
    slug = qualified.get("profile_slug") or qualified.get("profileUrl") or "unknown"
    return {
        "profileUrl": qualified.get("profileUrl"),
        "profile_slug": slug,
        "status": "qualified",
        "round": 0,
        "last_scores": {},
        "last_verdicts": {},
        "message_hash": None,
        "blockers": [],
        "timestamp": now_iso(),
    }


def cmd_init(qualified_path: Path, out_dir: Path, max_prospects: int) -> dict:
    if not qualified_path.exists():
        return {
            "tool": TOOL_NAME,
            "schema_version": SCHEMA_VERSION,
            "timestamp": now_iso(),
            "passed": False,
            "checks": [],
            "flags": ["qualified_missing"],
            "summary": f"qualified prospects file not found: {qualified_path}",
            "error": "FileNotFoundError",
        }
    try:
        qualified = json.loads(qualified_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError) as exc:
        return {
            "tool": TOOL_NAME,
            "schema_version": SCHEMA_VERSION,
            "timestamp": now_iso(),
            "passed": False,
            "checks": [],
            "flags": ["qualified_invalid"],
            "summary": f"could not parse qualified prospects: {exc}",
            "error": type(exc).__name__,
        }
    if not isinstance(qualified, list):
        return {
            "tool": TOOL_NAME,
            "schema_version": SCHEMA_VERSION,
            "timestamp": now_iso(),
            "passed": False,
            "checks": [],
            "flags": ["qualified_invalid"],
            "summary": "qualified.json must be a list",
            "error": "TypeError",
        }

    capped = qualified[:max_prospects]
    rows = [make_initial_row(q) for q in capped if isinstance(q, dict)]
    write_state(out_dir, rows)

    return {
        "tool": TOOL_NAME,
        "schema_version": SCHEMA_VERSION,
        "timestamp": now_iso(),
        "passed": True,
        "checks": [
            {
                "name": "state_initialized",
                "passed": True,
                "detail": f"{len(rows)} prospect row(s) written to {state_path(out_dir)}",
                "value": len(rows),
            }
        ],
        "flags": (["max_prospects_capped"] if len(qualified) > max_prospects else []),
        "state_file": str(state_path(out_dir)),
        "prospect_count": len(rows),
        "summary": (
            f"initialized state file with {len(rows)} prospect(s)"
            + (
                f" (capped from {len(qualified)} at max_prospects={max_prospects})"
                if len(qualified) > max_prospects
                else ""
            )
        ),
    }


def cmd_update(
    profile_slug: str, patch_path: str, out_dir: Path
) -> dict:
    if not SLUG_RE.match(profile_slug):
        return {
            "tool": TOOL_NAME,
            "schema_version": SCHEMA_VERSION,
            "timestamp": now_iso(),
            "passed": False,
            "checks": [],
            "flags": ["bad_slug"],
            "summary": f"profile_slug '{profile_slug}' is not kebab-case",
            "error": "ValueError",
        }

    if patch_path == "-":
        patch_text = sys.stdin.read()
    else:
        p = Path(patch_path)
        if not p.exists():
            return {
                "tool": TOOL_NAME,
                "schema_version": SCHEMA_VERSION,
                "timestamp": now_iso(),
                "passed": False,
                "checks": [],
                "flags": ["patch_missing"],
                "summary": f"patch file not found: {p}",
                "error": "FileNotFoundError",
            }
        patch_text = p.read_text(encoding="utf-8")

    try:
        patch = json.loads(patch_text)
    except json.JSONDecodeError as exc:
        return {
            "tool": TOOL_NAME,
            "schema_version": SCHEMA_VERSION,
            "timestamp": now_iso(),
            "passed": False,
            "checks": [],
            "flags": ["patch_invalid"],
            "summary": f"patch JSON parse error: {exc}",
            "error": "JSONDecodeError",
        }
    if not isinstance(patch, dict):
        return {
            "tool": TOOL_NAME,
            "schema_version": SCHEMA_VERSION,
            "timestamp": now_iso(),
            "passed": False,
            "checks": [],
            "flags": ["patch_invalid"],
            "summary": "patch must be a JSON object",
            "error": "TypeError",
        }

    rows, _malformed = read_state(out_dir)
    found = False
    for row in rows:
        if row.get("profile_slug") == profile_slug:
            # Shallow merge. profile_slug + profileUrl are immutable.
            for k, v in patch.items():
                if k in ("profile_slug", "profileUrl"):
                    continue
                row[k] = v
            row["timestamp"] = now_iso()
            found = True
            break

    if not found:
        return {
            "tool": TOOL_NAME,
            "schema_version": SCHEMA_VERSION,
            "timestamp": now_iso(),
            "passed": False,
            "checks": [],
            "flags": ["slug_not_found"],
            "summary": f"profile_slug '{profile_slug}' not in state file",
            "error": "KeyError",
        }

    write_state(out_dir, rows)
    return {
        "tool": TOOL_NAME,
        "schema_version": SCHEMA_VERSION,
        "timestamp": now_iso(),
        "passed": True,
        "checks": [
            {
                "name": "row_updated",
                "passed": True,
                "detail": f"updated row for '{profile_slug}'",
            }
        ],
        "flags": [],
        "profile_slug": profile_slug,
        "applied_fields": sorted(
            k for k in patch.keys() if k not in ("profile_slug", "profileUrl")
        ),
        "summary": f"updated state row for '{profile_slug}'",
    }


def cmd_resume(out_dir: Path, max_stale_hours: int) -> dict:
    rows, malformed_lines = read_state(out_dir)
    now = datetime.now(timezone.utc)
    to_skip: list[dict] = []
    to_continue: list[dict] = []
    to_restart: list[dict] = []

    for row in rows:
        slug = row.get("profile_slug") or row.get("profileUrl") or "unknown"
        status = row.get("status") or "qualified"
        entry = {"profile_slug": slug, "status": status, "round": row.get("round", 0)}

        if status in TERMINAL_STATUSES:
            to_skip.append(entry)
            continue

        if status in INITIAL_STATUSES:
            to_continue.append(entry)
            continue

        if status in IN_FLIGHT_STATUSES:
            ts = parse_iso(row.get("timestamp", ""))
            if ts is None:
                to_restart.append({**entry, "reason": "no_timestamp"})
                continue
            age_hours = (now - ts).total_seconds() / 3600.0
            if age_hours > max_stale_hours:
                to_restart.append(
                    {**entry, "reason": f"stale_{int(age_hours)}h"}
                )
            else:
                to_continue.append(entry)
            continue

        # Unknown status — flag for human review.
        to_restart.append({**entry, "reason": "unknown_status"})

    plan_total = len(to_skip) + len(to_continue) + len(to_restart)
    plan_summary = (
        f"resume plan: {len(to_continue)} to continue, "
        f"{len(to_skip)} already terminal, "
        f"{len(to_restart)} will restart"
    )

    flags: list[str] = []
    checks: list[dict] = [
        {
            "name": "resume_plan",
            "passed": True,
            "detail": plan_summary,
            "value": plan_total,
        }
    ]
    if malformed_lines:
        # Corruption is observable, not silent — but resume still produces
        # a plan from the rows it could parse. The skill is expected to
        # surface the warning to the user and decide whether to continue.
        flags.append("corrupted_state_rows")
        checks.append(
            {
                "name": "state_file_integrity",
                "passed": False,
                "detail": (
                    f"{len(malformed_lines)} malformed JSONL row(s) skipped "
                    f"at line(s): {malformed_lines[:10]}"
                    + ("…" if len(malformed_lines) > 10 else "")
                ),
                "value": len(malformed_lines),
                "malformed_lines": malformed_lines,
            }
        )

    summary = plan_summary + (
        f"; {len(malformed_lines)} corrupted row(s) skipped"
        if malformed_lines
        else ""
    )
    return {
        "tool": TOOL_NAME,
        "schema_version": SCHEMA_VERSION,
        "timestamp": now_iso(),
        "passed": not malformed_lines,
        "checks": checks,
        "flags": flags,
        "to_skip": to_skip,
        "to_continue": to_continue,
        "to_restart": to_restart,
        "malformed_rows": len(malformed_lines),
        "summary": summary,
    }


def parse_args(argv: list[str]) -> dict:
    if len(argv) < 2:
        raise SystemExit(
            "usage: outbound_state.py <init|update|resume> [args...]"
        )
    cmd = argv[1]
    args = {"cmd": cmd, "out_dir": DEFAULT_OUT_DIR}
    rest = argv[2:]
    if cmd == "init":
        positionals: list[str] = []
        for a in rest:
            if a.startswith("--out-dir="):
                args["out_dir"] = a.split("=", 1)[1]
            elif a.startswith("--max-prospects="):
                args["max_prospects"] = int(a.split("=", 1)[1])
            elif a.startswith("--"):
                raise SystemExit(f"unknown flag: {a}")
            else:
                positionals.append(a)
        if len(positionals) != 1:
            raise SystemExit(
                "usage: outbound_state.py init <qualified.json> [--out-dir=...] [--max-prospects=25]"
            )
        args["qualified_path"] = positionals[0]
        args.setdefault("max_prospects", DEFAULT_MAX_PROSPECTS)
    elif cmd == "update":
        positionals = []
        for a in rest:
            if a.startswith("--out-dir="):
                args["out_dir"] = a.split("=", 1)[1]
            elif a.startswith("--"):
                raise SystemExit(f"unknown flag: {a}")
            else:
                positionals.append(a)
        if len(positionals) != 2:
            raise SystemExit(
                "usage: outbound_state.py update <profile_slug> <patch.json|-> [--out-dir=...]"
            )
        args["profile_slug"] = positionals[0]
        args["patch_path"] = positionals[1]
    elif cmd == "resume":
        for a in rest:
            if a.startswith("--out-dir="):
                args["out_dir"] = a.split("=", 1)[1]
            elif a.startswith("--max-stale-hours="):
                args["max_stale_hours"] = int(a.split("=", 1)[1])
            else:
                raise SystemExit(f"unknown flag: {a}")
        args.setdefault("max_stale_hours", DEFAULT_MAX_STALE_HOURS)
    else:
        raise SystemExit(f"unknown subcommand: {cmd} (expected init|update|resume)")
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

    out_dir = Path(args["out_dir"])

    if args["cmd"] == "init":
        result = cmd_init(
            Path(args["qualified_path"]),
            out_dir,
            int(args["max_prospects"]),
        )
    elif args["cmd"] == "update":
        result = cmd_update(
            args["profile_slug"],
            args["patch_path"],
            out_dir,
        )
    elif args["cmd"] == "resume":
        result = cmd_resume(out_dir, int(args["max_stale_hours"]))
    else:  # pragma: no cover — parse_args guards
        result = error_result(
            f"unknown subcommand: {args['cmd']}", "ValueError", ["bad_subcommand"]
        )

    sys.stdout.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return 0 if result.get("passed") else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
