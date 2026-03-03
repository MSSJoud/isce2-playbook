#!/usr/bin/env python3
"""
Comprehensive SLC Metadata Inspector
Extracts all metadata from Sentinel-1 SLC products independently of data source
"""

import xml.etree.ElementTree as ET
import json
import os
from pathlib import Path
from datetime import datetime
import sys

def parse_isce_xml(xml_file):
    """Extract metadata from ISCE2-generated XML files"""
    metadata = {}
    
    if not os.path.exists(xml_file):
        return metadata
    
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # Recursive function to extract all properties
        def extract_properties(element, prefix=""):
            data = {}
            for child in element:
                if child.tag == 'property':
                    name = child.get('name', 'unknown')
                    value_elem = child.find('value')
                    if value_elem is not None and value_elem.text:
                        key = f"{prefix}{name}" if prefix else name
                        data[key] = value_elem.text.strip()
                elif child.tag == 'component':
                    comp_name = child.get('name', 'unknown')
                    new_prefix = f"{prefix}{comp_name}." if prefix else f"{comp_name}."
                    data.update(extract_properties(child, new_prefix))
            return data
        
        metadata = extract_properties(root)
        
    except Exception as e:
        print(f"Error parsing {xml_file}: {e}", file=sys.stderr)
    
    return metadata

def parse_safe_manifest(manifest_path):
    """Extract metadata from SAFE manifest.safe file"""
    metadata = {}
    
    if not os.path.exists(manifest_path):
        return metadata
    
    try:
        tree = ET.parse(manifest_path)
        root = tree.getroot()
        
        # Define namespaces
        ns = {
            'safe': 'http://www.esa.int/safe/sentinel-1.0',
            's1': 'http://www.esa.int/safe/sentinel-1.0/sentinel-1',
            'xfdu': 'urn:ccsds:schema:xfdu:1',
        }
        
        # Extract key metadata
        metadata['manifest_file'] = str(manifest_path)
        
        # Product information
        for elem in root.findall('.//xfdu:metadataObject[@ID="platform"]//safe:familyName', ns):
            metadata['platform_family'] = elem.text
        
        for elem in root.findall('.//xfdu:metadataObject[@ID="platform"]//safe:number', ns):
            metadata['platform_number'] = elem.text
            
        # Acquisition period
        for elem in root.findall('.//safe:acquisitionPeriod//safe:startTime', ns):
            metadata['acquisition_start'] = elem.text
            
        for elem in root.findall('.//safe:acquisitionPeriod//safe:stopTime', ns):
            metadata['acquisition_stop'] = elem.text
        
        # Orbit info
        for elem in root.findall('.//safe:orbitNumber[@type="start"]', ns):
            metadata['orbit_number_start'] = elem.text
            
        for elem in root.findall('.//safe:orbitNumber[@type="stop"]', ns):
            metadata['orbit_number_stop'] = elem.text
            
        for elem in root.findall('.//safe:pass', ns):
            metadata['orbit_direction'] = elem.text
            
        for elem in root.findall('.//s1:relativeOrbitNumber[@type="start"]', ns):
            metadata['relative_orbit_start'] = elem.text
        
    except Exception as e:
        print(f"Error parsing manifest: {e}", file=sys.stderr)
    
    return metadata

def extract_filename_metadata(filename):
    """Parse Sentinel-1 filename for metadata"""
    metadata = {}
    
    # Example: S1A_IW_SLC__1SDV_20210131T200841_20210131T200908_036423_0446A1_8572
    parts = Path(filename).stem.split('_')
    
    if len(parts) >= 9:
        metadata['mission'] = parts[0]  # S1A or S1B
        metadata['beam_mode'] = parts[1]  # IW, EW, SM, etc.
        metadata['product_type'] = parts[2]  # SLC, GRD, OCN
        metadata['resolution_class'] = parts[3][0]  # 1=High, 2=Medium
        metadata['polarization'] = parts[4]  # SH, SV, DH, DV
        metadata['start_datetime'] = parts[5]  # YYYYMMDDThhmmss
        metadata['stop_datetime'] = parts[6]  # YYYYMMDDThhmmss
        metadata['absolute_orbit'] = parts[7]  # 6-digit orbit number
        metadata['mission_datatake'] = parts[8]  # Mission datatake ID
        if len(parts) > 9:
            metadata['product_unique_id'] = parts[9]  # Product unique identifier
    
    return metadata

def get_gdal_metadata(file_path):
    """Extract metadata using GDAL"""
    metadata = {}
    
    try:
        from osgeo import gdal
        gdal.UseExceptions()
        
        ds = gdal.Open(str(file_path))
        if ds:
            # Geospatial info
            metadata['raster_size'] = f"{ds.RasterXSize} x {ds.RasterYSize}"
            metadata['raster_count'] = ds.RasterCount
            
            # Geotransform
            gt = ds.GetGeoTransform()
            if gt != (0.0, 1.0, 0.0, 0.0, 0.0, 1.0):
                metadata['geotransform'] = {
                    'origin_x': gt[0],
                    'origin_y': gt[3],
                    'pixel_width': gt[1],
                    'pixel_height': gt[5],
                    'rotation_x': gt[2],
                    'rotation_y': gt[4]
                }
                
                # Calculate bounds
                minx = gt[0]
                maxy = gt[3]
                maxx = minx + ds.RasterXSize * gt[1]
                miny = maxy + ds.RasterYSize * gt[5]
                
                metadata['geographic_bounds'] = {
                    'west': minx,
                    'east': maxx,
                    'north': maxy,
                    'south': miny
                }
            
            # Projection
            proj = ds.GetProjection()
            if proj:
                metadata['projection_wkt'] = proj[:200] + "..." if len(proj) > 200 else proj
            
            # Metadata domains
            for domain in ds.GetMetadataDomainList() or []:
                md = ds.GetMetadata(domain)
                if md:
                    metadata[f'metadata_{domain}'] = md
            
            ds = None
    except ImportError:
        print("GDAL not available - skipping GDAL metadata", file=sys.stderr)
    except Exception as e:
        print(f"Error reading GDAL metadata: {e}", file=sys.stderr)
    
    return metadata

def inspect_slc_data(base_dir, output_format='json'):
    """Main inspection function"""
    base_path = Path(base_dir)
    
    inspection_data = {
        'inspection_timestamp': datetime.now().isoformat(),
        'base_directory': str(base_path.absolute()),
        'reference': {},
        'secondary': {},
        'processing_info': {},
        'file_structure': {}
    }
    
    print("=" * 80)
    print("Comprehensive SLC Metadata Inspector")
    print("=" * 80)
    print()
    
    # 1. Check for ISCE2 XML files
    print("[1/6] Inspecting ISCE2 XML metadata...")
    for slc_type in ['reference', 'secondary']:
        xml_path = base_path / 'input-files' / f'{slc_type}.xml'
        if xml_path.exists():
            with open(xml_path, 'r') as f:
                content = f.read()
                # Extract SAFE path from XML
                if '<safe>' in content:
                    safe_path = content.split('<safe>')[1].split('</safe>')[0].strip()
                    inspection_data[slc_type]['safe_path'] = safe_path
                    inspection_data[slc_type]['filename_metadata'] = extract_filename_metadata(safe_path)
    
    # 2. Check ISCE2 processed metadata
    print("[2/6] Inspecting ISCE2 processed XML files...")
    for slc_type in ['reference', 'secondary']:
        slc_dir = Path(f'/mnt/data/tokyo_test/output/{slc_type}') if Path(f'/mnt/data/tokyo_test/output/{slc_type}').exists() else base_path / slc_type
        if slc_dir.exists():
            for xml_file in slc_dir.glob('**/*.xml'):
                if xml_file.name.startswith('IW'):
                    metadata = parse_isce_xml(xml_file)
                    if metadata:
                        inspection_data[slc_type]['isce_metadata'] = metadata
                        inspection_data[slc_type]['isce_xml_file'] = str(xml_file)
                        break
    
    # 3. Check for SAFE manifest files
    print("[3/6] Searching for SAFE manifest files...")
    for manifest in base_path.rglob('manifest.safe'):
        manifest_data = parse_safe_manifest(manifest)
        if 'acquisition_start' in manifest_data:
            if 'reference' not in inspection_data or not inspection_data['reference'].get('manifest'):
                key = 'reference'
            else:
                key = 'secondary'
            inspection_data[key]['manifest'] = manifest_data
    
    # 4. Check geometry files for geographic info
    print("[4/6] Extracting geographic coverage from radar geometry...")
    geom_dir = base_path / 'geom_reference' / 'IW1'
    if geom_dir.exists():
        lat_file = geom_dir / 'lat_03.rdr.vrt'
        lon_file = geom_dir / 'lon_02.rdr.vrt'
        
        if lat_file.exists():
            lat_metadata = get_gdal_metadata(lat_file)
            if 'metadata_' in str(lat_metadata):
                inspection_data['reference']['latitude_grid_info'] = lat_metadata
        
        if lon_file.exists():
            lon_metadata = get_gdal_metadata(lon_file)
            if 'metadata_' in str(lon_metadata):
                inspection_data['reference']['longitude_grid_info'] = lon_metadata
    
    # 5. Check geocoded outputs
    print("[5/6] Inspecting geocoded outputs...")
    merged_dir = base_path / 'merged'
    if merged_dir.exists():
        for geo_file in merged_dir.glob('*.geo.vrt'):
            geo_metadata = get_gdal_metadata(geo_file)
            if geo_metadata:
                inspection_data['processing_info'][geo_file.stem] = geo_metadata
                break  # Just get one example
    
    # 6. File structure summary
    print("[6/6] Analyzing file structure...")
    for root, dirs, files in os.walk(base_path):
        rel_path = Path(root).relative_to(base_path)
        if len(str(rel_path).split(os.sep)) <= 2:  # Only top 2 levels
            inspection_data['file_structure'][str(rel_path)] = {
                'directories': len(dirs),
                'files': len(files),
                'total_size_mb': sum(
                    os.path.getsize(os.path.join(root, f)) 
                    for f in files if os.path.isfile(os.path.join(root, f))
                ) / 1024 / 1024
            }
    
    print()
    print("=" * 80)
    
    return inspection_data

def format_output(data, format_type='json'):
    """Format output in requested format"""
    if format_type == 'json':
        return json.dumps(data, indent=2, default=str)
    
    elif format_type == 'text':
        output = []
        output.append("=" * 80)
        output.append("SLC METADATA INSPECTION REPORT")
        output.append("=" * 80)
        output.append(f"\nInspection Time: {data['inspection_timestamp']}")
        output.append(f"Base Directory: {data['base_directory']}\n")
        
        for slc_type in ['reference', 'secondary']:
            if slc_type in data and data[slc_type]:
                output.append("-" * 80)
                output.append(f"{slc_type.upper()} SLC")
                output.append("-" * 80)
                
                slc_data = data[slc_type]
                
                # Filename metadata
                if 'filename_metadata' in slc_data:
                    output.append("\n📋 Product Identifier:")
                    for key, value in slc_data['filename_metadata'].items():
                        output.append(f"  {key:25s}: {value}")
                
                # Manifest metadata
                if 'manifest' in slc_data:
                    output.append("\n🛰️  Acquisition Metadata:")
                    for key, value in slc_data['manifest'].items():
                        if not key.startswith('manifest_'):
                            output.append(f"  {key:25s}: {value}")
                
                # ISCE metadata (selected fields)
                if 'isce_metadata' in slc_data:
                    output.append("\n⚙️  Processing Metadata (selected):")
                    selected_keys = ['ascendingnodetime', 'sensing_start', 'sensing_stop', 
                                    'startingrange', 'prf', 'radarwavelength']
                    for key in selected_keys:
                        if key in slc_data['isce_metadata']:
                            output.append(f"  {key:25s}: {slc_data['isce_metadata'][key]}")
                
                output.append("")
        
        # Processing info
        if 'processing_info' in data and data['processing_info']:
            output.append("-" * 80)
            output.append("GEOCODED OUTPUT METADATA")
            output.append("-" * 80)
            for filename, info in data['processing_info'].items():
                output.append(f"\n📍 {filename}:")
                if 'geographic_bounds' in info:
                    bounds = info['geographic_bounds']
                    output.append(f"  West:  {bounds['west']:.6f}°")
                    output.append(f"  East:  {bounds['east']:.6f}°")
                    output.append(f"  North: {bounds['north']:.6f}°")
                    output.append(f"  South: {bounds['south']:.6f}°")
                if 'raster_size' in info:
                    output.append(f"  Size:  {info['raster_size']} pixels")
        
        # File structure
        if 'file_structure' in data and data['file_structure']:
            output.append("\n" + "-" * 80)
            output.append("FILE STRUCTURE SUMMARY")
            output.append("-" * 80)
            for path, info in sorted(data['file_structure'].items()):
                if path != '.':
                    output.append(f"\n{path}:")
                    output.append(f"  Directories: {info['directories']}")
                    output.append(f"  Files: {info['files']}")
                    output.append(f"  Total Size: {info['total_size_mb']:.1f} MB")
        
        output.append("\n" + "=" * 80)
        
        return "\n".join(output)
    
    return str(data)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Comprehensive SLC metadata inspector',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # JSON output (default)
  python inspect_slc_metadata.py /home/ubuntu/work/isce2-playbook
  
  # Human-readable text
  python inspect_slc_metadata.py /home/ubuntu/work/isce2-playbook --format text
  
  # Save to file
  python inspect_slc_metadata.py . --format json > slc_metadata.json
  python inspect_slc_metadata.py . --format text > slc_metadata.txt
        """
    )
    
    parser.add_argument(
        'directory',
        nargs='?',
        default='.',
        help='Base directory to inspect (default: current directory)'
    )
    
    parser.add_argument(
        '--format',
        choices=['json', 'text'],
        default='text',
        help='Output format (default: text)'
    )
    
    parser.add_argument(
        '--output',
        '-o',
        help='Output file (default: stdout)'
    )
    
    args = parser.parse_args()
    
    # Run inspection
    data = inspect_slc_data(args.directory, args.format)
    
    # Format output
    output_str = format_output(data, args.format)
    
    # Write to file or stdout
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output_str)
        print(f"\n✅ Metadata written to: {args.output}")
    else:
        print(output_str)
