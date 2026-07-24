# Fire Hotspot Data Download (NASA FIRMS)

## English

Download MODIS and VIIRS active fire hotspot data from NASA FIRMS.

### Installation

**ClawHub:**
```bash
clawhub install fire-hotspot-download
```

**Claude Code / skills.sh:**
```bash
claude skills install fire-hotspot-download
```

**Manual:**
```bash
git clone <repo-url> fire-hotspot-download
cd fire-hotspot-download
pip install requests tqdm
```

### Quick Start

```bash
# Get your free API key
# Visit: https://firms.modaps.eosdis.nasa.gov/api/map_key/

# Set your API key
python scripts/fire_hotspot_download.py set-key YOUR_API_KEY

# Download fire hotspots for China
python scripts/fire_hotspot_download.py download \
  --instrument VIIRS --product NRT \
  --bbox 73 18 135 54 \
  --start 2024-01-01 --end 2024-01-07 \
  --output china_fires.csv

# List available instruments
python scripts/fire_hotspot_download.py list-instruments
```

### API Key

A free API key is required. Get one at: https://firms.modaps.eosdis.nasa.gov/api/map_key/

### Data Source

- **API**: https://firms.modaps.eosdis.nasa.gov/api/
- **License**: Public Domain (NASA open data)
- **Citation**: Davies, D.K., et al., 2009. Fire Information for Resource Management System (FIRS).

---

## 中文

从 NASA FIRMS 下载 MODIS 和 VIIRS 活跃火点数据。

### 安装

**ClawHub:**
```bash
clawhub install fire-hotspot-download
```

**Claude Code / skills.sh:**
```bash
claude skills install fire-hotspot-download
```

**手动安装:**
```bash
git clone <repo-url> fire-hotspot-download
cd fire-hotspot-download
pip install requests tqdm
```

### 快速开始

```bash
# 获取免费 API 密钥
# 访问: https://firms.modaps.eosdis.nasa.gov/api/map_key/

# 设置 API 密钥
python scripts/fire_hotspot_download.py set-key YOUR_API_KEY

# 下载中国区域火点
python scripts/fire_hotspot_download.py download \
  --instrument VIIRS --product NRT \
  --bbox 73 18 135 54 \
  --start 2024-01-01 --end 2024-01-07 \
  --output china_fires.csv

# 列出可用传感器
python scripts/fire_hotspot_download.py list-instruments
```

### API 密钥

需要免费 API 密钥。获取地址：https://firms.modaps.eosdis.nasa.gov/api/map_key/

### 数据来源

- **API**: https://firms.modaps.eosdis.nasa.gov/api/
- **许可证**: 公共领域（NASA 开放数据）
- **引用**: Davies, D.K., et al., 2009. Fire Information for Resource Management System (FIRS).
