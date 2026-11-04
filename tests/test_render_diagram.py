import json
import pathlib
import re
import subprocess
import sys
import tempfile
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

    def _assert_rejected(self, spec):
        errs = rd.validate(spec)  # must not raise
        self.assertIsInstance(errs, list)
        self.assertTrue(errs)
        return errs

    def test_stage_missing_title_rejected(self):
        spec = make_spec(4)
        del spec["stages"][0]["title"]
        self._assert_rejected(spec)

    def test_panel_missing_title_rejected(self):
        spec = make_spec(4)
        del spec["panels"][0]["title"]
        self._assert_rejected(spec)

    def test_stages_none_rejected(self):
        self._assert_rejected(make_spec(4, stages=None))

    def test_stage_not_a_dict_rejected(self):
        spec = make_spec(4)
        spec["stages"][1] = "not a dict"
        self._assert_rejected(spec)

    def test_list_kind_rejected(self):
        spec = make_spec(4)
        spec["stages"][0]["kind"] = ["model"]
        self._assert_rejected(spec)

    def test_string_body_rejected(self):
        spec = make_spec(4)
        spec["stages"][0]["body"] = "just a string"
        self._assert_rejected(spec)

    def test_stage_num_must_match_position(self):
        spec = make_spec(6)
        for s, num in zip(spec["stages"], (9, 2, 3, 4, 5, 1)):
            s["num"] = num
        errs = rd.validate(spec)
        self.assertTrue(any("num must be 1" in e for e in errs), errs)
        with self.assertRaises(rd.SpecError):
            rd.render(spec)

    def test_input_missing_label_rejected(self):
        spec = make_spec(4)
        del spec["input"]["label"]
        self._assert_rejected(spec)


class RenderCoreTests(unittest.TestCase):
    def test_render_raises_on_invalid(self):
        with self.assertRaises(rd.SpecError):
            rd.render(make_spec(3))

    def test_render_raises_spec_error_on_stage_missing_title(self):
        spec = make_spec(4)
        del spec["stages"][0]["title"]
        with self.assertRaises(rd.SpecError):
            rd.render(spec)

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


class OverlayTests(unittest.TestCase):
    def test_data_source_refers_to_existing_stage(self):
        spec = make_spec(4, data_sources=[{"over": [9], "lines": ["x", "y"]}])
        self.assertTrue(any("data_sources[1]" in e and "stage 9" in e for e in rd.validate(spec)))

    def test_data_source_more_than_two_lines_rejected(self):
        spec = make_spec(6, data_sources=[{"over": [2], "lines": ["a", "b", "c"]}])
        errs = rd.validate(spec)
        self.assertTrue(any("data_sources[1] lines: more than 2 lines" in e for e in errs), errs)

    def test_data_sources_rendered_at_stage_center(self):
        spec = make_spec(6, data_sources=[{"over": [2], "lines": ["people.json", "flags"]}])
        svg = rd.render(spec)
        self.assertIn('class="feedb" text-anchor="middle">people.json</text>', svg)
        self.assertIn('x="515.5" y="200" class="feedb"', svg)

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

    def test_malformed_optional_sections_rejected_without_raising(self):
        bad = [
            {"data_sources": "x"}, {"data_sources": [None]}, {"data_sources": [{}]},
            {"data_sources": [{"over": []}]}, {"data_sources": [{"over": ["a"]}]},
            {"data_sources": [{"over": [True]}]}, {"data_sources": [{"over": 2}]},
            {"data_sources": [{"over": [1], "lines": "abc"}]},
            {"bypass": "x"}, {"bypass": {}}, {"bypass": {"from": "1", "to": 3}},
            {"bypass": {"from": 1, "to": 3, "note": 5}},
            {"feedback": []}, {"feedback": {}}, {"feedback": {"from_panel": True, "to_stage": 2}},
            {"feedback": {"from_panel": 0, "to_stage": "2"}},
            {"feedback": {"from_panel": 0, "to_stage": 2, "label": 7}},
        ]
        for extra in bad:
            spec = make_spec(6, **extra)
            errs = rd.validate(spec)  # must not raise
            self.assertTrue(errs, extra)
            with self.assertRaises(rd.SpecError):
                rd.render(spec)

    def test_overlay_errors_reported_when_stages_unusable(self):
        spec = make_spec(6, stages=None, bypass="x")
        self.assertTrue(any("bypass" in e for e in rd.validate(spec)))


class FixtureTests(unittest.TestCase):
    def test_maestro_fixture_is_valid_and_renders(self):
        spec = json.loads((ROOT / "reference" / "maestro.spec.json").read_text())
        self.assertEqual(rd.validate(spec), [])
        svg = rd.render(spec)
        parse(svg)
        self.assertIn("Maestro", svg)
        self.assertIn("6 · APPROVAL", svg)
        self.assertEqual(len(spec["stages"]), 6)
        self.assertEqual(len(spec["data_sources"]), 3)
        self.assertIn("bypass", spec)
        self.assertIn("feedback", spec)
        self.assertEqual(len(spec["panels"]), 2)

    def test_bypass_note_sits_on_last_dashed_run_not_in_gap(self):
        spec = json.loads((ROOT / "reference" / "maestro.spec.json").read_text())
        root = parse(rd.render(spec))
        note = spec["bypass"]["note"]
        notes = [t for t in root.iter(SVG_NS + "text") if t.text == note]
        self.assertEqual(len(notes), 1)
        note_x = float(notes[0].get("x"))
        calendar_drop_x = rd.centers(6)[4]  # stage 4 carries calendar.json
        self.assertGreater(note_x, calendar_drop_x + 10)

        # The note must be centred on the horizontal run of the LAST red dashed path.
        red = [p for p in root.iter(SVG_NS + "path") if p.get("stroke") == "#b3261e"]
        self.assertGreaterEqual(len(red), 2)
        d = red[-1].get("d")
        # last segment looks like "M s 272 L e 272 L e 306": run is s..e at y=272
        pts = re.findall(r"([ML])\s*([\d.]+)\s+([\d.]+)", d)
        run = [float(x) for _, x, y in pts if float(y) == rd.BYPASS_Y]
        self.assertGreaterEqual(len(run), 2, d)
        midpoint = (run[0] + run[-1]) / 2
        self.assertLess(abs(note_x - midpoint), 1.0, (note_x, midpoint, d))


class CliTests(unittest.TestCase):
    SCRIPT = str(ROOT / "scripts" / "render_diagram.py")

    def run_cli(self, *args):
        return subprocess.run([sys.executable, self.SCRIPT, *args],
                              capture_output=True, text=True)

    def test_missing_spec_file_exits_1(self):
        with tempfile.TemporaryDirectory() as d:
            r = self.run_cli(str(pathlib.Path(d) / "nope.json"), str(pathlib.Path(d) / "o.svg"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("not found", r.stderr)

    def test_invalid_spec_exits_2(self):
        with tempfile.TemporaryDirectory() as d:
            spec = pathlib.Path(d) / "bad.json"
            spec.write_text('{"title": "x"}')
            r = self.run_cli(str(spec), str(pathlib.Path(d) / "o.svg"))
        self.assertEqual(r.returncode, 2)
        self.assertIn("spec invalid", r.stderr)

    def test_fixture_renders_and_prints_output_path(self):
        with tempfile.TemporaryDirectory() as d:
            out = str(pathlib.Path(d) / "o.svg")
            r = self.run_cli(str(ROOT / "reference" / "maestro.spec.json"), out)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(r.stdout.strip(), out)
            self.assertTrue(pathlib.Path(out).is_file())


if __name__ == "__main__":
    unittest.main()
