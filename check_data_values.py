#!/usr/bin/env python
"""Quick script to check actual data values in InSAR products"""

import numpy as np
from osgeo import gdal

# Check amplitude
print("="*70)
print("CHECKING INTERFEROGRAM AMPLITUDE")
print("="*70)
ds = gdal.Open('/home/ubuntu/work/isce2-playbook/merged/filt_topophase.flat.vrt')
ifg_complex = ds.GetRasterBand(1).ReadAsArray()
ifg_complex_valid = ifg_complex[ifg_complex != 0]

amplitude = np.abs(ifg_complex_valid)
print(f"Amplitude statistics:")
print(f"  Min: {np.min(amplitude):.6f}")
print(f"  Max: {np.max(amplitude):.6f}")
print(f"  Mean: {np.mean(amplitude):.6f}")
print(f"  Median: {np.median(amplitude):.6f}")
print(f"  Std: {np.std(amplitude):.6f}")
print(f"  Percentiles [1%, 25%, 50%, 75%, 99%]:")
print(f"    {np.percentile(amplitude, [1, 25, 50, 75, 99])}")

# Check coherence
print("\n" + "="*70)
print("CHECKING COHERENCE")
print("="*70)
ds = gdal.Open('/home/ubuntu/work/isce2-playbook/merged/topophase.cor.vrt')
coherence = ds.GetRasterBand(1).ReadAsArray()
coherence_valid = coherence[coherence > 0]

print(f"Coherence statistics:")
print(f"  Min: {np.min(coherence_valid):.6f}")
print(f"  Max: {np.max(coherence_valid):.6f}")
print(f"  Mean: {np.mean(coherence_valid):.6f}")
print(f"  Median: {np.median(coherence_valid):.6f}")
print(f"  Std: {np.std(coherence_valid):.6f}")
print(f"  Percentiles [1%, 25%, 50%, 75%, 99%]:")
print(f"    {np.percentile(coherence_valid, [1, 25, 50, 75, 99])}")

# Check LOS bands
print("\n" + "="*70)
print("CHECKING LOS FILE")
print("="*70)
ds = gdal.Open('/home/ubuntu/work/isce2-playbook/merged/los.rdr.vrt')
print(f"Number of bands: {ds.RasterCount}")
print(f"Band 1 (Incidence angle):")
band1 = ds.GetRasterBand(1).ReadAsArray()
band1_valid = band1[band1 != 0]
print(f"  Min: {np.min(band1_valid):.6f}")
print(f"  Max: {np.max(band1_valid):.6f}")
print(f"  Mean: {np.mean(band1_valid):.6f}")

print(f"\nBand 2 (Azimuth/Heading angle):")
band2 = ds.GetRasterBand(2).ReadAsArray()
band2_valid = band2[band2 != 0]
print(f"  Min: {np.min(band2_valid):.6f}")
print(f"  Max: {np.max(band2_valid):.6f}")
print(f"  Mean: {np.mean(band2_valid):.6f}")

print("\n" + "="*70)
