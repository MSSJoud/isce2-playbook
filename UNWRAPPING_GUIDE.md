# Processing Guide: Unwrapped Phase & LOS Displacement

## Overview

This guide explains how to reprocess InSAR data with phase unwrapping enabled to get actual displacement measurements.

## What You'll Get

### Without Unwrapping (Current State):
- ✅ Wrapped phase (-π to π radians) - **color fringes**
- ❌ Cannot measure displacement > 1.4 cm (half wavelength)
- ❌ Phase discontinuities at wrap boundaries

### With Unwrapping (After Reprocessing):
- ✅ Unwrapped phase (continuous values) - **actual surface displacement**
- ✅ Files: `*.unw` (unwrapped), `*.unw.conncomp` (connected components)
- ✅ Can measure displacement of any magnitude
- ✅ Direct conversion to cm: **displacement = phase × (5.6 cm / 4π)**

## Processing Steps

### Option 1: Reprocess Everything (Clean Start)

This is the **recommended approach** for the cleanest results.

```bash
# 1. Clean previous processing outputs (keeps original data!)
rm -rf /home/ubuntu/work/isce2-playbook/merged
rm -rf /home/ubuntu/work/isce2-playbook/reference
rm -rf /home/ubuntu/work/isce2-playbook/secondary
rm -rf /home/ubuntu/work/isce2-playbook/coarse*
rm -rf /home/ubuntu/work/isce2-playbook/fine*
rm -rf /home/ubuntu/work/isce2-playbook/PICKLE

# 2. Run ISCE2 with unwrapping enabled
cd /home/ubuntu/work/isce2-playbook
docker compose run --rm isce2-insar topsApp.py /workspace/input-files/topsApp_with_unwrap.xml

# Processing time: 40-90 minutes (includes unwrapping step)
```

### Option 2: Resume from Existing Processing

If you want to keep previous outputs and just run unwrapping:

```bash
cd /home/ubuntu/work/isce2-playbook
docker compose run --rm isce2-insar topsApp.py \
    /workspace/input-files/topsApp_with_unwrap.xml \
    --start=unwrap
```

⚠️ **Note:** This requires that all previous steps completed successfully. If you get errors, use Option 1.

### Option 3: Process to New Output Directory

To keep both wrapped and unwrapped results:

```bash
# Create new working directory
cd /home/ubuntu/work
mkdir -p isce2-playbook-unwrapped
cp -r isce2-playbook/input-files isce2-playbook-unwrapped/
cp isce2-playbook/docker-compose.yml isce2-playbook-unwrapped/

# Link to existing data (no need to re-download!)
ln -s /mnt/data/tokyo_test isce2-playbook-unwrapped/data

# Process in new directory
cd isce2-playbook-unwrapped
docker compose run --rm isce2-insar topsApp.py /workspace/input-files/topsApp_with_unwrap.xml
```

## Expected Outputs

After unwrapping, you'll have in `merged/`:

| File | Description | Size | Use |
|------|-------------|------|-----|
| `filt_topophase.unw` | Unwrapped phase (radar coords) | ~50 MB | Direct phase measurements |
| `filt_topophase.unw.conncomp` | Connected components mask | ~17 MB | Quality control |
| `filt_topophase.unw.geo` | Unwrapped phase (geocoded) | ~500 MB | Geographic coordinates |
| `phsig.cor.geo` | Unwrapping coherence | ~300 MB | Reliability metric |

## Visualization

### Quick GDAL Check:

```bash
# Check unwrapped file exists
gdalinfo /home/ubuntu/work/isce2-playbook/merged/filt_topophase.unw.vrt

# Get data range
gdalinfo -stats /home/ubuntu/work/isce2-playbook/merged/filt_topophase.unw.vrt | grep STATISTICS
```

### Python Visualization:

```python
import numpy as np
import matplotlib.pyplot as plt
from osgeo import gdal

# Load unwrapped phase
ds = gdal.Open('merged/filt_topophase.unw.vrt')
unw_phase = ds.GetRasterBand(2).ReadAsArray()  # Band 2 is unwrapped phase
# Band 1 is amplitude (for reference)

# Convert to LOS displacement (cm)
wavelength = 0.056  # Sentinel-1 C-band: 5.6 cm
displacement_los = unw_phase * (wavelength / (4 * np.pi))  # In meters
displacement_los_cm = displacement_los * 100  # Convert to cm

# Mask invalid data
displacement_los_cm[displacement_los_cm == 0] = np.nan

# Plot
plt.figure(figsize=(12, 10))
plt.imshow(displacement_los_cm, cmap='RdBu_r', vmin=-5, vmax=5)
plt.colorbar(label='LOS Displacement (cm)', extend='both')
plt.title('Line-of-Sight Displacement\nPositive = motion toward satellite')
plt.xlabel('Range')
plt.ylabel('Azimuth')
plt.savefig('displacement_los.png', dpi=300, bbox_inches='tight')
plt.show()

print(f"Displacement range: {np.nanmin(displacement_los_cm):.2f} to {np.nanmax(displacement_los_cm):.2f} cm")
print(f"Mean displacement: {np.nanmean(displacement_los_cm):.2f} cm")
print(f"Std deviation: {np.nanstd(displacement_los_cm):.2f} cm")
```

## Interpreting Results

### Connected Components

- Unwrapping can fail in low-coherence areas
- Connected component labels show isolated regions
- Largest component = most reliable
- Check: `filt_topophase.unw.conncomp`

### Quality Checks

1. **Coherence**: Should be > 0.3 for reliable unwrapping
2. **Connected components**: Fewer, larger components = better
3. **Displacement magnitude**: Typical values for Tokyo:
   - Tectonic: 0-2 cm/year
   - Subsidence: 0-5 cm/year  
   - For 12-day pair: expect < 0.5 cm unless earthquake or rapid subsidence

### Common Issues

**Issue:** Unwrapping fails with error
**Solution:** 
- Reduce multilook ratio: `azimuth looks=3, range looks=9`
- Increase filter strength: `filter strength=0.7`

**Issue:** Many disconnected components
**Solution:**
- Scene has low coherence (vegetation, water)
- Mask out low-coherence pixels before interpretation

**Issue:** Unrealistic displacement values (> 10 cm)
**Solution:**
- Check for phase unwrapping errors
- Verify reference point is stable
- May need atmospheric correction (for time-series)

## Converting LOS to Vertical/Horizontal

LOS displacement is a projection. To separate vertical and horizontal:

### Requirements:
- Ascending AND descending orbits
- Assumes negligible North-South motion

### 2D Decomposition:

```python
# Given:
los_asc = LOS displacement from ascending pass
los_desc = LOS displacement from descending pass
inc_asc = incidence angle ascending (~33°)
inc_desc = incidence angle descending (~33°)

# Compute:
vertical = (los_asc / cos(inc_asc) + los_desc / cos(inc_desc)) / 2
east_west = (los_asc / sin(inc_asc) - los_desc / sin(inc_desc)) / 2
```

**For a single ascending pass:** Only LOS displacement is available. Cannot separate components without additional data.

## Next Steps

1. **Single interferogram analysis:**
   - Process with unwrapping
   - Interpret LOS displacement
   - Identify deformation features
   - No atmospheric correction needed

2. **Time-series analysis (future):**
   - Process multiple interferograms (different dates)
   - Stack with MintPy
   - Apply tropospheric correction (ERA5)
   - Estimate velocity maps

3. **Advanced processing:**
   - Persistent Scatterer InSAR (PSI)
   - Small Baseline Subset (SBAS)
   - 3D decomposition (multi-orbit)

## Monitoring Progress

```bash
# Watch ISCE2 log
tail -f /home/ubuntu/work/isce2-playbook/isce.log

# Check for "unwrap" step
grep -i "unwrap" /home/ubuntu/work/isce2-playbook/isce.log

# Estimate completion
# Steps: startup (2 min) → coregistration (15 min) → interferogram (10 min) → unwrap (15-60 min) → geocoding (5 min)
```

## Troubleshooting

### "SNAPHU not found"
ISCE2 Docker image includes SNAPHU. Check Docker image version.

### "Out of memory during unwrapping"
Reduce processing area:
```xml
<property name="region of interest">[35.5, 35.8, 139.6, 139.9]</property>
```

### "Unwrapping produces artifact"
Try 2-stage unwrapping (uncomment in XML):
```xml
<property name="do unwrap 2 stage">True</property>
```

## References

- SNAPHU unwrapper: Chen & Zebker (2000, 2002)
- Phase unwrapping theory: Ghiglia & Pritt (1998)
- InSAR displacement: Hanssen (2001)
