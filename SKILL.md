---
description: 'Download MODIS and VIIRS active fire hotspot data from NASA FIRMS.

  Supports filtering by date range, bounding box, and instrument.

  Outputs CSV and GeoJSON formats with near-real-time and standard products.

  '
name: fire-hotspot-download
---

# Fire Hotspot Data Download

Download active fire hotspot data from NASA FIRMS (Fire Information for Resource Management System).

## Overview

NASA FIRMS distributes active fire data from MODIS and VIIRS instruments in near-real-time.
This data is essential for fire monitoring, air quality studies, and land management.

## Instruments

| Instrument | Product | Satellite | Resolution |
|------------|---------|-----------|------------|
| MODIS | MCD14DL | Terra+Aqua | 1km |
| VIIRS (NRT) | VNP14IMGTDL_NRT | Suomi-NPP | 375m |
| VIIRS (Standard) | VNP14IMGT | Suomi-NPP | 375m |
| VIIRS (NOAA-20) | VJ114IMGML | NOAA-20 (JPSS-1) | 375m |

## Features

- **MODIS and VIIRS**: both instruments supported
- **Near-real-time and standard products**: NRT for monitoring, standard for research
- **Date range and bbox filtering**: precise spatial-temporal queries
- **CSV and GeoJSON output**: tabular and geospatial formats
- **API key management**: secure key storage in config file
- **Progress tracking**: download progress with tqdm

## Credentials

This skill needs a **NASA FIRMS MAP_KEY** (free, issued per email).

Resolution order:

1. FIRMS_MAP_KEY env var
2. ~/.netrc entry for machine firms.modaps.eosdis.nasa.gov (login = key)
3. **Default** (geoskill-core credentials.py): empty — user must register

Get a free key: https://firms.modaps.eosdis.nasa.gov/api/map_key/

## API Key

A free API key is required. Get one at: https://firms.modaps.eosdis.nasa.gov/api/map_key/

```bash
# Set your API key
python scripts\fire_hotspot_download.py set-key YOUR_API_KEY

# Or set via environment variable
export FIRMS_API_KEY="your_api_key"
```

## Credentials

This skill needs a **NASA FIRMS MAP_KEY** (free, issued per email).

Resolution order:

1. FIRMS_MAP_KEY env var
2. ~/.netrc entry for machine firms.modaps.eosdis.nasa.gov (login = key)
3. **Default** (geoskill-core credentials.py): empty — user must register

Get a free key: https://firms.modaps.eosdis.nasa.gov/api/map_key/

## Usage

```bash
# Download fire hotspots for China (last 7 days)
python scripts\fire_hotspot_download.py download \
  --instrument VIIRS --product NRT \
  --bbox 73 18 135 54 \
  --start 2024-01-01 --end 2024-01-07 \
  --output china_fires.csv

# Download MODIS fires as GeoJSON
python scripts\fire_hotspot_download.py download \
  --instrument MODIS --product STANDARD \
  --bbox 116.0 39.5 116.8 40.2 \
  --start 2024-03-01 --end 2024-03-31 \
  --output beijing_fires.geojson --format geojson

# Download both instruments
python scripts\fire_hotspot_download.py download \
  --instrument BOTH --product NRT \
  --bbox -125 25 -66 50 \
  --start 2024-06-01 --end 2024-06-07 \
  --output us_fires.csv

# List available instruments
python scripts\fire_hotspot_download.py list-instruments
```

## Parameters

- `--instrument`: MODIS, VIIRS, or BOTH
- `--product`: NRT (near-real-time) or STANDARD
- `--bbox`: Bounding box as `west south east north`
- `--start/--end`: Date range (YYYY-MM-DD, max 7 days for NRT)
- `--output`: Output file path
- `--format`: `csv` or `geojson`
- `--confidence`: Minimum confidence threshold (0-100)

## Data Fields

| Field | Description |
|-------|-------------|
| latitude | Latitude of fire pixel |
| longitude | Longitude of fire pixel |
| brightness | Brightness temperature (K) |
| scan | Scan pixel size |
| track | Track pixel size |
| acq_date | Acquisition date |
| acq_time | Acquisition time (HHMM) |
| satellite | Satellite name |
| confidence | Detection confidence (0-100) |
| version | Product version |
| bright_t31 | Channel 31 brightness (K) |
| frp | Fire Radiative Power (MW) |
| daynight | Day or Night |

## Installation

```bash
# Install dependencies
pip install requests>=2.28.0 tqdm

# Or install from requirements.txt
pip install -r scripts/requirements.txt
```

## Data Source

- **API**: https://firms.modaps.eosdis.nasa.gov/api/
- **Documentation**: https://firms.modaps.eosdis.nasa.gov/api/
- **License**: Public Domain (NASA open data)
- **Rate Limit**: No strict limit; recommended max 10 requests/minute
- **CRS**: WGS84 (EPSG:4326)

### Citation Format

```bibtex
@article{davies2009firms,
  title={Fire Information for Resource Management System (FIRS): archiving and distributing MODIS active fire data},
  author={Davies, D.K. and others},
  journal={IEEE Transactions on Geoscience and Remote Sensing},
  year={2009},
  doi={10.1109/TGRS.2009.2014067}
}
```

### NRT vs Standard Quality

| Product | Latency | Accuracy | Use Case |
|---------|---------|----------|----------|
| NRT (Near-Real-Time) | ~3 hours | Lower (automated QA) | Active fire monitoring, rapid response |
| Standard | ~2 weeks | Higher (manual QA) | Research, long-term analysis |

### Confidence Threshold

The `confidence` field ranges from 0–100%:
- **>75%**: High confidence — reliable fire detection
- **50–75%**: Medium confidence — possible fire, verify with other sources
- **<50%**: Low confidence — likely false positive

### VIIRS Satellites

| Satellite | Instrument ID | Product |
|-----------|--------------|---------|
| Suomi-NPP | VNP14IMGTDL_NRT / VNP14IMGT | 375m resolution |
| NOAA-20 (JPSS-1) | VJ114IMGML | 375m resolution |

Both provide similar spatial resolution; NOAA-20 offers improved nighttime detection.

### Long-Period Download Guidance

The API supports max 7 days per NRT request. For longer periods:

```bash
# Loop over weeks
for week in {0..3}; do
  start=$(date -d "2024-01-01 +${week} weeks" +%Y-%m-%d)
  end=$(date -d "2024-01-01 +${week} weeks + 6 days" +%Y-%m-%d)
  python scripts\fire_hotspot_download.py download \
    --instrument VIIRS --product NRT \
    --bbox 73 18 135 54 \
    --start $start --end $end \
    --output "fires_week${week}.csv"
done
```

### Global Download

For global-scale analysis, split into regional tiles and download separately to avoid timeout:
- Americas, Europe-Africa, Asia-Pacific (4–6 regions recommended)
- Merge results after download.

### API Key Storage

- Keys set via `set-key` are stored in the local config file.
- Environment variable `FIRMS_API_KEY` overrides stored key.
- Config location: same directory as the script.

### Visualization

- **Point maps**: Load GeoJSON in QGIS, color by `confidence` (red = high, yellow = medium).
- **Time series**: Aggregate daily fire counts, plot as bar chart.
- **Heatmaps**: Use QGIS Heatmap renderer or `datashader` in Python.

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `ConnectionError` | Network issue or API down | Check internet connection, retry in 1 minute |
| `HTTP 429` | Rate limit exceeded | Wait 60 seconds before retrying |
| `HTTP 404` | Invalid parameters or date range | Check parameter names and date format |
| `ValueError: bbox` | Invalid bounding box | Ensure format is `west,south,east,north` |
| Empty output | No data for query region/time | Try different date range or check coordinates |
| `ModuleNotFoundError` | Missing dependency | Run `pip install requests tqdm` |
| `403 Forbidden` | Invalid API key | Re-run `set-key` with valid key |

---

## Advanced Usage

### Automated Weekly Download
```bash
# Download last 7 days of fire data for China
python scripts\fire_hotspot_download.py download   --bbox 73 18 135 54 --instrument BOTH   --start $(date -d '7 days ago' +%Y-%m-%d)   --end $(date +%Y-%m-%d)   --output fires_weekly.csv
```

### CI/CD Integration (GitHub Actions)
```yaml
# .github/workflows/update-fires.yml
name: Fire Hotspot Monitor
on:
  schedule:
    - cron: '0 8 * * *'  # Daily at 08:00 UTC
jobs:
  download:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install requests
      - env:
          FIRMS_API_KEY: ${{ secrets.FIRMS_API_KEY }}
        run: |
          python scripts\fire_hotspot_download.py download \
            --bbox 73 18 135 54 --instrument BOTH \
            --start $(date -d '3 days ago' +%Y-%m-%d) \
            --end $(date +%Y-%m-%d) \
            --output data/fires_latest.csv
```

### PostgreSQL/PostGIS Import
```bash
python scripts\fire_hotspot_download.py download   --bbox 73 18 135 54 --start 2024-01-01 --end 2024-01-31   --output fires.csv

psql -d gis_db -c "\COPY fire_hotspots(lat, lon, confidence, acq_date, instrument) FROM 'fires.csv' CSV HEADER"
```

### Performance Tips
- NRT API accepts max 7-day windows; split longer ranges into weekly chunks
- Use `--instrument VIIRS` for higher resolution (375m vs 1km)
- Add `sleep 1` between weekly requests for multi-week batches

---

## 中文说明

从 NASA FIRMS（资源管理火灾信息系统）下载 MODIS 和 VIIRS 活跃火点数据。

### 传感器

| 传感器 | 产品 | 卫星 | 分辨率 |
|--------|------|------|--------|
| MODIS | MCD14DL | Terra+Aqua | 1km |
| VIIRS (近实时) | VNP14IMGTDL_NRT | Suomi-NPP | 375m |
| VIIRS (标准) | VNP14IMGT | Suomi-NPP | 375m |
| VIIRS (NOAA-20) | VJ114IMGML | NOAA-20 (JPSS-1) | 375m |

### 核心功能

- **MODIS 和 VIIRS**：支持两种传感器
- **近实时和标准产品**：近实时用于监测，标准产品用于科研
- **日期范围和区域过滤**：精确的时空查询
- **CSV 和 GeoJSON 输出**：表格和地理空间格式
- **API 密钥管理**：安全存储在配置文件中
- **进度跟踪**：使用 tqdm 显示下载进度

### API 密钥

需要免费 API 密钥。获取地址：https://firms.modaps.eosdis.nasa.gov/api/map_key/

```bash
# 设置 API 密钥
python scripts\fire_hotspot_download.py set-key YOUR_API_KEY

# 或通过环境变量
set FIRMS_API_KEY=your_api_key
```

### 使用示例

```bash
# 下载中国区域火点（最近7天）
python scripts\fire_hotspot_download.py download \
  --instrument VIIRS --product NRT \
  --bbox 73 18 135 54 \
  --start 2024-01-01 --end 2024-01-07 \
  --output china_fires.csv

# 下载 MODIS 火点为 GeoJSON
python scripts\fire_hotspot_download.py download \
  --instrument MODIS --product STANDARD \
  --bbox 116.0 39.5 116.8 40.2 \
  --start 2024-03-01 --end 2024-03-31 \
  --output beijing_fires.geojson --format geojson

# 下载两种传感器数据
python scripts\fire_hotspot_download.py download \
  --instrument BOTH --product NRT \
  --bbox -125 25 -66 50 \
  --start 2024-06-01 --end 2024-06-07 \
  --output us_fires.csv

# 列出可用传感器
python scripts\fire_hotspot_download.py list-instruments
```

### 数据字段

| 字段 | 描述 |
|------|------|
| latitude | 火点纬度 |
| longitude | 火点经度 |
| brightness | 亮温 (K) |
| scan | 扫描像元大小 |
| track | 轨道像元大小 |
| acq_date | 获取日期 |
| acq_time | 获取时间 (HHMM) |
| satellite | 卫星名称 |
| confidence | 检测置信度 (0-100) |
| version | 产品版本 |
| bright_t31 | 31通道亮温 (K) |
| frp | 火辐射功率 (MW) |
| daynight | 白天或夜间 |

### 数据来源

- **API**: https://firms.modaps.eosdis.nasa.gov/api/
- **文档**: https://firms.modaps.eosdis.nasa.gov/api/
- **许可证**: 公共领域（NASA 开放数据）
- **引用**: Davies, D.K., et al., 2009. Fire Information for Resource Management System (FIRS): archiving and distributing MODIS active fire data. IEEE Transactions on Geoscience and Remote Sensing.
