#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import pathlib
import subprocess
import sys
import hashlib
import json
from datetime import datetime, timezone

def find_boot_app0() -> pathlib.Path:
    candidates = []

    pkg_dir = os.environ.get("PLATFORMIO_PACKAGES_DIR")
    if pkg_dir:
      candidates.append(pathlib.Path(pkg_dir))

    candidates.append(pathlib.Path.home() / ".platformio" / "packages")

    for base in candidates:
        p = base / "framework-arduinoespressif32" / "tools" / "partitions" / "boot_app0.bin"
        if p.exists():
            return p

    raise FileNotFoundError("boot_app0.bin not found in PlatformIO package directories")


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge ESP32 firmware binaries into one flashable image")
    
    # Updated defaults
    parser.add_argument("--env-dir", default="firmware/.pio/build/", help="Base PlatformIO build directory")
    parser.add_argument("--export-dir", default="", help="Optional export directory for merged bins")
    parser.add_argument("--device", default="m5stick-c-plus2", choices=["m5stick-c-plus2", "m5stick-s3"], help="Target device (plus2 or s3)")
    
    parser.add_argument("--flash-mode", default="dio")
    parser.add_argument("--flash-freq", default="40m")
    parser.add_argument("--flash-size", default="4MB")
    args = parser.parse_args()

    # This map connects the friendly --device flag to the ACTUAL PlatformIO folder name
    # and the correct ESP32 chip architecture.
    device_map = {
        "m5stick-c-plus2": {
            "chip": "esp32", 
        },
        "m5stick-s3": {
            "chip": "esp32s3", 
        }
    }
    
    config = device_map[args.device]
    
    # CRITICAL: Construct the path to the specific environment folder
    # Result: firmware/.pio/build/m5stick-s3/ (for example)
    env_folder = pathlib.Path(args.env_dir) / args.device
    out_path = env_folder / f"tosstalk_merged.bin"    
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # All files are now looked for inside the specific env folder
    bootloader = env_folder / "bootloader.bin"
    partitions = env_folder / "partitions.bin"
    app = env_folder / "firmware.bin"
    boot_app0 = find_boot_app0()

    required = [bootloader, partitions, app, boot_app0]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        # Provide a helpful error message showing exactly where the script looked
        raise FileNotFoundError(f"Missing required files in {env_folder}:\n{missing}")

    cmd = [
        "esptool",
        "--chip",
        config["chip"], 
        "merge_bin",
        "-o",
        str(out_path),
        "--flash_mode",
        args.flash_mode,
        "--flash_freq",
        args.flash_freq,
        "--flash_size",
        args.flash_size,
        "0x1000",
        str(bootloader),
        "0x8000",
        str(partitions),
        "0xe000",
        str(boot_app0),
        "0x10000",
        str(app),
    ]

    subprocess.run(cmd, check=True)
    print(f"Successfully merged {args.device} firmware: {out_path}")

    # Output can be optionally copied into another destination
    if args.export_dir:
        export_folder = pathlib.Path(args.export_dir)
        export_path = export_folder / f"tosstalk_merged.bin"
        export_path.parent.mkdir(parents=True, exist_ok=True)
   
        cmd = [
            "cp",
            str(out_path),
            str(export_path),
        ]
        subprocess.run(cmd, check=True)

        digest = hashlib.sha256(export_path.read_bytes()).hexdigest()
        meta = {
            'file': export_path.name,
            'sha256': digest,
            'size': export_path.stat().st_size,
            'generatedAtUtc': datetime.now(timezone.utc).isoformat(),
        }
        
        manifest_path = export_folder / "manifest.json"
        manifest_path.write_text(json.dumps(meta, indent=2) + '\n')
        
        print(f"Exported merged firmware to {export_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
