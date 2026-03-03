# Atmospheric Corrections for InSAR

## Overview

InSAR phase measurements are affected by two main atmospheric effects:

1. **Ionospheric delay** (dispersive - affects L-band more than C-band)
2. **Tropospheric delay** (non-dispersive - affects all frequencies)

For Sentinel-1 (C-band), **tropospheric effects dominate**.

## Correction Methods

### 1. Ionospheric Correction (ISCE2 Built-in)

**When needed?** Mainly for L-band SAR (ALOS, NISAR). Less critical for Sentinel-1 C-band.

**How to enable in ISCE2:**
Add to `topsApp.xml`:
```xml
<property name="do ionosphere correction">True</property>
<property name="height of ionosphere layer in km">200.0</property>
<property name="apply polynomial fit before filtering ionosphere phase">True</property>
```

**Limitations:**
- Requires dual-frequency or split-spectrum processing
- Computationally expensive
- Not typically necessary for Sentinel-1

### 2. Tropospheric Correction (Post-processing with MintPy)

**When needed?** Almost always! Especially for:
- Time-series analysis
- Slow deformation monitoring
- Areas with variable weather/topography

**Method A: Weather Model Correction (ERA5)**

This is the **recommended approach** for tropospheric correction.

**Requirements:**
- ERA5 weather model data (download from Copernicus Climate Data Store)
- MintPy for time-series analysis

**ERA5 Data Download:**
```python
# Using cdsapi (Climate Data Store API)
import cdsapi

c = cdsapi.Client()
c.retrieve(
    'reanalysis-era5-single-levels',
    {
        'product_type': 'reanalysis',
        'variable': ['total_column_water_vapour', 'temperature', 'geopotential'],
        'year': '2021',
        'month': ['01', '02'],
        'day': list(range(1, 32)),
        'time': ['00:00', '06:00', '12:00', '18:00'],
        'area': [36, 139, 35, 140],  # Tokyo area: [N, W, S, E]
        'format': 'netcdf',
    },
    'era5_tokyo_202101_202102.nc')
```

**MintPy Configuration:**
Add to `smallbaselineApp.cfg`:
```
##---------tropospheric delay correction:
mintpy.troposphericDelay.method        = weatherModel
mintpy.weatherModel.weatherModel       = ERA5
mintpy.weatherModel.weatherDir         = /path/to/era5/data
mintpy.weatherModel.weatherFile        = era5_*.nc
mintpy.weatherModel.heightRef          = auto  # or specify reference height in meters
```

**Method B: Phase-Based Empirical Correction**

Alternative if ERA5 data is unavailable:
```
mintpy.troposphericDelay.method        = height_correlation
mintpy.troposphericDelay.polyOrder     = 1
```

This assumes tropospheric delay correlates with topography.

## Recommended Workflow for Tokyo Data

### Step 1: Process with ISCE2 (with unwrapping)

**NOTE:** ISCE2 does NOT perform tropospheric correction. Run normal processing with unwrapping enabled.

### Step 2: Download ERA5 Data

```bash
# Install cdsapi
pip install cdsapi

# Configure credentials at ~/.cdsapirc:
# url: https://cds.climate.copernicus.eu/api/v2
# key: YOUR_UID:YOUR_API_KEY
```

Download variables:
- Total column water vapour (TCWV)
- Temperature (T)
- Geopotential (Z)

Coverage: Your AOI + buffer, all SAR acquisition dates

### Step 3: Run MintPy with Tropospheric Correction

```bash
smallbaselineApp.py --dir ./mintpy_work \
                   --template ./tropocorr_config.cfg
```

Expected correction magnitude: **2-10 cm** for typical weather variations

## Quick Comparison

| Correction Type | Where Applied | When Needed | For Sentinel-1? |
|-----------------|---------------|-------------|----------------|
| Ionospheric | ISCE2 | L-band data | Rarely |
| Tropospheric | MintPy | Almost always | **YES** |

## Additional Resources

- ERA5 CDS registration: https://cds.climate.copernicus.eu
- MintPy tropospheric docs: https://mintpy.readthedocs.io/en/latest/tropospheric_correction/
- ISCE2 ionospheric parameters: `/contrib/stack/topsStack/ion_param.txt`

## Tokyo Example

For the test case data (Venezuela Feb 2021, 12-day pair):
1. **Skip ionospheric correction** (not needed for single C-band pair)
2. **Enable unwrapping** for displacement
3. **Apply tropospheric correction in MintPy** if doing time-series (requires multiple interferograms and ERA5 data)

For a single interferogram, tropospheric effects are typically **not correctable** (need temporal redundancy).
