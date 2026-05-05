#!/usr/bin/env python3
"""Per-draft hard verification for blog-batch-20260505.

Runs the same checks the auto-blog-review-loop skill enforces in Phase B.7:
- word count in [500, 4000]
- exactly one H1
- >= 2 H2s
- no header-level skips (H1 -> H3 etc.)
- no H4 without an H3 above
- code-fence count is even AND every opening fence has a language tag
- no platform pollutants (emojis, hashtags, @-handles)

Link resolution is delegated to tools/verify_links.sh (kept separate
because it's I/O-bound). This script is pure-text / synchronous.

Output: single JSON blob to stdout.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

EMOJI_RE = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F600-\U0001F64F]"
)
HASHTAG_RE = re.compile(r"(?<![\w&])#[A-Za-z0-9_\-]+\b")
HANDLE_RE = re.compile(r"(?<![\w@])@[A-Za-z0-9_]{2,}\b")
LINK_RE = re.compile(r"\[[^\]]+\]\((https?://[^)\s]+)\)")
HEADER_RE = re.compile(r"^(#{1,6})\s+\S", re.MULTILINE)
FENCE_RE = re.compile(r"^```([^\s`]*)?", re.MULTILINE)


def count_words(text: str) -> int:
    body = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    body = re.sub(r"`[^`]+`", "", body)
    body = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", body)
    body = re.sub(r"[#>*_~`-]", " ", body)
    tokens = re.findall(r"[\w一-鿿]+", body)
    cjk = sum(1 for t in tokens if re.search(r"[一-鿿]", t))
    if cjk > 50:
        cjk_chars = sum(len(re.findall(r"[一-鿿]", t)) for t in tokens)
        latin = sum(1 for t in tokens if not re.search(r"[一-鿿]", t))
        return cjk_chars + latin
    return len(tokens)


def verify(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    issues: list[dict] = []

    word_count = count_words(text)
    word_ok = 500 <= word_count <= 4000
    if not word_ok:
        issues.append(
            {
                "severity": "CRITICAL",
                "check": "word_count",
                "issue": f"word count {word_count} outside [500, 4000]",
            }
        )

    headers = [(len(m.group(1)), m.start()) for m in HEADER_RE.finditer(text)]
    h1s = [h for h in headers if h[0] == 1]
    h2s = [h for h in headers if h[0] == 2]

    if len(h1s) != 1:
        issues.append(
            {
                "severity": "CRITICAL",
                "check": "h1_count",
                "issue": f"expected exactly 1 H1, found {len(h1s)}",
            }
        )
    if len(h2s) < 2:
        issues.append(
            {
                "severity": "CRITICAL",
                "check": "h2_count",
                "issue": f"expected >= 2 H2s, found {len(h2s)}",
            }
        )

    prev_level = 0
    for level, _ in headers:
        if prev_level and level - prev_level > 1:
            issues.append(
                {
                    "severity": "CRITICAL",
                    "check": "skip_level",
                    "issue": f"header jumps from H{prev_level} to H{level}",
                }
            )
            break
        prev_level = level

    fences = FENCE_RE.findall(text)
    if len(fences) % 2 != 0:
        issues.append(
            {
                "severity": "CRITICAL",
                "check": "fence_unmatched",
                "issue": f"odd number of code fences: {len(fences)}",
            }
        )
    for i in range(0, len(fences) - 1, 2):
        opener = fences[i]
        if not opener:
            issues.append(
                {
                    "severity": "MAJOR",
                    "check": "fence_no_lang",
                    "issue": "opening code fence missing language tag",
                }
            )

    text_no_urls = re.sub(r"https?://\S+", "", text)
    text_no_urls = re.sub(r"\[[^\]]+\]\([^)]+\)", "", text_no_urls)

    emojis = EMOJI_RE.findall(text_no_urls)
    if emojis:
        issues.append(
            {
                "severity": "MAJOR",
                "check": "emojis",
                "issue": f"found {len(emojis)} emoji(s): {emojis[:3]}",
            }
        )
    hashtags = HASHTAG_RE.findall(text_no_urls)
    if hashtags:
        issues.append(
            {
                "severity": "MAJOR",
                "check": "hashtags",
                "issue": f"found hashtags: {hashtags[:3]}",
            }
        )
    handles = HANDLE_RE.findall(text_no_urls)
    if handles:
        issues.append(
            {
                "severity": "MINOR",
                "check": "at_handles",
                "issue": f"found @-handles: {handles[:3]}",
            }
        )

    links = LINK_RE.findall(text)
    if len(links) < 2:
        issues.append(
            {
                "severity": "CRITICAL",
                "check": "link_count",
                "issue": f"expected >= 2 inline https links, found {len(links)}",
            }
        )

    return {
        "path": str(path),
        "word_count": word_count,
        "h1_count": len(h1s),
        "h2_count": len(h2s),
        "fence_count": len(fences),
        "link_count": len(links),
        "passed": not any(i["severity"] == "CRITICAL" for i in issues),
        "issues": issues,
        "links": links,
    }


def main() -> int:
    if len(sys.argv) < 2:
        print(json.dumps({"error": "usage: verify_one.py <draft.md> [draft2.md ...]"}))
        return 2
    out = [verify(Path(p)) for p in sys.argv[1:]]
    print(json.dumps(out if len(out) > 1 else out[0], indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
