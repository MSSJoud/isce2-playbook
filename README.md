# isce2-insar

Please review this before processing to confirm whether it works regarding the credentials: test.py
  
## What This Project Does
 
This is an **InSAR (Interferometric Synthetic Aperture Radar) processing pipeline** for **Sentinel-1** satellite data. It uses **ISCE2** to compute interferograms (phase difference maps) that can detect ground surface deformation. The project is focused on the **Tokyo, Japan** area.
 
The pipeline has 3 Docker services working together.
 
## Architecture: 3 Docker Services
 
### 1. `stac-search` — Data Discovery & Download
 
Searches the Copernicus STAC API for Sentinel-1 SLC data, downloads SAR scenes and orbit files.
 
| Script | Purpose | Command |
|---|---|---|
| `search_insar_pair.py` | Find matching SAR pairs | `python src/search_insar_pair.py --start_date 2024-08-01 --end_date 2024-09-01` |
| `download_insar_pair_safe.py` | Download SAR SAFE archives | `python src/download_insar_pair_safe.py --first_id <ID> --second_id <ID>` |
| `download_orbit.py` | Download precise orbit files | `python src/download_orbit.py` |
 
### 2. `isce2-insar` — Core SAR Processing (Where ISCE2 is used)
 
Uses the official `isce/isce2:latest` Docker image. **ISCE2** is used here via `topsApp.py`, its TOPS (Terrain Observation by Progressive Scans) processing application. It:
 
- Ingests Sentinel-1 SLC data from SAFE archives
- Applies orbit corrections
- Co-registers reference and secondary images
- Computes the interferogram (phase difference)
- Filters the interferogram
- Phase unwrapping is currently **disabled** in `topsApp.xml`
 
Configuration is in 3 XML files under `input-files/`:
 
- `topsApp.xml` — Main ISCE2 config (sensor, swaths, unwrapping toggle)
- `reference.xml` — Reference scene path + orbit directory
- `secondary.xml` — Secondary scene path + orbit directory
 
### 3. `analyze-insar` — Visualization
 
Uses GDAL + matplotlib to plot amplitude and phase images from the ISCE2 output (`plot.py`).
 
## Data Flow
 
```
Copernicus STAC API
       │
       ▼
  stac-search  ──→  data/stac/insar.csv
       │              data/safe/unzip/*.SAFE
       │              data/orbit/*.EOF
       ▼
  isce2-insar  ──→  output/merged/filt_topophase.flat.vrt
  (topsApp.py)       output/reference/  output/secondary/
       │
       ▼
 analyze-insar ──→  output/filt_topophase_flat.png
   (plot.py)
```
 
## How to Run (Step by Step)
 
### Prerequisites
 
- Docker & Docker Compose installed
- A [Copernicus Dataspace](https://dataspace.copernicus.eu/) account (for downloading Sentinel-1 data)
 
### Step 0: Set credentials & build
 
```bash
export COPERNICUS_USER=<your_username>
export COPERNICUS_PASSWORD=<your_password>
 
docker compose build
```
 
### Step 1: Search for InSAR pairs
 
```bash
docker compose run stac-search python src/search_insar_pair.py \
  --start_date 2024-08-01 --end_date 2024-09-01
```
 
Outputs a CSV at `data/stac/insar.csv` with paired scene IDs.
 
### Step 2: Download SAR data
 
```bash
docker compose run stac-search python src/download_insar_pair_safe.py \
  --first_id <REFERENCE_ID> --second_id <SECONDARY_ID>
```
 
Downloads to `data/safe/zip/` and unzips to `data/safe/unzip/`.
 
### Step 3: Download orbit files
 
```bash
docker compose run stac-search python src/download_orbit.py
```
 
Downloads to `data/orbit/`.
 
### Step 4: Run ISCE2 processing
 
```bash
docker compose run isce2-insar bash
```
 
Inside the container at `/workspace`:
 
```bash
topsApp.py input-files/topsApp.xml
```
 
The two `ENV` lines in the Dockerfile are what make this work:
 
```dockerfile
ENV ISCE_HOME=/usr/lib/python3.8/dist-packages/isce/
ENV PATH=$ISCE_HOME/applications:$PATH
```
 
- `ISCE_HOME` tells ISCE2 where its Python packages live inside the `isce/isce2:latest` base image.
- The `PATH` addition puts `topsApp.py` (and other ISCE2 scripts) on your PATH so you can call them directly.
 
These do **not** conflict with the volume mount (`./:/workspace`). The mount gives you your project files at `/workspace`, and the ENV lines make the ISCE2 tools callable. They work together.
 
You can verify `topsApp.py` is available with:
 
```bash
which topsApp.py
# /usr/lib/python3.8/dist-packages/isce/applications/topsApp.py
```
 
**Before running** — make sure the data exists:
 
- SAR data in `data/safe/unzip/` (the `.SAFE` directories referenced in `reference.xml` and `secondary.xml`)
- Orbit files in `data/orbit/`
 
If those directories are empty, `topsApp.py` will fail. Run the download steps (Steps 1–3) first.
 
This generates interferometric products in `output/`.
 
### Step 5: Visualize results
 
```bash
docker compose run analyze-insar python src/plot.py
```
 
Generates `output/filt_topophase_flat.png` showing amplitude + phase.
 
## Key Configuration Notes
 
- **Area of interest**: Tokyo `[139.41°E, 35.49°N → 140.06°E, 35.97°N]` (hardcoded in `stac-search/src/settings.py`)
- **Example scenes**: 12-day temporal baseline (Aug 4 → Aug 16, 2024)
- **All 3 IW swaths** are processed
- **Phase unwrapping** is disabled — you can enable it by uncommenting these lines in `input-files/topsApp.xml`:
 
  ```xml
  <property name="do unwrap">True</property>
  <property name="unwrapper name">snaphu_mcf</property>
  ```
 
- To change the target area, edit the `BBOX` in `stac-search/src/settings.py`
- To use different scenes, update `reference.xml` and `secondary.xml` with the correct SAFE file paths
 
## Project Structure
 
```
.
├── README.md
├── docker-compose.yml
├── isce2-insar/
│   └── Dockerfile                     # ISCE2 environment (isce/isce2:latest)
├── stac-search/
│   ├── Dockerfile                     # Python 3.11 environment
│   ├── requirements.txt
│   └── src/
│       ├── search_insar_pair.py       # STAC search for SAR pairs
│       ├── download_insar_pair_safe.py # Download SAR data
│       ├── download_orbit.py          # Download orbit files
│       ├── download_utils.py          # Download utilities & auth
│       └── settings.py                # Configuration & paths
├── analyze-insar/
│   ├── Dockerfile                     # Python 3.11 + GDAL environment
│   ├── requirements.txt
│   └── src/
│       ├── plot.py                    # Visualization of results
│       └── settings.py                # Configuration
├── input-files/
│   ├── topsApp.xml                    # ISCE2 TOPS processing config
│   ├── reference.xml                  # Reference scene config
│   └── secondary.xml                  # Secondary scene config
├── output/                            # Processing outputs
└── data/
    ├── orbit/                         # Orbital ephemeris files
    ├── safe/
    │   ├── zip/                       # Downloaded SAR data (compressed)
    │   └── unzip/                     # Uncompressed SAR data
    └── stac/                          # STAC metadata files
```
