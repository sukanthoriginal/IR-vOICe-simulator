import re
import unittest
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class IdCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()

    def handle_starttag(self, _tag, attrs):
        attributes = dict(attrs)
        if "id" in attributes:
            self.ids.add(attributes["id"])


class L2WebStaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / "web" / "index.html").read_text()
        cls.javascript = (ROOT / "web" / "app.js").read_text()

    def test_every_dom_lookup_has_a_matching_element(self):
        parser = IdCollector()
        parser.feed(self.html)
        looked_up = set(re.findall(
            r"getElementById\(['\"]([^'\"]+)", self.javascript,
        ))
        self.assertEqual(looked_up - parser.ids, set())

    def test_display_preserves_the_native_soundscape_aspect(self):
        self.assertIn("aspect-ratio: 178 / 64", self.html)
        self.assertNotIn("aspect-ratio: 16 / 10", self.html)
        self.assertIn("const SOUNDSCAPE_ASPECT_RATIO = 178 / 64", self.javascript)
        self.assertIn("const MAX_GRID_WIDTH_CSS_PX = 2020", self.javascript)
        self.assertIn(
            "MAX_GRID_WIDTH_CSS_PX / SOUNDSCAPE_ASPECT_RATIO",
            self.javascript,
        )
        self.assertIn(
            "const height = width / SOUNDSCAPE_ASPECT_RATIO",
            self.javascript,
        )
        self.assertIn("manifest.image_width !== 178", self.javascript)
        self.assertIn("manifest.image_height !== 64", self.javascript)

    def test_every_trial_logs_the_actual_geometry(self):
        self.assertIn("const geometryAudit = auditGridGeometry(rect)", self.javascript)
        self.assertIn("...geometryAudit", self.javascript)
        for field in (
            "display_geometry_version",
            "grid_width_css_px",
            "grid_height_css_px",
            "grid_aspect_ratio",
            "css_px_per_audio_column",
            "css_px_per_audio_row",
            "display_axis_stretch_y_over_x",
        ):
            self.assertIn(field, self.javascript)
        self.assertIn("soundscape-native-178x64-v1", self.javascript)


if __name__ == "__main__":
    unittest.main()
