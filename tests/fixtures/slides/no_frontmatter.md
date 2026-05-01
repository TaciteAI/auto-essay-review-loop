---

# Slide 1: deck opens with a thematic break

This deck has NO frontmatter. The opening `---` is a slide separator, not the
opening of a YAML block. A previous version of the parser treated any
opening `---...---` as frontmatter and dropped the first slide.

<!-- Regression test. -->

---

## Slide 2: the assertion

- The parser must produce N slides, not N-1
- The first slide's title must survive

<!-- Land the point. -->

---

## Slide 3: a third slide for good measure

- Three is enough to verify
- Counts and titles all matter
- Don't lose the first one

<!-- Close. -->

---

## Slide 4: a closing slide

- Wrap up so verification has an agenda_or_close

<!-- Done. -->

---

## Takeaways

- Frontmatter requires a YAML key inside the markers
- Without one, the opening `---` is a slide separator
- Bug fix; ship it

<!-- Final. -->
