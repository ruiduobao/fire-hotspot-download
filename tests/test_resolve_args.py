"""test_resolve_args.py — Tests the resolve_args() helper for fire-hotspot-download."""

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import fire_hotspot_download  # noqa: E402


def make_args(**kwargs):
    defaults = dict(
        instrument="VIIRS",
        product="NRT",
        bbox=None,
        place=None,
        preset=None,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


class TestResolveArgs(unittest.TestCase):
    def test_bbox_wins(self):
        args = make_args(bbox=[116.0, 39.5, 116.8, 40.2], place="北京市")
        bbox, label = fire_hotspot_download.resolve_args(args)
        self.assertEqual(bbox, (116.0, 39.5, 116.8, 40.2))
        self.assertIn("--bbox", label)

    def test_place(self):
        args = make_args(place="北京市")
        bbox, label = fire_hotspot_download.resolve_args(args)
        self.assertEqual(bbox, (115.7, 39.4, 116.8, 40.3))
        self.assertIn("北京市", label)

    def test_preset_fills_bbox_and_instrument(self):
        args = make_args(preset="china-fires")
        bbox, label = fire_hotspot_download.resolve_args(args)
        self.assertEqual(bbox, (73.0, 18.0, 135.0, 54.0))
        # preset should have filled in args.instrument and args.product
        self.assertEqual(args.instrument, "VIIRS")
        self.assertEqual(args.product, "NRT")

    def test_no_extent_raises(self):
        args = make_args()
        with self.assertRaises(ValueError):
            fire_hotspot_download.resolve_args(args)

    def test_unknown_place_raises_and_exits(self):
        args = make_args(place="某不存在的地点xyz")
        with self.assertRaises(SystemExit):
            fire_hotspot_download.resolve_args(args)


if __name__ == "__main__":
    unittest.main(verbosity=2)
