"""test_place_resolver.py — Place resolver + preset tests for fire-hotspot-download."""

import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from place_resolver import (  # noqa: E402
    HARDCODED_BBOXES,
    PRESETS,
    format_bbox,
    get_preset,
    list_presets,
    resolve_place,
    PlaceNotFoundError,
)


class TestHardcodedBboxes(unittest.TestCase):
    def test_china(self):
        self.assertEqual(resolve_place("中国"), (73.0, 18.0, 135.0, 54.0))

    def test_yangtze(self):
        bbox = resolve_place("长江流域")
        self.assertEqual(bbox, (90.0, 24.0, 122.0, 36.0))

    def test_alias(self):
        self.assertEqual(resolve_place("北京市"), resolve_place("北京"))

    def test_unknown_no_nominatim(self):
        with self.assertRaises(PlaceNotFoundError):
            resolve_place("某不存在的地点xyz", use_nominatim=False)


class TestPresets(unittest.TestCase):
    def test_china_fires(self):
        p = get_preset("china-fires")
        self.assertEqual(p["instrument"], "VIIRS")
        self.assertEqual(p["product"], "NRT")
        self.assertEqual(p["bbox"], (73.0, 18.0, 135.0, 54.0))

    def test_yangtze_fires(self):
        p = get_preset("yangtze-fires")
        self.assertEqual(p["bbox"], (90.0, 24.0, 122.0, 36.0))

    def test_unknown_preset_raises(self):
        with self.assertRaises(ValueError):
            get_preset("not-a-preset")

    def test_presets_have_bbox(self):
        for name, p in PRESETS.items():
            self.assertEqual(len(p["bbox"]), 4, name)
            w, s, e, n = p["bbox"]
            self.assertLess(w, e, name)
            self.assertLess(s, n, name)


class TestFormatBbox(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(format_bbox((1.0, 2.0, 3.0, 4.0)), "1.0 2.0 3.0 4.0")


class TestAllBboxesValid(unittest.TestCase):
    def test_all(self):
        for k, b in HARDCODED_BBOXES.items():
            self.assertEqual(len(b), 4, k)
            w, s, e, n = b
            self.assertLess(w, e)
            self.assertLess(s, n)


if __name__ == "__main__":
    unittest.main(verbosity=2)
