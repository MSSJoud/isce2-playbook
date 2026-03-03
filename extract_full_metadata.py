#!/usr/bin/env python3
"""
Extract complete SLC metadata from ISCE2 XML files
"""

import xml.etree.ElementTree as ET
import json
import sys
from pathlib import Path

def extract_all_isce_metadata(xml_file):
    """Recursively extract all metadata from ISCE2 XML"""
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    metadata = {}
    
    def recurse(elem, path=''):
        for child in elem:
            if child.tag == 'property':
                name = child.get('name', 'unknown')
                value_elem = child.find('value')
                if value_elem is not None and value_elem.text:
                    full_key = f'{path}.{name}' if path else name
                    metadata[full_key] = value_elem.text.strip()
            elif child.tag == 'component':
                comp_name = child.get('name', 'unknown')
                new_path = f'{path}.{comp_name}' if path else comp_name
                recurse(child, new_path)
    
    recurse(root)
    return metadata

def parse_sentinel_filename(safe_path):
    """Parse Sentinel-1 SAFE filename for quick metadata"""
    filename = Path(safe_path).name
    # S1A_IW_SLC__1SDV_20210131T094602_20210131T094630_036380_044503_40CB.SAFE
    parts = filename.replace('.SAFE', '').split('_')
    
    if len(parts) >= 9:
        return {
            'mission': parts[0],  # S1A or S1B
            'mode': parts[1],  # IW, EW, SM
            'product_type': parts[2],  # SLC, GRD, OCN
            'resolution': parts[3][0],  # 1, 2
            'polarization': parts[4],  # SH, SV, DH, DV
            'start_time': parts[5],  # YYYYMMDDThhmmss
            'stop_time': parts[6],  # YYYYMMDDThhmmss
            'absolute_orbit': parts[7],  # 6-digit
            'datatake_id': parts[8],  # Mission datatake ID
            'product_id': parts[9] if len(parts) > 9 else 'N/A'
        }
    return {}

def print_section(title, items):
    """Print a formatted section of metadata"""
    if items:
        print(f'\n{title}')
        for key, value in items.items():
            print(f'  {key:35s}: {value}')

def main():
    # Paths
    reference_xml = '/mnt/data/tokyo_test/output/reference/IW1.xml'
    secondary_xml = '/mnt/data/tokyo_test/output/secondary/IW1.xml'
    input_files = [
        '/mnt/data/tokyo_test/output/reference/../../input-files/reference.xml',
        '/workspace/input-files/reference.xml'
    ]
    
    # Extract input file paths
    safe_paths = {}
    for input_xml in input_files:
        if Path(input_xml).exists():
            try:
                tree = ET.parse(input_xml)
                for elem in tree.findall('.//property[@name="safe"]'):
                    value = elem.find('value')
                    if value is not None and value.text:
                        if 'reference' in input_xml:
                            safe_paths['reference'] = value.text.strip()
                        else:
                            safe_paths['secondary'] = value.text.strip()
            except:
                pass
    
    # Process both SLCs
    for slc_type in ['reference', 'secondary']:
        xml_path = reference_xml if slc_type == 'reference' else secondary_xml
        
        print('\n' + '=' * 80)
        print(f'{slc_type.upper()} SLC - Complete Metadata')
        print('=' * 80)
        
        try:
            metadata = extract_all_isce_metadata(xml_path)
            
            # SAFE filename metadata
            if slc_type in safe_paths:
                print(f'\n📁 SAFE File: {Path(safe_paths[slc_type]).name}')
                filename_meta = parse_sentinel_filename(safe_paths[slc_type])
                if filename_meta:
                    print_section('🆔 FROM FILENAME:', filename_meta)
            
            # Identification
            id_fields = {}
            for key in ['ascendingnodetime', 'missionid', 'spacecraftname', 'orbitnumber']:
                if key in metadata:
                    id_fields[key] = metadata[key]
            print_section('🆔 IDENTIFICATION:', id_fields)
            
            # Timing
            time_fields = {}
            for key, value in sorted(metadata.items()):
                if any(tk in key.lower() for tk in ['sensing', 'time']) and 'image' not in key.lower():
                    time_fields[key] = value
            print_section('📅 TIMING:', time_fields)
            
            # Orbit
            orbit_fields = {}
            for key, value in sorted(metadata.items()):
                if any(ok in key.lower() for ok in ['orbit', 'pass', 'track']):
                    orbit_fields[key] = value
            print_section('🛰️  ORBIT:', orbit_fields)
            
            # Sensor parameters
            sensor_fields = {}
            for key in ['radarwavelength', 'prf', 'rangepixelsize', 'azimuthpixelsize', 
                       'rangeSamplingRate', 'pulseLength', 'chirpSlope']:
                if key in metadata:
                    sensor_fields[key] = metadata[key]
            print_section('📡 SENSOR PARAMETERS:', sensor_fields)
            
            # Geometry
            geom_fields = {}
            for key in ['startingrange', 'farrange', 'numberoflines', 'numberofsamples', 
                       'width', 'length', 'rangeFirstTime', 'rangeLastTime']:
                if key in metadata:
                    geom_fields[key] = metadata[key]
            print_section('📏 GEOMETRY:', geom_fields)
            
            # Bursts
            burst_fields = {}
            for key, value in sorted(metadata.items()):
                if 'burst' in key.lower() and 'imagefile' not in key.lower():
                    burst_fields[key] = value
            print_section('📦 BURST INFORMATION:', burst_fields)
            
            print(f'\n📋 TOTAL METADATA FIELDS EXTRACTED: {len(metadata)}')
            
            # Save full JSON
            output_file = f'/workspace/{slc_type}_full_metadata.json'
            with open(output_file, 'w') as f:
                json.dump(metadata, f, indent=2, sort_keys=True)
            print(f'✅ Full metadata saved to: {slc_type}_full_metadata.json')
            print(f'   ({len(json.dumps(metadata, indent=2))} bytes)')
            
        except FileNotFoundError:
            print(f'❌ Error: XML file not found: {xml_path}')
        except Exception as e:
            print(f'❌ Error: {e}')
            import traceback
            traceback.print_exc()
    
    print('\n' + '=' * 80)
    print('Use these JSON files for programmatic access to all metadata')
    print('=' * 80)

if __name__ == '__main__':
    main()
