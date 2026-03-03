# ISCE2 Coherence Files - Quick Reference

## The Confusion: Two "Coherence" Files

ISCE2 outputs multiple correlation/coherence products. **Using the wrong one will give incorrect results!**

## File Comparison

| File | Range | Description | Use? |
|------|-------|-------------|------|
| `topophase.cor` | **1-516** | Raw correlation values (not normalized) | ❌ NO |
| `phsig.cor` | **0-1** | **Actual interferometric coherence** | ✅ **YES** |

## What Each File Contains

### `topophase.cor` (DON'T USE for coherence metrics)
- **Raw correlation magnitude** in undefined units
- Values typically 1-500+
- Used internally by ISCE2 for processing
- NOT suitable for quality assessment

### `phsig.cor` (CORRECT FILE)
- **Standard interferometric coherence**: γ = |E[s₁ · s₂*]| / √(E[|s₁|²] · E[|s₂|²])
- Range: 0 (decorrelated) to 1 (perfect correlation)
- This is what the InSAR community calls "coherence"
- Use for quality assessment and masking

## GDAL Statistics Example

```bash
# WRONG FILE (topophase.cor)
$ gdalinfo -stats topophase.cor.vrt | grep Mean
  Mean=89.849  # <-- These values are meaningless for coherence!

# CORRECT FILE (phsig.cor)  
$ gdalinfo -stats phsig.cor.vrt | grep Mean
  Mean=0.679  # <-- This is actual coherence (excellent for 12-day urban!)
```

## Quality Interpretation (using `phsig.cor`)

| Coherence Value | Quality | Typical Use Case |
|-----------------|---------|------------------|
| > 0.8 | Excellent | Urban areas, rock, short temporal baseline |
| 0.7 - 0.8 | Very Good | Most urban/rock, usable for precise measurements |
| 0.5 - 0.7 | Good | Acceptable, mask areas < 0.5 for unwrapping |
| 0.3 - 0.5 | Moderate | Marginal, may have unwrapping errors |
| < 0.3 | Poor | Decorrelated, exclude from analysis |

## Test Case Data Results (Venezuela 2021)

**Using `phsig.cor` (CORRECT):**
- Mean coherence: **0.679** ✅
- Range: 0.0 - 1.0
- Temporal baseline: 12 days
- **Interpretation**: Excellent coherence for urban InSAR!

**Previous (WRONG) result using `topophase.cor`:**
- Mean "coherence": 0.172 after normalization ❌
- Range: 1.3 - 516.2
- This made it look like 100% low coherence - completely incorrect!

## Why ISCE2 Has Both Files

1. **`topophase.cor`**: Internal processing metric
   - Used for filtering decisions
   - Not normalized for user interpretation
   
2. **`phsig.cor`**: Quality metric for users
   - Standard coherence definition
   - Ready for masking, visualization, reporting

## Bottom Line

**Always use `phsig.cor` for coherence analysis!**

The presence of `topophase.cor` is a common trap for new ISCE2 users. When you see coherence values > 1, you know you're looking at the wrong file.

## References

- ISCE2 Documentation: TopsProc output files
- Touzi et al. (1999): "Coherence estimation for SAR imagery"
- Standard coherence formula in Hanssen (2001) "Radar Interferometry"
