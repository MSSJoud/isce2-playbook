#!/bin/bash
# Quick SLC Metadata Summary - All Key Information

echo "================================================================================"
echo "  COMPLETE SLC METADATA INSPECTION"
echo "================================================================================"
echo ""

# Check if JSON files exist
if [ ! -f "reference_full_metadata.json" ] || [ ! -f "secondary_full_metadata.json" ]; then
    echo "❌ Metadata JSON files not found!"
    echo "   Run: docker compose run --rm isce2-insar python3 /workspace/extract_full_metadata.py"
    exit 1
fi

echo "📊 Data Source: ISCE2 XML Metadata (IW1.xml)"
echo "📁 Location: /home/ubuntu/work/isce2-playbook/"
echo ""

for SLC in reference secondary; do
    JSON_FILE="${SLC}_full_metadata.json"
    
    echo "================================================================================"
    echo "  ${SLC^^} SLC"
    echo "================================================================================"
    echo ""
    
    # From input file - get SAFE filename
    if [ "$SLC" = "reference" ]; then
        SAFE_PATH="/mnt/data/tokyo_test/data/safe/unzip/S1A_IW_SLC__1SDV_20210131T094602_20210131T094630_036380_044503_40CB.SAFE"
    else
        SAFE_PATH="/mnt/data/tokyo_test/data/safe/unzip/S1A_IW_SLC__1SDV_20210212T094602_20210212T094630_036555_044B1A_A7D9.SAFE"
    fi
    
    SAFE_NAME=$(basename "$SAFE_PATH" .SAFE)
    
    # Parse SAFE filename
    IFS='_' read -ra PARTS <<< "$SAFE_NAME"
    MISSION="${PARTS[0]}"
    MODE="${PARTS[1]}"
    PRODUCT="${PARTS[2]}"
    POL="${PARTS[4]}"
    START_TIME="${PARTS[5]}"
    STOP_TIME="${PARTS[6]}"
    ABS_ORBIT="${PARTS[7]}"
    DATATAKE_ID="${PARTS[8]}"
    PRODUCT_ID="${PARTS[9]}"
    
    echo "🆔 PRODUCT IDENTIFICATION"
    echo "───────────────────────────────────────────────────────────────────────────"
    echo "  SAFE Filename:     $SAFE_NAME"
    echo "  Mission:           $MISSION (Sentinel-1A or 1B)"
    echo "  Mode:              $MODE (Interferometric Wide swath)"
    echo "  Product Type:      $PRODUCT (Single Look Complex)"
    echo "  Polarization:      $POL"
    echo "  Absolute Orbit:    $ABS_ORBIT"
    echo "  Datatake ID:       $DATATAKE_ID"
    echo "  Product ID:        $PRODUCT_ID"
    echo ""
    
    echo "📅 ACQUISITION TIMING"
    echo "───────────────────────────────────────────────────────────────────────────"
    echo "  Start Time:        ${START_TIME}"
    echo "  Stop Time:         ${STOP_TIME}"
    
    # From JSON
    ASCENDING_NODE=$(jq -r '.["instance.ascendingnodetime"] // "N/A"' "$JSON_FILE")
    echo "  Ascending Node:    $ASCENDING_NODE"
    
    # Get first and last burst times
    FIRST_BURST=$(jq -r '.["instance.bursts.burst1.burststartutc"] // "N/A"' "$JSON_FILE")
    LAST_BURST=$(jq -r '.["instance.bursts.burst10.burststoputc"] // .["instance.bursts.burst1.burststoputc"] // "N/A"' "$JSON_FILE")
    echo "  First Burst:       $FIRST_BURST"
    echo "  Last Burst:        $LAST_BURST"
    echo ""
    
    echo "🌍 GEOGRAPHIC COVERAGE (from radar geometry)"
    echo "───────────────────────────────────────────────────────────────────────────"
    if [ -f "geom_reference/IW1/lat_03.rdr.vrt" ] && [ "$SLC" = "reference" ]; then
        LAT_MIN=$(gdalinfo -stats geom_reference/IW1/lat_03.rdr.vrt 2>&1 | grep "Minimum=" | grep -oP 'Minimum=\K[0-9.-]+')
        LAT_MAX=$(gdalinfo -stats geom_reference/IW1/lat_03.rdr.vrt 2>&1 | grep "Maximum=" | grep -oP 'Maximum=\K[0-9.-]+')
        LON_MIN=$(gdalinfo -stats geom_reference/IW1/lon_02.rdr.vrt 2>&1 | grep "Minimum=" | grep -oP 'Minimum=\K[0-9.-]+')
        LON_MAX=$(gdalinfo -stats geom_reference/IW1/lon_02.rdr.vrt 2>&1 | grep "Maximum=" | grep -oP 'Maximum=\K[0-9.-]+')
        
        echo "  Latitude Range:    ${LAT_MIN}° to ${LAT_MAX}° N"
        echo "  Longitude Range:   ${LON_MIN}° to ${LON_MAX}° E"
        echo "  Location:          Venezuela/Guyana coast, South America"
    else
        echo "  (Use geom_reference lat/lon grids for precise coverage)"
    fi
    echo ""
    
    echo "📦 BURSTS & SWATHS"
    echo "───────────────────────────────────────────────────────────────────────────"
    BURST_COUNT=$(jq '[keys[] | select(contains("bursts.burst") and contains(".burstnumber"))] | length' "$JSON_FILE")
    echo "  Number of Bursts:  $BURST_COUNT"
    echo "  Swath:             IW1 (processed subswath)"
    echo ""
    
    echo "📡 SENSOR PARAMETERS"
    echo "───────────────────────────────────────────────────────────────────────────"
    echo "  Satellite:         Sentinel-1 (C-band SAR)"
    echo "  Frequency:         5.405 GHz"
    echo "  Wavelength:        ~5.55 cm (C-band)"
    echo "  Look Direction:    Right-side looking"
    echo ""
    
    echo "📏 SCENE DIMENSIONS"
    echo "───────────────────────────────────────────────────────────────────────────"
    # Get from first burst image
    WIDTH=$(jq -r '.["instance.bursts.burst1.image.width"] // "N/A"' "$JSON_FILE")
    LENGTH=$(jq -r '.["instance.bursts.burst1.image.length"] // "N/A"' "$JSON_FILE")
    echo "  Burst Width:       $WIDTH samples"
    echo "  Burst Length:      $LENGTH lines"
    echo ""
    
    echo "📋 METADATA SUMMARY"
    echo "───────────────────────────────────────────────────────────────────────────"
    FIELD_COUNT=$(jq 'keys | length' "$JSON_FILE")
    FILE_SIZE=$(ls -lh "$JSON_FILE" | awk '{print $5}')
    echo "  Total Fields:      $FIELD_COUNT metadata fields extracted"
    echo "  JSON File:         $JSON_FILE ($FILE_SIZE)"
    echo ""
    
done

echo "================================================================================"
echo "  PROCESSING CONFIGURATION"
echo "================================================================================"
echo ""

if [ -f "input-files/topsApp_with_unwrap.xml" ]; then
    echo "Configuration used:"
    grep -A1 "swaths\|azimuth looks\|range looks\|filter strength\|unwrap" input-files/topsApp_with_unwrap.xml | \
        grep -E "<property|<value" | \
        sed 's/<property name="/  /; s/">/: /; s/<value>/   Value: /; s/<\/value>//' | \
        head -10
fi

echo ""
echo "================================================================================"
echo "  QUICK ACCESS TO METADATA"
echo "================================================================================"
echo ""
echo "View specific fields:"
echo "  jq '.\"instance.ascendingnodetime\"' reference_full_metadata.json"
echo "  jq '.\"instance.bursts.burst1.burststartutc\"' reference_full_metadata.json"
echo ""
echo "Search for keys:"
echo "  jq 'keys | .[] | select(contains(\"orbit\"))' reference_full_metadata.json"
echo ""
echo "Count burst metadata:"
echo "  jq '[keys[] | select(contains(\"burst\"))] | length' reference_full_metadata.json"
echo ""
echo "Export to CSV (selected fields):"
echo "  jq -r '[.\"instance.ascendingnodetime\", .\"instance.bursts.burst1.burststartutc\"] | @csv' *.json"
echo ""
echo "================================================================================"
