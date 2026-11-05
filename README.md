# design-ai-system

Source of truth for two Cursor skills that design AI systems:

| Skill | Path | What it does |
|---|---|---|
| `/design-ai-system` | `SKILL.md` (repo root) | Staging ClickUp task → Maestro-shaped design → one-page architecture PNG and executive summary. |
| `/voice-design-ai-system` | `skills/voice-design-ai-system/SKILL.md` | ClickUp task **or** meeting transcript → one normalized brief → either talk it out in voice, or scaffold the system and interview to a final design. Picks the architecture rung with a boring-first decision tree. |

## voice-design-ai-system

Input is a ClickUp task from a space or list the user names, or a meeting transcript (file, Drive
link, ClickUp Doc, or pasted text). Both are normalized into the same brief
(`skills/voice-design-ai-system/reference/brief-template.md`), then the skill forks:

- **Fork A, talk it out**: a voice conversation that walks the four decision-tree questions and
  logs every decision into the brief.
- **Fork B, scaffold and interview**: writes `DESIGN.md` with the gaps marked, then asks one
  question per turn until the design is final.

Architecture is chosen by `reference/architecture-decision-tree.md`: problem type, available data
(labeled or not), latency and cost budget, team maintenance ability. Start at the boring rung and
escalate only when a prototype on real items fails a written metric.

Install:

```bash
git clone https://github.com/scallaway-dotcom/design-ai-system ~/Projects/design-ai-system
mkdir -p ~/.cursor/skills
ln -s ~/Projects/design-ai-system/skills/voice-design-ai-system ~/.cursor/skills/voice-design-ai-system
```

Use:

```
/voice-design-ai-system clickup "Finance Ops" invoice approval --mode talk
/voice-design-ai-system transcript ~/Downloads/2026-11-05-ops-sync.vtt --mode scaffold
```

## design-ai-system

A Cursor skill. Given a staging ClickUp task describing an inefficient process, it reads the task,
its comment threads, attachments, an optional chat thread, and a ClickUp Brain query; proposes two
or three AI system shapes built on the Maestro principles; and, once one is chosen, delivers:

- `architecture.png` and `architecture.svg`, a one-page diagram in the style of
  [maestro-ceo-scheduling/static/architecture.png](https://github.com/stevencallaway1/maestro-ceo-scheduling/blob/main/static/architecture.png)
- `EXECUTIVE-SUMMARY.md`
- `CONTEXT.md`, the dossier of what was pulled and what was inferred
- `architecture.spec.json`, the editable source of the diagram

## Install

```bash
git clone https://github.com/scallaway-dotcom/design-ai-system ~/Projects/design-ai-system
mkdir -p ~/.cursor/skills
ln -s ~/Projects/design-ai-system ~/.cursor/skills/design-ai-system
```

Requirements: Python 3 (stdlib only), Google Chrome at
`/Applications/Google Chrome.app`, the ClickUp staging plugin signed in.

## Use

In any Cursor chat:

```
/design-ai-system https://app.clickup-stg.com/t/<task_id>
```

Optionally append a ClickUp chat channel or thread URL.

## Render a spec by hand

```bash
python3 scripts/render_diagram.py reference/maestro.spec.json /tmp/maestro.svg
bash scripts/svg_to_png.sh /tmp/maestro.svg /tmp/maestro.png
```

`svg_to_png.sh` exits 0 ok, 2 usage, 3 Chrome missing, 4 no output, 5 wrong size.
`render_diagram.py` exits 0 ok, 1 bad arguments / missing file / invalid JSON, 2 invalid spec.

## Test

```bash
python3 -m unittest discover -s tests -v
```

## Publish changes

The initial publish goes through the GitHub connector. For ordinary pushes:

```bash
brew install gh && gh auth login
git push -u origin main
```

## Layout

```
SKILL.md                       /design-ai-system, the diagram skill
reference/maestro-principles.md  the rubric every design at rung R3+ answers
reference/maestro.spec.json    reference diagram as a spec; worked example and test fixture
reference/summary-template.md  EXECUTIVE-SUMMARY.md skeleton
scripts/render_diagram.py      spec.json -> SVG, no dependencies
scripts/svg_to_png.sh          SVG -> PNG via headless Chrome, 1580x800
tests/                         renderer tests
docs/superpowers/              design spec and implementation plan

skills/voice-design-ai-system/
  SKILL.md                                 /voice-design-ai-system, the voice skill
  reference/brief-template.md              normalized brief; ClickUp and transcript mappings
  reference/architecture-decision-tree.md  rungs R0-R7, four questions, escalation rule
  reference/voice-guide.md                 voice turn rules, Fork A talk track, Fork B interview
  reference/scaffold-template.md           DESIGN.md skeleton for Fork B
```
