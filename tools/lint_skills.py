#!/usr/bin/env python3
"""
lint_skills.py — structural linter for the skill markdown corpus.

Catches drift between the prose in `skills/<name>/SKILL.md` and the rest of
the repo. The product *is* these markdown files, so a typo'd cross-reference
or a renamed persona file ships as a real bug.

Stdlib-only. Cross-platform. Emits one JSON document on stdout matching the
conventions in shared-references/verification-protocols.md:

    {
      "tool": "lint_skills",
      "schema_version": 1,
      "passed": <bool>,
      "checks": [{"name", "passed", "detail"}, ...],
      "flags": [...],
      "summary": "...",
    }

Exit code 0 if passed, 1 otherwise. Run from repo root:

    bash tools/run.sh lint_skills.py
    py tools/lint_skills.py
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

TOOL_NAME = "lint_skills"
SCHEMA_VERSION = 1

# Repo layout assumptions. Resolved relative to the script's location so the
# tool works regardless of cwd.
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
SKILLS_DIR = REPO_ROOT / "skills"
PERSONAS_DIR = REPO_ROOT / "personas"
TOOLS_DIR = REPO_ROOT / "tools"
SHARED_REF_DIR = SKILLS_DIR / "shared-references"
UMBRELLA_SKILL = SKILLS_DIR / "auto-essay-review-loop" / "SKILL.md"

# Match repo-rooted paths embedded anywhere in skill prose. Captures one
# of the four root buckets we care about. Trailing punctuation/quotes
# are stripped after match.
PATH_RE = re.compile(
    r"(?:\.\.[\\/])*"
    r"((?:personas|tools|shared-references|skills|docs)"
    r"[\\/][^\s`\"'<>)\]]+?\.(?:md|py|sh))"
)

# Persona filename pattern (kebab-case .md under a format dir).
PERSONA_FILE_RE = re.compile(r"^[a-z0-9][a-z0-9-]*\.md$")

# Format directories under personas/ — also the set the umbrella table covers
# (minus business-plan oddities handled below).
FORMAT_DIRS = {
    "blog",
    "social",
    "linkedin",
    "linkedin-outbound",
    "business-plan",
    "application",
    "cv",
    "slides",
}


def now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def repo_relative(p: Path) -> str:
    try:
        return str(p.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(p).replace("\\", "/")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def find_skill_files() -> list[Path]:
    if not SKILLS_DIR.is_dir():
        return []
    return sorted(SKILLS_DIR.glob("*/SKILL.md"))


def extract_path_refs(text: str) -> set[str]:
    """Return distinct repo-root-relative path strings referenced by `text`."""
    refs: set[str] = set()
    for m in PATH_RE.finditer(text):
        ref = m.group(1).replace("\\", "/")
        # `shared-references/x.md` (no `skills/` prefix) is the form that
        # appears inside skill bodies — they're under skills/ implicitly.
        if ref.startswith("shared-references/"):
            ref = "skills/" + ref
        refs.add(ref)
    return refs


def check_cross_references(skill_files: list[Path]) -> tuple[dict, list[str]]:
    """Every personas/tools/shared-references/skills/docs path mentioned by a
    SKILL.md must exist on disk."""
    broken: list[tuple[str, str]] = []  # (skill_file, missing_ref)
    for sf in skill_files:
        text = read(sf)
        for ref in sorted(extract_path_refs(text)):
            target = REPO_ROOT / ref
            if not target.exists():
                broken.append((repo_relative(sf), ref))
    passed = not broken
    detail = (
        f"all referenced files resolve across {len(skill_files)} skill file(s)"
        if passed
        else f"{len(broken)} broken reference(s): "
        + ", ".join(f"{s}→{r}" for s, r in broken[:5])
        + (" …" if len(broken) > 5 else "")
    )
    return (
        {"name": "cross_references_resolve", "passed": passed, "detail": detail,
         "broken": [{"skill": s, "ref": r} for s, r in broken]},
        [] if passed else ["broken_cross_reference"],
    )


def is_sibling_skill_dir(name: str) -> bool:
    """True for skills like `auto-linkedin-outbound-loop` — they end in
    `-loop` but aren't draft-review skills, so they bypass the umbrella
    dispatcher and require a different lint contract."""
    return (
        name.startswith("auto-")
        and name.endswith("-loop")
        and not name.endswith("-review-loop")
    )


def check_dispatcher_table(skill_files: list[Path]) -> tuple[dict, list[str]]:
    """The umbrella SKILL.md has a `| Format | Skill name |` table near
    Phase 2. The set of `auto-*-review-loop` names in that table must match
    the set of `auto-*-review-loop/` directories on disk (excluding the
    umbrella itself)."""
    if not UMBRELLA_SKILL.is_file():
        return (
            {"name": "dispatcher_table_matches_skills", "passed": False,
             "detail": f"umbrella skill not found at {repo_relative(UMBRELLA_SKILL)}"},
            ["dispatcher_missing"],
        )

    text = read(UMBRELLA_SKILL)
    # Pull every backtick-wrapped `auto-*-review-loop` token from the file.
    # Slicing to a single table is brittle; the bullet list and table both
    # name the same skills, and any drift in either will trip the check.
    table_skills = set(re.findall(r"`(auto-[a-z0-9-]+-review-loop)`", text))

    on_disk = {
        p.parent.name
        for p in skill_files
        if p.parent.name.startswith("auto-") and p.parent.name.endswith("-review-loop")
        and p.parent.name != "auto-essay-review-loop"
    }

    missing_from_table = sorted(on_disk - table_skills)
    extra_in_table = sorted(table_skills - on_disk)

    passed = not missing_from_table and not extra_in_table
    parts: list[str] = []
    if missing_from_table:
        parts.append(f"on disk but not in dispatcher: {missing_from_table}")
    if extra_in_table:
        parts.append(f"in dispatcher but not on disk: {extra_in_table}")
    detail = (
        f"dispatcher names exactly the {len(on_disk)} format skill(s) on disk"
        if passed
        else "; ".join(parts)
    )
    flags = [] if passed else ["dispatcher_drift"]
    return (
        {"name": "dispatcher_table_matches_skills", "passed": passed,
         "detail": detail,
         "missing_from_table": missing_from_table,
         "extra_in_table": extra_in_table},
        flags,
    )


def check_umbrella_mentions_siblings(skill_files: list[Path]) -> tuple[dict, list[str]]:
    """Sibling skills (`auto-*-loop` minus `-review-loop`) live outside the
    umbrella's dispatch path — the umbrella does not detect them, so users
    have to learn the name some other way. To keep that surface honest we
    require the umbrella SKILL.md to name every sibling on disk inside
    backticks at least once (typically in the 'Sibling workflows' section).

    Drift modes this catches:
      - Sibling skill added on disk but never linked from the umbrella.
      - Sibling skill removed but the umbrella still names it.
    """
    if not UMBRELLA_SKILL.is_file():
        return (
            {"name": "umbrella_mentions_siblings", "passed": False,
             "detail": f"umbrella skill not found at {repo_relative(UMBRELLA_SKILL)}"},
            ["dispatcher_missing"],
        )

    on_disk = sorted(
        p.parent.name
        for p in skill_files
        if is_sibling_skill_dir(p.parent.name)
    )

    if not on_disk:
        # No sibling skills today — vacuously passes. We still register the
        # check so the JSON output documents it ran.
        return (
            {"name": "umbrella_mentions_siblings", "passed": True,
             "detail": "no sibling skills on disk — nothing to mention",
             "siblings_on_disk": [],
             "missing_from_umbrella": [],
             "extra_in_umbrella": []},
            [],
        )

    text = read(UMBRELLA_SKILL)
    mentioned = {
        m for m in re.findall(r"`(auto-[a-z0-9-]+-loop)`", text)
        if is_sibling_skill_dir(m)
    }

    missing_from_umbrella = sorted(set(on_disk) - mentioned)
    extra_in_umbrella = sorted(mentioned - set(on_disk))

    passed = not missing_from_umbrella and not extra_in_umbrella
    parts: list[str] = []
    if missing_from_umbrella:
        parts.append(f"on disk but not in umbrella: {missing_from_umbrella}")
    if extra_in_umbrella:
        parts.append(f"in umbrella but not on disk: {extra_in_umbrella}")
    detail = (
        f"umbrella names all {len(on_disk)} sibling skill(s)"
        if passed
        else "; ".join(parts)
    )
    flags = [] if passed else ["sibling_drift"]
    return (
        {"name": "umbrella_mentions_siblings", "passed": passed,
         "detail": detail,
         "siblings_on_disk": on_disk,
         "missing_from_umbrella": missing_from_umbrella,
         "extra_in_umbrella": extra_in_umbrella},
        flags,
    )


def check_persona_files() -> tuple[dict, list[str]]:
    """Every file under personas/<format>/ must (a) sit in a recognized
    format dir and (b) start with a YAML frontmatter block. Personas with
    no frontmatter cannot be loaded by the format skills (they validate
    YAML on load, per persona-library.md)."""
    if not PERSONAS_DIR.is_dir():
        return (
            {"name": "persona_files_well_formed", "passed": False,
             "detail": f"{repo_relative(PERSONAS_DIR)} not found"},
            ["personas_dir_missing"],
        )

    bad_dirs: list[str] = []
    bad_names: list[str] = []
    no_frontmatter: list[str] = []
    persona_count = 0

    for entry in sorted(PERSONAS_DIR.iterdir()):
        if not entry.is_dir():
            continue
        if entry.name not in FORMAT_DIRS:
            bad_dirs.append(entry.name)
            continue
        for pf in sorted(entry.iterdir()):
            if not pf.is_file() or not pf.name.endswith(".md"):
                continue
            persona_count += 1
            if not PERSONA_FILE_RE.match(pf.name):
                bad_names.append(repo_relative(pf))
            try:
                head = pf.read_text(encoding="utf-8")[:2048]
            except (OSError, UnicodeDecodeError):
                no_frontmatter.append(repo_relative(pf))
                continue
            # Frontmatter: starts with `---\n`, has a closing `---` on its
            # own line within the first ~2KB. We don't validate fields here
            # — that's the format skill's job at load time. The linter only
            # asserts the block exists.
            if not head.startswith("---"):
                no_frontmatter.append(repo_relative(pf))
                continue
            rest = head.split("\n", 1)[1] if "\n" in head else ""
            if "\n---" not in rest and not rest.startswith("---"):
                no_frontmatter.append(repo_relative(pf))

    problems = bool(bad_dirs or bad_names or no_frontmatter)
    flags: list[str] = []
    if bad_dirs:
        flags.append("unknown_persona_format_dir")
    if bad_names:
        flags.append("malformed_persona_filename")
    if no_frontmatter:
        flags.append("persona_missing_frontmatter")

    parts: list[str] = []
    if bad_dirs:
        parts.append(f"unknown format dirs: {bad_dirs}")
    if bad_names:
        parts.append(f"non-kebab-case persona files: {bad_names[:5]}")
    if no_frontmatter:
        parts.append(f"persona files without YAML frontmatter: {no_frontmatter[:5]}")

    detail = (
        f"{persona_count} persona file(s) across {len(FORMAT_DIRS)} format dir(s) all well-formed"
        if not problems
        else "; ".join(parts)
    )
    return (
        {"name": "persona_files_well_formed", "passed": not problems,
         "detail": detail,
         "unknown_format_dirs": bad_dirs,
         "malformed_filenames": bad_names,
         "missing_frontmatter": no_frontmatter,
         "persona_count": persona_count},
        flags,
    )


def check_persona_orphans(skill_files: list[Path]) -> tuple[dict, list[str]]:
    """A persona file that no SKILL.md or shared-references/*.md mentions is
    unreachable. Either the skill drifted away from it (delete the file) or
    the SKILL.md drifted away from a persona it should be using (add the
    reference). persona-library.md counts as a reference — that's where the
    blog skill enumerates personas through a shared roster instead of
    inlining each filename."""
    if not PERSONAS_DIR.is_dir():
        return ({"name": "no_orphan_personas", "passed": True,
                 "detail": "personas/ not present — skipped"}, [])

    on_disk: set[str] = set()
    for fmt_dir in PERSONAS_DIR.iterdir():
        if not fmt_dir.is_dir() or fmt_dir.name not in FORMAT_DIRS:
            continue
        for pf in fmt_dir.iterdir():
            if pf.is_file() and pf.name.endswith(".md"):
                rel = f"personas/{fmt_dir.name}/{pf.name}"
                on_disk.add(rel)

    referenced: set[str] = set()
    sources: list[Path] = list(skill_files)
    if SHARED_REF_DIR.is_dir():
        sources.extend(sorted(SHARED_REF_DIR.glob("*.md")))
    for src in sources:
        for ref in extract_path_refs(read(src)):
            if ref.startswith("personas/"):
                referenced.add(ref)

    orphans = sorted(on_disk - referenced)
    passed = not orphans
    detail = (
        f"all {len(on_disk)} persona file(s) referenced by at least one SKILL.md"
        if passed
        else f"{len(orphans)} orphan(s): {orphans[:5]}"
    )
    return (
        {"name": "no_orphan_personas", "passed": passed,
         "detail": detail, "orphans": orphans},
        [] if passed else ["orphan_persona"],
    )


def check_skill_frontmatter(skill_files: list[Path]) -> tuple[dict, list[str]]:
    """Every SKILL.md must open with a `---\\nname: ...\\ndescription: ...\\n---`
    block — that's how the harness discovers the skill. A SKILL.md without
    frontmatter is silently invisible to the agent."""
    bad: list[str] = []
    for sf in skill_files:
        head = read(sf)[:1024]
        if not head.startswith("---"):
            bad.append(repo_relative(sf))
            continue
        if not re.search(r"^name:\s*\S+", head, re.MULTILINE):
            bad.append(repo_relative(sf))
            continue
        if not re.search(r"^description:\s*\S+", head, re.MULTILINE):
            bad.append(repo_relative(sf))
    passed = not bad
    detail = (
        f"{len(skill_files)} SKILL.md file(s) all have name+description frontmatter"
        if passed
        else f"missing frontmatter or fields: {bad}"
    )
    return (
        {"name": "skill_frontmatter_present", "passed": passed,
         "detail": detail, "bad": bad},
        [] if passed else ["skill_missing_frontmatter"],
    )


def main() -> int:
    skill_files = find_skill_files()
    if not skill_files:
        result = {
            "tool": TOOL_NAME,
            "schema_version": SCHEMA_VERSION,
            "timestamp": now_iso(),
            "passed": False,
            "checks": [],
            "flags": ["no_skills_found"],
            "summary": f"no SKILL.md files under {repo_relative(SKILLS_DIR)}",
        }
        sys.stdout.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        return 1

    checks: list[dict] = []
    flags: list[str] = []

    for fn in (
        check_cross_references,
        check_dispatcher_table,
        check_umbrella_mentions_siblings,
        check_persona_files,
        check_persona_orphans,
        check_skill_frontmatter,
    ):
        try:
            if fn is check_persona_files:
                check, fs = fn()
            else:
                check, fs = fn(skill_files)
        except Exception as exc:
            checks.append({"name": fn.__name__, "passed": False,
                           "detail": f"linter crashed: {type(exc).__name__}: {exc}"})
            flags.append("linter_crash")
            continue
        checks.append(check)
        flags.extend(fs)

    passed = all(c["passed"] for c in checks)
    invariant_phrase = (
        "skill-shape invariant"
        if len(checks) == 1
        else "skill-shape invariants"
    )
    summary = (
        f"all {len(checks)} {invariant_phrase} hold across {len(skill_files)} skill(s)"
        if passed
        else "; ".join(c["detail"] for c in checks if not c["passed"])
    )

    result = {
        "tool": TOOL_NAME,
        "schema_version": SCHEMA_VERSION,
        "timestamp": now_iso(),
        "skills_dir": repo_relative(SKILLS_DIR),
        "skill_count": len(skill_files),
        "passed": passed,
        "checks": checks,
        "flags": sorted(set(flags)),
        "summary": summary,
    }
    sys.stdout.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
