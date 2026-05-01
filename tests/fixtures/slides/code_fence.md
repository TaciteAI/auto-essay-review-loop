---
marp: true
title: Deck with code fences containing slide-separator look-alikes
---

# Why we replaced our YAML splitter

- Our old splitter blew up on YAML inside slides
- The fix: track fence state before applying the slide rule
- Cost us a day; saved future weeks of debugging

<!-- Open with the lesson, not the code. -->

---

## The bug, in code

```yaml
config:
  ---
  legacy: true
  ---
  fallback: false
```

That fragment used to break the splitter — three thematic-break-shaped lines.

<!-- Show the bug. -->

---

## The fix

```python
def split_markdown_slides(text):
    masked = _mask_fenced_blocks(text)
    breaks = list(THEMATIC_BREAK_RE.finditer(masked))
    ...
```

Six lines of pre-pass, plus a fence-tracker. Took 18 minutes to write, including tests.

<!-- The fix is small. The lesson is bigger. -->

---

## Lesson: parsers should respect fences

- A markdown parser that doesn't track fenced blocks is a markdown parser that mis-parses any deck containing code
- This applies to `---`, `## `, `# `, and any other line-prefix delimiter
- The fix is always cheaper than the bug

<!-- Land the recurring point. -->

---

## Takeaways

- Track fenced state before applying line-level rules
- Test fixtures should include the failure mode you're protecting against
- This deck is itself a regression test for our splitter

<!-- Close with the meta-joke: this very file is the test. -->
