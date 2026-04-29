# Brand Voice

<!--
  Place this file at the root of your project as `BRAND_VOICE.md`.
  When the loop detects it, every persona's review prompt is augmented
  with this content. Personas check the draft for voice consistency
  and flag drift.

  Without this file: personas converge the draft toward generic
  high-engagement templates (AI-slop optimization risk).
  With this file: personas defend YOUR voice.

  Spec: skills/shared-references/brand-voice-protocol.md

  Replace every < ... > placeholder. Delete sections you don't need.
-->

## Who

<!--
  One paragraph. Who are you, what do you write about, who reads it?
  Be specific. "Indie hacker building dev tools, reads of indie hackers
  and infra engineers, known for short technical posts with concrete
  numbers" beats "tech writer."
-->

<your role>. <your audience>. <what you're known for>.

Example:
> Indie hacker building dev tools. Audience is other indie hackers and
> infra engineers. Known for short technical posts with concrete numbers
> and zero corporate framing. Writes from lived experience — first-person,
> what actually happened, what actually broke, what the fix was.

---

## Voice attributes

<!-- Pick what fits. Delete what doesn't. -->

- **Tone:** <direct / playful / academic / contrarian / dry / warm / ...>
- **Sentence rhythm:** <short and punchy / mixed / long-form / fragments OK>
- **Humor:** <none / dry / self-deprecating / observational / footnote-tier>
- **Vocabulary:** <plain / technical / jargon-heavy / minimal jargon>
- **POV:** <I / we / you / mixed>
- **Cadence:** <one idea per paragraph / dense / list-heavy / story-arc>
- **Reading speed:** <skimmable / dense / requires focus>

Example:
> - **Tone:** direct, builder-to-builder. No corporate fluff.
> - **Sentence rhythm:** short. Mixed with the occasional long one for
>   contrast.
> - **Humor:** dry, observational. No jokes that announce themselves.
> - **Vocabulary:** technical when needed, plain otherwise. Jargon only
>   if a non-technical reader can infer it from context.
> - **POV:** I. Sometimes "you" for direct address. Never "we" unless
>   it's actually a team.

---

## Banned phrases

<!--
  Phrases that are NOT this voice. Personas reject drafts that contain them.
  These are dealbreakers — if a phrase from this list appears, the persona
  flags voice_drift.
-->

- "delve into"
- "in today's fast-paced world"
- "let me break this down"
- "the power of <X>"
- "<X> is more important than ever"
- "let's dive in"
- "without further ado"
- "I hope this finds you well"
- <add your specific bans>

---

## Allowed / preferred phrases

<!--
  Patterns that ARE this voice. Personas use these as positive signal —
  drafts that hit these patterns score better on voice match.
-->

- Concrete numbers in the first line ("Cut review time from 2 days to 4 hours")
- First-person past tense ("I shipped...", "We tried...")
- Direct addressing the reader ("If you're doing X, stop")
- Naming specific tools / companies / people instead of "leading platforms"
- Em dashes — used liberally — like this
- Single-sentence paragraphs for emphasis.
- <add your specific preferences>

---

## Structural preferences

<!-- How do you usually structure a piece? -->

- Open with: <the claim / a story / a question / a contrarian take>
- Section length: <short / medium / variable>
- Use H2s as: <claims / questions / signposts>
- Conclusion: <recap / call-to-action / open question / no conclusion>
- Code blocks: <yes / no / when relevant>
- Lists: <bullet / numbered / sparingly / freely>

Example:
> - Open with the claim. No preamble. No "in this post I'll explain."
> - Section length is short — most posts are 800-1200 words.
> - H2s are claims with numbers when possible ("Cut design review by 80%"
>   beats "The result").
> - No formal conclusion. End on the next question.
> - Code blocks: yes, when concrete. Always with language tags.

---

## Example posts (3+ recommended)

<!--
  This is the most important section. Paste 3+ examples of your actual
  published work. Personas use these as the ground truth for "what this
  voice sounds like." More examples = better voice fidelity.

  Examples can be the full post or representative excerpts (1-2 paragraphs
  is enough if the excerpt is voice-dense).
-->

### Example 1 — <one-line description, e.g., "blog post about shipping fast">

```
<paste your actual post here>
```

### Example 2 — <description>

```
<paste post>
```

### Example 3 — <description>

```
<paste post>
```

<!-- Add more examples as needed. 5-10 is ideal. -->

---

## Anti-examples (optional)

<!--
  If there are well-known voices you specifically do NOT want to sound
  like, list them here with a one-line reason. This catches drift toward
  named-style traps.
-->

- **NOT:** Medium-style "The X mistake every Y makes" listicle headlines
- **NOT:** LinkedIn broetry ("\nLet me\n\ntell you\n\nwhat I learned.")
- **NOT:** Twitter thread guru voice ("Here's what nobody tells you 🧵")
- <add specifics>

---

## Notes for personas

<!--
  Free-form. Anything else a persona should know to evaluate voice
  consistency. Often useful: things you're consciously trying to do that
  might LOOK like errors but aren't.
-->

- Sentence fragments are intentional. Don't flag them.
- Lower-case h1s in some posts are intentional (stylistic).
- I sometimes break the "show don't tell" rule when telling is faster.
- <your notes>
