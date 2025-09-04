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

def run_misthelper(output_format="csv", menu=None, test=False, fast=False):
    """Run MistHelper in Podman container with detected executable."""
    
    # Ensure data directory exists
    data_dir = Path("./data")
    data_dir.mkdir(exist_ok=True)
    
    # Ensure script.log exists for mounting (create empty file if it doesn't exist)
    script_log_path = Path("./script.log")
    if not script_log_path.exists():
        script_log_path.touch()  # Create empty log file
        print(f"📝 Created script.log file: {script_log_path}")
    
    # Build image first
    print("🔨 Building Podman image...")
    build_cmd = [PODMAN_EXECUTABLE, "build", "-t", "misthelper", "."]
    build_result = subprocess.run(build_cmd)
    
    if build_result.returncode != 0:
        print("❌ Failed to build Podman image")
        return False
    else:
        print("✅ Smart Podman image built successfully!")
    
    # Run container
    print("🚀 Running MistHelper container...")
    print(f"📊 Output format: {output_format}")
    if menu:
        print(f"📋 Menu option: {menu}")
    else:
        print("📋 Menu option: Interactive mode")
    print(f"🧪 Test mode: {'enabled' if test else 'disabled'}")
    print(f"⚡ Fast mode: {'enabled' if fast else 'disabled'}")
    
    # Build the command with conditional arguments
    run_cmd = [
        PODMAN_EXECUTABLE, "run", "--rm", "-it",
        "-v", f"{os.getcwd()}/data:/app/data:Z",
        "-v", f"{os.getcwd()}/.env:/app/.env:Z",
        "-v", f"{os.getcwd()}/script.log:/app/script.log:Z",  # Mount script.log to persist logs
        "-e", f"OUTPUT_FORMAT={output_format}",  # Set output format via environment variable
        "-e", "PYTHONHTTPSVERIFY=0",             # Disable Python SSL verification
        "-e", "SSL_VERIFY=false",                # Disable SSL verification
        "-e", "REQUESTS_CA_BUNDLE=",             # Clear CA bundle for requests
        "-e", "CURL_CA_BUNDLE=",                 # Clear CA bundle for curl
        # Container-specific overrides: Use pip only, disable auto-features
        "-e", "DISABLE_UV_CHECK=true",           # Disable UV checking for containers
        "-e", "DISABLE_AUTO_INSTALL=true",       # Disable auto-installation for containers
        "-e", "AUTO_UPGRADE_UV=false",           # Disable UV auto-upgrade in containers
        "-e", "AUTO_UPGRADE_DEPENDENCIES=false", # Disable dependency auto-upgrade in containers
        "-e", "PYTHONPATH=/app",                 # Set Python path
        "misthelper",
        "python", "MistHelper.py",
        "--output-format", output_format         # Always add output format
    ]
    
    # Add optional menu selection
    if menu:
        run_cmd.extend(["--menu", menu])
    
    # Add optional flags
    if test:
        run_cmd.append("--test")
    if fast:
        run_cmd.append("--fast")
    
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
    parser.add_argument("--output-format", default="csv", choices=["csv", "sqlite"],
                       help="Output format (default: csv)")
    parser.add_argument("--menu", default=None, 
                       help="Menu option to execute (default: interactive mode)")
    parser.add_argument("--test", action="store_true", default=False,
                       help="Enable test mode (default: disabled)")
    parser.add_argument("--no-test", action="store_false", dest="test",
                       help="Disable test mode")
    parser.add_argument("--fast", action="store_true", default=False,
                       help="Enable fast mode (default: disabled)")
    parser.add_argument("--no-fast", action="store_false", dest="fast",
                       help="Disable fast mode")
    
    args = parser.parse_args()
    
    success = run_misthelper(args.output_format, args.menu, args.test, args.fast)
    sys.exit(0 if success else 1)
