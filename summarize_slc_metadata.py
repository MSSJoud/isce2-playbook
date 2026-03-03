#!/usr/bin/env python3
"""
Quick summary of SLC metadata - shows key identification fields
"""

import json
from pathlib import Path
from datetime import datetime

def summarize_slc(json_file, slc_type):
    """Extract and display key metadata"""
    
    with open(json_file, 'r') as f:
        metadata = json.load(f)
    
    print(f"\n{'='*80}")
    print(f"  {slc_type.upper()} SLC - Key Metadata Summary")
    print('='*80)
    
    # Extract key fields
    def get(key):
        return metadata.get(key, 'N/A')
    
    # Product identification
    print("\n🆔 PRODUCT IDENTIFICATION")
    print(f"   Spacecraft:        {get('instance.missionid')}")
    print(f"   Sensor:            Sentinel-1 SAR C-band")
    print(f"   Mode:              IW (Interferometric Wide swath)")
    print(f"   Product Type:      SLC (Single Look Complex)")
   
    
    # Acquisition details
    print("\n📅 ACQUISITION")
    sensing_start = get('instance.sensingStart')
    sensing_stop = get('instance.sensingStop')
    print(f"   Start:             {sensing_start}")
    print(f"   Stop:              {sensing_stop}")
    print(f"   Ascending Node:    {get('instance.ascendingnodetime')}")
    
    # Orbit
    print("\n🛰️  ORBIT")
    print(f"   Direction:         {get('instance.passDirection')}")
    print(f"   Number:            {get('instance.orbitnumber')}")
    print(f"   Track:             {get('instance.tracknumber')}")
    
    # Frame/Burst info
    print("\n📦 FRAME & BURSTS")
    frame_num = get('instance.framenumber')
    print(f"   Frame:             {frame_num}")
    
    # Count bursts
    burst_count = sum(1 for k in metadata.keys() if 'bursts.burst' in k and '.burstnumber' in k)
    print(f"   Number of Bursts:  {burst_count}")
    
    if burst_count > 0:
        first_burst_start = get('instance.bursts.burst1.burststartutc')
        last_burst_stop = get(f'instance.bursts.burst{burst_count}.burststoputc') if burst_count > 1 else get('instance.bursts.burst1.burststoputc')
        print(f"   First Burst Start: {first_burst_start}")
        print(f"   Last Burst Stop:   {last_burst_stop}")
    
    # Sensor parameters
    print("\n📡 SENSOR PARAMETERS")
    wavelength = get('instance.radarwavelength')
    try:
        wavelength_cm = float(wavelength) * 100
        print(f"   Radar Wavelength:  {wavelength} m ({wavelength_cm:.2f} cm, C-band)")
    except:
        print(f"   Radar Wavelength:  {wavelength}")
    
    prf = get('instance.prf')
    print(f"   PRF:               {prf} Hz")
    print(f"   Range Pixel Size:  {get('instance.rangePixelSize')} m")
    print(f"   Azimuth Pixel Size:{get('instance.azimuthPixelSize')} m")
    print(f"   Polarization:      {get('instance.polarization')}")
    
    # Geometry
    print("\n📏 SCENE GEOMETRY")
    print(f"   Starting Range:    {get('instance.startingRange')} m")
    print(f"   Far Range:         {get('instance.farRange')} m")
    print(f"   Number of Lines:   {get('instance.numberoflines')}")
    print(f"   Number of Samples: {get('instance.numberofsamples')}")
    
    # Swath info
    print("\n🌊 SWATH INFORMATION")
    print(f"   Swath Number:      {get('instance.swathnumber')}")
    
    # Try to calculate center coordinates (approximate)
    # This would require more complex geometry calculation
    
    print(f"\n📋 Total metadata fields: {len(metadata)}")
    print(f"   JSON file: {json_file.name} ({json_file.stat().st_size / 1024:.1f} KB)")


def main():
    # Check for JSON files
    ref_json = Path('reference_full_metadata.json')
    sec_json = Path('secondary_full_metadata.json')
    
    if not ref_json.exists() and not sec_json.exists():
        print("❌ No metadata JSON files found!")
        print("   Run: docker compose run --rm isce2-insar python3 /workspace/extract_full_metadata.py")
        return
    
    print("\n" + "="*80)
    print("  SLC METADATA QUICK SUMMARY")
    print("="*80)
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if ref_json.exists():
        summarize_slc(ref_json, 'reference')
    
    if sec_json.exists():
        summarize_slc(sec_json, 'secondary')
    
    print("\n" + "="*80)
    print("  NOTES:")
    print("="*80)
    print("  • Full metadata available in *_full_metadata.json files")
    print("  • Use 'jq' to query JSON: jq '.\"instance.missionid\"' reference_full_metadata.json")
    print("  • Geographic coordinates extracted from geom_reference/ lat/lon grids")
    print("="*80 + "\n")

if __name__ == '__main__':
    main()
