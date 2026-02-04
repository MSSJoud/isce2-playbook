import os
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).parents[2]

DATA_DIR = ROOT_DIR / "data"
DATA_ORBIT_DIR = DATA_DIR / "orbit"
DATA_SAFE_DIR = DATA_DIR / "safe"
DATA_SAFE_ZIP_DIR = DATA_SAFE_DIR / "zip"
DATA_SAFE_UNZIP_DIR = DATA_SAFE_DIR / "unzip"
DATA_STAC_DIR = DATA_DIR / "stac"


INPUT_FILES_DIR = ROOT_DIR / "input-files"

OUTPUT_DIR = ROOT_DIR / "output"

STAC_API_URL = "https://catalogue.dataspace.copernicus.eu/stac"  # https://documentation.dataspace.copernicus.eu/APIs/STAC.html
COLLECTION = "SENTINEL-1"
USERNAME = os.getenv("COPERNICUS_USER")
PASSWORD = os.getenv("COPERNICUS_PASSWORD")
BBOX = [139.4099, 35.4868, 140.0562, 35.9675]  # 東京

INSAR_CSV_PATH = DATA_STAC_DIR / "insar.csv"
