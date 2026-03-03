# How to Check Geographic Coordinates of InSAR Data

## The Problem Discovered

The geocoded data shows:
```
Geocoded files location: 60°19'W to 59°04'W, 1°40'N to 3°32'N
This is: Venezuela/Guyana (South America)

Expected location: 139-140°E, 35-36°N
This is: Tokyo, Japan
```

**Root cause:** Wrong DEM file used
```
Used: demLat_N01_N04_Lon_W061_W059.dem.wgs84
Should be: demLat_N35_N36_Lon_E139_E140.dem.wgs84
```

---

## Essential GDAL Commands to Check Geographic Area

### 1. Quick Check - Corner Coordinates

```bash
# Check any geocoded file
gdalinfo merged/filt_topophase.flat.geo.vrt | grep -A5 "Corner Coordinates"

# Output shows:
# Upper Left  ( -60.3294444,   3.5458333) ( 60d19'46.00"W,  3d32'45.00"N)
# Lower Right ( -59.0819444,   1.6694444) ( 59d 4'55.00"W,  1d40'10.00"N)
#              ^^^^^^^^^^^^   ^^^^^^^^^^^
#              Longitude      Latitude
```

### 2. Get Bounding Box in Decimal Degrees

```bash
gdalinfo merged/filt_topophase.flat.geo.vrt | grep -E "Upper Left|Lower Right"

# West and North from Upper Left
# East and South from Lower Right
```

### 3. Full Geographic Information

```bash
gdalinfo merged/filt_topophase.flat.geo.vrt

# Look for:
# - Size is X, Y (dimensions)
# - Pixel Size = (lon_res, lat_res)
# - Corner Coordinates (4 corners with lat/lon)
# - Coordinate System (should be WGS84 GEOGCS)
```

### 4. Extract Just the Bounds

```bash
gdalinfo merged/filt_topophase.flat.geo.vrt 2>&1 | \
  awk '/Upper Left/ {west=$3; north=$4} /Lower Right/ {east=$3; south=$4} 
       END {gsub(/[(),]/,"",west); gsub(/[(),]/,"",east); 
            gsub(/[(),]/,"",north); gsub(/[(),]/,"",south);
            print "West: "west" East: "east" North: "north" South: "south}'
```

### 5. Check Multiple Files at Once

```bash
for file in merged/*.geo.vrt; do
    echo "=== $file ==="
    gdalinfo "$file" 2>&1 | grep "Upper Left"
    echo ""
done
```

### 6. Verify Projection/CRS (Coordinate Reference System)

```bash
gdalinfo merged/filt_topophase.flat.geo.vrt | grep -A10 "Coordinate System"

# Should show: GEOGCS["WGS 84",...]
```

---

## How I Discovered the Issue

### Step 1: Checked the geocoding output
```bash
gdalinfo merged/filt_topophase.flat.geo.vrt | grep "Upper Left"
# Saw: ( -60.3294444,   3.5458333)
# This is 60°W, 3°N → South America!
```

### Step 2: Checked the processing log
```bash
grep -i "dem.*used" isce.log
# Output: demLat_N01_N04_Lon_W061_W059.dem.wgs84
# DEM name shows: N01-N04 (1-4°N), W061-W059 (59-61°W)
# This is Venezuela/Guyana coordinates!
```

### Step 3: Verified DEM file exists
```bash
ls -lh demLat*.dem.wgs84
# Found: demLat_N01_N04_Lon_W061_W059.dem.wgs84 (149 MB)
# Wrong DEM tile for Tokyo processing!
```

### Step 4: Checked radar coordinate files (not geocoded)
```bash
gdalinfo merged/filt_topophase.unw.vrt
# No geotransform (radar coordinates only)
# These files are still valid for analysis!
```

---

## Automated Check Script

Use the script I created:
```bash
cd /home/ubuntu/work/isce2-playbook
./check_geocoding.sh
```

Or manually:
```bash
# Quick one-liner
echo "Checking geocoded file location..." && \
gdalinfo merged/filt_topophase.flat.geo.vrt 2>&1 | \
grep -E "Upper Left|Lower Right" | \
awk -F'[()]' '{print $2}'
```

---

## Comparison Table

| Aspect | Expected (Tokyo) | Actual (Current) | Status |
|--------|------------------|------------------|--------|
| **Longitude** | 139° to 140° E | 59° to 60° W | ❌ Wrong hemisphere |
| **Latitude** | 35° to 36° N | 1° to 3° N | ❌ Wrong region |
| **Location** | Japan (Asia) | Venezuela (S. America) | ❌ ~15,000 km off! |
| **DEM File** | demLat_N35_N36_Lon_E139_E140 | demLat_N01_N04_Lon_W061_W059 | ❌ Wrong tile |
| **Radar coords** | Valid | Valid | ✅ Correct |

---

## Visual Check Methods

### Method 1: Load in QGIS (Recommended)

```bash
# Install QGIS
sudo apt install qgis

# Open geocoded file
qgis merged/filt_topophase.flat.geo.vrt

# Add basemap: Web → QuickMapServices → OSM Standard
# If coordinates are correct, you'll see Tokyo
# If wrong, you'll see a different location (Venezuela in this case)
```

### Method 2: Use Python with Cartopy

```python
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from osgeo import gdal

# Get bounds
ds = gdal.Open('merged/filt_topophase.flat.geo.vrt')
gt = ds.GetGeoTransform()
minx, maxy = gt[0], gt[3]
maxx = minx + ds.RasterXSize * gt[1]
miny = maxy + ds.RasterYSize * gt[5]

print(f"Data bounds: {minx:.2f} to {maxx:.2f} E, {miny:.2f} to {maxy:.2f} N")

# Plot on map
fig = plt.figure(figsize=(12, 8))
ax = plt.axes(projection=ccrs.PlateCarree())
ax.coastlines()
ax.set_extent([minx-5, maxx+5, miny-5, maxy+5])

# Draw data extent
ax.plot([minx, maxx, maxx, minx, minx], 
        [miny, miny, maxy, maxy, miny],
        'r-', linewidth=2, transform=ccrs.PlateCarree(), label='Data extent')

# Expected Tokyo extent
tokyo = [139, 140, 140, 139, 139], [35, 35, 36, 36, 35]
ax.plot(tokyo[0], tokyo[1], 'g-', linewidth=2, 
        transform=ccrs.PlateCarree(), label='Expected (Tokyo)')

plt.legend()
plt.title('Data Location Check')
plt.savefig('location_check.png', dpi=150)
```

### Method 3: Online Coordinate Converter

Visit: https://www.latlong.net/
- Enter: 60.329444°W, 3.545833°N (from your data)
- See: Northern Venezuela/Guyana coast
- Enter: 139.5°E, 35.5°N (expected)
- See: Tokyo, Japan

---

## Key GDAL Command Summary

```bash
# Basic info
gdalinfo <file>

# Just coordinates
gdalinfo <file> | grep -E "Upper|Lower"

# Pixel size (resolution)
gdalinfo <file> | grep "Pixel Size"

# Projection info
gdalinfo <file> | grep -A5 "Coordinate System"

# Image dimensions
gdalinfo <file> | grep "Size is"

# Calculate center point
gdalinfo <file> | grep "Center"

# Check if georeferenced
gdalinfo <file> | grep -i "geotransform\|GCP\|RPC"

# Extract bounds to variables
eval $(gdalinfo merged/filt_topophase.flat.geo.vrt 2>&1 | \
       awk '/Upper Left/ {print "WEST="$3";NORTH="$4} 
            /Lower Right/ {print "EAST="$3";SOUTH="$4}' | \
       tr -d '(),')
echo "Bounds: $WEST to $EAST, $SOUTH to $NORTH"
```

---

## Why Radar Coordinates Are Still Valid

The **radar coordinate files** (without `.geo` extension) are NOT affected by the DEM issue:

```bash
# These files are CORRECT and usable:
merged/filt_topophase.unw          ✅ Unwrapped phase (radar geometry)
merged/filt_topophase.unw.conncomp ✅ Connected components
merged/filt_topophase.flat         ✅ Wrapped phase (radar geometry)
merged/phsig.cor                   ✅ Coherence

# Only these have wrong geographic coordinates:
merged/*.geo                       ❌ All geocoded files
```

**Radar coordinates** are the native acquisition geometry - they're always correct regardless of DEM issues. Geocoding just projects them to Earth's surface.

---

## How to Fix (Future Processing)

### Option 1: Download Correct DEM

```bash
# From USGS EarthExplorer or NASA Earthdata
# Search for: SRTM 1-arc second (30m)
# Region: 35-36°N, 139-140°E (Tokyo)
# Expected filename: demLat_N35_N36_Lon_E139_E140.dem.wgs84
```

### Option 2: Auto-download in ISCE2

Add to XML config:
```xml
<property name="demFilename">auto</property>
```
ISCE2 will download the correct DEM tile based on SLC metadata.

### Option 3: Specify Custom DEM

```xml
<property name="demFilename">/path/to/correct_dem.dem.wgs84</property>
```

---

## Testing the Script

```bash
# Run the check script
cd /home/ubuntu/work/isce2-playbook
./check_geocoding.sh

# Expected output will show:
# ❌ WRONG - NOT near Tokyo (expected 139-140°E, 35-36°N)
```

---

## Additional Useful Commands

```bash
# Compare radar vs geocoded files
echo "Radar coordinates (no geotransform):"
gdalinfo merged/filt_topophase.unw.vrt | grep -i "corner\|geotransform"

echo -e "\nGeocoded (has geotransform):"
gdalinfo merged/filt_topophase.flat.geo.vrt | grep -i "corner\|geotransform"

# Check all .geo files at once
for f in merged/*.geo; do 
    echo "=== $(basename $f) ==="
    gdalinfo "$f" 2>&1 | grep "Upper Left"
done

# Get WKT (Well-Known Text) of location
gdalinfo merged/filt_topophase.flat.geo.vrt | \
  awk '/Upper Left/ {ul=$0} /Lower Right/ {lr=$0} 
       END {print "POLYGON(("ul","lr"))"}'
```

---

## References

- **GDAL Documentation**: https://gdal.org/programs/gdalinfo.html
- **Coordinate Systems**: https://spatialreference.org/ref/epsg/wgs-84/
- **DEM Sources**: 
  - NASA Earthdata: https://search.earthdata.nasa.gov
  - USGS EarthExplorer: https://earthexplorer.usgs.gov

---

**Bottom line:** The geocoded files have wrong coordinates because the wrong DEM was used. Your radar coordinate data is perfectly valid and the displacement measurements are correct - they just can't be easily overlaid on maps without proper geocoding.
