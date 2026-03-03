#!/usr/bin/env python3
"""
Enhanced InSAR Visualization Script using analyze-insar Docker service

This script generates comprehensive visualizations of ISCE2 outputs:
- Filtered interferogram (amplitude + wrapped phase)
- Coherence map
- Geocoded products
- Multi-panel summary

Usage:
    docker compose run --rm analyze-insar python src/plot_enhanced.py
"""

import matplotlib.pyplot as plt
import numpy as np
import rasterio
from pathlib import Path


def plot_interferogram(input_file, output_file, title="Interferogram", 
                      amp_min=0, amp_max=10000):
    """Plot complex interferogram showing amplitude and wrapped phase"""
    
    with rasterio.open(input_file) as ds:
        data = ds.read(1)
        transform = ds.transform
        
        # Get spatial extent
        firstx, firsty = transform.c, transform.f
        deltax, deltay = transform.a, transform.e
        lastx = firstx + data.shape[1] * deltax
        lasty = firsty + data.shape[0] * deltay
        extent = [min(firstx, lastx), max(firstx, lastx), 
                 min(firsty, lasty), max(firsty, lasty)]
    
    # Mask zeros
    data[data == 0] = np.nan
    
    # Create figure
    fig, axes = plt.subplots(1, 2, figsize=(18, 8))
    
    # Amplitude (log scale for better visualization)
    amp = np.abs(data)
    amp_log = np.log10(amp + 1)
    im1 = axes[0].imshow(amp_log, cmap='gray', extent=extent)
    axes[0].set_title(f'{title} - Amplitude (log scale)', fontsize=14, fontweight='bold')
    axes[0].set_xlabel('X coordinate')
    axes[0].set_ylabel('Y coordinate')
    fig.colorbar(im1, ax=axes[0], label='log₁₀(Amplitude)')
    
    # Wrapped phase
    phase = np.angle(data)
    im2 = axes[1].imshow(phase, cmap='twilight', vmin=-np.pi, vmax=np.pi, extent=extent)
    axes[1].set_title(f'{title} - Wrapped Phase', fontsize=14, fontweight='bold')
    axes[1].set_xlabel('X coordinate')
    axes[1].set_ylabel('Y coordinate')
    cbar = fig.colorbar(im2, ax=axes[1], label='Phase (radians)')
    cbar.set_ticks([-np.pi, -np.pi/2, 0, np.pi/2, np.pi])
    cbar.set_ticklabels(['-π', '-π/2', '0', 'π/2', 'π'])
    
    fig.text(0.5, 0.01, 'Each 2π cycle = ~2.8 cm LOS displacement (Sentinel-1 C-band)', 
             ha='center', fontsize=11, bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))
    
    plt.tight_layout(rect=[0, 0.03, 1, 1])
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Saved: {output_file}")


def plot_coherence(input_file, output_file, title="Coherence"):
    """Plot coherence map"""
    
    with rasterio.open(input_file) as ds:
        coherence = ds.read(1)
        transform = ds.transform
        
        # Get spatial extent
        firstx, firsty = transform.c, transform.f
        deltax, deltay = transform.a, transform.e
        lastx = firstx + coherence.shape[1] * deltax
        lasty = firsty + coherence.shape[0] * deltay
        extent = [min(firstx, lastx), max(firstx, lastx), 
                 min(firsty, lasty), max(firsty, lasty)]
    
    # Mask zeros
    coherence[coherence == 0] = np.nan
    
    # Statistics
    mean_coh = np.nanmean(coherence)
    high_coh = (np.sum(coherence > 0.7) / np.sum(~np.isnan(coherence))) * 100
    good_coh = (np.sum((coherence > 0.5) & (coherence <= 0.7)) / np.sum(~np.isnan(coherence))) * 100
    low_coh = (np.sum(coherence < 0.5) / np.sum(~np.isnan(coherence))) * 100
    
    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    
    im = ax.imshow(coherence, cmap='jet', vmin=0, vmax=1, extent=extent)
    ax.set_title(f'{title} (Mean: {mean_coh:.3f})', fontsize=14, fontweight='bold')
    ax.set_xlabel('X coordinate')
    ax.set_ylabel('Y coordinate')
    cbar = fig.colorbar(im, ax=ax, label='Coherence (0=poor, 1=excellent)')
    
    # Add quality text
    quality_text = f"Quality: High (>0.7): {high_coh:.1f}% | Good (0.5-0.7): {good_coh:.1f}% | Low (<0.5): {low_coh:.1f}%"
    fig.text(0.5, 0.01, quality_text, ha='center', fontsize=11,
             bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7))
    
    plt.tight_layout(rect=[0, 0.03, 1, 1])
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Saved: {output_file}")
    print(f"   Coherence stats: Mean={mean_coh:.3f}, High={high_coh:.1f}%, Good={good_coh:.1f}%, Low={low_coh:.1f}%")


def plot_summary_panel(merged_dir, output_file):
    """Create 4-panel summary with interferogram and coherence"""
    
    fig, axes = plt.subplots(2, 2, figsize=(18, 16))
    fig.suptitle('InSAR Processing Summary - Tokyo, Japan (2021-01-31 to 2021-02-12)', 
                 fontsize=16, fontweight='bold')
    
    # Load filtered interferogram (radar coords)
    with rasterio.open(merged_dir / 'filt_topophase.flat.vrt') as ds:
        ifg_data = ds.read(1)
        ifg_data[ifg_data == 0] = np.nan
        amp = np.abs(ifg_data)
        phase = np.angle(ifg_data)
    
    # Load coherence
    with rasterio.open(merged_dir / 'phsig.cor.vrt') as ds:
        coherence = ds.read(1)
        coherence[coherence == 0] = np.nan
    
    # Plot 1: Amplitude (log scale)
    amp_log = np.log10(amp + 1)
    im1 = axes[0, 0].imshow(amp_log, cmap='gray', aspect='auto')
    axes[0, 0].set_title('Amplitude (Log Scale)', fontsize=12, fontweight='bold')
    axes[0, 0].set_xlabel('Range (pixels)')
    axes[0, 0].set_ylabel('Azimuth (pixels)')
    fig.colorbar(im1, ax=axes[0, 0], label='log₁₀(Amplitude)')
    
    # Plot 2: Wrapped Phase
    im2 = axes[0, 1].imshow(phase, cmap='twilight', vmin=-np.pi, vmax=np.pi, aspect='auto')
    axes[0, 1].set_title('Wrapped Phase', fontsize=12, fontweight='bold')
    axes[0, 1].set_xlabel('Range (pixels)')
    axes[0, 1].set_ylabel('Azimuth (pixels)')
    cbar2 = fig.colorbar(im2, ax=axes[0, 1], label='Phase (radians)')
    cbar2.set_ticks([-np.pi, -np.pi/2, 0, np.pi/2, np.pi])
    cbar2.set_ticklabels(['-π', '-π/2', '0', 'π/2', 'π'])
    
    # Plot 3: Coherence
    im3 = axes[1, 0].imshow(coherence, cmap='jet', vmin=0, vmax=1, aspect='auto')
    axes[1, 0].set_title(f'Coherence (Mean: {np.nanmean(coherence):.3f})', fontsize=12, fontweight='bold')
    axes[1, 0].set_xlabel('Range (pixels)')
    axes[1, 0].set_ylabel('Azimuth (pixels)')
    fig.colorbar(im3, ax=axes[1, 0], label='Coherence')
    
    # Plot 4: Phase histogram
    phase_flat = phase[~np.isnan(phase)]
    axes[1, 1].hist(phase_flat, bins=100, color='steelblue', alpha=0.7, edgecolor='black')
    axes[1, 1].set_xlabel('Wrapped Phase (radians)', fontsize=11)
    axes[1, 1].set_ylabel('Frequency', fontsize=11)
    axes[1, 1].set_title('Phase Distribution', fontsize=12, fontweight='bold')
    axes[1, 1].axvline(0, color='red', linestyle='--', linewidth=2, label='Zero phase')
    axes[1, 1].axvline(-np.pi, color='orange', linestyle=':', linewidth=2)
    axes[1, 1].axvline(np.pi, color='orange', linestyle=':', linewidth=2, label='Wrap boundaries')
    axes[1, 1].grid(True, alpha=0.3)
    axes[1, 1].legend()
    
    plt.tight_layout(rect=[0, 0.02, 1, 0.98])
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Saved: {output_file}")


if __name__ == "__main__":
    # Define paths (inside Docker container)
    merged_dir = Path("/workspace/merged")
    output_dir = Path("/workspace")
    
    print("="*70)
    print("Enhanced InSAR Visualization")
    print("="*70)
    
    # 1. Filtered interferogram (radar coordinates)
    print("\n📊 Generating interferogram plots...")
    plot_interferogram(
        input_file=merged_dir / "filt_topophase.flat.vrt",
        output_file=output_dir / "01_interferogram_radar.png",
        title="Filtered Interferogram (Radar Coords)",
        amp_min=0,
        amp_max=10000
    )
    
    # 2. Geocoded interferogram
    print("\n📊 Generating geocoded interferogram...")
    plot_interferogram(
        input_file=merged_dir / "filt_topophase.flat.geo.vrt",
        output_file=output_dir / "02_interferogram_geocoded.png",
        title="Filtered Interferogram (Geographic Coords)",
        amp_min=0,
        amp_max=10000
    )
    
    # 3. Coherence map
    print("\n📊 Generating coherence map...")
    plot_coherence(
        input_file=merged_dir / "phsig.cor.vrt",
        output_file=output_dir / "03_coherence.png",
        title="Interferometric Coherence"
    )
    
    # 4. Summary panel
    print("\n📊 Generating summary panel...")
    plot_summary_panel(
        merged_dir=merged_dir,
        output_file=output_dir / "04_summary_panel.png"
    )
    
    print("\n" + "="*70)
    print("✨ All visualizations complete!")
    print("="*70)
    print("\nGenerated files:")
    print("  📁 /workspace/01_interferogram_radar.png")
    print("  📁 /workspace/02_interferogram_geocoded.png")
    print("  📁 /workspace/03_coherence.png")
    print("  📁 /workspace/04_summary_panel.png")
    print("\n💡 To view: Open these PNG files or use the Jupyter notebook")
    print("="*70)
