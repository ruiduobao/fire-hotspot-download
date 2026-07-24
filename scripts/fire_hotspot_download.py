#!/usr/bin/env python3
"""
NASA FIRMS Fire Hotspot Download CLI
=====================================
Download MODIS and VIIRS active fire hotspot data from NASA FIRMS.

Privacy Notice:
- This tool sends ONLY the following data to firms.modaps.eosdis.nasa.gov:
  * Bounding box coordinates
  * Date range
  * Instrument selection
- Your API key is stored locally in ~/.config/fire-hotspot-download/config.json
  and is sent only to authenticate API requests.
- NO personal data beyond the API key is sent.
- All data is processed locally except the API request itself.

License: MIT-0 (Public Domain)
Data: NASA FIRMS, Public Domain
"""

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    import requests
except ImportError:
    print("Error: 'requests' package is required. Install with: pip install requests>=2.28.0")
    sys.exit(1)

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

# ── Constants ──────────────────────────────────────────────────────────────────
FIRMS_API_BASE = "https://firms.modaps.eosdis.nasa.gov/api"
AREA_ENDPOINT_CSV = f"{FIRMS_API_BASE}/area/csv"
AREA_ENDPOINT_GEOJSON = f"{FIRMS_API_BASE}/geojson/area"
MAP_KEY_URL = "https://firms.modaps.eosdis.nasa.gov/api/map_key/"

CONFIG_DIR = Path.home() / ".config" / "fire-hotspot-download"
CONFIG_FILE = CONFIG_DIR / "config.json"

INSTRUMENTS = {
    "MODIS": {
        "label": "MODIS (Terra+Aqua)",
        "NRT": "MODIS_NRT",
        "STANDARD": "MODIS_SP",
        "description": "1km resolution, MCD14DL product",
    },
    "VIIRS": {
        "label": "VIIRS (Suomi-NPP)",
        "NRT": "VIIRS_SNPP_NRT",
        "STANDARD": "VIIRS_SNPP_SP",
        "description": "375m resolution, VNP14IMGTDL_NRT product",
    },
    "BOTH": {
        "label": "MODIS + VIIRS Combined",
        "NRT": "VIIRS_SNPP_NRT,MODIS_NRT",
        "STANDARD": "VIIRS_SNPP_SP,MODIS_SP",
        "description": "Combined MODIS and VIIRS data",
    },
}

VALID_FORMATS = ["csv", "geojson"]

# ── Config Management ──────────────────────────────────────────────────────────
def load_config():
    """Load configuration from file."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(config):
    """Save configuration to file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
    try:
        os.chmod(CONFIG_FILE, 0o600)
    except OSError:
        pass

def get_api_key():
    """Get FIRMS API key from env or config."""
    key = os.environ.get("FIRMS_API_KEY")
    if key:
        return key

    config = load_config()
    return config.get("api_key")

# ── Validation ─────────────────────────────────────────────────────────────────
def validate_bbox(bbox):
    """Validate bounding box: west, south, east, north."""
    if len(bbox) != 4:
        raise ValueError("Bounding box must have 4 values: west south east north")
    west, south, east, north = bbox
    if not (-90 <= south <= 90) or not (-90 <= north <= 90):
        raise ValueError("Latitude must be between -90 and 90")
    if not (-180 <= west <= 180) or not (-180 <= east <= 180):
        raise ValueError("Longitude must be between -180 and 180")
    if south >= north:
        raise ValueError(f"South ({south}) must be less than North ({north})")
    if west >= east:
        raise ValueError(f"West ({west}) must be less than East ({east})")
    return west, south, east, north

def validate_date_range(start_str, end_str, product):
    """Validate date range."""
    try:
        start = datetime.strptime(start_str, "%Y-%m-%d")
        end = datetime.strptime(end_str, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Dates must be in YYYY-MM-DD format")

    if end < start:
        raise ValueError("End date must be >= start date")

    # FIRMS NRT limited to 7 days
    if product == "NRT":
        max_range = timedelta(days=7)
        if (end - start) > max_range:
            raise ValueError("NRT product limited to 7-day range")
    elif product == "STANDARD":
        max_range = timedelta(days=365)
        if (end - start) > max_range:
            print("Warning: Standard product range > 1 year. Request may be large.")

    return start, end

def validate_instrument(instrument):
    """Validate instrument selection."""
    instrument = instrument.upper()
    if instrument not in INSTRUMENTS:
        raise ValueError(f"Unknown instrument: {instrument}. Valid: {', '.join(INSTRUMENTS.keys())}")
    return instrument

def validate_confidence(confidence):
    """Validate confidence threshold."""
    if confidence is not None:
        if not (0 <= confidence <= 100):
            raise ValueError("Confidence must be between 0 and 100")
    return confidence

# ── API Functions ──────────────────────────────────────────────────────────────
def fetch_fire_data(api_key, instrument, product, bbox, start, end):
    """Fetch fire hotspot data from FIRMS API."""
    instrument_info = INSTRUMENTS[instrument]
    source = instrument_info[product]

    endpoint = AREA_ENDPOINT_CSV if source != "geojson" else AREA_ENDPOINT_GEOJSON

    # Format: west,south,east,north
    bbox_str = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"

    url = f"{endpoint}/{api_key}/{source}/{bbox_str}/{start.strftime('%Y-%m-%d')}/{end.strftime('%Y-%m-%d')}"

    try:
        resp = requests.get(url, timeout=120)
        resp.raise_for_status()
    except requests.exceptions.Timeout:
        raise RuntimeError("Request timed out. Try a smaller date range or bbox.")
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Connection error. Check your internet connection.")
    except requests.exceptions.HTTPError as e:
        if resp.status_code == 403:
            raise RuntimeError("Authentication error. Check your API key.")
        elif resp.status_code == 422:
            raise RuntimeError(f"Invalid parameters: {resp.text[:200]}")
        raise RuntimeError(f"HTTP error {resp.status_code}: {resp.text[:200]}")

    return resp.text

def parse_csv_data(csv_text, min_confidence=None):
    """Parse CSV response into list of records."""
    lines = csv_text.strip().split("\n")
    if len(lines) < 2:
        return []

    reader = csv.DictReader(lines)
    records = []
    for row in reader:
        if min_confidence is not None:
            try:
                conf = float(row.get("confidence", 0))
                if conf < min_confidence:
                    continue
            except (ValueError, TypeError):
                pass
        records.append(dict(row))

    return records

def records_to_geojson(records):
    """Convert records to GeoJSON FeatureCollection."""
    features = []
    for record in records:
        try:
            lat = float(record.get("latitude", 0))
            lon = float(record.get("longitude", 0))
        except (ValueError, TypeError):
            continue

        properties = {k: v for k, v in record.items() if k not in ("latitude", "longitude")}
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [lon, lat],
            },
            "properties": properties,
        }
        features.append(feature)

    return {
        "type": "FeatureCollection",
        "features": features,
    }

# ── Output Functions ───────────────────────────────────────────────────────────
def write_csv_output(records, output_path):
    """Write records to CSV file."""
    if not records:
        print("Warning: No fire hotspots found.")
        return

    fieldnames = list(records[0].keys())
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    print(f"Written {len(records)} fire hotspot(s) to {output_path}")

def write_geojson_output(records, output_path):
    """Write records to GeoJSON file."""
    geojson = records_to_geojson(records)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(geojson, f, indent=2, ensure_ascii=False)
    print(f"Written {len(geojson['features'])} fire hotspot(s) to {output_path}")

# ── CLI Commands ───────────────────────────────────────────────────────────────
def cmd_download(args):
    """Download fire hotspot data."""
    api_key = get_api_key()
    if not api_key:
        print("Error: FIRMS API key not configured.")
        print(f"Get a free key at: {MAP_KEY_URL}")
        print("Then run: python scripts/fire-hotspot-download.py set-key YOUR_KEY")
        print("   Or set FIRMS_API_KEY environment variable.")
        sys.exit(1)

    instrument = validate_instrument(args.instrument)
    start, end = validate_date_range(args.start, args.end, args.product.upper())
    bbox = validate_bbox(args.bbox)
    confidence = validate_confidence(args.confidence)

    print(f"Downloading fire hotspot data:")
    print(f"  Instrument: {INSTRUMENTS[instrument]['label']}")
    print(f"  Product: {args.product}")
    print(f"  Period: {args.start} to {args.end}")
    print(f"  BBox: {bbox}")
    if confidence is not None:
        print(f"  Min confidence: {confidence}")

    csv_text = fetch_fire_data(api_key, instrument, args.product.upper(), bbox, start, end)
    records = parse_csv_data(csv_text, confidence)

    if not records:
        print("No fire hotspots found for the given criteria.")
        sys.exit(0)

    # Output
    output_path = args.output
    if args.format == "geojson" or output_path.endswith(".geojson"):
        write_geojson_output(records, output_path)
    else:
        write_csv_output(records, output_path)

def cmd_list_instruments(args):
    """List available instruments."""
    print("=" * 70)
    print("NASA FIRMS - Available Instruments")
    print("=" * 70)
    for inst, info in INSTRUMENTS.items():
        print(f"\n  {inst}: {info['label']}")
        print(f"    {info['description']}")
        print(f"    NRT product: {info['NRT']}")
        print(f"    Standard product: {info['STANDARD']}")
    print()
    print("=" * 70)
    print(f"API Key: Get a free key at {MAP_KEY_URL}")

def cmd_set_key(args):
    """Set FIRMS API key."""
    config = load_config()
    config["api_key"] = args.api_key.strip()
    save_config(config)
    print(f"API key saved to {CONFIG_FILE}")
    print("You can also set FIRMS_API_KEY environment variable.")

# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        prog="fire-hotspot-download",
        description="Download NASA FIRMS MODIS/VIIRS active fire hotspot data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s download --instrument VIIRS --product NRT \\
    --bbox 73 18 135 54 --start 2024-01-01 --end 2024-01-07 \\
    --output china_fires.csv

  %(prog)s download --instrument MODIS --product STANDARD \\
    --bbox 116.0 39.5 116.8 40.2 --start 2024-03-01 --end 2024-03-31 \\
    --output beijing_fires.geojson --format geojson

  %(prog)s download --instrument BOTH --product NRT \\
    --bbox 116.0 39.5 116.8 40.2 --start 2024-06-01 --end 2024-06-07 \\
    --output fires.csv --confidence 50

  %(prog)s set-key YOUR_FIRMS_API_KEY
  %(prog)s list-instruments
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Download command
    dl = subparsers.add_parser("download", help="Download fire hotspot data")
    dl.add_argument("--instrument", default="VIIRS",
                    choices=list(INSTRUMENTS.keys()),
                    help="Instrument: MODIS, VIIRS, or BOTH (default: VIIRS)")
    dl.add_argument("--product", default="NRT", choices=["NRT", "STANDARD"],
                    help="Product type: NRT or STANDARD (default: NRT)")
    dl.add_argument("--bbox", nargs=4, type=float, required=True,
                    metavar=("W", "S", "E", "N"),
                    help="Bounding box: west south east north")
    dl.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    dl.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    dl.add_argument("--output", default="fire_hotspots.csv",
                    help="Output file path (default: fire_hotspots.csv)")
    dl.add_argument("--format", choices=["csv", "geojson"], default="csv",
                    help="Output format (default: csv)")
    dl.add_argument("--confidence", type=float, default=None,
                    help="Minimum confidence threshold (0-100)")
    dl.set_defaults(func=cmd_download)

    # List instruments command
    li = subparsers.add_parser("list-instruments", help="List available instruments")
    li.set_defaults(func=cmd_list_instruments)

    # Set key command
    sk = subparsers.add_parser("set-key", help="Set FIRMS API key")
    sk.add_argument("api_key", help="Your FIRMS API key")
    sk.set_defaults(func=cmd_set_key)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        args.func(args)
    except ValueError as e:
        print(f"Validation error: {e}")
        sys.exit(1)
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        sys.exit(130)

if __name__ == "__main__":
    main()
