# Brand Voice Protocol

Optional layer. When `BRAND_VOICE.md` exists in the project root or is
passed via skill argument, every persona's review prompt is augmented
with brand-voice context. Personas check the draft for voice consistency
and flag drift.

This kills the AI-slop optimization risk: without brand voice, personas
will steer the draft toward generic high-engagement templates. With it,
personas defend the writer's actual voice.

## Format

`BRAND_VOICE.md` (template at `templates/BRAND_VOICE.template.md`):

```markdown
# Brand Voice

## Who
One paragraph: writer's role, audience, what they're known for.

## Voice attributes
- **Tone:** direct / playful / academic / contrarian / etc.
- **Sentence rhythm:** short / mixed / long-form
- **Humor:** dry / none / self-deprecating / observational
- **Vocabulary:** plain / technical / jargon-heavy / minimal jargon
- **POV:** I / we / you / mixed

## Banned phrases
List of phrases that are NOT this voice. Personas reject drafts containing them.

Examples:
- "delve into"
- "in today's fast-paced world"
- "let me break this down"
- (any phrase the writer specifically wants to avoid)

## Allowed/preferred phrases
Phrases or patterns that ARE this voice.

## Example posts (3+ recommended)
Paste 3+ examples of the writer's actual published work. Personas use these
as the ground truth for "what this voice sounds like."

### Example 1
[paste actual post]

### Example 2
[paste actual post]

### Example 3
[paste actual post]
```

## Skill integration

When the skill detects `BRAND_VOICE.md`:

1. Load it once at init
2. Inject into every persona's system prompt under a `## Brand Voice Context` section
3. Add a `voice_drift` field to every persona's expected JSON output:
   ```json
   {
     "score": 7,
     "verdict": "almost",
     "voice_drift": {
       "drifts_from_voice": true,
       "specifics": ["uses 'delve into' (banned phrase)", "tone shifted to corporate"]
     }
   }
   ```
4. If ANY persona reports `drifts_from_voice: true`, treat as a hard fix item (Phase C)

## Why this matters

Without brand voice, the loop converges toward generic high-engagement
patterns. Tweets all sound like @naval. Blog posts all sound like Medium.
LinkedIn all sounds like broetry. The whole point of the loop is to
preserve and sharpen YOUR voice — not flatten it into AI-slop.

## When to skip

For business plans, brand voice matters less (rigor > voice). The skill
may treat it as informational only, not a hard fix item, when format =
`business-plan`.
