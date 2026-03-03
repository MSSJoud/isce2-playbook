#!/bin/bash
# Unwrapping Script - Run Full Processing with Unwrap Enabled
# Time: ~60-90 minutes

set -e  # Exit on error

echo "======================================================================"
echo "ISCE2 InSAR Processing with Phase Unwrapping"
echo "======================================================================"
echo ""
echo "Working directory: /home/ubuntu/work/isce2-playbook"
echo "Config file: /workspace/input-files/topsApp_with_unwrap.xml"
echo ""
echo "Processing steps:"
echo "  ✓ Load Sentinel-1 SLC data"
echo "  ✓ Coregistration (reference + secondary)"
echo "  ✓ Interferogram generation"  
echo "  ✓ Filtering"
echo "  → Unwrapping (SNAPHU algorithm)"
echo "  → Geocoding"
echo ""
echo "Expected runtime: 60-90 minutes"
echo "======================================================================"
echo ""

# Navigate to project directory
cd /home/ubuntu/work/isce2-playbook

# Optional: Clean previous outputs (keeps raw data)
echo "Cleaning previous processing outputs..."
rm -rf merged reference secondary coarse* fine* PICKLE geom_reference 2>/dev/null || true
echo "✓ Cleaned"
echo ""

# Start processing
echo "Starting ISCE2 processing with unwrapping..."
echo "Log file: /home/ubuntu/work/isce2-playbook/isce.log"
echo ""
echo "Users can monitor progress in another terminal with:"
echo "  tail -f /home/ubuntu/work/isce2-playbook/isce.log"
echo ""
echo "======================================================================"
echo ""

# Run ISCE2 with unwrapping enabled
docker compose run --rm isce2-insar topsApp.py /workspace/input-files/topsApp_with_unwrap.xml

echo ""
echo "======================================================================"
echo "Processing Complete!"
echo "======================================================================"
echo ""
echo "Outputs in: /home/ubuntu/work/isce2-playbook/merged/"
echo ""
echo "Generated files:"
echo "  📄 filt_topophase.unw           - Unwrapped phase (radar coords)"
echo "  📄 filt_topophase.unw.conncomp  - Connected components mask"
echo "  📄 filt_topophase.unw.geo       - Unwrapped phase (geographic)"
echo "  📄 phsig.cor                    - Coherence"
echo ""
echo "Next step: Visualize displacement!"
echo "======================================================================"
