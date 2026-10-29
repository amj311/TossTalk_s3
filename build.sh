#!/bin/bash

# Define the devices
DEVICES=("m5stick-c-plus2" "m5stick-s3")

for DEVICE in "${DEVICES[@]}"; do
    echo "================================================="
    echo "--- Processing Device: $DEVICE ---"
    echo "================================================="
    
    # 1. Run pio build for the current device
    echo "Step 1/2: Running pio build for $DEVICE..."
	cd firmware
    pio run -e "$DEVICE"
    
    # 2. Merge firmware for the current device
    echo ""
    echo "Step 2/2: Running merge firmware script for $DEVICE..."
	cd ..
    # Check if the script was run with --export argument
    if [[ "$@" =~ "--export" ]]; then
        python3 scripts/merge_firmware.py --device "$DEVICE" --export-dir web/firmware/"$DEVICE"
    else
        python3 scripts/merge_firmware.py --device "$DEVICE"
    fi
    
    echo "-------------------------------------------------"
    echo "Successfully processed $DEVICE."
    echo "-------------------------------------------------"
done

echo "================================================="
echo "Build process completed for all defined devices."
echo "================================================="