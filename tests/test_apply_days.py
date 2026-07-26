"""test_apply_days.py — Tests the --days N helper."""

import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import fire_hotspot_download  # noqa: E402


def make_args(**kwargs):
    """Build a SimpleNamespace mimicking parsed argparse args."""
    defaults = dict(
        instrument="VIIRS",
        product="NRT",
        bbox=None,
        place=None,
        preset=None,
        start=None,
        end=None,
        days=None,
        output="fires.csv",
        format="csv",
        confidence=None,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


class TestApplyDays(unittest.TestCase):
    def test_no_days_no_change(self):
        args = make_args()
        fire_hotspot_download.apply_days(args)
        self.assertIsNone(args.start)
        self.assertIsNone(args.end)

    def test_days_3_fills_dates(self):
        args = make_args(days=3)
        fire_hotspot_download.apply_days(args)
        self.assertIsNotNone(args.start)
        self.assertIsNotNone(args.end)
        # Check date range is exactly 3 days
        start = datetime.strptime(args.start, "%Y-%m-%d").date()
        end = datetime.strptime(args.end, "%Y-%m-%d").date()
        self.assertEqual((end - start).days, 2)  # inclusive: 3 days means start..end = 2 diff

    def test_days_5_with_nrt_keeps_nrt(self):
        args = make_args(days=5, product="NRT")
        fire_hotspot_download.apply_days(args)
        self.assertEqual(args.product, "NRT")
        start = datetime.strptime(args.start, "%Y-%m-%d").date()
        end = datetime.strptime(args.end, "%Y-%m-%d").date()
        self.assertEqual((end - start).days, 4)

    def test_days_30_with_nrt_switches_to_standard(self):
        args = make_args(days=30, product="NRT")
        fire_hotspot_download.apply_days(args)
        self.assertEqual(args.product, "STANDARD")
        start = datetime.strptime(args.start, "%Y-%m-%d").date()
        end = datetime.strptime(args.end, "%Y-%m-%d").date()
        self.assertEqual((end - start).days, 29)

    def test_days_6_with_nrt_switches_to_standard(self):
        # FIRMS NRT accepts 1-5 days; --days 6 must switch
        args = make_args(days=6, product="NRT")
        fire_hotspot_download.apply_days(args)
        self.assertEqual(args.product, "STANDARD")

    def test_explicit_dates_not_overridden(self):
        args = make_args(days=7, start="2024-01-01", end="2024-01-07")
        fire_hotspot_download.apply_days(args)
        self.assertEqual(args.start, "2024-01-01")
        self.assertEqual(args.end, "2024-01-07")

    def test_invalid_days_raises(self):
        args = make_args(days=0)
        with self.assertRaises(ValueError):
            fire_hotspot_download.apply_days(args)
        args = make_args(days=400)
        with self.assertRaises(ValueError):
            fire_hotspot_download.apply_days(args)


if __name__ == "__main__":
    unittest.main(verbosity=2)
