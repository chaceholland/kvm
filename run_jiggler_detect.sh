#!/bin/bash
# Run Mouse Jiggler Detector on Work Mac
# Usage: curl the script or copy it over, then: bash run_jiggler_detect.sh

set -e

SCRIPT_URL="https://raw.githubusercontent.com/chaceholland/kvm/claude/detect-mouse-jiggler-XaEl4/detect_jiggler.py"
SCRIPT_NAME="detect_jiggler.py"

echo "=== Mouse Jiggler Detector Setup ==="
echo ""

# Check for Python 3
if ! command -v python3 &>/dev/null; then
    echo "Error: python3 not found. Install Python 3 first."
    exit 1
fi

# Install dependency if missing
if ! python3 -c "import Quartz" 2>/dev/null; then
    echo "Installing pyobjc-framework-Quartz..."
    pip3 install --user pyobjc-framework-Quartz
    echo ""
fi

# Download the detector script if not present
if [ ! -f "$SCRIPT_NAME" ]; then
    echo "Downloading detect_jiggler.py..."
    curl -fsSL "$SCRIPT_URL" -o "$SCRIPT_NAME"
    echo ""
fi

# Check Accessibility permission
echo "NOTE: Terminal needs Accessibility permission to monitor mouse events."
echo "  System Settings > Privacy & Security > Accessibility > enable Terminal"
echo ""

# Run detector
echo "Starting jiggler detection (Ctrl+C to stop and see final report)..."
echo ""
python3 "$SCRIPT_NAME" "$@"
