# SLC Metadata Inspection Tools

Complete toolkit for extracting and viewing ALL metadata from Sentinel-1 SLC products, independent of data source.

## Quick Start

```bash
# 1. Extract full metadata (do this once)
docker compose run --rm isce2-insar python3 /workspace/extract_full_metadata.py

# 2. View formatted summary
./show_slc_metadata.sh

# 3. Check geographic coordinates
./check_geocoding.sh
```

## Tools Overview

### 1. `extract_full_metadata.py` - Complete Metadata Extraction

Extracts **ALL** metadata fields from ISCE2 XML files into structured JSON.

```bash
# Run inside Docker (has GDAL/Python dependencies)
docker compose run --rm isce2-insar python3 /workspace/extract_full_metadata.py

# Creates two files:
# - reference_full_metadata.json (122KB, 1579 fields)
# - secondary_full_metadata.json (122KB, 1579 fields)
```

**What it extracts:**
- Product identifiers (mission, orbit, datatake ID)
- Acquisition timing (start, stop, burst times)
- Orbit parameters (ascending node, orbit number)
- Sensor parameters (wavelength, PRF, pixel size)
- Geometry (range, azimuth, burst dimensions)
- Full burst metadata (10 bursts × ~150 fields)
- Processing parameters
- State vectors (orbit positions/velocities)

### 2. `show_slc_metadata.sh` - Human-Readable Summary

Displays key metadata in organized sections.

```bash
./show_slc_metadata.sh
```

**Shows:**
- ✓ Product SAFE filename breakdown
- ✓ Mission (S1A/S1B), mode (IW), product type (SLC)
- ✓ Acquisition dates and times
- ✓ Geographic coverage (from radar geometry grids)
- ✓ Orbit information
- ✓ Sensor parameters 
- ✓ Number of bursts and scene dimensions
- ✓ How to query the JSON files

### 3. `check_geocoding.sh` - Geographic Verification

Verifies that geocoded outputs match the actual SLC coverage.

```bash
./check_geocoding.sh
```

**Checks:**
1. Actual SLC geographic coverage (from lat/lon grids)
2. DEM file used for geocoding
3. Geocoded output coordinates
4. Whether they match (detects wrong DEM issues)

## Data Summary

Based on the inspection:

```
Reference SLC:  S1A_IW_SLC__1SDV_20210131T094602_..._036380_044503_40CB
Secondary SLC:  S1A_IW_SLC__1SDV_20210212T094602_..._036555_044B1A_A7D9

Mission:        Sentinel-1A
Dates:          2021-01-31 to 2021-02-12 (12-day baseline)
Location:       Venezuela/Guyana coast, South America
                Lat: 2.84° - 3.19° N
                Lon: 59.12° - 59.95° W
Orbit:          Absolute orbits 036380 → 036555
                Ascending pass
Bursts:         10 per SLC
Swath:          IW1 (processed)
Dimensions:     21,320 samples × 1,491 lines per burst
```

## Querying JSON Metadata

The JSON files contain **all** metadata in dot-notation keys.

### Common Queries

```bash
# View all available keys
jq 'keys' reference_full_metadata.json

# Get specific field
jq '.["instance.ascendingnodetime"]' reference_full_metadata.json
jq '.["instance.bursts.burst1.burststartutc"]' reference_full_metadata.json

# Search for keys containing a word
jq 'keys | .[] | select(contains("orbit"))' reference_full_metadata.json

# Get all burst start times
jq '[keys[] | select(contains("burststartutc"))] as $keys | 
    [$keys[] | {key: ., value: .[$keys[]]}]' reference_full_metadata.json

# Export selected fields to CSV
jq -r '[
    .["instance.ascendingnodetime"],
    .["instance.bursts.burst1.burststartutc"],
    .["instance.bursts.burst10.burststoputc"]
] | @csv' *_full_metadata.json

# Pretty print with color (if jq supports)
jq -C '.' reference_full_metadata.json | less -R

# Count metadata by category
jq 'keys | map(split(".")[1]) | group_by(.) | 
    map({key: .[0], count: length}) | from_entries' reference_full_metadata.json
```

### Key Categories in JSON

All keys follow pattern: `instance.[category].[subcategory].[field]`

```
instance.ascendingnodetime              # Orbit timing
instance.bursts.burst1.*                # Burst 1 metadata
instance.bursts.burst1.image.*          # Image dimensions
instance.bursts.burst1.orbit.*          # Orbit data
instance.bursts.burst1.doppler.*        # Doppler parameters
instance.bursts.burst2.*                # Burst 2 metadata
...                                     # Repeats for 10 bursts
```

## Integration with ASF Search Results

These tools are **independent** of ASF search - they read directly from:
1. ISCE2-processed XML files (`/mnt/data/tokyo_test/output/*/IW1.xml`)
2. Input configuration files (`input-files/reference.xml`)
3. GDAL metadata from radar geometry grids (`geom_reference/IW1/*.vrt`)

**Comparison:**

| Source | What it gives |
|--------|---------------|
| **ASF Search CSV** | Pre-processing metadata (what's available to download) |
| **These tools** | Post-processing metadata (what was actually processed by ISCE2) |

**Advantage:** These tools show:
- Exact bursts used in processing
- Actual geographic coverage (not just scene footprint)
- Processing-specific parameters
- Derived geometry (range, azimuth, orbit state vectors)

## Files Created

After running the tools:

```
.
├── check_geocoding.sh              # Geographic verification script
├── show_slc_metadata.sh            # Pretty summary display
├── extract_full_metadata.py        # Full extraction (run in Docker)
├── inspect_slc_metadata.py         # Alternative inspector
├── summarize_slc_metadata.py       # Python summary (less detailed)
├── reference_full_metadata.json    # All reference metadata (122KB)
└── secondary_full_metadata.json    # All secondary metadata (122KB)
```

## Example Use Cases

### 1. Build interferogram database
```bash
# Extract key fields to CSV
jq -r '[
    .["instance.ascendingnodetime"],
    .["instance.bursts.burst1.burststartutc"],
    "orbit:" + .["instance.bursts.burst1.orbit.orbit_source"]
] | @csv' *_full_metadata.json > interferogram_metadata.csv
```

### 2. Verify temporal baseline
```python
import json
from datetime import datetime

with open('reference_full_metadata.json') as f:
    ref = json.load(f)
with open('secondary_full_metadata.json') as f:
    sec = json.load(f)

ref_time = datetime.fromisoformat(ref['instance.ascendingnodetime'].replace(' ', 'T'))
sec_time = datetime.fromisoformat(sec['instance.ascendingnodetime'].replace(' ', 'T'))

baseline_days = (sec_time - ref_time).days
print(f"Temporal baseline: {baseline_days} days")
```

### 3. Export to database
```python
import json
import sqlite3

conn = sqlite3.connect('slc_metadata.db')
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS slc_products (
    name TEXT PRIMARY KEY,
    ascending_node TEXT,
    start_time TEXT,
    orbit_number TEXT,
    metadata_json TEXT
)''')

for slc in ['reference', 'secondary']:
    with open(f'{slc}_full_metadata.json') as f:
        data = json.load(f)
    
    cursor.execute('''INSERT OR REPLACE INTO slc_products VALUES (?, ?, ?, ?, ?)''',
        (slc, 
         data.get('instance.ascendingnodetime'),
         data.get('instance.bursts.burst1.burststartutc'),
         data.get('instance.bursts.burst1.orbit.orbit_source'),
         json.dumps(data)))

conn.commit()
```

## Troubleshooting

**"JSON files not found":**
```bash
# Extract them first:
docker compose run --rm isce2-insar python3 /workspace/extract_full_metadata.py
```

**"GDAL not available":**
```bash
# Run inside Docker container:
docker compose run --rm isce2-insar bash
cd /workspace
python3 extract_full_metadata.py
```

**"N/A" showing for many fields:**
- Check that IW1.xml exists: `ls -la /mnt/data/tokyo_test/output/*/IW1.xml`
- Verify JSON was created: `ls -lh *_full_metadata.json`
- Try re-running extraction

## Advanced: Custom Metadata Inspector

Create your own query:

```python
import json

with open('reference_full_metadata.json') as f:
    metadata = json.load(f)

# Find all fields related to azimuth
azimuth_fields = {k: v for k, v in metadata.items() if 'azimuth' in k.lower()}

# Find all burst-specific orbit data
for i in range(1, 11):  # 10 bursts
    orbit_source = metadata.get(f'instance.bursts.burst{i}.orbit.orbit_source')
    print(f"Burst {i}: {orbit_source}")

# Calculate average PRF across bursts (if exists)
prfs = [float(metadata.get(f'instance.bursts.burst{i}.prf', 0)) 
        for i in range(1, 11)]
if any(prfs):
    print(f"Average PRF: {sum(prfs)/len([p for p in prfs if p > 0]):.2f} Hz")
```

---

**Summary:** These tools give you complete, structured access to ALL metadata from your SLC products, independent of any external database or search service. Perfect for building custom workflows, databases, or automated processing pipelines.
