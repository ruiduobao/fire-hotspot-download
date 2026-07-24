#!/usr/bin/env python3
"""
Tests for fire-hotspot-download CLI.
Run with: python -m pytest tests/ -v
"""

import sys
import os
import json
import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

try:
    import fire_hotspot_download as fhd
except ImportError:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "fire_hotspot_download",
        str(Path(__file__).parent.parent / "scripts" / "fire_hotspot_download.py"),
    )
    fhd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fhd)


class TestValidation(unittest.TestCase):
    """Test input validation functions."""

    def test_validate_bbox_valid(self):
        """Test valid bounding box."""
        result = fhd.validate_bbox([73, 18, 135, 54])
        self.assertEqual(result, (73, 18, 135, 54))

    def test_validate_bbox_invalid_order(self):
        """Test invalid bbox (south >= north)."""
        with self.assertRaises(ValueError):
            fhd.validate_bbox([73, 54, 135, 18])

    def test_validate_bbox_invalid_lat(self):
        """Test invalid latitude in bbox."""
        with self.assertRaises(ValueError):
            fhd.validate_bbox([73, 91, 135, 54])

    def test_validate_date_range_valid(self):
        """Test valid date range."""
        start, end = fhd.validate_date_range("2024-01-01", "2024-01-07", "NRT")
        self.assertEqual(start.year, 2024)

    def test_validate_date_range_nrt_too_long(self):
        """Test NRT date range > 7 days."""
        with self.assertRaises(ValueError):
            fhd.validate_date_range("2024-01-01", "2024-01-15", "NRT")

    def test_validate_date_range_invalid_format(self):
        """Test invalid date format."""
        with self.assertRaises(ValueError):
            fhd.validate_date_range("2024/01/01", "2024/01/07", "NRT")

    def test_validate_date_range_end_before_start(self):
        """Test end date before start date."""
        with self.assertRaises(ValueError):
            fhd.validate_date_range("2024-01-07", "2024-01-01", "NRT")

    def test_validate_instrument_valid(self):
        """Test valid instrument names."""
        self.assertEqual(fhd.validate_instrument("MODIS"), "MODIS")
        self.assertEqual(fhd.validate_instrument("viirs"), "VIIRS")
        self.assertEqual(fhd.validate_instrument("both"), "BOTH")

    def test_validate_instrument_invalid(self):
        """Test invalid instrument name."""
        with self.assertRaises(ValueError):
            fhd.validate_instrument("INVALID")

    def test_validate_confidence_valid(self):
        """Test valid confidence values."""
        self.assertEqual(fhd.validate_confidence(50), 50)
        self.assertEqual(fhd.validate_confidence(0), 0)
        self.assertEqual(fhd.validate_confidence(100), 100)
        self.assertIsNone(fhd.validate_confidence(None))

    def test_validate_confidence_invalid(self):
        """Test invalid confidence values."""
        with self.assertRaises(ValueError):
            fhd.validate_confidence(101)
        with self.assertRaises(ValueError):
            fhd.validate_confidence(-1)


class TestParseCSV(unittest.TestCase):
    """Test CSV parsing."""

    def test_parse_csv_data(self):
        """Test parsing CSV response data."""
        csv_text = """latitude,longitude,brightness,scan,track,acq_date,acq_time,satellite,confidence,version,bright_t31,frp,daynight
39.9042,116.4074,320.5,1.2,1.1,2024-01-01,0230,Terra,75,6.1,305.2,12.5,D
40.1234,116.5678,310.2,1.0,1.0,2024-01-01,0230,Aqua,60,6.1,300.1,8.3,D"""
        records = fhd.parse_csv_data(csv_text)
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["latitude"], "39.9042")
        self.assertEqual(records[0]["confidence"], "75")

    def test_parse_csv_with_confidence_filter(self):
        """Test parsing CSV with confidence filter."""
        csv_text = """latitude,longitude,brightness,confidence
39.9042,116.4074,320.5,75
40.1234,116.5678,310.2,30"""
        records = fhd.parse_csv_data(csv_text, min_confidence=50)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["latitude"], "39.9042")

    def test_parse_csv_empty(self):
        """Test parsing empty CSV."""
        records = fhd.parse_csv_data("latitude,longitude\n")
        self.assertEqual(len(records), 0)


class TestGeoJSON(unittest.TestCase):
    """Test GeoJSON conversion."""

    def test_records_to_geojson(self):
        """Test converting records to GeoJSON."""
        records = [
            {"latitude": "39.9042", "longitude": "116.4074", "confidence": "75"},
            {"latitude": "40.1234", "longitude": "116.5678", "confidence": "60"},
        ]
        geojson = fhd.records_to_geojson(records)
        self.assertEqual(geojson["type"], "FeatureCollection")
        self.assertEqual(len(geojson["features"]), 2)
        self.assertEqual(geojson["features"][0]["geometry"]["type"], "Point")
        self.assertEqual(geojson["features"][0]["geometry"]["coordinates"], [116.4074, 39.9042])

    def test_records_to_geojson_empty(self):
        """Test converting empty records to GeoJSON."""
        geojson = fhd.records_to_geojson([])
        self.assertEqual(geojson["type"], "FeatureCollection")
        self.assertEqual(len(geojson["features"]), 0)


class TestConfig(unittest.TestCase):
    """Test configuration management."""

    def test_load_config_nonexistent(self):
        """Test loading config when file doesn't exist."""
        with patch("fire_hotspot_download.CONFIG_FILE") as mock_path:
            mock_path.exists.return_value = False
            config = fhd.load_config()
            self.assertEqual(config, {})

    def test_save_and_load_config(self):
        """Test saving and loading config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            with patch("fire_hotspot_download.CONFIG_FILE", config_file):
                with patch("fire_hotspot_download.CONFIG_DIR", Path(tmpdir)):
                    test_config = {"api_key": "test_key_123"}
                    fhd.save_config(test_config)
                    loaded = fhd.load_config()
                    self.assertEqual(loaded["api_key"], "test_key_123")


class TestCLI(unittest.TestCase):
    """Test CLI argument parsing."""

    def test_help_message(self):
        """Test that help message can be displayed."""
        with self.assertRaises(SystemExit) as cm:
            with patch("sys.argv", ["fire-hotspot-download", "--help"]):
                fhd.main()
        self.assertEqual(cm.exception.code, 0)

    def test_list_instruments_command(self):
        """Test list-instruments command."""
        with patch("sys.argv", ["fire-hotspot-download", "list-instruments"]):
            fhd.main()

    def test_download_help(self):
        """Test download subcommand help."""
        with self.assertRaises(SystemExit) as cm:
            with patch("sys.argv", ["fire-hotspot-download", "download", "--help"]):
                fhd.main()
        self.assertEqual(cm.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
