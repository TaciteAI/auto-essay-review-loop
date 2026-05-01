#!/usr/bin/env python3
"""
verify_slides.py - verification tool for slide decks.

Stdlib-only. Cross-platform (Windows + Unix). No external deps.

Supports two input formats:

  1. Markdown slides (.md, .txt). Slides are separated either by a `---`
     thematic break (Marp / Slidev / reveal.js convention) or by `## `
     H2 headings. Speaker notes inside an HTML comment (`<!-- ... -->`)
     are treated as the slide's notes (Marp convention).

  2. PowerPoint (.pptx). Parsed by reading the OOXML zip directly with
     stdlib `zipfile` + `xml.etree.ElementTree`. We pull text from
     `<a:t>` runs and notes from `notesSlide{N}.xml`. No python-pptx.

Usage (from a skill):
    bash tools/run.sh verify_slides.py <draft_path> [--slide-count-min=N] [--slide-count-max=N] [--max-words-per-slide=N] [--max-bullets-per-slide=N] [--notes-coverage-target=PCT]

Direct invocation:
    py  tools/verify_slides.py <draft_path>
    python3 tools/verify_slides.py <draft_path>

Emits a JSON object to stdout matching the verification-protocols schema.

Checks (all enforced; deck "passed" only if all pass):
    1. slide_count             - within [min, max] (default 5-30)
    2. words_per_slide_max     - no slide exceeds N words (default 50)
    3. bullets_per_slide_max   - no slide exceeds N bullets (default 7)
    4. title_length            - all slide titles <= 12 words
    5. title_uniqueness        - no duplicate titles (boilerplate exempt)
    6. notes_coverage          - >= PCT of slides have speaker notes (default 50)
    7. agenda_or_close         - deck has either an agenda or a closing slide
    8. claim_title_ratio       - >= 30% of titles read as claims, not nouns
"""

from __future__ import annotations

import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

TOOL_NAME = "verify_slides"
SCHEMA_VERSION = 1

# ---------------------------------------------------------------------------
# Shared regex / constants
# ---------------------------------------------------------------------------

THEMATIC_BREAK_RE = re.compile(r"^---\s*$", re.MULTILINE)
H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
H2_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
H_TITLE_RE = re.compile(r"^(#{1,2})\s+(.+?)\s*$", re.MULTILINE)
BULLET_RE = re.compile(r"^\s*[\-\*\+]\s+(.+?)\s*$", re.MULTILINE)
NOTES_RE = re.compile(r"<!--\s*(.+?)\s*-->", re.DOTALL)
# Frontmatter: opening `---` at start, content that looks like YAML key:value lines,
# closing `---` followed by either a newline OR end-of-file. The YAML-key check
# is what disambiguates real Marp/Slidev frontmatter from a deck that just opens
# with a slide separator.
FRONTMATTER_RE = re.compile(
    r"\A---\s*\n(?P<body>.*?)\n---\s*(?:\n|\Z)", re.DOTALL
)
# A line that looks like a YAML key (used to confirm a `---...---` block is real frontmatter).
YAML_KEY_LINE_RE = re.compile(r"^\s*[A-Za-z_][\w-]*\s*:", re.MULTILINE)
# Fenced code blocks ``` or ~~~ — used to mask out content before slide-splitting.
FENCE_OPEN_RE = re.compile(r"^(\s*)(```+|~~~+)(\S*)\s*$")

# Boilerplate titles that are allowed to repeat or be generic.
BOILERPLATE_TITLES = {
    # generic / both scenarios
    "agenda", "outline", "thank you", "thanks", "questions", "q&a",
    "discussion", "appendix", "references", "title", "introduction",
    "summary", "conclusion", "next steps", "recap", "takeaways",
    "key takeaways", "wrap-up", "wrap up",
    # pitch-deck close slots
    "the ask", "our ask", "use of funds", "contact",
    # academic close slots
    "future work", "limitations", "threats to validity",
    "acknowledgments", "acknowledgements",
}

# Words that, when used as a verb in a title, signal a claim rather than a noun-phrase.
# E.g. "Latency dropped 40%" (claim) vs "Latency Improvements" (noun).
CLAIM_VERB_TOKENS = {
    "is", "are", "was", "were", "drops", "dropped", "fell", "rose", "grew",
    "shrunk", "doubled", "tripled", "halved", "beats", "beat", "wins", "won",
    "loses", "lost", "kills", "killed", "ships", "shipped", "saves", "saved",
    "costs", "cost", "delivers", "delivered", "needs", "broke", "breaks",
    "scales", "scaled", "cuts", "cut", "raises", "raised", "drives", "drove",
    "exits", "exited", "earns", "earned", "owns", "owned", "matters", "mattered",
    "fails", "failed", "works", "worked", "should", "must", "can", "cannot",
    "will", "outperforms", "outperformed",
    "reduces", "reduced", "increases", "increased", "moves", "moved",
}

# Numeric or percentage tokens also signal claim-titles.
NUMERIC_RE = re.compile(r"\d")

# "X for Y" — pitch-deck positioning ("Stripe for dental claims", "Cursor for SQL").
POSITIONING_FOR_RE = re.compile(r"\b\w[\w\-]*\s+for\s+\w", re.IGNORECASE)
# "From X to Y" — transformation claim ("From intake to paid claim", "From idea to ship in 60s").
FROM_TO_RE = re.compile(r"^\s*from\s+\w[\w\-\s]*\s+to\s+\w", re.IGNORECASE)
# "X: Y" — colon claim ("Acme: post-op recovery for ortho", "Q4 strategy: cut consumer").
COLON_CLAIM_RE = re.compile(r"^[^:]{2,40}:\s*\S{2,}")

PPTX_NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


# ---------------------------------------------------------------------------
# Markdown slide parsing
# ---------------------------------------------------------------------------

def strip_frontmatter(text: str) -> str:
    """Remove YAML frontmatter at the top of the doc (if present).

    Only strips when the content between the `---` markers actually looks like
    YAML (contains at least one `key:` line). This prevents mis-eating a deck
    whose first content is a `---` slide separator.
    """
    m = FRONTMATTER_RE.match(text)
    if not m:
        return text
    fm_body = m.group("body")
    if not YAML_KEY_LINE_RE.search(fm_body):
        return text
    return text[m.end():]


def _mask_fenced_blocks(text: str) -> str:
    """Replace fenced-code-block content (``` or ~~~) with blank lines so that
    `---` and `## ` inside code blocks are not treated as slide delimiters.
    Line count is preserved so that regex line offsets stay valid."""
    out_lines: list[str] = []
    fence_marker: str | None = None
    for line in text.splitlines():
        stripped = line.lstrip()
        if fence_marker is None:
            m = FENCE_OPEN_RE.match(line)
            if m and m.group(2):
                fence_marker = m.group(2)[0]  # ` or ~
                out_lines.append(line)
                continue
            out_lines.append(line)
        else:
            # Inside a fence; close on a matching fence-close line.
            if stripped.startswith(fence_marker * 3):
                out_lines.append(line)
                fence_marker = None
            else:
                # Mask the content; keep the line break so offsets line up.
                out_lines.append("")
    return "\n".join(out_lines)


def split_markdown_slides(text: str) -> list[dict]:
    """
    Return a list of slide dicts: {"title": str, "body": str, "notes": str}.

    Detection (in order):
      - Frontmatter (if present) is stripped first.
      - If at least one `---` thematic break appears outside fenced code, split by them.
      - Else if multiple H1 headings exist, split by H1.
      - Else if multiple H2 headings exist, split by H2.
      - Else treat the whole document as one slide.

    Splitting on `---` and headings ignores content inside fenced code blocks.
    """
    body = strip_frontmatter(text)
    if not body.strip():
        return []
    masked = _mask_fenced_blocks(body)

    breaks = list(THEMATIC_BREAK_RE.finditer(masked))
    if breaks:
        chunks: list[str] = []
        prev_end = 0
        for m in breaks:
            chunk = body[prev_end:m.start()].strip()
            if chunk:
                chunks.append(chunk)
            prev_end = m.end()
        tail = body[prev_end:].strip()
        if tail:
            chunks.append(tail)
        if len(chunks) >= 2:
            return [_chunk_to_slide(c) for c in chunks]
        # Fall through if a single break produced only one non-empty chunk.

    h1s = list(H1_RE.finditer(masked))
    h2s = list(H2_RE.finditer(masked))
    headings: list[re.Match] | None = None
    if len(h1s) >= 2:
        headings = h1s
    elif len(h2s) >= 2:
        headings = h2s
    if headings:
        slides: list[dict] = []
        for i, m in enumerate(headings):
            start = m.start()
            end = headings[i + 1].start() if i + 1 < len(headings) else len(body)
            chunk = body[start:end].strip()
            slides.append(_chunk_to_slide(chunk))
        return slides

    chunk = body.strip()
    if not chunk:
        return []
    return [_chunk_to_slide(chunk)]


def _chunk_to_slide(chunk: str) -> dict:
    """Pull title / body / notes out of one markdown chunk."""
    notes_parts = NOTES_RE.findall(chunk)
    notes = "\n".join(p.strip() for p in notes_parts).strip()
    body_no_notes = NOTES_RE.sub("", chunk).strip()

    title = ""
    title_match = H_TITLE_RE.search(body_no_notes)
    if title_match:
        title = title_match.group(2).strip()
        body_no_notes = (
            body_no_notes[: title_match.start()] + body_no_notes[title_match.end():]
        ).strip()

    return {"title": title, "body": body_no_notes, "notes": notes}


# ---------------------------------------------------------------------------
# .pptx parsing (stdlib only)
# ---------------------------------------------------------------------------

def _ordered_slide_paths(zf: zipfile.ZipFile) -> list[str]:
    """Return slide XML paths in canonical presentation order.

    Resolves `ppt/presentation.xml` `<p:sldIdLst>` -> `r:id` -> `ppt/_rels/presentation.xml.rels`
    -> target. Falls back to filename-number sort if relationships are missing.
    """
    names = zf.namelist()
    fallback = sorted(
        (n for n in names if re.match(r"ppt/slides/slide\d+\.xml$", n)),
        key=lambda n: int(re.search(r"slide(\d+)\.xml$", n).group(1)),
    )
    pres_xml_name = "ppt/presentation.xml"
    rels_name = "ppt/_rels/presentation.xml.rels"
    if pres_xml_name not in names or rels_name not in names:
        return fallback
    try:
        with zf.open(pres_xml_name) as f:
            pres_root = ET.fromstring(f.read())
        with zf.open(rels_name) as f:
            rels_root = ET.fromstring(f.read())
    except (ET.ParseError, KeyError):
        return fallback
    rid_to_target: dict[str, str] = {}
    rels_ns = "http://schemas.openxmlformats.org/package/2006/relationships"
    for rel in rels_root.iter("{%s}Relationship" % rels_ns):
        rid = rel.get("Id")
        target = rel.get("Target") or ""
        if rid and target:
            # Targets are relative to ppt/; normalize to repo-style path.
            if target.startswith("/"):
                normalized = target.lstrip("/")
            else:
                normalized = "ppt/" + target.lstrip("./")
            rid_to_target[rid] = normalized
    ordered: list[str] = []
    for sld_id in pres_root.iter("{%s}sldId" % PPTX_NS["p"]):
        rid = sld_id.get("{%s}id" % PPTX_NS["r"])
        if rid and rid in rid_to_target and rid_to_target[rid] in names:
            ordered.append(rid_to_target[rid])
    return ordered or fallback


def _slide_to_notes_path(zf: zipfile.ZipFile, slide_path: str) -> str | None:
    """Resolve a slide's notesSlide path via its per-slide rels file."""
    rels_path = slide_path.replace("ppt/slides/", "ppt/slides/_rels/") + ".rels"
    if rels_path not in zf.namelist():
        return None
    try:
        with zf.open(rels_path) as f:
            root = ET.fromstring(f.read())
    except (ET.ParseError, KeyError):
        return None
    rels_ns = "http://schemas.openxmlformats.org/package/2006/relationships"
    notes_type = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide"
    for rel in root.iter("{%s}Relationship" % rels_ns):
        if rel.get("Type") == notes_type:
            target = rel.get("Target") or ""
            # Targets like "../notesSlides/notesSlide1.xml" -> "ppt/notesSlides/notesSlide1.xml"
            if target.startswith("../"):
                resolved = "ppt/" + target[3:]
            elif target.startswith("/"):
                resolved = target.lstrip("/")
            else:
                resolved = "ppt/slides/" + target
            if resolved in zf.namelist():
                return resolved
    return None


def parse_pptx(path: Path) -> list[dict]:
    """Return slides list from a .pptx file using stdlib zipfile + xml.

    Slide order is taken from `ppt/presentation.xml` + relationships (canonical
    presentation order, robust to slide reordering). Notes are resolved via
    each slide's own `_rels/slideN.xml.rels` rather than by index.
    """
    slides: list[dict] = []
    with zipfile.ZipFile(path) as zf:
        slide_paths = _ordered_slide_paths(zf)
        for slide_path in slide_paths:
            with zf.open(slide_path) as f:
                slide_xml = f.read()
            title, body, bullets = _extract_pptx_slide_text(slide_xml)
            notes = ""
            notes_path = _slide_to_notes_path(zf, slide_path)
            if notes_path:
                with zf.open(notes_path) as nf:
                    notes_xml = nf.read()
                notes = _extract_pptx_notes_text(notes_xml)
            slides.append(
                {
                    "title": title,
                    "body": body,
                    "notes": notes,
                    "_pptx_bullets": bullets,
                }
            )
    return slides


# Placeholder types that hold chrome (slide number, date, header, footer), not content.
PPTX_CHROME_PH_TYPES = {"sldNum", "dt", "ftr", "hdr"}


def _extract_pptx_slide_text(xml_bytes: bytes) -> tuple[str, str, list[str]]:
    """Pull (title, body_text, bullet_list) from a slide XML.

    Title detection (in order):
      1. Shape whose `<p:ph>` has type='title' or 'ctrTitle'.
      2. Shape whose `<p:ph>` has idx='0' (templates often put title there
         and inherit the type from the layout, leaving an empty type=).
      3. First non-empty placeholder shape (last-resort fallback).
    """
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return "", "", []

    title = ""
    body_lines: list[str] = []
    bullets: list[str] = []
    candidates_for_fallback_title: list[str] = []  # populated only if no explicit title found

    for sp in root.iter("{%s}sp" % PPTX_NS["p"]):
        ph = sp.find(".//{%s}ph" % PPTX_NS["p"])
        ph_type = ph.get("type", "") if ph is not None else ""
        ph_idx = ph.get("idx", "") if ph is not None else ""
        if ph_type in PPTX_CHROME_PH_TYPES:
            continue  # slide number, date, footer, header — not content
        is_explicit_title = ph_type in ("title", "ctrTitle")
        is_implicit_title = ph is not None and ph_idx == "0" and not ph_type

        paragraphs: list[str] = []
        for p in sp.iter("{%s}p" % PPTX_NS["a"]):
            text_runs = [t.text or "" for t in p.iter("{%s}t" % PPTX_NS["a"])]
            line = "".join(text_runs).strip()
            if line:
                paragraphs.append(line)
        if not paragraphs:
            continue

        if is_explicit_title and not title:
            title = " ".join(paragraphs).strip()
            continue
        if is_implicit_title and not title:
            # Treat idx='0' placeholder as title only if no explicit title appears.
            # We park it as a candidate so we can still walk the rest of the shapes.
            candidates_for_fallback_title.append(" ".join(paragraphs).strip())
            continue
        body_lines.extend(paragraphs)
        bullets.extend(paragraphs)

    if not title and candidates_for_fallback_title:
        title = candidates_for_fallback_title[0]
        # The remaining idx=0 candidates (rare) become body.
        for extra in candidates_for_fallback_title[1:]:
            body_lines.append(extra)
            bullets.append(extra)

    return title, "\n".join(body_lines), bullets


def _extract_pptx_notes_text(xml_bytes: bytes) -> str:
    """Pull free text from a notesSlide XML.

    Skips chrome placeholder shapes (slide number, date, footer, header) so we
    don't count them as speaker notes.
    """
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return ""
    lines: list[str] = []
    for sp in root.iter("{%s}sp" % PPTX_NS["p"]):
        ph = sp.find(".//{%s}ph" % PPTX_NS["p"])
        ph_type = ph.get("type", "") if ph is not None else ""
        if ph_type in PPTX_CHROME_PH_TYPES:
            continue
        for p in sp.iter("{%s}p" % PPTX_NS["a"]):
            text_runs = [t.text or "" for t in p.iter("{%s}t" % PPTX_NS["a"])]
            line = "".join(text_runs).strip()
            if line:
                lines.append(line)
    return "\n".join(lines).strip()


# ---------------------------------------------------------------------------
# Slide-level metric helpers
# ---------------------------------------------------------------------------

def count_slide_words(slide: dict) -> int:
    """Word count for the slide body + title (notes excluded — they aren't on screen)."""
    text = (slide.get("title") or "") + " " + (slide.get("body") or "")
    cleaned = re.sub(r"[`*_#>\-\[\]\(\)]", " ", text)
    return len([t for t in cleaned.split() if t])


def count_slide_bullets(slide: dict) -> int:
    """Number of bullet items in this slide."""
    if "_pptx_bullets" in slide:
        return len(slide["_pptx_bullets"])
    body = slide.get("body") or ""
    return len(BULLET_RE.findall(body))


def title_word_count(title: str) -> int:
    cleaned = re.sub(r"[`*_]", "", title)
    return len([t for t in cleaned.split() if t])


def is_claim_title(title: str) -> bool:
    """A claim-title makes an assertion; a noun-title is just a topic.

    Heuristic, in order of confidence:
      1. Contains a digit ("Latency dropped 40%", "Migration ships March 1").
      2. Contains a verb token from CLAIM_VERB_TOKENS.
      3. Matches "X for Y" pattern (pitch positioning: "Stripe for X").
      4. Matches "From X to Y" pattern (transformation claim).
      5. Matches "X: Y" colon pattern (claim with restatement).
    """
    if not title:
        return False
    if NUMERIC_RE.search(title):
        return True
    tokens = {t.lower().strip(".,;:!?") for t in title.split()}
    if tokens & CLAIM_VERB_TOKENS:
        return True
    if POSITIONING_FOR_RE.search(title):
        return True
    if FROM_TO_RE.match(title):
        return True
    if COLON_CLAIM_RE.match(title):
        return True
    return False


def normalize_title(title: str) -> str:
    """Lowercase, collapse whitespace, strip leading/trailing punctuation.
    `Questions` and `Questions?` should normalize to the same value."""
    cleaned = re.sub(r"\s+", " ", title.strip().lower())
    return cleaned.strip(".,;:!?\"'()[] ")


# ---------------------------------------------------------------------------
# Main check assembly
# ---------------------------------------------------------------------------

def build_result(
    *,
    input_file: str,
    slides: list[dict],
    slide_count_min: int,
    slide_count_max: int,
    max_words_per_slide: int,
    max_bullets_per_slide: int,
    max_title_words: int,
    notes_coverage_target: float,
    claim_title_target_pct: float,
) -> dict:
    n = len(slides)

    # 1. slide_count
    count_passed = slide_count_min <= n <= slide_count_max
    count_check = {
        "name": "slide_count",
        "passed": count_passed,
        "value": n,
        "target": f"{slide_count_min}-{slide_count_max}",
        "detail": (
            f"deck has {n} slide(s); target {slide_count_min}-{slide_count_max}"
        ),
    }

    # 2. words_per_slide_max
    word_overs: list[tuple[int, int, str]] = []  # (slide_idx_1based, words, title)
    max_words_observed = 0
    for i, s in enumerate(slides, start=1):
        w = count_slide_words(s)
        max_words_observed = max(max_words_observed, w)
        if w > max_words_per_slide:
            word_overs.append((i, w, (s.get("title") or "")[:60]))
    words_check = {
        "name": "words_per_slide_max",
        "passed": len(word_overs) == 0,
        "value": max_words_observed,
        "target": max_words_per_slide,
        "detail": (
            f"max words on any slide: {max_words_observed}; limit {max_words_per_slide}"
            + (f". Over-limit slides: {word_overs}" if word_overs else "")
        ),
    }

    # 3. bullets_per_slide_max
    bullet_overs: list[tuple[int, int, str]] = []
    max_bullets_observed = 0
    for i, s in enumerate(slides, start=1):
        b = count_slide_bullets(s)
        max_bullets_observed = max(max_bullets_observed, b)
        if b > max_bullets_per_slide:
            bullet_overs.append((i, b, (s.get("title") or "")[:60]))
    bullets_check = {
        "name": "bullets_per_slide_max",
        "passed": len(bullet_overs) == 0,
        "value": max_bullets_observed,
        "target": max_bullets_per_slide,
        "detail": (
            f"max bullets on any slide: {max_bullets_observed}; limit {max_bullets_per_slide}"
            + (f". Over-limit slides: {bullet_overs}" if bullet_overs else "")
        ),
    }

    # 4. title_length
    title_overs: list[tuple[int, int, str]] = []
    titles_present = 0
    for i, s in enumerate(slides, start=1):
        t = (s.get("title") or "").strip()
        if not t:
            continue
        titles_present += 1
        wc = title_word_count(t)
        if wc > max_title_words:
            title_overs.append((i, wc, t[:80]))
    title_len_check = {
        "name": "title_length",
        "passed": len(title_overs) == 0,
        "value": len(title_overs),
        "target": 0,
        "detail": (
            f"{titles_present} of {n} slides have a title; "
            f"{len(title_overs)} title(s) exceed {max_title_words} words"
            + (f": {title_overs}" if title_overs else "")
        ),
    }

    # 5. title_uniqueness (non-boilerplate duplicates only)
    seen: dict[str, list[int]] = {}
    for i, s in enumerate(slides, start=1):
        t = normalize_title(s.get("title") or "")
        if not t or t in BOILERPLATE_TITLES:
            continue
        seen.setdefault(t, []).append(i)
    duplicates = {t: idxs for t, idxs in seen.items() if len(idxs) > 1}
    uniq_check = {
        "name": "title_uniqueness",
        "passed": len(duplicates) == 0,
        "value": len(duplicates),
        "target": 0,
        "detail": (
            "all non-boilerplate titles unique"
            if not duplicates
            else f"duplicate titles (excluding boilerplate): {duplicates}"
        ),
    }

    # 6. notes_coverage
    with_notes = sum(1 for s in slides if (s.get("notes") or "").strip())
    coverage_pct = round(100.0 * with_notes / n, 1) if n else 0.0
    notes_check = {
        "name": "notes_coverage",
        "passed": coverage_pct >= notes_coverage_target,
        "value": coverage_pct,
        "target": notes_coverage_target,
        "detail": (
            f"{with_notes} of {n} slides have speaker notes ({coverage_pct}%); "
            f"target >={notes_coverage_target}%"
        ),
    }

    # 7. agenda_or_close — first 2 OR last 2 slides should include either an agenda
    #    or a closing slide. Tiny decks (n<=3) get a free pass.
    has_agenda_or_close = False
    if n <= 3:
        has_agenda_or_close = True
        detail_ac = "deck too short for agenda/close requirement (n<=3)"
    else:
        head = slides[:2]
        tail = slides[-2:]
        targets = head + tail
        for s in targets:
            t = normalize_title(s.get("title") or "")
            if t in BOILERPLATE_TITLES or any(
                kw in t for kw in (
                    # Front: agenda / outline patterns
                    "agenda", "outline", "what we'll cover", "what i'll cover",
                    "what's in this deck", "roadmap",
                    # Back: generic close
                    "summary", "conclusion", "next step", "takeaway",
                    "wrap", "recap", "thank", "questions", "q&a",
                    # Pitch-deck close
                    "the ask", "our ask", "ask:", "use of funds",
                    "contact", "let's talk",
                    # Academic close
                    "future work", "limitations",
                )
            ):
                has_agenda_or_close = True
                break
        detail_ac = (
            "agenda or closing slide present"
            if has_agenda_or_close
            else "neither an agenda slide (front) nor a closing slide (back) detected"
        )
    ac_check = {
        "name": "agenda_or_close",
        "passed": has_agenda_or_close,
        "value": has_agenda_or_close,
        "detail": detail_ac,
    }

    # 8. claim_title_ratio — fraction of titles that read as a claim
    titled_slides = [s for s in slides if (s.get("title") or "").strip()]
    if not titled_slides:
        claim_ratio = 0.0
        claim_passed = False
        claim_detail = "no slide titles found"
    else:
        # Skip boilerplate titles in the claim-ratio judgment — agendas don't need verbs.
        non_boiler = [
            s for s in titled_slides
            if normalize_title(s["title"]) not in BOILERPLATE_TITLES
            and not any(kw in normalize_title(s["title"]) for kw in (
                "agenda", "outline", "thank", "questions", "q&a", "title slide",
            ))
        ]
        if not non_boiler:
            claim_ratio = 100.0
            claim_passed = True
            claim_detail = "all titled slides are boilerplate; claim-title check waived"
        else:
            claims = sum(1 for s in non_boiler if is_claim_title(s["title"]))
            claim_ratio = round(100.0 * claims / len(non_boiler), 1)
            claim_passed = claim_ratio >= claim_title_target_pct
            claim_detail = (
                f"{claims} of {len(non_boiler)} non-boilerplate titles read as claims "
                f"({claim_ratio}%); target >={claim_title_target_pct}%. "
                "A claim-title contains a verb or a number "
                "('Latency dropped 40%') vs a noun-title ('Latency Improvements')."
            )
    claim_check = {
        "name": "claim_title_ratio",
        "passed": claim_passed,
        "value": claim_ratio,
        "target": claim_title_target_pct,
        "detail": claim_detail,
    }

    checks = [
        count_check,
        words_check,
        bullets_check,
        title_len_check,
        uniq_check,
        notes_check,
        ac_check,
        claim_check,
    ]
    passed = all(c["passed"] for c in checks)
    failed_names = [c["name"] for c in checks if not c["passed"]]
    summary = (
        "all checks passed"
        if passed
        else f"{len(failed_names)} of {len(checks)} checks failed: {', '.join(failed_names)}"
    )

    total_words = sum(count_slide_words(s) for s in slides)
    total_bullets = sum(count_slide_bullets(s) for s in slides)

    return {
        "tool": TOOL_NAME,
        "schema_version": SCHEMA_VERSION,
        "timestamp": now_iso(),
        "input_file": input_file,
        "passed": passed,
        "checks": checks,
        "summary": summary,
        "metrics": {
            "slide_count": n,
            "total_words": total_words,
            "avg_words_per_slide": round(total_words / n, 1) if n else 0,
            "max_words_per_slide": max_words_observed,
            "total_bullets": total_bullets,
            "slides_with_notes": with_notes,
            "notes_coverage_pct": coverage_pct,
            "claim_title_ratio_pct": claim_ratio,
        },
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str]) -> dict:
    if len(argv) < 2:
        raise SystemExit(
            "usage: verify_slides.py <draft_path> "
            "[--slide-count-min=N] [--slide-count-max=N] "
            "[--max-words-per-slide=N] [--max-bullets-per-slide=N] "
            "[--max-title-words=N] [--notes-coverage-target=PCT] "
            "[--claim-title-target=PCT]"
        )
    out = {
        "draft_path": argv[1],
        "slide_count_min": 5,
        "slide_count_max": 30,
        "max_words_per_slide": 50,
        "max_bullets_per_slide": 7,
        "max_title_words": 12,
        "notes_coverage_target": 50.0,
        "claim_title_target": 30.0,
    }
    int_flags = {
        "--slide-count-min=": "slide_count_min",
        "--slide-count-max=": "slide_count_max",
        "--max-words-per-slide=": "max_words_per_slide",
        "--max-bullets-per-slide=": "max_bullets_per_slide",
        "--max-title-words=": "max_title_words",
    }
    float_flags = {
        "--notes-coverage-target=": "notes_coverage_target",
        "--claim-title-target=": "claim_title_target",
    }
    for arg in argv[2:]:
        matched = False
        for prefix, key in int_flags.items():
            if arg.startswith(prefix):
                try:
                    out[key] = int(arg.split("=", 1)[1])
                except ValueError as e:
                    raise SystemExit(f"invalid {prefix} value: {arg}") from e
                matched = True
                break
        if matched:
            continue
        for prefix, key in float_flags.items():
            if arg.startswith(prefix):
                try:
                    out[key] = float(arg.split("=", 1)[1])
                except ValueError as e:
                    raise SystemExit(f"invalid {prefix} value: {arg}") from e
                matched = True
                break
        if matched:
            continue
        if arg.startswith("--"):
            raise SystemExit(f"unknown flag: {arg}")
        raise SystemExit(f"unknown positional argument: {arg}")
    return out


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


def load_slides(p: Path) -> list[dict]:
    suffix = p.suffix.lower()
    if suffix == ".pptx":
        return parse_pptx(p)
    text = p.read_text(encoding="utf-8")
    return split_markdown_slides(text)


def main(argv: list[str]) -> int:
    try:
        opts = parse_args(argv)
    except SystemExit as exc:
        emit_error(argv[1] if len(argv) > 1 else "", str(exc).strip() or "argument error", "ArgumentError")
        return 2

    p = Path(opts["draft_path"])
    if not p.exists():
        emit_error(str(p), f"input file not found: {p}", "FileNotFoundError")
        return 2

    try:
        slides = load_slides(p)
    except (UnicodeDecodeError, OSError, zipfile.BadZipFile) as exc:
        emit_error(str(p), f"could not read draft: {exc}", type(exc).__name__)
        return 2

    if not slides:
        emit_error(str(p), "no slides detected (empty file or unrecognized structure)", "EmptyDeckError")
        return 2

    try:
        result = build_result(
            input_file=str(p),
            slides=slides,
            slide_count_min=opts["slide_count_min"],
            slide_count_max=opts["slide_count_max"],
            max_words_per_slide=opts["max_words_per_slide"],
            max_bullets_per_slide=opts["max_bullets_per_slide"],
            max_title_words=opts["max_title_words"],
            notes_coverage_target=opts["notes_coverage_target"],
            claim_title_target_pct=opts["claim_title_target"],
        )
    except Exception as exc:  # defensive: never traceback to stdout
        emit_error(str(p), f"unexpected error during verification: {exc}", type(exc).__name__)
        return 2

    sys.stdout.write(json.dumps(result, ensure_ascii=False, indent=2))
    sys.stdout.write("\n")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
