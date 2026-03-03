import os
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).parents[2]

# Use /mnt/data/tokyo_test as the root data directory
DATA_ROOT = Path("/mnt/data/tokyo_test")
DATA_DIR = DATA_ROOT / "data"
DATA_ORBIT_DIR = DATA_DIR / "orbit"
DATA_SAFE_DIR = DATA_DIR / "safe"
DATA_SAFE_ZIP_DIR = DATA_SAFE_DIR / "zip"
DATA_SAFE_UNZIP_DIR = DATA_SAFE_DIR / "unzip"
DATA_STAC_DIR = DATA_DIR / "stac"


INPUT_FILES_DIR = ROOT_DIR / "input-files"

OUTPUT_DIR = DATA_ROOT / "output"

STAC_API_URL = "https://catalogue.dataspace.copernicus.eu/stac"  # https://documentation.dataspace.copernicus.eu/APIs/STAC.html
COLLECTION = "sentinel-1-slc"
USERNAME = os.getenv("COPERNICUS_USER")
PASSWORD = os.getenv("COPERNICUS_PASSWORD")
#BBOX = [139.4099, 35.4868, 140.0562, 35.9675]  # 東京
BBOX = [-59.5938, 2.5704, -59.3955, 2.7478]
INSAR_CSV_PATH = DATA_STAC_DIR / "insar.csv"
