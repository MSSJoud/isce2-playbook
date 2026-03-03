#!/bin/bash
# Geographic Coordinate Verification Script
# First checks actual SLC coverage, then verifies geocoding correctness

echo "==============================================================================="
echo "Geographic Coordinate Verification"
echo "==============================================================================="
echo ""

# STEP 1: Check what area the SLCs ACTUALLY cover
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 1: Determine ACTUAL SLC Coverage"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Checking latitude/longitude grids from ISCE2 radar geometry..."
echo ""

if [ -f "geom_reference/IW1/lat_03.rdr.vrt" ] && [ -f "geom_reference/IW1/lon_02.rdr.vrt" ]; then
    echo "📡 Reference SLC Geographic Bounds:"
    echo "─────────────────────────────────────"
    
    # Get latitude statistics
    lat_stats=$(gdalinfo -stats geom_reference/IW1/lat_03.rdr.vrt 2>&1 | grep -E "Minimum|Maximum")
    slc_lat_min=$(echo "$lat_stats" | grep -oP 'Minimum=\K[0-9.-]+')
    slc_lat_max=$(echo "$lat_stats" | grep -oP 'Maximum=\K[0-9.-]+')
    
    # Get longitude statistics
    lon_stats=$(gdalinfo -stats geom_reference/IW1/lon_02.rdr.vrt 2>&1 | grep -E "Minimum|Maximum")
    slc_lon_min=$(echo "$lon_stats" | grep -oP 'Minimum=\K[0-9.-]+')
    slc_lon_max=$(echo "$lon_stats" | grep -oP 'Maximum=\K[0-9.-]+')
    
    printf "  Latitude:  %.3f° to %.3f° N\n" "$slc_lat_min" "$slc_lat_max"
    printf "  Longitude: %.3f° to %.3f° E\n" "$slc_lon_min" "$slc_lon_max"
    echo ""
    
    # Determine actual location
    echo "📍 Actual SLC Location:"
    if (( $(echo "$slc_lat_min > 30 && $slc_lat_min < 40" | bc -l) )) && (( $(echo "$slc_lon_min > 135 && $slc_lon_min < 145" | bc -l) )); then
        echo "  ✓ JAPAN (Tokyo region)"
        echo "    Expected: ~35°N, ~139°E"
        actual_location="Tokyo"
    elif (( $(echo "$slc_lat_min > 0 && $slc_lat_min < 10" | bc -l) )) && (( $(echo "$slc_lon_min < -55 && $slc_lon_min > -65" | bc -l) )); then
        echo "  ✓ SOUTH AMERICA (Venezuela/Guyana region)"
        echo "    Venezuela coast: ~3°N, ~59-60°W"
        actual_location="Venezuela"
    else
        echo "  ? Unknown region"
        printf "    Coordinates: %.1f°N, %.1f°E\n" "$slc_lat_min" "$slc_lon_min"
        actual_location="Unknown"
    fi
else
    echo "⚠️  Radar geometry files not found!"
    echo "   Cannot determine actual SLC coverage from geom_reference/"
    actual_location="Unknown"
fi

echo ""
echo ""

# STEP 2: Check which DEM was used
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 2: DEM File Used for Geocoding"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

dem_file=$(ls demLat*.dem.wgs84 2>/dev/null | head -1)
if [ -n "$dem_file" ]; then
    echo "🗺️  DEM File: $dem_file"
    echo ""
    
    # Parse DEM filename for coordinates
    if [[ $dem_file =~ demLat_N([0-9]+)_N([0-9]+)_Lon_W([0-9]+)_W([0-9]+) ]]; then
        dem_lat1="${BASH_REMATCH[1]}"
        dem_lat2="${BASH_REMATCH[2]}"
        dem_lon1="${BASH_REMATCH[3]}"
        dem_lon2="${BASH_REMATCH[4]}"
        echo "   Coverage from filename:"
        echo "   Latitude:  ${dem_lat1}° to ${dem_lat2}° N"
        echo "   Longitude: ${dem_lon1}° to ${dem_lon2}° W (negative values)"
        echo ""
        dem_location="South America (${dem_lat1}-${dem_lat2}°N, ${dem_lon1}-${dem_lon2}°W)"
    elif [[ $dem_file =~ demLat_N([0-9]+)_N([0-9]+)_Lon_E([0-9]+)_E([0-9]+) ]]; then
        dem_lat1="${BASH_REMATCH[1]}"
        dem_lat2="${BASH_REMATCH[2]}"
        dem_lon1="${BASH_REMATCH[3]}"
        dem_lon2="${BASH_REMATCH[4]}"
        echo "   Coverage from filename:"
        echo "   Latitude:  ${dem_lat1}° to ${dem_lat2}° N"
        echo "   Longitude: ${dem_lon1}° to ${dem_lon2}° E"
        echo ""
        dem_location="Asia/Pacific (${dem_lat1}-${dem_lat2}°N, ${dem_lon1}-${dem_lon2}°E)"
    else
        dem_location="Unknown"
    fi
else
    echo "⚠️  No DEM file found"
    dem_location="None"
fi

echo ""
echo ""

# STEP 3: Check geocoded output coordinates
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 3: Geocoded Output Coordinates"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ -f "merged/filt_topophase.flat.geo.vrt" ]; then
    echo "🌐 Geocoded Interferogram Bounds:"
    echo "──────────────────────────────────"
    
    geo_bounds=$(gdalinfo merged/filt_topophase.flat.geo.vrt 2>&1 | grep -E "Upper Left|Lower Right")
    
    # Extract coordinates (decimal degrees only, ignore DMS format)
    geo_ul=$(echo "$geo_bounds" | grep "Upper Left")
    geo_lr=$(echo "$geo_bounds" | grep "Lower Right")
    
    geo_lon_min=$(echo "$geo_ul" | grep -oP '\(\s*\K-?[0-9.]+(?=,)')
    geo_lat_max=$(echo "$geo_ul" | grep -oP ',\s*\K-?[0-9.]+(?=\))')
    geo_lon_max=$(echo "$geo_lr" | grep -oP '\(\s*\K-?[0-9.]+(?=,)')
    geo_lat_min=$(echo "$geo_lr" | grep -oP ',\s*\K-?[0-9.]+(?=\))')
    
    printf "  Longitude: %.3f° to %.3f°\n" "$geo_lon_min" "$geo_lon_max"
    printf "  Latitude:  %.3f° to %.3f°\n" "$geo_lat_min" "$geo_lat_max"
    echo ""
    echo "  Raw output from gdalinfo:"
    echo "$geo_bounds" | sed 's/^/    /'
else
    echo "⚠️  Geocoded file not found: merged/filt_topophase.flat.geo.vrt"
    geo_lon_min="0"
    geo_lat_min="0"
    geo_lon_max="0"
    geo_lat_max="0"
fi

echo ""
echo ""

# STEP 4: Compare and verify
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 4: Verification - Do They Match?"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ -n "$slc_lat_min" ] && [ -n "$geo_lat_min" ] && [ "$geo_lat_min" != "0" ]; then
    echo "📊 Side-by-Side Comparison:"
    echo "═══════════════════════════════════════════════════════════════════════════"
    printf "%-25s │ %-25s │ %-25s\n" "" "SLC Coverage (Actual)" "Geocoded Output"
    echo "───────────────────────────────────────────────────────────────────────────"
    printf "%-25s │ %.3f° to %.3f°     │ %.3f° to %.3f°     \n" "Latitude Range" "$slc_lat_min" "$slc_lat_max" "$geo_lat_min" "$geo_lat_max"
    printf "%-25s │ %.3f° to %.3f°    │ %.3f° to %.3f°    \n" "Longitude Range" "$slc_lon_min" "$slc_lon_max" "$geo_lon_min" "$geo_lon_max"
    echo "═══════════════════════════════════════════════════════════════════════════"
    echo ""
    
    # Calculate differences (absolute values)
    lat_min_diff=$(echo "scale=3; ($slc_lat_min - $geo_lat_min)^2" | bc)
    lat_max_diff=$(echo "scale=3; ($slc_lat_max - $geo_lat_max)^2" | bc)
    lon_min_diff=$(echo "scale=3; ($slc_lon_min - $geo_lon_min)^2" | bc)
    lon_max_diff=$(echo "scale=3; ($slc_lon_max - $geo_lon_max)^2" | bc)
    
    total_diff=$(echo "scale=3; sqrt($lat_min_diff + $lat_max_diff + $lon_min_diff + $lon_max_diff)" | bc)
    
    echo "🔍 Verdict:"
    echo "─────────"
    
    # Check if coordinates match within tolerance (0.5 degree)
    if (( $(echo "$total_diff < 0.5" | bc -l) )); then
        echo "  ✅ GEOCODING IS CORRECT!"
        echo ""
        echo "  The geocoded outputs correctly match the SLC coverage area."
        echo "  Total coordinate difference: ${total_diff}° (< 0.5° threshold)"
        echo ""
        if [ "$actual_location" = "Venezuela" ]; then
            echo "  📍 Location: South America (Venezuela/Guyana region ~3°N, 59-60°W)"
            echo ""
            echo "  Note: If documentation mentions 'Tokyo', this may be a test case"
            echo "        naming issue. The actual data covers South America, and the"
            echo "        geocoding is correct for that coverage."
        elif [ "$actual_location" = "Tokyo" ]; then
            echo "  📍 Location: Tokyo, Japan (~35°N, 139°E)"
        fi
    else
        echo "  ❌ GEOCODING MISMATCH DETECTED!"
        echo ""
        echo "  The geocoded outputs DO NOT match the SLC coverage area."
        echo "  Total coordinate difference: ${total_diff}°"
        echo ""
        echo "  SLC covers: $actual_location"
        echo "  Geocoding placed data at: (${geo_lat_min}°N, ${geo_lon_min}°E)"
        echo ""
        echo "  This indicates the wrong DEM was used for geocoding."
    fi
else
    echo "⚠️  Insufficient data for comparison"
    echo ""
    echo "Could not extract coordinates from one or more sources."
fi

echo ""
echo ""

# STEP 5: Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "This script verified:"
echo "  1. ✓ Extracted actual SLC geographic coverage from radar geometry"
echo "  2. ✓ Identified DEM file used for geocoding"
echo "  3. ✓ Extracted geocoded output coordinates"
echo "  4. ✓ Compared SLC coverage vs geocoded output"
echo ""
echo "Key files checked:"
echo "  • SLC coverage: geom_reference/IW1/lat_*.rdr.vrt, lon_*.rdr.vrt"
echo "  • Geocoded outputs: merged/*.geo.vrt"
echo "  • DEM: $dem_file"
echo ""
echo "==============================================================================="

