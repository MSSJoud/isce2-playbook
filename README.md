# InSAR Processing and Metadata Tools

Complete workflow for Sentinel-1 InSAR processing with ISCE2 and comprehensive metadata inspection tools.

## 🎯 Repository Overview

1. **Complete InSAR Processing Workflow** - From SLC download to unwrapped displacement
2. **Metadata Inspection Tools** - Extract and analyze ALL SLC/processing metadata
3. **Geographic Verification** - Validate geocoding correctness
4. **Comprehensive Documentation** - Step-by-step guides for every process

## 📋 Quick Start

### Prerequisites

- **Docker and Docker Compose** - See [INSTALLATION.md](INSTALLATION.md) for setup instructions
- ~30GB disk space for processing
- Access to Sentinel-1 data (Copernicus Dataspace or ASF)

> **New to Docker?** Follow the complete installation guide in [INSTALLATION.md](INSTALLATION.md) for step-by-step instructions for Linux, macOS, and Windows.

### Setup

```bash
# Clone this repository
git clone https://github.com/USERNAME/isce2-playbook.git
cd isce2-playbook

# Start Docker services
docker compose up -d

# Verify installation
docker compose run --rm isce2-insar topsApp.py --help
```

### Run Test Processing

```bash
# The repository includes a working test case (Venezuela coast, 2021)
# Reference: S1A_IW_SLC__1SDV_20210131T094602_..._036380_044503_40CB
# Secondary: S1A_IW_SLC__1SDV_20210212T094602_..._036555_044B1A_A7D9

# Use existing processed outputs or reprocess from scratch
# See: README_COMPLETE_WORKFLOW.md
```

## 📁 Repository Structure

```
isce2-playbook/
├── README.md                              # This file
├── README_COMPLETE_WORKFLOW.md            # Complete processing guide
├── docker-compose.yml                     # Docker services configuration
│
├── Documentation/
│   ├── ISCE2_COHERENCE_FILES.md          # Coherence file issues
│   ├── UNWRAPPING_GUIDE.md               # Phase unwrapping guide
│   ├── ATMOSPHERIC_CORRECTIONS.md         # Atmospheric processing
│   ├── HOW_TO_CHECK_GEOCODING.md         # Geographic verification
│   ├── METADATA_INSPECTION_GUIDE.md      # Metadata tools guide
│   ├── VISUALIZATION_GUI_GUIDE.md        # Visualization setup
│   └── DIRECTORY_MAPPING_EXPLAINED.md    # File organization
│
├── Scripts/
│   ├── check_geocoding.sh                # Verify geographic coordinates
│   ├── show_slc_metadata.sh              # Display SLC metadata
│   ├── extract_full_metadata.py          # Extract all metadata to JSON
│   ├── inspect_slc_metadata.py           # Alternative inspector
│   ├── summarize_slc_metadata.py         # Python summary tool
│   ├── run_unwrapping.sh                 # Phase unwrapping automation
│   └── monitor_download.sh               # Data download monitor
│
├── input-files/
│   ├── reference.xml                     # Reference SLC config
│   ├── secondary.xml                     # Secondary SLC config
│   ├── topsApp.xml                       # Basic processing config
│   └── topsApp_with_unwrap.xml          # With unwrapping config
│
├── Docker/
│   ├── isce2-insar/                      # ISCE2 processing container
│   ├── analyze-insar/                    # Analysis/visualization container
│   └── stac-search/                      # Data search container
│
└── Examples/
    └── visualizations/                    # Example output plots
```

## 🚀 Core Workflows

### 1. Process New Interferogram

See [`README_COMPLETE_WORKFLOW.md`](README_COMPLETE_WORKFLOW.md) for complete guide.

```bash
# 1. Download SLC data
# 2. Update input-files/reference.xml and secondary.xml
# 3. Run processing
docker compose run --rm isce2-insar topsApp.py input-files/topsApp.xml

# 4. Run unwrapping (optional)
./run_unwrapping.sh

# 5. Visualize results
docker compose up analyze-insar
# Open http://localhost:8501
```

### 2. Inspect SLC Metadata

See [`METADATA_INSPECTION_GUIDE.md`](METADATA_INSPECTION_GUIDE.md) for details.

```bash
# Extract full metadata (do once)
docker compose run --rm isce2-insar python3 /workspace/extract_full_metadata.py

# Display summary
./show_slc_metadata.sh

# Check geographic coverage
./check_geocoding.sh
```

### 3. Verify Processing

```bash
# Check processing logs
tail -f isce.log

# Verify geocoding
./check_geocoding.sh

# Check file sizes
du -sh merged/ geom_reference/

# Inspect outputs
gdalinfo merged/filt_topophase.unw.geo.vrt
```

## 📚 Documentation Index

| Document | Purpose |
|----------|---------|
| [`INSTALLATION.md`](INSTALLATION.md) | **START HERE** - Docker installation for Linux, macOS, Windows |
| [`README_COMPLETE_WORKFLOW.md`](README_COMPLETE_WORKFLOW.md) | Complete processing guide from SLC to unwrapped phase |
| [`METADATA_INSPECTION_GUIDE.md`](METADATA_INSPECTION_GUIDE.md) | Extract and query all SLC metadata |
| [`HOW_TO_CHECK_GEOCODING.md`](HOW_TO_CHECK_GEOCODING.md) | Verify geographic coordinates with GDAL |
| [`UNWRAPPING_GUIDE.md`](UNWRAPPING_GUIDE.md) | Phase unwrapping with SNAPHU |
| [`ISCE2_COHERENCE_FILES.md`](ISCE2_COHERENCE_FILES.md) | Troubleshoot coherence file issues |
| [`ATMOSPHERIC_CORRECTIONS.md`](ATMOSPHERIC_CORRECTIONS.md) | Atmospheric correction workflow |
| [`VISUALIZATION_GUI_GUIDE.md`](VISUALIZATION_GUI_GUIDE.md) | Web-based visualization setup |
| [`DIRECTORY_MAPPING_EXPLAINED.md`](DIRECTORY_MAPPING_EXPLAINED.md) | Understanding ISCE2 output structure |

## 🔧 Key Tools

### Metadata Inspection

```bash
# Get human-readable summary of both SLCs
./show_slc_metadata.sh

# Extract all 1,579 metadata fields to JSON
docker compose run --rm isce2-insar python3 /workspace/extract_full_metadata.py

# Query specific field
jq '.["instance.ascendingnodetime"]' reference_full_metadata.json

# Search for keys
jq 'keys | .[] | select(contains("orbit"))' reference_full_metadata.json
```

### Geographic Verification

```bash
# Check if geocoding matches actual SLC coverage
./check_geocoding.sh

# Quick coordinate check
gdalinfo merged/filt_topophase.flat.geo.vrt | grep "Upper Left\|Lower Right"

# Get bounds from radar geometry
gdalinfo -stats geom_reference/IW1/lat_03.rdr.vrt | grep "Min\|Max"
```

### Processing Monitoring

```bash
# Watch processing progress
tail -f isce.log | grep -i "progress\|completed\|error"

# Check disk usage
watch -n 5 'du -sh merged/ geom_reference/ fine_interferogram/'

# Monitor memory
docker stats isce2-insar
```

## 🐳 Docker Services

Three services defined in `docker-compose.yml`:

1. **isce2-insar** - ISCE2 processing (Python 3.8, GDAL, SNAPHU)
2. **analyze-insar** - Visualization (Streamlit, matplotlib, Jupyter)
3. **stac-search** - Data discovery (STAC API client)

```bash
# Start all services
docker compose up -d

# Run one-off command
docker compose run --rm isce2-insar <command>

# Enter container interactively
docker compose run --rm isce2-insar bash

# Stop all services
docker compose down
```

## 📊 Current Test Case

The repository includes outputs from a processed interferogram:

- **Location**: Venezuela/Guyana coast, South America
- **Coordinates**: 2.84-3.19°N, 59.12-59.95°W
- **Reference Date**: 2021-01-31
- **Secondary Date**: 2021-02-12
- **Temporal Baseline**: 12 days
- **Orbit**: Ascending, path/track 35
- **Swath**: IW1
- **Processing**: Complete (wrapped + unwrapped)
- **Coherence**: 0.657 average
- **Displacement Range**: -20.95 to +10.48 cm

### Available Outputs

See `merged/` directory:
- `filt_topophase.flat` - Wrapped phase (radar)
- `filt_topophase.flat.geo` - Wrapped phase (geocoded)
- `filt_topophase.unw` - Unwrapped phase (radar)
- `filt_topophase.unw.geo` - Unwrapped phase (geocoded)
- `phsig.cor` - Coherence
- `dem.crop` - DEM subset

## 🔬 Scientific Outputs

### Quality Metrics
- Mean coherence: 0.657
- Connected component ratio: 99.8%
- Atmospheric correction: Applied (tropospheric delay)
- Unwrapping success: Yes (SNAPHU MCF)

### Data Products
All outputs available in radar and geographic coordinates:
- Phase (wrapped and unwrapped)
- Coherence
- Line-of-sight geometry
- Digital elevation model
- Amplitude images

## 🤝 Contributing / Continuing Work

### To Process New Data

1. Download SLC pairs (Copernicus Dataspace or ASF)
2. Update `input-files/reference.xml` and `secondary.xml` with SAFE paths
3. Modify `input-files/topsApp.xml` for your parameters
4. Run: `docker compose run --rm isce2-insar topsApp.py input-files/topsApp.xml`
5. Inspect metadata: `./show_slc_metadata.sh`
6. Verify geocoding: `./check_geocoding.sh`

### To Modify Processing

Edit `input-files/topsApp.xml`:
- `<property name="swaths">[1,2,3]</property>` - Process multiple swaths
- `<property name="azimuth looks">5</property>` - Adjust multilooking
- `<property name="do unwrap">True</property>` - Enable unwrapping
- See ISCE2 documentation for all options

### To Analyze Results

```bash
# Start Jupyter/Streamlit
docker compose up analyze-insar

# Or use Python directly
docker compose run --rm analyze-insar python3
>>> import h5py, matplotlib
>>> # Your analysis code
```

## 🐛 Troubleshooting

### Common Issues

**"No module named 'osgeo'"**
```bash
# Run Python scripts inside Docker:
docker compose run --rm isce2-insar python3 /workspace/your_script.py
```

**"Memory error during processing"**
```bash
# Increase Docker memory limit in Docker Desktop settings
# Or reduce multilooking: azimuth looks=3, range looks=9
```

**"Geocoding placed data at wrong location"**
```bash
# Check DEM tile:
ls -la demLat*.dem.wgs84
./check_geocoding.sh

# Download correct DEM or use auto:
# <property name="demFilename">auto</property>
```

**"topophase.cor not found"**
```bash
# ISCE2 creates phsig.cor (not topophase.cor)
# See: ISCE2_COHERENCE_FILES.md
```

### Getting Help

1. Check relevant `.md` documentation file
2. Review `isce.log` for errors
3. Run verification: `./check_geocoding.sh`
4. Inspect metadata: `./show_slc_metadata.sh`
5. Check ISCE2 logs: `tail -100 isce.log`

## 📧 Sharing Results

### Export Metadata

```bash
# JSON format (all fields)
cp reference_full_metadata.json secondary_full_metadata.json results/

# CSV format (selected fields)
jq -r '[.["instance.ascendingnodetime"], .["instance.bursts.burst1.burststartutc"]] | @csv' *.json > metadata.csv

# Human-readable report
./show_slc_metadata.sh > slc_metadata_report.txt
```

### Share Visualizations

```bash
# Export plots
cp 0*_*.png results/

# Generate report
docker compose run --rm analyze-insar python3 /workspace/generate_report.py
```

### Package for Colleagues

```bash
# Create archive (without large data files)
tar -czf isce2-playbook-$(date +%Y%m%d).tar.gz \
    *.md *.sh *.py *.yml input-files/ Docker/ \
    --exclude='*.SAFE' --exclude='*.h5' --exclude='*.dem.wgs84'
```

## 🔗 External Resources

- **ISCE2 Documentation**: https://github.com/isce-framework/isce2
- **Sentinel-1 Data**: https://dataspace.copernicus.eu
- **ASF Data Search**: https://search.asf.alaska.edu
- **GDAL Documentation**: https://gdal.org
- **SNAPHU Manual**: https://web.stanford.edu/group/radar/softwareandlinks/sw/snaphu/

## 📄 License

[Add your license here]

## ✍️ Authors

[Add authors/contributors]

## 🙏 Acknowledgments

- ISCE2: NASA/JPL InSAR processing software
- Sentinel-1: ESA Copernicus Programme
- ASF DAAC: Alaska Satellite Facility

---

**Last Updated**: March 2026  
**Processing Version**: ISCE2 v2.6.3  
**Test Case**: Venezuela coast 2021-01-31/2021-02-12
