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

def _lines_ok(errors, where, lines, max_lines=MAX_LINES):
    if not isinstance(lines, list) or not all(isinstance(x, str) for x in lines):
        errors.append(f"{where}: must be a list of strings")
        return
    if len(lines) > max_lines:
        errors.append(f"{where}: more than {max_lines} lines")


def _strs_ok(errors, where, obj, keys):
    for key in keys:
        if key not in obj:
            errors.append(f"{where}: missing required key: {key}")
        elif not isinstance(obj[key], str):
            errors.append(f"{where}: {key} must be a string")


def _box_ok(errors, name, box):
    _strs_ok(errors, name, box, ("label", "title"))
    if "lines" in box:
        _lines_ok(errors, f"{name} lines", box["lines"])


def validate(spec):
    if not isinstance(spec, dict):
        return ["spec must be an object"]
    errors = []
    types = {"title": (str, "string"), "subtitle": (str, "string"), "thesis": (str, "string"),
             "input": (dict, "object"), "stages": (list, "list"), "execution": (dict, "object"),
             "panels": (list, "list"), "caption": (list, "list")}
    ok = {}
    for key, (typ, tname) in types.items():
        if key not in spec:
            errors.append(f"missing required key: {key}")
        elif not isinstance(spec[key], typ):
            errors.append(f"{key} must be a {tname}")
        else:
            ok[key] = spec[key]

    n = None  # stage count; stays None unless stages is a valid list
    if "stages" in ok:
        stages = ok["stages"]
        n = len(stages)
        if not MIN_STAGES <= n <= MAX_STAGES:
            errors.append(f"stages must have {MIN_STAGES}-{MAX_STAGES} entries, got {n}")
        for i, s in enumerate(stages, 1):
            if not isinstance(s, dict):
                errors.append(f"stage {i}: must be an object")
                continue
            kind = s.get("kind")
            if not (isinstance(kind, str) and kind in KINDS):
                errors.append(f"stage {i}: unknown kind {kind!r}; expected one of {sorted(KINDS)}")
            _strs_ok(errors, f"stage {i}", s, ("label", "title"))
            num = s.get("num")
            if not isinstance(num, int) or isinstance(num, bool):
                errors.append(f"stage {i}: num must be an int")
            elif num != i:
                errors.append(f"stage {i}: num must be {i}")
            if "body" in s:
                _lines_ok(errors, f"stage {i} body", s["body"])
    for box in ("input", "execution"):
        if box in ok:
            _box_ok(errors, box, ok[box])
    if "panels" in ok:
        panels = ok["panels"]
        if len(panels) != 2:
            errors.append(f"panels must have exactly 2 entries, got {len(panels)}")
        for i, p in enumerate(panels, 1):
            if not isinstance(p, dict):
                errors.append(f"panel {i}: must be an object")
                continue
            _strs_ok(errors, f"panel {i}", p, ("title",))
            if "body" in p:
                _lines_ok(errors, f"panel {i} body", p["body"])
    if "caption" in ok:
        caption = ok["caption"]
        if not all(isinstance(c, str) for c in caption):
            errors.append("caption: must be a list of strings")
        if len(caption) > 2:
            errors.append("caption: more than 2 lines")
    _overlays_ok(errors, spec, n)
    return errors


def _is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def _overlays_ok(errors, spec, n):
    """Validate optional data_sources / bypass / feedback. n is None if stages is unusable."""
    def in_range(num):
        return n is None or 1 <= num <= n

    rng = f"1-{n}" if n is not None else "valid"

    if "data_sources" in spec:
        sources = spec["data_sources"]
        if not isinstance(sources, list):
            errors.append("data_sources must be a list")
            sources = []
        for i, d in enumerate(sources, 1):
            if not isinstance(d, dict):
                errors.append(f"data_sources[{i}]: must be an object")
                continue
            over = d.get("over")
            if not isinstance(over, list) or not over or not all(_is_int(k) for k in over):
                errors.append(f"data_sources[{i}]: 'over' must be a non-empty list of stage numbers")
            else:
                for num in over:
                    if not in_range(num):
                        errors.append(f"data_sources[{i}]: 'over' refers to stage {num}, which does not exist")
            _lines_ok(errors, f"data_sources[{i}] lines", d.get("lines", []), max_lines=2)

    if spec.get("bypass") is not None:
        b = spec["bypass"]
        if not isinstance(b, dict):
            errors.append("bypass must be an object")
        else:
            a, z = b.get("from"), b.get("to")
            if not (_is_int(a) and _is_int(z)):
                errors.append("bypass: 'from' and 'to' must be stage numbers (ints)")
            elif not (a < z and in_range(a) and in_range(z) and a >= 1):
                errors.append(f"bypass: 'from' ({a}) must be before 'to' ({z}) and both must be stage numbers {rng}")
            if not isinstance(b.get("note", ""), str):
                errors.append("bypass: note must be a string")

    if spec.get("feedback") is not None:
        f = spec["feedback"]
        if not isinstance(f, dict):
            errors.append("feedback must be an object")
        else:
            panel, t = f.get("from_panel"), f.get("to_stage")
            if not (_is_int(panel) and panel in (0, 1)):
                errors.append("feedback.from_panel must be 0 (left panel) or 1 (right panel)")
            if not (_is_int(t) and t >= 1 and in_range(t)):
                errors.append(f"feedback.to_stage must be a stage number {rng}")
            if not isinstance(f.get("label", ""), str):
                errors.append("feedback: label must be a string")


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

    # optional overlays
    out.extend(_overlays(spec, card_w, xs, cx, band_x, div_x))

    # caption
    for i, line in enumerate(spec["caption"][:2]):
        out.append(text(MARGIN, 754 + 20 * i, "note", line))

    body = "\n".join(out)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
            f'font-family="-apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, Helvetica, Arial, sans-serif">\n'
            f'{STYLE}\n  <rect width="{W}" height="{H}" fill="#ffffff"/>\n{DEFS}\n{body}\n</svg>\n')


SRC_Y1, SRC_Y2, SRC_DROP_TOP, SRC_DROP_BOT = 200, 217, 228, 306
BYPASS_Y, BYPASS_NOTE_Y, BYPASS_GAP = 272, 260, 10
FEED_Y, FEED_TOP = 478, 452


def _overlays(spec, card_w, xs, cx, band_x, div_x):
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
        # Centre the note on the last dashed run so it does not straddle the final crossing drop.
        note_x = (segments[-1][0] + segments[-1][1]) / 2
        out.append(text(note_x, BYPASS_NOTE_Y, "lg", b.get("note", ""),
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


# ── cli ──────────────────────────────────────────────────────────────────────

def main(argv):
    if len(argv) != 3:
        print(__doc__, file=sys.stderr)
        return 1
    try:
        with open(argv[1], encoding="utf-8") as f:
            spec = json.load(f)
    except FileNotFoundError:
        print(f"error: spec file not found: {argv[1]}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"error: spec is not valid JSON: {e}", file=sys.stderr)
        return 1
    errors = validate(spec)
    if errors:
        print("spec invalid:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 2
    with open(argv[2], "w", encoding="utf-8") as f:
        f.write(render(spec))
    print(argv[2])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
