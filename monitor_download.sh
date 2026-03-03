#!/bin/bash
# Monitor SAR data download progress

ZIP_DIR="/mnt/data/tokyo_test/data/safe/zip"
EXPECTED_SIZE_GB=8

echo "=== SAR Data Download Monitor ==="
echo "Expected size per file: ~${EXPECTED_SIZE_GB}GB"
echo ""

while true; do
    clear
    echo "=== Download Progress (updated every 30s) ==="
    echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    
    if [ -d "$ZIP_DIR" ] && [ "$(ls -A $ZIP_DIR 2>/dev/null)" ]; then
        for file in $ZIP_DIR/*.zip; do
            if [ -f "$file" ]; then
                filename=$(basename "$file")
                size_mb=$(du -m "$file" | cut -f1)
                size_gb=$(echo "scale=2; $size_mb / 1024" | bc)
                percent=$(echo "scale=1; ($size_gb / $EXPECTED_SIZE_GB) * 100" | bc)
                
                echo "📦 $filename"
                echo "   Size: ${size_gb}GB / ${EXPECTED_SIZE_GB}GB (${percent}%)"
                echo ""
            fi
        done
        
        total_size_gb=$(du -sh $ZIP_DIR | cut -f1)
        echo "Total downloaded: $total_size_gb"
    else
        echo "⏳ Waiting for download to start..."
    fi
    
    echo ""
    echo "Press Ctrl+C to exit monitor"
    sleep 30
done
