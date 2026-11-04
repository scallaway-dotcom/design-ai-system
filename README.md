# design-ai-system

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
SKILL.md                       the agent
reference/maestro-principles.md  the rubric every design answers
reference/maestro.spec.json    reference diagram as a spec; worked example and test fixture
reference/summary-template.md  EXECUTIVE-SUMMARY.md skeleton
scripts/render_diagram.py      spec.json -> SVG, no dependencies
scripts/svg_to_png.sh          SVG -> PNG via headless Chrome, 1580x800
tests/                         renderer tests
docs/superpowers/              design spec and implementation plan
```
