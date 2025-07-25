#!/usr/bin/env python3
"""
Cross-platform MistHelper Podman wrapper
Auto-generated with detected Podman path: C:\\Program Files\\RedHat\\Podman\\podman.exe
"""

import sys
import subprocess
import os
from pathlib import Path

PODMAN_EXECUTABLE = r"C:\\Program Files\\RedHat\\Podman\\podman.exe"

def run_misthelper(output_format=None, menu=None):
    """Run MistHelper in Podman container with detected executable."""
    
    # Ensure data directory exists
    data_dir = Path("./data")
    data_dir.mkdir(exist_ok=True)
    
    # Build image first
    print("🔨 Building Podman image...")
    build_cmd = [PODMAN_EXECUTABLE, "build", "-t", "misthelper", "."]
    build_result = subprocess.run(build_cmd)
    
    if build_result.returncode != 0:
        print("❌ Failed to build Podman image")
        return False
    
    # Run container
    print("🚀 Running MistHelper container...")
    if output_format:
        print(f"📊 Output format: {output_format}")
    if menu:
        print(f"📋 Menu option: {menu}")
    
    run_cmd = [
        PODMAN_EXECUTABLE, "run", "--rm", "-it",
        "-v", f"{os.getcwd()}/data:/app/data:Z",
        "-v", f"{os.getcwd()}/.env:/app/.env:Z",
        "misthelper",
        "python", "MistHelper.py"
    ]
    
    # Only add arguments if they're provided
    if output_format:
        run_cmd.extend(["--output-format", output_format])
    if menu:
        run_cmd.extend(["--menu", menu])
    
    result = subprocess.run(run_cmd)
    
    if result.returncode == 0:
        print("✅ MistHelper completed successfully!")
        print(f"📁 Check ./data directory for output files")
    else:
        print("❌ MistHelper encountered an error")
    
    return result.returncode == 0

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Cross-platform MistHelper Podman runner")
    parser.add_argument("--output-format", choices=["csv", "sqlite"],
                       help="Output format (if not specified, runs interactively)")
    parser.add_argument("--menu", 
                       help="Menu option to execute (if not specified, shows interactive menu)")
    
    args = parser.parse_args()
    
    success = run_misthelper(args.output_format, args.menu)
    sys.exit(0 if success else 1)
