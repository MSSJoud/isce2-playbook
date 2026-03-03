#!/usr/bin/env python3
"""
Unwrapped Displacement Visualization
Generates visualizations from unwrapped InSAR phase data
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import colors
import rasterio
import sys

# Constants
WAVELENGTH = 0.056  # Sentinel-1 C-band wavelength in meters

def load_data():
    """Load unwrapped phase and coherence data"""
    print("📂 Loading data...")
    
    # Load unwrapped phase (radar coordinates)
    with rasterio.open('/workspace/merged/filt_topophase.unw.vrt') as src:
        amplitude = src.read(1)
        unw_phase = src.read(2)
        print(f"   ✅ Unwrapped phase: {src.width} x {src.height} pixels")
    
    # Load coherence for masking
    with rasterio.open('/workspace/merged/phsig.cor.vrt') as src:
        coherence = src.read(1)
        print(f"   ✅ Coherence: {src.width} x {src.height} pixels")
    
    # Load connected components
    with rasterio.open('/workspace/merged/filt_topophase.unw.conncomp.vrt') as src:
        conncomp = src.read(1)
        print(f"   ✅ Connected components: {src.width} x {src.height} pixels")
    
    return amplitude, unw_phase, coherence, conncomp

def phase_to_displacement(phase):
    """Convert unwrapped phase (radians) to LOS displacement (cm)"""
    return phase * (WAVELENGTH / (4 * np.pi)) * 100

def plot_unwrapped_displacement():
    """Generate comprehensive unwrapped displacement visualization"""
    
    print("\n" + "=" * 70)
    print("UNWRAPPED DISPLACEMENT VISUALIZATION")
    print("=" * 70)
    
    # Load data
    amplitude, unw_phase, coherence, conncomp = load_data()
    
    # Convert to displacement
    print("\n📊 Converting phase to displacement...")
    displacement_cm = phase_to_displacement(unw_phase)
    
    # Mask zero values
    displacement_cm_masked = displacement_cm.copy()
    displacement_cm_masked[displacement_cm == 0] = np.nan
    
    # Statistics
    print(f"\n📈 Displacement Statistics:")
    print(f"   Min: {np.nanmin(displacement_cm):.2f} cm")
    print(f"   Max: {np.nanmax(displacement_cm):.2f} cm")
    print(f"   Mean: {np.nanmean(displacement_cm):.2f} cm") 
    print(f"   Std: {np.nanstd(displacement_cm):.2f} cm")
    print(f"   Range: {np.nanmax(displacement_cm) - np.nanmin(displacement_cm):.2f} cm")
    
    # Coherence statistics
    coh_high = np.sum(coherence > 0.7) / coherence.size * 100
    coh_medium = np.sum((coherence > 0.5) & (coherence <= 0.7)) / coherence.size * 100
    coh_low = np.sum(coherence <= 0.5) / coherence.size * 100
    
    print(f"\n📊 Coherence Quality:")
    print(f"   Mean coherence: {np.mean(coherence):.3f}")
    print(f"   High (>0.7): {coh_high:.1f}%")
    print(f"   Medium (0.5-0.7): {coh_medium:.1f}%")
    print(f"   Low (<0.5): {coh_low:.1f}%")
    
    # Connected components
    n_components = len(np.unique(conncomp[conncomp > 0]))
    largest_comp_size = np.max(np.bincount(conncomp[conncomp > 0].flatten()))
    print(f"\n🔗 Unwrapping Quality:")
    print(f"   Connected components: {n_components}")
    print(f"   Largest component: {largest_comp_size} pixels ({largest_comp_size/conncomp.size*100:.1f}%)")
    
    # Create figure
    print("\n🎨 Generating plots...")
    fig = plt.figure(figsize=(20, 12))
    
    # 1. Amplitude (log scale)
    ax1 = plt.subplot(2, 3, 1)
    amp_log = np.log10(amplitude + 1)
    im1 = ax1.imshow(amp_log, cmap='gray', aspect='auto')
    ax1.set_title('Amplitude (log scale)', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Range')
    ax1.set_ylabel('Azimuth')
    plt.colorbar(im1, ax=ax1, label='log₁₀(amplitude)')
    
    # 2. Unwrapped displacement
    ax2 = plt.subplot(2, 3, 2)
    vmin, vmax = np.nanpercentile(displacement_cm_masked, [2, 98])
    im2 = ax2.imshow(displacement_cm_masked, cmap='RdBu_r', vmin=vmin, vmax=vmax, aspect='auto')
    ax2.set_title(f'LOS Displacement (unwrapped)\n{vmin:.1f} to {vmax:.1f} cm', 
                  fontsize=14, fontweight='bold')
    ax2.set_xlabel('Range')
    ax2.set_ylabel('Azimuth')
    cbar2 = plt.colorbar(im2, ax=ax2, label='Displacement (cm)', extend='both')
    cbar2.set_label('LOS Displacement (cm)\nPositive = toward satellite', fontsize=10)
    
    # 3. Coherence
    ax3 = plt.subplot(2, 3, 3)
    im3 = ax3.imshow(coherence, cmap='jet', vmin=0, vmax=1, aspect='auto')
    ax3.set_title(f'Interferometric Coherence\nMean = {np.mean(coherence):.3f}', 
                  fontsize=14, fontweight='bold')
    ax3.set_xlabel('Range')
    ax3.set_ylabel('Azimuth')
    plt.colorbar(im3, ax=ax3, label='Coherence (0-1)')
    
    # 4. Masked displacement (high coherence only)
    ax4 = plt.subplot(2, 3, 4)
    disp_hq = displacement_cm_masked.copy()
    disp_hq[coherence < 0.5] = np.nan
    im4 = ax4.imshow(disp_hq, cmap='RdBu_r', vmin=vmin, vmax=vmax, aspect='auto')
    ax4.set_title('High-Quality Displacement\n(coherence > 0.5)', 
                  fontsize=14, fontweight='bold')
    ax4.set_xlabel('Range')
    ax4.set_ylabel('Azimuth')
    plt.colorbar(im4, ax=ax4, label='Displacement (cm)', extend='both')
    
    # 5. Connected components
    ax5 = plt.subplot(2, 3, 5)
    conncomp_plot = conncomp.copy().astype(float)
    conncomp_plot[conncomp == 0] = np.nan
    im5 = ax5.imshow(conncomp_plot, cmap='tab20', aspect='auto')
    ax5.set_title(f'Connected Components\n{n_components} regions', 
                  fontsize=14, fontweight='bold')
    ax5.set_xlabel('Range')
    ax5.set_ylabel('Azimuth')
    plt.colorbar(im5, ax=ax5, label='Component ID')
    
    # 6. Displacement histogram
    ax6 = plt.subplot(2, 3, 6)
    disp_valid = displacement_cm_masked[~np.isnan(displacement_cm_masked)]
    ax6.hist(disp_valid, bins=100, color='steelblue', alpha=0.7, edgecolor='black')
    ax6.axvline(0, color='red', linestyle='--', linewidth=2, label='Zero displacement')
    ax6.axvline(np.nanmean(displacement_cm), color='orange', linestyle='--', 
                linewidth=2, label=f'Mean = {np.nanmean(displacement_cm):.2f} cm')
    ax6.set_xlabel('Displacement (cm)', fontsize=12)
    ax6.set_ylabel('Pixel Count', fontsize=12)
    ax6.set_title('Displacement Distribution', fontsize=14, fontweight='bold')
    ax6.legend()
    ax6.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save
    output_file = '/workspace/05_unwrapped_displacement_analysis.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"\n✅ Saved: {output_file}")
    
    return displacement_cm, coherence, conncomp

def plot_displacement_simple():
    """Generate simple displacement visualization"""
    
    print("\n🎨 Generating simple displacement map...")
    
    with rasterio.open('/workspace/merged/filt_topophase.unw.vrt') as src:
        amplitude = src.read(1)
        unw_phase = src.read(2)
    
    displacement_cm = phase_to_displacement(unw_phase)
    displacement_cm[displacement_cm == 0] = np.nan
    
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    
    # Amplitude
    axes[0].imshow(np.log10(amplitude + 1), cmap='gray', aspect='auto')
    axes[0].set_title('Amplitude (log scale)', fontsize=14, fontweight='bold')
    axes[0].axis('off')
    
    # Displacement
    vmin, vmax = np.nanpercentile(displacement_cm, [2, 98])
    im = axes[1].imshow(displacement_cm, cmap='RdBu_r', vmin=vmin, vmax=vmax, aspect='auto')
    axes[1].set_title('LOS Displacement (cm)', fontsize=14, fontweight='bold')
    axes[1].axis('off')
    cbar = plt.colorbar(im, ax=axes[1], label='Displacement (cm)', extend='both', fraction=0.046)
    cbar.set_label('LOS Displacement (cm)\n+ = toward satellite, - = away', fontsize=10)
    
    plt.tight_layout()
    
    output_file = '/workspace/06_unwrapped_displacement_simple.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✅ Saved: {output_file}")

if __name__ == '__main__':
    try:
        # Generate comprehensive analysis
        displacement, coherence, conncomp = plot_unwrapped_displacement()
        
        # Generate simple version
        plot_displacement_simple()
        
        print("\n" + "=" * 70)
        print("✨ Visualization Complete!")
        print("=" * 70)
        print("\nGenerated files:")
        print("  📊 /workspace/05_unwrapped_displacement_analysis.png")
        print("  📊 /workspace/06_unwrapped_displacement_simple.png")
        print("\n⚠️  Note: Data is in RADAR COORDINATES (not geocoded)")
        print("   Geocoding failed due to incorrect DEM (South America instead of Tokyo)")
        print("   Displacement measurements are valid in radar geometry")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
