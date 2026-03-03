# Unwrapping Processing Status Report
**Generated:** March 1, 2026 - 10:39 AM

---

## ✅ PROCESSING STATUS: PARTIALLY COMPLETE

### Summary
The unwrapping process **successfully completed** and generated unwrapped phase data in **radar coordinates**. However, the geocoded version of the unwrapped file is **missing** (expected but not created).

---

## 📊 Output Files Status

### ✅ Successfully Generated (Radar Coordinates)

| File | Size | Status | Description |
|------|------|--------|-------------|
| `filt_topophase.unw` | **30 MB** | ✅ **COMPLETE** | Unwrapped phase (radar coords) |
| `filt_topophase.unw.conncomp` | **3.7 MB** | ✅ **COMPLETE** | Connected components mask |
| `filt_topophase.unw.vrt` | 714 B | ✅ **COMPLETE** | GDAL virtual raster |
| `filt_topophase.unw.xml` | 4.0 KB | ✅ **COMPLETE** | Metadata |

**Data Dimensions:** 1421 × 2713 pixels

### ❌ Missing (Geographic Coordinates)

| File | Expected Size | Status | Description |
|------|---------------|--------|-------------|
| `filt_topophase.unw.geo` | ~500 MB | ❌ **MISSING** | Geocoded unwrapped phase |
| `filt_topophase.unw.geo.vrt` | ~1 KB | ❌ **MISSING** | VRT for geocoded unwrapped |
| `filt_topophase.unw.geo.xml` | ~4 KB | ❌ **MISSING** | Metadata for geocoded |

### ✅ Other Geocoded Files (Present from Earlier)

These files were geocoded in previous processing:
- `los.rdr.geo` (232 MB) - Line-of-sight geometry
- `phsig.cor.geo` (116 MB) - Coherence (geocoded)
- `topophase.cor.geo` (232 MB) - Correlation (geocoded)
- `topophase.flat.geo` (232 MB) - Wrapped phase (geocoded)
- `dem.crop.geo` - DEM (not listed but expected)

---

## 📈 Unwrapped Phase Data Validation

### Data Range Analysis
```
Band 1 (Amplitude):
  Min: 0.000
  Max: 3,481,024.75
  Mean: 3,335.62
  Status: ✅ Valid (log scale recommended for visualization)

Band 2 (Unwrapped Phase):
  Min: -47.01 radians
  Max: +23.52 radians
  Mean: 0.39 radians
  StdDev: 3.14 radians
  Status: ✅ Valid
```

### Displacement Conversion
Using Sentinel-1 C-band wavelength (5.6 cm):

**Formula:** Displacement (cm) = Phase (radians) × (5.6 cm / 4π)

**Results:**
- **Minimum displacement:** -20.95 cm (moving away from satellite)
- **Maximum displacement:** +10.48 cm (moving toward satellite)
- **Total deformation span:** 31.43 cm

**Interpretation:**
- 31 cm range over 12 days is **significant deformation**
- Could indicate:
  - Urban subsidence
  - Tectonic activity
  - Atmospheric effects (needs verification)
  - Possible unwrapping errors in low-coherence areas

---

## 🔍 Processing Log Summary

**Last Run:** March 1, 2026 01:09 - 01:39 AM
**Duration:** 2,303 seconds (~38 minutes)

**Steps Completed:**
1. ✅ SLC loading and preparation
2. ✅ Coregistration (coarse + fine)
3. ✅ Interferogram generation
4. ✅ Correlation calculation
5. ✅ Filtering (power-spectral filter, strength 0.5)
6. ✅ **Phase unwrapping** (SNAPHU algorithm)
7. ⚠️ Geocoding (only previous wrapped files, NOT unwrapped)

**Issue Identified:**
The log shows "Geocoding Image" was called but processing stopped at "Total Time" without geocoding the unwrapped file. This is likely because:
- The geocode list in the config didn't include unwrapped files
- Processing ended before geocoding unwrapped outputs
- ISCE2 may geocode wrapped phase but not automatically geocode unwrapped

---

## 🎯 Data Usability Assessment

### ✅ What You Can Do NOW:

1. **Visualize unwrapped displacement (radar coordinates)**
   - File: `merged/filt_topophase.unw.vrt`
   - 1421 × 2713 pixels
   - Ready for immediate analysis

2. **Quality control with connected components**
   - File: `merged/filt_topophase.unw.conncomp`
   - Identify reliable unwrapped regions

3. **Convert to physical displacement**
   - Multiply phase (band 2) by λ/(4π) = 0.00446 m/radian
   - Results in meters or cm of LOS displacement

4. **Overlay with coherence**
   - Use `phsig.cor` to mask low-quality areas

### ⚠️ What's Limited:

1. **No geographic coordinates for unwrapped data**
   - Cannot directly overlay on maps
   - Cannot georeference with GIS tools
   - Need to run geocoding step manually

2. **Large displacement values need verification**
   - 31 cm total span is unusually high for 12 days
   - Check for:
     - Atmospheric artifacts
     - Unwrapping errors
     - Reference point issues

---

## 🛠️ Options to Complete Processing

### Option A: Manual Geocoding (Fastest - 5 minutes)

Run only the geocoding step for the unwrapped file:

```bash
cd /home/ubuntu/work/isce2-playbook

# Use ISCE2's geocoding tool directly
docker compose run --rm isce2-insar python3 << 'EOF'
import isce
from isceobj.TopsProc.runGeocode import runGeocode
from isceobj.TopsProc import TopsProc

# Load existing processing state
insar = TopsProc.TopsProc()
insar.loadProduct('reference/IW1.xml')  # Adjust if needed

# Geocode unwrapped file
# (Need to set proper parameters - may require investigation)
EOF
```

**Note:** This is complex and may require more investigation into ISCE2's geocoding API.

### Option B: Re-run Geocoding Step (Recommended - 10 minutes)

Edit the config to include unwrapped files in geocode list and rerun:

```bash
cd /home/ubuntu/work/isce2-playbook

# Check current geocode list
docker compose run --rm isce2-insar topsApp.py \
    /workspace/input-files/topsApp_with_unwrap.xml \
    --dostep=geocode
```

### Option C: Use GDAL to Manually Geocode (Advanced - 30 minutes)

Use existing geocoded files as reference and apply same transformation:

```bash
# Extract geotransform from existing geocoded file
gdalinfo merged/topophase.flat.geo.vrt > geo_params.txt

# Apply to unwrapped file (requires manual GCP matching)
```

### Option D: Continue with Radar Coordinates (Simplest)

The unwrapped data in radar coordinates is **fully usable** for:
- Displacement analysis
- Time-series (if you process more dates)
- Scientific interpretation

Users can convert to geographic coordinates later if needed.

---

## 📋 Recommended Next Steps

### Immediate Actions:

1. **Visualize the unwrapped displacement** ✅
   - Create Python/Jupyter notebook to plot displacement
   - Convert phase to cm
   - Overlay coherence mask
   - Identify deformation patterns

2. **Quality check the results** ⚠️
   - Verify 31 cm displacement is realistic
   - Check connected components
   - Identify unwrapping errors
   - Select stable reference point

3. **Decide on geocoding need** 🤔
   - If you need GIS integration → Run geocoding (Option B)
   - If radar coordinates are sufficient → Continue with analysis

### Future Processing:

4. **Process more interferograms**
   - Different date pairs
   - Build time-series
   - Reduce atmospheric noise

5. **Apply atmospheric corrections**
   - Use MintPy with ERA5 data
   - Requires multiple interferograms

---

## 🎨 Quick Visualization Command

```bash
cd /home/ubuntu/work/isce2-playbook

# Quick preview with Python
python3 << 'EOF'
import numpy as np
import matplotlib.pyplot as plt
from osgeo import gdal

# Load unwrapped phase
ds = gdal.Open('merged/filt_topophase.unw.vrt')
amplitude = ds.GetRasterBand(1).ReadAsArray()
unw_phase = ds.GetRasterBand(2).ReadAsArray()

# Convert to displacement (cm)
wavelength = 0.056  # meters
displacement_cm = unw_phase * (wavelength / (4 * np.pi)) * 100

# Mask zeros
displacement_cm[displacement_cm == 0] = np.nan

# Quick plot
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# Amplitude
axes[0].imshow(np.log10(amplitude + 1), cmap='gray')
axes[0].set_title('Amplitude (log scale)')
axes[0].axis('off')

# Displacement
im = axes[1].imshow(displacement_cm, cmap='RdBu_r', vmin=-25, vmax=15)
axes[1].set_title('LOS Displacement (cm)\nPositive = toward satellite')
axes[1].axis('off')
plt.colorbar(im, ax=axes[1], label='Displacement (cm)')

plt.tight_layout()
plt.savefig('unwrapped_displacement_quick.png', dpi=150, bbox_inches='tight')
print(f"✅ Saved: unwrapped_displacement_quick.png")
print(f"Displacement range: {np.nanmin(displacement_cm):.2f} to {np.nanmax(displacement_cm):.2f} cm")
EOF
```

---

## ✅ CONCLUSION

**Unwrapping Status:** ✅ **SUCCESS** (radar coordinates completed)  
**Geocoding Status:** ⚠️ **INCOMPLETE** (unwrapped file not geocoded)  
**Data Usability:** ✅ **READY FOR ANALYSIS** (with radar coordinates)

**Users can proceed with displacement analysis using the radar coordinate data!**

The missing geocoded version is not critical for most analyses - it's mainly needed for overlaying on maps or GIS integration.

---

## 📞 Next Question?

Should I create:
1. **Visualization notebook** for unwrapped displacement?
2. **Geocoding script** to generate the missing .geo file?
3. **Quality control analysis** to verify the 31 cm deformation?

Let me know what you'd like to explore next! 🚀
