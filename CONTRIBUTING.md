# Contributing

Four kinds of contributions land here:

1. **New personas** — the highest-leverage contribution. Specific personas
   that catch defect classes the existing roster misses.
2. **New formats** — e.g., newsletter, technical RFC, podcast script. Each
   needs a skill, a persona roster, and a verification config.
3. **New backends** — DeepSeek, MiniMax, Ollama, etc. Plug into the
   `--reviewer=...` dispatch.
4. **New verification tools** — objective checks for new defect classes
   (readability score, fact-check against a corpus, etc.).

## Schema versioning

The persona schema is at `schema_version: 1`. Bumps are coordinated:

| Schema version | Status | Compatibility |
|----------------|--------|---------------|
| 1 | current (v0.1) | personas with version 1 work in all v0.x skills |
| 2 | proposed | will add `dimensions[]` array for multi-axis scoring |

Bumping the schema requires:

- Update `skills/shared-references/persona-library.md` schema section
- Migrate ALL shipped personas (not optional — the parser loads them all)
- Update `docs/PERSONA_AUTHORING.md`
- Bump the repo VERSION minor (`0.1.0` → `0.2.0`)

We will not silently accept v1 and v2 personas in the same skill run. Every
persona for a given format must declare the same `schema_version`.

## Contributing a persona

See [docs/PERSONA_AUTHORING.md](docs/PERSONA_AUTHORING.md) for the full how-to.

PR checklist:

- [ ] File at `personas/{format}/{name}.md`, kebab-case name matches frontmatter
- [ ] YAML frontmatter has all required fields (`name`, `format`,
      `schema_version`, optionally `weight`, `veto`, `requires_verification`)
- [ ] `## System prompt` section in first person, with concrete dealbreakers
- [ ] `## User prompt template` uses the standard placeholders
- [ ] `## Output format` matches the JSON schema in
      [persona-library.md](skills/shared-references/persona-library.md)
- [ ] Tested against a known-bad fixture (rejects with score ≤4) AND a
      known-good fixture (approves with score ≥6)
- [ ] Added to the index in
      [skills/shared-references/persona-library.md](skills/shared-references/persona-library.md)
- [ ] PR description: who is this persona, what defect class does it
      catch that existing personas miss, who would actually be this
      persona in real life

## Contributing a format

Higher bar — adding a format adds a skill, a persona roster, a verification
config, fixtures, and example output.

PR checklist:

- [ ] `skills/auto-{format}-review-loop/SKILL.md` following the loop contract
- [ ] At minimum 4 personas in `personas/{format}/` (3 is too few — the
      consensus check needs disagreement room)
- [ ] Verification config in `skills/shared-references/verification-protocols.md`
- [ ] Fixtures at `tests/fixtures/{format}/good_*.{ext}` and `bad_*.{ext}`
- [ ] At least one verification tool in `tools/` if the format has
      objective checks (char count, structural sanity, etc.)
- [ ] Termination criteria added to the table in
      [loop-contract.md](skills/shared-references/loop-contract.md)
- [ ] Detection rule added to `skills/auto-essay-review-loop/SKILL.md`
      Phase 1
- [ ] Walkthrough section in [docs/EXAMPLES.md](docs/EXAMPLES.md)
- [ ] PR description includes: what's the format, who writes it, what
      bars do you need 4 personas to enforce, what verification is
      objectively true (not opinion)

## Contributing a backend

The reviewer call is a single dispatch in each format skill. To add a
backend:

1. Add a `--reviewer={name}` value the skill recognizes
2. Implement the dispatch — it must take `(system, user, config)` and
   return the model's text response
3. The dispatch must use a fresh thread/conversation per call (never
   reuse — see reviewer-independence.md)
4. Document setup in `docs/BACKEND_CONFIG.md` under the v0.2+ section
5. Add backend-specific troubleshooting to `docs/TROUBLESHOOTING.md`

Backend contributions need real-run evidence: at least one full loop run
on a non-trivial draft, with `traces/` showing the backend was called and
returned valid JSON. Attach as a gist or repo branch in the PR.

## Contributing a verification tool

Tools live in `tools/`. JSON output schema is fixed (see
[verification-protocols.md](skills/shared-references/verification-protocols.md)).

PR checklist:

- [ ] Tool emits the standard JSON schema to stdout
- [ ] `passed: bool` is the top-level pass/fail signal
- [ ] `flags: [...]` for granular reasons (used by persona `veto` fields)
- [ ] Works on Git Bash on Windows (no GNU-specific flags)
- [ ] Works in `tests/run_tests.sh` against the fixtures
- [ ] Documented in `verification-protocols.md` table

## PR template (suggested)

```markdown
## What

One sentence on what this adds or changes.

## Why

Concrete motivation. If it's a persona: what defect did existing personas
miss? If it's a format: who writes this and where is the gap? If it's a
backend: what's the cost/quality/availability win over Codex MCP?

## Test plan

- [ ] Tested against `tests/fixtures/{format}/good_*` — passes
- [ ] Tested against `tests/fixtures/{format}/bad_*` — fails appropriately
- [ ] (For personas) Score variance ≤2 points across 3 runs on same input
- [ ] (For backends) One full loop run included as evidence

## Schema impact

- Schema version: unchanged / bumped to N (with migration plan)
- Affects: list of personas / skills / fixtures touched

## Docs touched

- [ ] README persona/format table
- [ ] persona-library.md index
- [ ] EXAMPLES.md (if user-visible)
- [ ] BACKEND_CONFIG.md (if backend)
- [ ] TROUBLESHOOTING.md (if known failure modes)
```

## Code style

- **Markdown:** 80-char lines for prose, no hard wrap inside code blocks
- **YAML frontmatter:** alphabetize fields after the required ones
- **JSON schemas:** 2-space indent, no trailing commas
- **Bash:** `#!/usr/bin/env bash`, `set -euo pipefail`, works on Git Bash
- **Python:** Python 3.10+, no external deps unless absolutely required
  (the verification tools are stdlib-only by policy)

## What we will NOT merge

- Personas that are slight rewordings of existing ones (specificity is the
  moat — alternates without a defect class to defend get rejected)
- Backends that don't preserve reviewer independence (no per-round-thread =
  no merge)
- Verification tools that match on subjective criteria ("checks if the
  prose flows well") — verification is the objective layer
- Anything that adds a hard runtime dependency on a hosted API for a layer
  that's currently local (e.g., a verification tool that calls OpenAI to
  check links)

## Questions?

Open an issue with the `question` label. We respond faster to issues than
to email.
