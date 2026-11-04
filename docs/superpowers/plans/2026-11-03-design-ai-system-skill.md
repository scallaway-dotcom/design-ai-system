# design-ai-system Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A Cursor skill, `/design-ai-system <clickup task url>`, that reads an inefficient process from staging ClickUp, proposes Maestro-shaped AI systems, and delivers a one-page architecture PNG, an executive summary, and a context dossier.

**Architecture:** The skill is a `SKILL.md` that drives three phases (Intake, Design, Deliver) with two user gates. The agent writes a JSON spec; a dependency-free Python renderer turns it into SVG with the exact geometry of the Maestro reference diagram; a shell script rasterizes it with headless Chrome. A rubric file and a summary template keep designs Maestro-shaped.

**Tech Stack:** Python 3 stdlib only (`json`, `html`, `unittest`, `xml.etree`), bash, Google Chrome headless, Cursor skills, ClickUp staging MCP, GitHub MCP.

## Global Constraints

- Spec: `docs/superpowers/specs/2026-11-03-design-ai-system-skill-design.md`. Read it before any task.
- Repo root: `/Users/stevencallaway/Projects/design-ai-system`. All paths below are relative to it.
- Python: `/usr/bin/python3`, no third-party packages. Tests use `unittest`, run with `python3 -m unittest discover -s tests -v`.
- Canvas is exactly `1580x800`. Reference SVG for geometry: `/tmp/maestro-ref/architecture.svg` (re-download from `https://maestro-ceo-scheduling.vercel.app/static/architecture.svg` if missing). Reference PNG: `/tmp/maestro-ref/architecture.png` (from `https://raw.githubusercontent.com/stevencallaway1/maestro-ceo-scheduling/main/static/architecture.png`).
- Stage count 4 to 8 inclusive. Body/lines arrays at most 3 entries. Caption at most 2 lines. Exactly 2 panels.
- `kind` values: `deterministic`, `model`, `human`, `external`.
- Chrome binary: `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`.
- ClickUp: staging only, MCP namespace `plugin-clickupstaging-clickupStaging`. Never production.
- GitHub target: `scallaway-dotcom/design-ai-system`. Connector is signed in as `scallaway-dotcom`. No `gh`, no SSH key, no credential helper on this machine.
- Git author email in this repo: `349025977+scallaway-dotcom@users.noreply.github.com` (already set repo-locally).
- Commits: run git from the repo root; shell commands that write `.git/config` need `required_permissions: ["all"]`.
- Keep `SKILL.md` under 500 lines. Frontmatter `name: design-ai-system`, `disable-model-invocation: true`.
- Prose rule for all authored markdown: no filler, no marketing adjectives, third person in the skill description.

---

## File structure

| Path | Responsibility |
|---|---|
| `scripts/render_diagram.py` | `validate(spec) -> list[str]`, `render(spec) -> str` (SVG), CLI `render_diagram.py SPEC OUT`. Owns all geometry and style. |
| `scripts/svg_to_png.sh` | Wraps SVG in a zero-margin HTML page, screenshots with headless Chrome at 1580x800. |
| `tests/test_render_diagram.py` | Renderer unit tests. |
| `reference/maestro.spec.json` | The reference diagram as a spec. Worked example and test fixture. |
| `reference/maestro-principles.md` | The 12-point rubric the skill applies before proposing. |
| `reference/summary-template.md` | `EXECUTIVE-SUMMARY.md` skeleton. |
| `SKILL.md` | The agent. |
| `README.md` | Install (symlink), run, test, publish. |

---

### Task 1: Renderer core (header, legend, row, band, caption, validation)

**Files:**
- Create: `scripts/render_diagram.py`
- Create: `tests/test_render_diagram.py`
- Create: `tests/__init__.py` (empty)

**Interfaces:**
- Produces: `render_diagram.validate(spec: dict) -> list[str]` (empty list means valid), `render_diagram.render(spec: dict) -> str` (raises `render_diagram.SpecError` if invalid), `render_diagram.layout(n: int) -> tuple[float, list[float]]` returning `(card_w, xs)` where `xs[0]` is the input box x, `xs[1..n]` the stage xs, `xs[n+1]` the execution box x. Constants `ROW_Y=312`, `CARD_H=132`, `BAND_Y=588`, `BAND_H=112`, `MARGIN=60`, `RIGHT_MARGIN=42`, `GAP=34`.
- Task 2 adds overlays into `render()` using `layout()` and the helpers `text()` and `centers()` defined here.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_render_diagram.py
import pathlib
import sys
import unittest
from xml.etree import ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import render_diagram as rd  # noqa: E402

SVG_NS = "{http://www.w3.org/2000/svg}"


def make_spec(n=6, **overrides):
    spec = {
        "title": "Title",
        "subtitle": "Subtitle",
        "thesis": "Thesis line.",
        "input": {"label": "REQUEST", "title": "Inbound", "lines": ["Email"]},
        "stages": [
            {"num": i, "label": f"STAGE{i}", "kind": "deterministic",
             "title": f"Stage {i}", "body": ["one", "two"]}
            for i in range(1, n + 1)
        ],
        "execution": {"label": "EXECUTION", "title": "Out", "lines": ["Writes"]},
        "panels": [
            {"title": "Audit log", "body": ["a"]},
            {"title": "Trust ladder & eval loop", "body": ["b"]},
        ],
        "caption": ["cap one", "cap two"],
    }
    spec.update(overrides)
    return spec


def parse(svg_text):
    return ET.fromstring(svg_text)


class ValidateTests(unittest.TestCase):
    def test_valid_spec_has_no_errors(self):
        self.assertEqual(rd.validate(make_spec(6)), [])

    def test_stage_count_bounds(self):
        for n in (4, 8):
            self.assertEqual(rd.validate(make_spec(n)), [], n)
        for n in (3, 9):
            errs = rd.validate(make_spec(n))
            self.assertTrue(any("stages must have 4-8" in e for e in errs), (n, errs))

    def test_unknown_kind_rejected(self):
        spec = make_spec(4)
        spec["stages"][0]["kind"] = "agent"
        errs = rd.validate(spec)
        self.assertTrue(any("unknown kind" in e for e in errs), errs)

    def test_too_many_body_lines_rejected(self):
        spec = make_spec(4)
        spec["stages"][1]["body"] = ["a", "b", "c", "d"]
        self.assertTrue(any("more than 3 lines" in e for e in rd.validate(spec)))

    def test_panels_must_be_two(self):
        spec = make_spec(4, panels=[{"title": "x", "body": ["y"]}])
        self.assertTrue(any("exactly 2" in e for e in rd.validate(spec)))

    def test_missing_key_reported(self):
        spec = make_spec(4)
        del spec["caption"]
        self.assertTrue(any("missing required key: caption" in e for e in rd.validate(spec)))


class RenderCoreTests(unittest.TestCase):
    def test_render_raises_on_invalid(self):
        with self.assertRaises(rd.SpecError):
            rd.render(make_spec(3))

    def test_output_is_svg_with_canvas_size(self):
        root = parse(rd.render(make_spec(6)))
        self.assertEqual(root.tag, SVG_NS + "svg")
        self.assertEqual(root.get("viewBox"), "0 0 1580 800")

    def test_card_count_matches_stages_plus_two(self):
        for n in (4, 6, 8):
            root = parse(rd.render(make_spec(n)))
            cards = [r for r in root.iter(SVG_NS + "rect")
                     if r.get("height") == str(rd.CARD_H)]
            self.assertEqual(len(cards), n + 2, n)

    def test_layout_matches_reference_for_six_stages(self):
        card_w, xs = rd.layout(6)
        self.assertAlmostEqual(card_w, 155.0)
        self.assertEqual([round(x) for x in xs],
                         [60, 249, 438, 627, 816, 1005, 1194, 1383])

    def test_layout_fits_canvas_for_eight_stages(self):
        card_w, xs = rd.layout(8)
        self.assertLessEqual(xs[-1] + card_w, 1580 - rd.RIGHT_MARGIN + 0.01)

    def test_kind_styles_applied(self):
        spec = make_spec(4)
        spec["stages"][1]["kind"] = "model"
        spec["stages"][2]["kind"] = "human"
        svg = rd.render(spec)
        self.assertIn('fill="#eeedfc" stroke="#4f46e5"', svg)
        self.assertIn('fill="#fdf3d7" stroke="#9a6700"', svg)

    def test_text_is_escaped(self):
        spec = make_spec(4)
        spec["panels"][1]["title"] = "Trust & eval <loop>"
        svg = rd.render(spec)
        self.assertIn("Trust &amp; eval &lt;loop&gt;", svg)
        parse(svg)  # still well-formed

    def test_optional_sections_absent_is_fine(self):
        spec = make_spec(5)
        for key in ("data_sources", "bypass", "feedback"):
            spec.pop(key, None)
        parse(rd.render(spec))

    def test_execution_highlight_last_colours_last_line(self):
        spec = make_spec(4)
        spec["execution"]["lines"] = ["a", "Simulated"]
        spec["execution"]["highlight_last"] = True
        svg = rd.render(spec)
        self.assertIn('class="bn" fill="#9a6700">Simulated</text>', svg)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/stevencallaway/Projects/design-ai-system && touch tests/__init__.py && python3 -m unittest discover -s tests -v 2>&1 | tail -5`
Expected: `ModuleNotFoundError: No module named 'render_diagram'`

- [ ] **Step 3: Write the renderer core**

```python
#!/usr/bin/env python3
"""Render an architecture spec (JSON) into a 1580x800 SVG in the Maestro style.

Usage:
    python3 render_diagram.py SPEC.json OUT.svg

Exit codes: 0 rendered, 2 invalid spec (errors printed to stderr), 1 other error.
Pure standard library. Geometry matches maestro-ceo-scheduling/static/architecture.svg.
"""
import json
import sys
from html import escape

W, H = 1580, 800
MARGIN, RIGHT_MARGIN = 60, 42
ROW_Y, CARD_H, GAP = 312, 132, 34          # GAP = 26px arrow + 4px clearance each side
BAND_Y, BAND_H = 588, 112
BAND_SPLIT = 751 / 1289                    # left panel share of the band width
MIN_STAGES, MAX_STAGES = 4, 8
MAX_LINES = 3

KINDS = {
    "deterministic": dict(fill="#ffffff", stroke="#d7d5cf", sw="1.5", dash="",    num=None),
    "model":         dict(fill="#eeedfc", stroke="#4f46e5", sw="1.8", dash="",    num="#4f46e5"),
    "human":         dict(fill="#fdf3d7", stroke="#9a6700", sw="1.8", dash="",    num="#9a6700"),
    "external":      dict(fill="#f4f3f0", stroke="#b6b4ad", sw="1.5", dash="5 4", num=None),
}
AMBER = "#9a6700"

STYLE = """  <style>
    .t     { font-size: 31px; font-weight: 700; fill: #17181c; letter-spacing: -0.5px; }
    .sub   { font-size: 15px; fill: #5c5e66; }
    .lg    { font-size: 12.5px; fill: #5c5e66; }
    .bt    { font-size: 15.5px; font-weight: 650; fill: #17181c; }
    .bn    { font-size: 11.5px; fill: #5c5e66; }
    .bnum  { font-size: 11px; font-weight: 700; fill: #9a9ca4; letter-spacing: .08em; }
    .feed  { font-size: 11.5px; fill: #7a7c84; }
    .feedb { font-size: 11.5px; fill: #7a7c84; font-weight: 600; }
    .band  { font-size: 14.5px; font-weight: 650; fill: #17181c; }
    .bandn { font-size: 11.5px; fill: #5c5e66; }
    .note  { font-size: 12.5px; fill: #7a7c84; }
  </style>"""

DEFS = """  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#b6b4ad"/>
    </marker>
    <marker id="arrowLoop" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#4f46e5"/>
    </marker>
    <marker id="arrowThin" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#c4c2bb"/>
    </marker>
    <marker id="arrowRed" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#b3261e"/>
    </marker>
  </defs>"""

LEGEND = """  <g transform="translate(60,112)">
    <rect x="0" y="0" width="15" height="15" rx="4" fill="#ffffff" stroke="#d7d5cf" stroke-width="1.5"/>
    <text x="23" y="12" class="lg">Deterministic code</text>
    <rect x="175" y="0" width="15" height="15" rx="4" fill="#eeedfc" stroke="#4f46e5" stroke-width="1.5"/>
    <text x="198" y="12" class="lg">Model-backed (one call)</text>
    <rect x="382" y="0" width="15" height="15" rx="4" fill="#fdf3d7" stroke="#9a6700" stroke-width="1.5"/>
    <text x="405" y="12" class="lg">Human decision point</text>
    <rect x="579" y="0" width="15" height="15" rx="4" fill="#f4f3f0" stroke="#b6b4ad" stroke-width="1.5" stroke-dasharray="4 3"/>
    <text x="602" y="12" class="lg">External system / adapter</text>
  </g>"""


class SpecError(ValueError):
    """Raised by render() when validate() reports errors."""


# ── validation ───────────────────────────────────────────────────────────────

def _lines_ok(errors, where, lines):
    if len(lines) > MAX_LINES:
        errors.append(f"{where}: more than {MAX_LINES} lines")


def validate(spec):
    errors = []
    for key in ("title", "subtitle", "thesis", "input", "stages", "execution", "panels", "caption"):
        if key not in spec:
            errors.append(f"missing required key: {key}")
    stages = spec.get("stages", [])
    n = len(stages)
    if not MIN_STAGES <= n <= MAX_STAGES:
        errors.append(f"stages must have {MIN_STAGES}-{MAX_STAGES} entries, got {n}")
    for i, s in enumerate(stages, 1):
        if s.get("kind") not in KINDS:
            errors.append(f"stage {i}: unknown kind {s.get('kind')!r}; expected one of {sorted(KINDS)}")
        _lines_ok(errors, f"stage {i} body", s.get("body", []))
    for box in ("input", "execution"):
        _lines_ok(errors, f"{box} lines", spec.get(box, {}).get("lines", []))
    panels = spec.get("panels", [])
    if len(panels) != 2:
        errors.append(f"panels must have exactly 2 entries, got {len(panels)}")
    for i, p in enumerate(panels, 1):
        _lines_ok(errors, f"panel {i} body", p.get("body", []))
    if len(spec.get("caption", [])) > 2:
        errors.append("caption: more than 2 lines")
    return errors


# ── geometry ─────────────────────────────────────────────────────────────────

def layout(n):
    """Return (card_w, xs). xs[0]=input, xs[1..n]=stages, xs[n+1]=execution."""
    cards = n + 2
    card_w = (W - MARGIN - RIGHT_MARGIN - GAP * (cards - 1)) / cards
    xs = [MARGIN + i * (card_w + GAP) for i in range(cards)]
    return card_w, xs


def centers(n):
    card_w, xs = layout(n)
    return [x + card_w / 2 for x in xs]


# ── primitives ───────────────────────────────────────────────────────────────

def text(x, y, cls, s, fill=None, anchor=None):
    attrs = f'x="{x:.1f}" y="{y}" class="{cls}"'
    if fill:
        attrs += f' fill="{fill}"'
    if anchor:
        attrs += f' text-anchor="{anchor}"'
    return f'<text {attrs}>{escape(str(s))}</text>'


def card(x, w, kind, num_label, title, lines, highlight_last=False):
    k = KINDS[kind]
    dash = f' stroke-dasharray="{k["dash"]}"' if k["dash"] else ""
    out = [f'<rect x="{x:.1f}" y="{ROW_Y}" width="{w:.1f}" height="{CARD_H}" rx="10" '
           f'fill="{k["fill"]}" stroke="{k["stroke"]}" stroke-width="{k["sw"]}"{dash}/>']
    tx = x + 16
    out.append(text(tx, ROW_Y + 25, "bnum", num_label, fill=k["num"]))
    out.append(text(tx, ROW_Y + 50, "bt", title))
    for i, line in enumerate(lines):
        fill = AMBER if (highlight_last and i == len(lines) - 1) else None
        out.append(text(tx, ROW_Y + 75 + 18 * i, "bn", line, fill=fill))
    return "\n".join(out)


def arrow(x1, x2, y):
    return (f'<path d="M {x1:.1f} {y} L {x2:.1f} {y}" stroke="#b6b4ad" '
            f'stroke-width="1.8" marker-end="url(#arrow)"/>')


# ── render ───────────────────────────────────────────────────────────────────

def render(spec):
    errors = validate(spec)
    if errors:
        raise SpecError("\n".join(errors))

    stages = spec["stages"]
    n = len(stages)
    card_w, xs = layout(n)
    cx = centers(n)
    out = []

    # header
    title = spec["title"]
    out.append(text(MARGIN, 56, "t", title))
    out.append(text(MARGIN + round(len(title) * 31 * 0.58), 56, "sub", spec["subtitle"]))
    out.append(text(MARGIN, 84, "sub", spec["thesis"]))
    out.append(LEGEND)

    # main row
    inp, exe = spec["input"], spec["execution"]
    out.append(card(xs[0], card_w, "external", inp["label"], inp["title"], inp.get("lines", [])))
    for i, s in enumerate(stages, 1):
        out.append(arrow(xs[i - 1] + card_w + 4, xs[i] - 4, ROW_Y + 66))
        out.append(card(xs[i], card_w, s["kind"], f'{s["num"]} · {s["label"]}', s["title"], s.get("body", [])))
    out.append(arrow(xs[n] + card_w + 4, xs[n + 1] - 4, ROW_Y + 66))
    out.append(card(xs[n + 1], card_w, "external", exe["label"], exe["title"],
                    exe.get("lines", []), highlight_last=bool(exe.get("highlight_last"))))

    # drops from every stage and the execution box into the band
    drops = [f'<path d="M {c:.1f} {ROW_Y + CARD_H + 4} L {c:.1f} {BAND_Y - 4}"/>' for c in cx[1:]]
    out.append('<g stroke="#d3d1ca" stroke-width="1.2" stroke-dasharray="3 4">\n' + "\n".join(drops) + "\n</g>")

    # band with two panels
    band_x = xs[1]
    band_w = xs[n + 1] + card_w - band_x
    div_x = band_x + band_w * BAND_SPLIT
    out.append(f'<rect x="{band_x:.1f}" y="{BAND_Y}" width="{band_w:.1f}" height="{BAND_H}" rx="10" '
               f'fill="#ffffff" stroke="#d7d5cf" stroke-width="1.5"/>')
    out.append(f'<path d="M {div_x:.1f} {BAND_Y} L {div_x:.1f} {BAND_Y + BAND_H}" stroke="#e7e5de" stroke-width="1.5"/>')
    for px, panel in zip((band_x, div_x), spec["panels"]):
        out.append(text(px + 28, BAND_Y + 30, "band", panel["title"]))
        for i, line in enumerate(panel.get("body", [])):
            out.append(text(px + 28, BAND_Y + 54 + 18 * i, "bandn", line))

    # optional overlays (Task 2 fills these in)
    out.extend(_overlays(spec, n, card_w, xs, cx, band_x, div_x))

    # caption
    for i, line in enumerate(spec["caption"][:2]):
        out.append(text(MARGIN, 754 + 20 * i, "note", line))

    body = "\n".join(out)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
            f'font-family="-apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, Helvetica, Arial, sans-serif">\n'
            f'{STYLE}\n  <rect width="{W}" height="{H}" fill="#ffffff"/>\n{DEFS}\n{body}\n</svg>\n')


def _overlays(spec, n, card_w, xs, cx, band_x, div_x):
    """Data-source drops, bypass arrow, feedback arrow. Implemented in Task 2."""
    return []


# ── cli ──────────────────────────────────────────────────────────────────────

def main(argv):
    if len(argv) != 3:
        print(__doc__, file=sys.stderr)
        return 1
    with open(argv[1]) as f:
        spec = json.load(f)
    errors = validate(spec)
    if errors:
        print("spec invalid:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 2
    with open(argv[2], "w") as f:
        f.write(render(spec))
    print(argv[2])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/stevencallaway/Projects/design-ai-system && python3 -m unittest discover -s tests -v 2>&1 | tail -20`
Expected: all tests `ok`, final line `OK`.

- [ ] **Step 5: Commit**

```bash
cd /Users/stevencallaway/Projects/design-ai-system
git add scripts/render_diagram.py tests/__init__.py tests/test_render_diagram.py
git commit -m "feat(renderer): core layout, validation, cards, band, caption"
```

---

### Task 2: Renderer overlays (data sources, bypass, feedback) and their validation

**Files:**
- Modify: `scripts/render_diagram.py` (`validate`, `_overlays`)
- Modify: `tests/test_render_diagram.py` (append a test class)

**Interfaces:**
- Consumes: `layout`, `centers`, `text`, `ROW_Y`, `CARD_H`, `BAND_Y` from Task 1.
- Produces: spec keys `data_sources: [{over: [int], lines: [str, str]}]`, `bypass: {from: int, to: int, note: str}`, `feedback: {from_panel: 0|1, to_stage: int, label: str}`.

- [ ] **Step 1: Append failing tests**

```python
# append to tests/test_render_diagram.py, before `if __name__ == "__main__":`

class OverlayTests(unittest.TestCase):
    def test_data_source_refers_to_existing_stage(self):
        spec = make_spec(4, data_sources=[{"over": [9], "lines": ["x", "y"]}])
        self.assertTrue(any("data_sources[1]" in e and "stage 9" in e for e in rd.validate(spec)))

    def test_data_sources_rendered_at_stage_center(self):
        spec = make_spec(6, data_sources=[{"over": [2], "lines": ["people.json", "flags"]}])
        svg = rd.render(spec)
        self.assertIn('class="feedb" text-anchor="middle">people.json</text>', svg)
        self.assertIn('x="516.5" y="200" class="feedb"', svg)

    def test_bypass_requires_from_before_to(self):
        spec = make_spec(6, bypass={"from": 5, "to": 3, "note": "n"})
        self.assertTrue(any("bypass" in e for e in rd.validate(spec)))

    def test_bypass_rendered_red_with_gap_at_crossing_drop(self):
        spec = make_spec(
            6,
            data_sources=[{"over": [4], "lines": ["calendar.json", "first"]}],
            bypass={"from": 3, "to": 6, "note": "Sensitive: straight to a human"},
        )
        svg = rd.render(spec)
        self.assertIn('stroke="#b3261e"', svg)
        self.assertIn("Sensitive: straight to a human", svg)
        # two red segments: one before the crossing drop, one after
        self.assertEqual(svg.count('stroke="#b3261e" stroke-width="1.6"'), 2)

    def test_bypass_without_crossing_is_one_segment(self):
        spec = make_spec(6, bypass={"from": 3, "to": 6, "note": "n"})
        svg = rd.render(spec)
        self.assertEqual(svg.count('stroke="#b3261e" stroke-width="1.6"'), 1)

    def test_feedback_validation(self):
        spec = make_spec(6, feedback={"from_panel": 2, "to_stage": 4, "label": "l"})
        self.assertTrue(any("from_panel" in e for e in rd.validate(spec)))
        spec = make_spec(6, feedback={"from_panel": 1, "to_stage": 7, "label": "l"})
        self.assertTrue(any("to_stage" in e for e in rd.validate(spec)))

    def test_feedback_rendered(self):
        spec = make_spec(6, feedback={"from_panel": 1, "to_stage": 4, "label": "sets autonomy"})
        svg = rd.render(spec)
        self.assertIn('marker-end="url(#arrowLoop)"', svg)
        self.assertIn('fill="#4f46e5" text-anchor="end">sets autonomy</text>', svg)
```

- [ ] **Step 2: Run tests to verify the new ones fail**

Run: `cd /Users/stevencallaway/Projects/design-ai-system && python3 -m unittest tests.test_render_diagram.OverlayTests -v 2>&1 | tail -12`
Expected: `FAILED (failures=7)` or a mix of failures (the overlays return nothing, validation passes everything).

- [ ] **Step 3: Extend validate() and implement _overlays()**

Add to the end of `validate()` (before `return errors`):

```python
    for i, d in enumerate(spec.get("data_sources", []), 1):
        for num in d.get("over", []):
            if not 1 <= num <= n:
                errors.append(f"data_sources[{i}]: 'over' refers to stage {num}, which does not exist")
        _lines_ok(errors, f"data_sources[{i}] lines", d.get("lines", []))
    b = spec.get("bypass")
    if b:
        a, z = b.get("from", 0), b.get("to", 0)
        if not (1 <= a < z <= n):
            errors.append(f"bypass: 'from' ({a}) must be before 'to' ({z}) and both must be stage numbers 1-{n}")
    f = spec.get("feedback")
    if f:
        if f.get("from_panel") not in (0, 1):
            errors.append("feedback.from_panel must be 0 (left panel) or 1 (right panel)")
        if not 1 <= f.get("to_stage", 0) <= n:
            errors.append(f"feedback.to_stage must be a stage number 1-{n}")
```

Replace the `_overlays` stub with:

```python
SRC_Y1, SRC_Y2, SRC_DROP_TOP, SRC_DROP_BOT = 200, 217, 228, 306
BYPASS_Y, BYPASS_NOTE_Y, BYPASS_GAP = 272, 260, 10
FEED_Y, FEED_TOP = 478, 452


def _overlays(spec, n, card_w, xs, cx, band_x, div_x):
    out = []

    # data sources above specific stages, dotted drop into the card
    src_xs = []
    for d in spec.get("data_sources", []):
        x = sum(cx[k] for k in d["over"]) / len(d["over"])
        src_xs.append(x)
        lines = d.get("lines", [])
        if lines:
            out.append(text(x, SRC_Y1, "feedb", lines[0], anchor="middle"))
        for i, line in enumerate(lines[1:]):
            out.append(text(x, SRC_Y2 + 17 * i, "feed", line, anchor="middle"))
        out.append(f'<path d="M {x:.1f} {SRC_DROP_TOP} L {x:.1f} {SRC_DROP_BOT}" stroke="#c4c2bb" '
                   f'stroke-width="1.4" marker-end="url(#arrowThin)"/>')

    # bypass: red dashed hop from one stage to a later one, broken where it crosses a drop
    b = spec.get("bypass")
    if b:
        a, z = b["from"], b["to"]
        from_x = min(cx[a] + 55, xs[a] + card_w - 10)
        to_x = min(cx[z] + 29, xs[z] + card_w - 10)
        crossings = sorted(x for x in src_xs if from_x < x < to_x)
        segments = []
        start = from_x
        for x in crossings:
            segments.append((start, x - BYPASS_GAP))
            start = x + BYPASS_GAP
        segments.append((start, to_x))
        red = 'stroke="#b3261e" stroke-width="1.6" fill="none" stroke-dasharray="6 4"'
        for i, (s, e) in enumerate(segments):
            first, last = i == 0, i == len(segments) - 1
            d = (f"M {s:.1f} {SRC_DROP_BOT} L {s:.1f} {BYPASS_Y} L {e:.1f} {BYPASS_Y}" if first
                 else f"M {s:.1f} {BYPASS_Y} L {e:.1f} {BYPASS_Y}")
            if last:
                d += f" L {e:.1f} {SRC_DROP_BOT}"
            marker = ' marker-end="url(#arrowRed)"' if last else ""
            out.append(f'<path d="{d}" {red}{marker}/>')
        out.append(text((from_x + to_x) / 2, BYPASS_NOTE_Y, "lg", b.get("note", ""),
                        fill="#b3261e", anchor="middle"))

    # feedback: blue loop from a panel up into a stage
    f = spec.get("feedback")
    if f:
        start_x = (band_x if f["from_panel"] == 0 else div_x) + 10
        t = f["to_stage"]
        tx = min(cx[t] + 36, xs[t] + card_w - 10)
        out.append(f'<path d="M {start_x:.1f} {BAND_Y - 4} L {start_x:.1f} {FEED_Y} L {tx:.1f} {FEED_Y} L {tx:.1f} {FEED_TOP}" '
                   f'stroke="#4f46e5" stroke-width="1.6" fill="none" marker-end="url(#arrowLoop)"/>')
        label = f.get("label", "")
        rect_w = round(len(label) * 5.5) + 10
        out.append(f'<rect x="{tx - 8 - rect_w:.1f}" y="{FEED_Y - 8}" width="{rect_w}" height="18" fill="#ffffff"/>')
        out.append(text(tx - 12, FEED_Y + 6, "lg", label, fill="#4f46e5", anchor="end"))

    return out
```

- [ ] **Step 4: Run the full suite**

Run: `cd /Users/stevencallaway/Projects/design-ai-system && python3 -m unittest discover -s tests -v 2>&1 | tail -5`
Expected: `OK`.

- [ ] **Step 5: Commit**

```bash
cd /Users/stevencallaway/Projects/design-ai-system
git add scripts/render_diagram.py tests/test_render_diagram.py
git commit -m "feat(renderer): data-source drops, bypass hop, feedback loop"
```

---

### Task 3: Maestro fixture, PNG rasterizer, visual reproduction check

**Files:**
- Create: `reference/maestro.spec.json`
- Create: `scripts/svg_to_png.sh`
- Modify: `tests/test_render_diagram.py` (append fixture test)

**Interfaces:**
- Consumes: `render_diagram.py` CLI from Tasks 1–2.
- Produces: `scripts/svg_to_png.sh IN.svg OUT.png` (exit 3 if Chrome missing, 4 if no output; prints OUT path on success). `reference/maestro.spec.json` is the canonical worked example the skill shows the agent.

- [ ] **Step 1: Append the fixture test**

```python
# append to tests/test_render_diagram.py, before `if __name__ == "__main__":`
import json  # move to the top imports


class FixtureTests(unittest.TestCase):
    def test_maestro_fixture_is_valid_and_renders(self):
        spec = json.loads((ROOT / "reference" / "maestro.spec.json").read_text())
        self.assertEqual(rd.validate(spec), [])
        svg = rd.render(spec)
        parse(svg)
        self.assertIn("Maestro", svg)
        self.assertIn("6 · APPROVAL", svg)
        self.assertEqual(len(spec["stages"]), 6)
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd /Users/stevencallaway/Projects/design-ai-system && python3 -m unittest tests.test_render_diagram.FixtureTests -v 2>&1 | tail -4`
Expected: `FileNotFoundError` for `reference/maestro.spec.json`.

- [ ] **Step 3: Write the fixture (transcribed from the reference SVG)**

```json
{
  "title": "Maestro",
  "subtitle": "AI scheduling for the Office of the CEO",
  "thesis": "One request, end to end. Two of the six stages call a model, once each. Everything that decides, books, or records is deterministic.",
  "input": {
    "label": "REQUEST",
    "title": "Inbound ask",
    "lines": ["Email", "Slack", "ClickUp task"]
  },
  "stages": [
    { "num": 1, "label": "INTAKE",   "kind": "deterministic", "title": "Normalize",       "body": ["Type, duration,", "urgency, channel.", "Decides nothing."] },
    { "num": 2, "label": "CONTEXT",  "kind": "deterministic", "title": "Dossier",         "body": ["Who this is to Zeb:", "relevance, VIP,", "sensitivity, history."] },
    { "num": 3, "label": "POLICY",   "kind": "deterministic", "title": "Rule engine",     "body": ["Sets the outcome and", "the slot constraints.", "Sensitive = hard lock."] },
    { "num": 4, "label": "PLANNER",  "kind": "model",         "title": "Writes the plan", "body": ["Rationale and reply in", "the CEO's voice. Picks", "from legal slots only."] },
    { "num": 5, "label": "CRITIC",   "kind": "model",         "title": "Reviews it",      "body": ["Decision match, leaks,", "voice, unmet promises.", "pass / revise / block"] },
    { "num": 6, "label": "APPROVAL", "kind": "human",         "title": "Human decides",   "body": ["Approve, or override", "with a reason.", "Nothing skips this."] }
  ],
  "data_sources": [
    { "over": [2], "lines": ["people.json · history.json", "relationship, flags, open threads"] },
    { "over": [3], "lines": ["policies.json", "13 hand-editable rules"] },
    { "over": [4], "lines": ["calendar.json · voice.json", "free-slot search runs first"] }
  ],
  "bypass": { "from": 3, "to": 6, "note": "Sensitive category: skips both model stages, straight to a human" },
  "execution": {
    "label": "EXECUTION",
    "title": "Calendar",
    "lines": ["Idempotent hold, or", "route with no write.", "Simulated in the demo."],
    "highlight_last": true
  },
  "panels": [
    { "title": "Audit log",
      "body": ["Append-only. Every stage, every human verdict, and every",
               "calendar write, timestamped and attributed. Nothing that",
               "happens here happens off the record."] },
    { "title": "Trust ladder & eval loop",
      "body": ["Approvals and overrides are scored per category. L0 suggest-only through L3 bounded",
               "negotiation: promotion is earned from measured acceptance, demotion is automatic on any",
               "critical miss, and sensitive categories are locked at L0 permanently."] }
  ],
  "feedback": { "from_panel": 1, "to_stage": 4, "label": "sets how much autonomy this category gets" },
  "caption": [
    "Model calls are capped at two per request, both structured, both behind one interface. The Planner never invents a time: free-slot search runs first, so it can only write",
    "about slots that are provably legal. In this build both model stages run on deterministic templates, and the calendar adapter builds its event payload without sending it."
  ]
}
```

- [ ] **Step 4: Run the suite**

Run: `cd /Users/stevencallaway/Projects/design-ai-system && python3 -m unittest discover -s tests -v 2>&1 | tail -4`
Expected: `OK`.

- [ ] **Step 5: Write the rasterizer**

```bash
#!/usr/bin/env bash
# Rasterize an SVG to a 1580x800 PNG with headless Google Chrome.
# Usage: svg_to_png.sh IN.svg OUT.png
# Exit: 0 ok (prints OUT path), 2 usage, 3 Chrome missing, 4 Chrome produced no file.
set -euo pipefail

CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
W=1580; H=800

[ $# -eq 2 ] || { echo "usage: $0 IN.svg OUT.png" >&2; exit 2; }
[ -f "$1" ] || { echo "error: input not found: $1" >&2; exit 2; }
if [ ! -x "$CHROME" ]; then
  echo "error: Google Chrome not found at: $CHROME" >&2
  echo "Ship the SVG instead and tell the user the PNG was not produced." >&2
  exit 3
fi

IN="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
OUT_DIR="$(cd "$(dirname "$2")" && pwd)"
OUT="$OUT_DIR/$(basename "$2")"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
# Inline the SVG in a zero-margin page so Chrome lays it out at exactly WxH.
{
  printf '<!doctype html><html><head><meta charset="utf-8"><style>html,body{margin:0;padding:0;width:%spx;height:%spx;overflow:hidden;background:#fff}svg{display:block}</style></head><body>' "$W" "$H"
  cat "$IN"
  printf '</body></html>'
} > "$TMP/page.html"

"$CHROME" --headless=new --disable-gpu --hide-scrollbars --no-first-run --no-default-browser-check \
  --user-data-dir="$TMP/profile" --force-device-scale-factor=1 \
  --window-size="$W,$H" --screenshot="$OUT" "file://$TMP/page.html" >/dev/null 2>&1 || true

[ -s "$OUT" ] || { echo "error: Chrome produced no output at $OUT" >&2; exit 4; }
echo "$OUT"
```

Then: `chmod +x scripts/svg_to_png.sh`

- [ ] **Step 6: Render the fixture and compare with the reference**

Run:
```bash
cd /Users/stevencallaway/Projects/design-ai-system
mkdir -p /tmp/maestro-ref
[ -f /tmp/maestro-ref/architecture.png ] || curl -sL -o /tmp/maestro-ref/architecture.png https://raw.githubusercontent.com/stevencallaway1/maestro-ceo-scheduling/main/static/architecture.png
python3 scripts/render_diagram.py reference/maestro.spec.json /tmp/maestro-ref/ours.svg
scripts/svg_to_png.sh /tmp/maestro-ref/ours.svg /tmp/maestro-ref/ours.png
python3 -c "import struct;d=open('/tmp/maestro-ref/ours.png','rb').read(24);print(struct.unpack('>II',d[16:24]))"
```
Expected: `(1580, 800)`.

Then Read both `/tmp/maestro-ref/ours.png` and `/tmp/maestro-ref/architecture.png` with the Read tool and compare: same legend, 8 boxes in the row, three data-source labels with drops, red dashed bypass from Policy to Approval with a gap at the calendar drop, two panels, blue feedback arrow into Planner with label, two caption lines. Fix any layout drift in `render_diagram.py` before continuing. Embed both images in the chat response for the user.

- [ ] **Step 7: Commit**

```bash
cd /Users/stevencallaway/Projects/design-ai-system
git add reference/maestro.spec.json scripts/svg_to_png.sh tests/test_render_diagram.py
git commit -m "feat: Maestro fixture, Chrome rasterizer, fixture test"
```

---

### Task 4: Rubric and summary template

**Files:**
- Create: `reference/maestro-principles.md`
- Create: `reference/summary-template.md`

**Interfaces:**
- Produces: two files `SKILL.md` (Task 5) tells the agent to read at Phase 2 and Phase 3.

- [ ] **Step 1: Write the rubric**

```markdown
# Maestro principles

Read this before proposing any candidate system. Every candidate in Phase 2 and the final design
must answer each point. If a point does not apply, say why in one line rather than skipping it.

Source: github.com/stevencallaway1/maestro-ceo-scheduling (README and EXECUTIVE-SUMMARY).

## 1. Reframe the process as a judgment
What decision is this process really making, and why has it stayed with a human? The answer is
usually trust, not capability. Name the judgment in one sentence. A system that only automates the
mechanical part leaves the bottleneck in place.

## 2. Stages in order, each with one kind
Four to eight stages. Each is exactly one of: deterministic, model-backed (one call), human
decision point, external adapter. Intake never decides. Context (the dossier) is its own stage so
that flags come from assembled context rather than from surface text of the request.

## 3. Policy sets the outcome, not the model
Rules live in data, in plain English, editable by the process owner without an engineer. The
model writes about the outcome; it does not choose it. A model cannot talk its way past a rule.

## 4. The model cannot invent a resource
Any search for a legal option (a time slot, a vendor, an approver, a document, a budget line) runs
in deterministic code before the model call. The model only writes about that list.

## 5. Model-call cap as a number, with a zero path
State the maximum model calls per run. State the path where the count is zero: sensitive
categories stop at the policy stage and never reach a model, so they are never summarized or
paraphrased by one.

## 6. A Critic that reviews judgment, not arithmetic
If there is a reviewer stage, its checks are things code cannot do: does the output match the
decision, did a locked topic leak into an outbound message, is the voice right, was an existing
commitment ignored. Do not re-check what is already legal by construction. The verdict is a
server-side gate: block cannot be approved, revise needs an acknowledged override recorded on the
decision.

## 7. Human gate
Nothing executes without a person. Overrides require a one-line reason and are recorded. Approval
executes only what the output promised, nothing more.

## 8. Trust ladder per category
L0 suggest-only, L1 drafts with per-item approval, L2 auto-handles low-stakes items and logs, L3
bounded autonomy within policy. Promotion requires a measured acceptance rate over a rolling
window. Demotion is automatic on a critical miss. Name the categories locked at L0 permanently,
which no track record can promote.

## 9. Append-only audit
Every stage, every verdict, every external write: timestamped and attributed. No path through the
system leaves no trace.

## 10. Idempotent execution and verdicts
One approval, one record, one external write, even under replay or simultaneous clicks. A
duplicated verdict skews the metric that moves the trust ladder, so this is a data-integrity rule.

## 11. Honest about what is simulated
The model seam and the external adapter can be simulated on day one behind one interface. The
pipeline, policy, trust ladder, and audit run for real. Say which is which.

## 12. Not an agent swarm
Name only what adds capability. Fewer stages with one clear kind each beats many "agents". Two
model calls is a defensible number; ten is a smell.

## Candidate checklist
For each candidate in Phase 2, state in this order:
- Reframe (one sentence)
- Stages, numbered, each tagged with its kind
- Model-call cap and the zero path
- Where the human gate sits and what cannot execute without a person
- Hard-locked categories
- Trade-off versus the other candidates
```

- [ ] **Step 2: Write the summary template**

```markdown
# {{SYSTEM_NAME}}

**{{ONE_LINE_WHAT_IT_IS}}**
{{AUTHOR}} · {{TEAM_OR_CONTEXT}}

## The problem

{{Two short paragraphs. First: the process as it is, the judgment hiding inside it, where the
bottleneck sits and why. Second: why software has not taken it so far. Cite the ClickUp sources
by name where a stakeholder said it.}}

## The system

{{One paragraph: what one run turns an inbound item into, and where it stops for a human.}}

> **{{STAGE_1}} → {{STAGE_2}} → ... → {{EXECUTION}}**

**{{Principle 1 in bold, e.g. "No decision without a dossier."}}** {{One or two sentences.}}

**{{Principle 2 in bold, e.g. "Autonomy is earned per category."}}** {{One or two sentences on the
ladder, promotion, automatic demotion, and the permanently locked categories.}}

**{{Principle 3 in bold, e.g. "Every override is the input, not a failure."}}** {{One sentence.}}

## What the model does, and what it never does

{{Which stages call a model and how many calls per run. Then everything that is deterministic,
listed. Then the zero path. Then why the split: policy sets the outcome, the resource search runs
before the model, language is the only part a model touches. If there is a Critic, what it catches
and why its verdict is a gate.}}

## Approvals and the record

{{Policy as data and who edits it. What cannot happen without a human. What approval executes and
what it deliberately does not. Idempotency of verdicts. The audit log.}}

## Why this shape

{{The obvious build and how it fails. What this design is built for. Why it is useful at L0 on day
one.}}

## What is simulated

{{What runs for real. What is simulated and labelled. What changes to go to production.}}

---

**Architecture:** architecture.png
**Context dossier:** CONTEXT.md
**Source task:** {{CLICKUP_TASK_LINK}}
```

- [ ] **Step 3: Verify no placeholders leaked other than the intended `{{...}}` slots**

Run: `cd /Users/stevencallaway/Projects/design-ai-system && rg -n "TBD|TODO" reference/ || echo clean`
Expected: `clean`.

- [ ] **Step 4: Commit**

```bash
cd /Users/stevencallaway/Projects/design-ai-system
git add reference/maestro-principles.md reference/summary-template.md
git commit -m "docs: Maestro rubric and executive summary template"
```

---

### Task 5: SKILL.md, README, and the symlink install

**Files:**
- Create: `SKILL.md`
- Create: `README.md`
- Create: `.gitignore`
- Create symlink: `~/.cursor/skills/design-ai-system -> ~/Projects/design-ai-system`

**Interfaces:**
- Consumes: `scripts/render_diagram.py`, `scripts/svg_to_png.sh`, `reference/*` from Tasks 1–4.
- Produces: the invocable skill.

- [ ] **Step 1: Write SKILL.md**

```markdown
---
name: design-ai-system
description: Designs a Maestro-shaped AI system to improve an inefficient process described in a staging ClickUp task, then renders a one-page architecture PNG, an executive summary, and a context dossier. Use when the user invokes /design-ai-system with a ClickUp task URL, or says they have been pulled into a broken process and need to design an AI system for it.
disable-model-invocation: true
---

# design-ai-system

Turn a process problem that lives in ClickUp into a decided AI system design with a one-page
architecture diagram in the style of Maestro (github.com/stevencallaway1/maestro-ceo-scheduling).

`<skill-dir>` below means the directory containing this file.

## Invocation

```
/design-ai-system <clickup task url> [clickup chat channel or thread url]
```

Task URLs look like `https://app.clickup-stg.com/t/<task_id>` or
`https://app.clickup-stg.com/t/<team_id>/<custom_id>`. Chat URLs contain `/chat/` or `/r/`.

If no task URL is given, ask for one. Do not proceed on pasted text alone unless ClickUp is
unreachable (see Failure rules).

## Hard rules

- ClickUp **staging** only: namespace `plugin-clickupstaging-clickupStaging`. Never production.
- Call `GetDynamicTools` on that namespace once before the first ClickUp call to load schemas.
- Three phases, in order. Two gates. Never skip a gate or proceed on a guess.
- Phase 1 decides nothing. No candidate designs appear in `CONTEXT.md`.
- Never write back to ClickUp.
- Write ClickUp task links as inline markdown links with the task name as anchor text.
- Output directory: `./ai-system-designs/<task-slug>/` in the current workspace. If the workspace
  is the home directory, use `~/Documents/ai-system-designs/<task-slug>/`. `<task-slug>` is the task
  name lowercased, non-alphanumerics replaced by `-`, trimmed to 50 chars.

## Phase 1: Intake

Copy this checklist into a TodoWrite and work it:

```
- [ ] 1. clickup_get_task (include subtasks, custom fields)
- [ ] 2. clickup_get_task_comments, then clickup_get_threaded_comments for every comment that has replies
- [ ] 3. Attachments: list all; clickup_download_task_attachment for md/txt/csv/pdf; linked docs via clickup_get_document_pages
- [ ] 4. If a chat URL was given: clickup_get_chat_channel_messages, then clickup_get_chat_message_replies for threads
- [ ] 5. clickup_ask_brain with the prompt below; poll clickup_get_brain_response until complete or 3 polls
- [ ] 6. Write CONTEXT.md
```

Brain prompt (fill the braces from the task):

```
Find tasks, docs, and comments related to this process: "{task name}". Context: {first 500 chars
of description}. Return prior attempts to fix it, who owns each step, systems involved, volumes
or timings mentioned, and anything marked sensitive or confidential.
```

### CONTEXT.md format

```markdown
# Context: {task name}

## Sources pulled
- [{task name}]({task url}) — task, {n} comments, {m} attachments
- {one bullet per doc, attachment, chat thread, Brain query, each linked}

## The current process as described
{Numbered steps. Actors, systems, handoffs. Quote stakeholders where they described it.}

## Pain points
- {pain point} — {who said it, linked}

## People and roles
- {name}: {role in this process}

## Stated vs inferred
**Stated:** {bullets, each attributable to a source}
**Inferred:** {bullets; things you concluded that no source says outright}

## Gaps
- {what you needed and could not find; Brain timeouts; unreadable attachments}
```

Everything in "Inferred" stays labelled inferred for the rest of the run.

## Phase 2: Design

Read `<skill-dir>/reference/maestro-principles.md` in full, then `CONTEXT.md`.

### Step 1: candidates

Build 2 or 3 candidate systems. Each must follow the Candidate checklist at the bottom of the
rubric: reframe, numbered stages with kinds, model-call cap and zero path, human gate, hard-locked
categories, trade-off. Stage counts 4 to 8.

Present them with AskQuestion. The recommended candidate goes first with "(Recommended)" in its
label and one sentence of why. Each option label carries the reframe and the stage list in short
form; the full checklist for each goes in the message above the question.

**Gate 1: wait for the pick.** If the user picks "Other", read it and re-propose.

### Step 2: finalize

Expand the chosen candidate into the full design and show it as text in chat, in this order:

1. Title, subtitle, one-sentence thesis.
2. Input box: the inbound item and its channels (max 3 lines).
3. Stage strip: for each stage `num · LABEL`, kind, title (2–3 words), body (max 3 short lines,
   each under ~22 characters for 6 stages; shorter for 7–8).
4. Data sources: which hand-editable files or systems feed which stage.
5. Bypass path, if any: the condition that skips model stages straight to a human.
6. Execution box: the external adapter, its idempotency note, and whether it is simulated.
7. Two bottom panels: audit log; trust ladder and eval loop (max 3 lines each).
8. Feedback arrow: which panel adjusts which stage, with its label.
9. Caption: two lines stating the model-call cap and what the model never does.
10. Trust ladder table: L0–L3, promotion gates, automatic demotion trigger, permanently locked
    categories.
11. Simulated on day one vs real.

**Gate 2: ask "Draw this?" and wait.** Changes loop back to this step.

## Phase 3: Deliver

1. Create the output directory. Move `CONTEXT.md` there.
2. Write `architecture.spec.json`. Schema and a complete example:
   `<skill-dir>/reference/maestro.spec.json`. Keys: `title, subtitle, thesis, input{label,title,
   lines}, stages[{num,label,kind,title,body}], data_sources[{over,lines}], bypass{from,to,note},
   execution{label,title,lines,highlight_last}, panels[2]{title,body}, feedback{from_panel,
   to_stage,label}, caption[2]`. `kind` ∈ `deterministic | model | human | external`.
3. Render:
   ```bash
   python3 <skill-dir>/scripts/render_diagram.py architecture.spec.json architecture.svg
   <skill-dir>/scripts/svg_to_png.sh architecture.svg architecture.png
   ```
   If the renderer exits 2, read its errors, fix the spec, re-run. If `svg_to_png.sh` exits 3,
   ship the SVG and tell the user Chrome was not found.
4. Read `architecture.png` with the Read tool and check it: no text overflowing a card, bypass and
   feedback land where intended, caption fits on two lines. Shorten text in the spec and re-render
   if not.
5. Write `EXECUTIVE-SUMMARY.md` from `<skill-dir>/reference/summary-template.md`, filling every
   `{{slot}}`. Cite ClickUp sources inline.
6. Reply with the embedded PNG (`![architecture](<absolute path>)`), the list of output files,
   and the three to five design decisions most worth the user's attention.

## Failure rules

| Condition | Do |
|---|---|
| ClickUp tool fails or task unreadable | Stop. Say what failed. Ask the user to paste the task text and comments. Continue from Phase 1 step 6 with that. |
| Brain times out or is empty after 3 polls | Continue. Record it under Gaps. |
| Chat URL unreadable | Continue without it. Record under Gaps. |
| Renderer exit 2 | Fix the spec per the message. Never pad or truncate silently. |
| Stage count outside 4–8 | Re-plan the stages. Do not squeeze. |
| Chrome missing (exit 3) | Ship SVG. Say so. |
| User rejects at a gate | Loop back to that step. |

## Worked example

`<skill-dir>/reference/maestro.spec.json` is the reference diagram as a spec. Render it to see the
target look before writing a new one:

```bash
python3 <skill-dir>/scripts/render_diagram.py <skill-dir>/reference/maestro.spec.json /tmp/maestro.svg
<skill-dir>/scripts/svg_to_png.sh /tmp/maestro.svg /tmp/maestro.png
```
```

- [ ] **Step 2: Write README.md**

```markdown
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
scripts/svg_to_png.sh /tmp/maestro.svg /tmp/maestro.png
```

## Test

```bash
python3 -m unittest discover -s tests -v
```

## Publish changes

The initial publish was done through the GitHub connector. For ordinary pushes:

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
```

- [ ] **Step 3: Write .gitignore and create the symlink**

`.gitignore`:
```
__pycache__/
*.pyc
.DS_Store
ai-system-designs/
```

Run:
```bash
mkdir -p ~/.cursor/skills
ln -sfn ~/Projects/design-ai-system ~/.cursor/skills/design-ai-system
ls -la ~/.cursor/skills/ && head -5 ~/.cursor/skills/design-ai-system/SKILL.md && wc -l ~/Projects/design-ai-system/SKILL.md
```
Expected: symlink listed, frontmatter printed, line count under 500.

- [ ] **Step 4: Commit**

```bash
cd /Users/stevencallaway/Projects/design-ai-system
git add SKILL.md README.md .gitignore
git commit -m "feat: SKILL.md, README, gitignore"
```

---

### Task 6: Publish to GitHub (scallaway-dotcom/design-ai-system)

**Files:**
- No file changes. Remote operations via the GitHub MCP, then local git remote setup.

**Interfaces:**
- Consumes: all committed files from Tasks 1–5.

- [ ] **Step 1: Check the connector's schemas**

Call `GetDynamicTools` for `plugin-github-github` tools `create_repository` and `push_files`. Confirm `get_me` returns `scallaway-dotcom`.

- [ ] **Step 2: Create the repository**

`create_repository` with `name: design-ai-system`, `description: Cursor skill that designs a Maestro-shaped AI system from a ClickUp task and renders a one-page architecture diagram`, `private: false`, `autoInit: false`.

- [ ] **Step 3: Push all tracked files as one commit**

Run `cd ~/Projects/design-ai-system && git ls-files` to list files. Read each and pass them to `push_files` with `owner: scallaway-dotcom`, `repo: design-ai-system`, `branch: main`, `message: Initial publish of design-ai-system skill`. Skip `tests/__init__.py` only if the connector rejects empty files; otherwise include it.

- [ ] **Step 4: Point local main at the remote and verify trees match**

```bash
cd ~/Projects/design-ai-system
git remote add origin https://github.com/scallaway-dotcom/design-ai-system.git
git fetch origin
git diff --stat HEAD origin/main
```
Expected: empty diff. If files differ, push the missing ones with `push_files` and fetch again. Only when the diff is empty:

```bash
git reset --hard origin/main
git branch --set-upstream-to=origin/main main
git log --oneline -3
```
(Needs `required_permissions: ["all"]` because it writes `.git/config`.)

- [ ] **Step 5: Verify**

Open `https://github.com/scallaway-dotcom/design-ai-system` via `get_file_contents` for `SKILL.md` and confirm it is readable. Confirm `ls -la ~/.cursor/skills/design-ai-system/SKILL.md` still resolves.

---

### Task 7: End-to-end dry run against staging ClickUp

**Files:**
- Output: `~/Documents/ai-system-designs/<slug>/` (outside the repo; not committed).

**Interfaces:**
- Consumes: the installed skill at `~/.cursor/skills/design-ai-system`.

- [ ] **Step 1: Find a list to create the throwaway task in**

Call `GetDynamicTools` on `plugin-clickupstaging-clickupStaging`, then `clickup_get_user` (for `current_time`) and `clickup_get_workspace_hierarchy`. Pick a list the user owns or a sandbox list; note its id.

- [ ] **Step 2: Create the task and two comments**

`clickup_create_task` in that list:

- name: `Vendor invoice approval takes 11 days`
- description:
  ```
  Every vendor invoice over $5k goes: AP inbox -> Priya checks PO match in NetSuite -> posts in #finance-approvals -> budget owner approves in Slack (or doesn't) -> Priya chases after 3 days -> CFO approves anything over $25k by email -> Priya keys it into NetSuite -> payment run Fridays. Median 11 days, vendors call Priya directly, two late-fee incidents last quarter. Legal/HR vendor invoices (outside counsel, recruiters, severance) must never be auto-approved. Budget owners say they can't tell from the Slack post whether the invoice is in budget.
  ```
- Then `clickup_create_task_comment` twice:
  1. `Priya here. 60% of my chasing is budget owners who never saw the Slack ping. If the system just told them "this is 4% of your remaining Q4 budget" they'd click approve in a minute.`
  2. `From the CFO: I will not accept anything that pays a vendor without a human clicking. I also want to see why the system thought an invoice was fine, not just that it did.`

Record the task URL.

- [ ] **Step 3: Run the skill end to end**

Invoke `/design-ai-system <task url>` in this session and follow `SKILL.md` exactly: Phase 1 through `CONTEXT.md`; Phase 2 candidates via AskQuestion (Gate 1), finalize (Gate 2); Phase 3 render and summary. The user answers both gates.

- [ ] **Step 4: Inspect outputs**

```bash
ls -la ~/Documents/ai-system-designs/*/
python3 -c "import struct,glob;p=glob.glob('/Users/stevencallaway/Documents/ai-system-designs/*/architecture.png')[0];d=open(p,'rb').read(24);print(p,struct.unpack('>II',d[16:24]))"
rg -n "\{\{" ~/Documents/ai-system-designs/*/EXECUTIVE-SUMMARY.md || echo "no unfilled slots"
```
Expected: five files, PNG `(1580, 800)`, `no unfilled slots`. Read the PNG and embed it in chat. Read `CONTEXT.md` and confirm no design content appears in it.

- [ ] **Step 5: Fix anything the dry run exposed, re-test, commit, re-publish**

If `SKILL.md`, the rubric, or the renderer needed changes: edit, run `python3 -m unittest discover -s tests`, commit, and push the changed files with `push_files` (then `git fetch origin && git diff --stat HEAD origin/main` must be empty; if local has extra commits, `git reset --hard origin/main` after confirming identical trees).

- [ ] **Step 6: Delete the throwaway task**

`clickup_delete_task` with the task id from Step 2. Confirm with `clickup_get_task` returning not found.

---

## Self-review

**Spec coverage**

| Spec section | Task |
|---|---|
| Form and home, symlink, GitHub target | 5, 6 |
| Trigger, staging-only | 5 (SKILL.md) |
| Phase 1 sources, CONTEXT.md format, rules | 5 |
| Phase 2 candidates, Gate 1, finalize, Gate 2 | 5 |
| Maestro rubric | 4 |
| Phase 3 outputs, output directory | 5 |
| Diagram rendering: layout, kinds, optional overlays, 4–8 bound, Chrome | 1, 2, 3 |
| Spec schema incl. `highlight_last`, array bodies | 1, 2, 3 |
| Testing: reference reproduction, unit tests, dry run | 3, 1–2, 7 |
| Error handling table | 5 (Failure rules), 1 (validate), 3 (exit codes) |
| Publishing via connector, reset to origin/main | 6 |
| Out of scope (no write-back, no prod) | 5 (Hard rules) |

**Placeholder scan:** `{{...}}` slots in `summary-template.md` are intentional and the skill requires all to be filled (Task 7 Step 4 checks). No TBD/TODO elsewhere.

**Type consistency:** `layout(n) -> (card_w, xs)` and `centers(n)` are used identically in Tasks 1–2. `text(x, y, cls, s, fill=None, anchor=None)` signature matches every call. Spec keys in `SKILL.md` Phase 3 match `validate()` and `maestro.spec.json`. Exit codes: renderer 0/1/2, rasterizer 0/2/3/4, referenced consistently in `SKILL.md` Failure rules.
