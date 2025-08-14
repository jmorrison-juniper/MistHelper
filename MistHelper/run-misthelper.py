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
    build_result = subprocess.run(build_cmd, capture_output=True, text=True)
    
    if build_result.returncode != 0:
        print("❌ Failed to build Podman image")
        print("Error details:")
        if build_result.stderr:
            print(build_result.stderr)
        if build_result.stdout:
            print(build_result.stdout)
        
        # Check if it's a UV-related error and suggest fallback
        error_output = (build_result.stderr + build_result.stdout).lower()
        if "ghcr.io/astral-sh/uv" in error_output or "uv:latest" in error_output:
            print("\n💡 UV installation issue detected. Trying fallback methods...")
            
            # Try fallback #1: Official UV installer
            if Path("Containerfile.uv-official").exists():
                print("🔄 Fallback #1: Attempting build with official UV installer...")
                fallback_cmd = [PODMAN_EXECUTABLE, "build", "-f", "Containerfile.uv-official", "-t", "misthelper", "."]
                fallback_result = subprocess.run(fallback_cmd, capture_output=True, text=True)
                
                if fallback_result.returncode == 0:
                    print("✅ Fallback #1 successful!")
                    # Don't return here, continue to run the container
                else:
                    print("❌ Fallback #1 failed")
                    if "curl" in fallback_result.stderr.lower() or "network" in fallback_result.stderr.lower():
                        print("   Network connectivity issue detected")
            
            # Try fallback #2: Traditional pip (no UV)
            if Path("Containerfile.pip-fallback").exists():
                print("� Fallback #2: Attempting build with traditional pip (no UV)...")
                pip_fallback_cmd = [PODMAN_EXECUTABLE, "build", "-f", "Containerfile.pip-fallback", "-t", "misthelper", "."]
                pip_result = subprocess.run(pip_fallback_cmd, capture_output=True, text=True)
                
                if pip_result.returncode == 0:
                    print("✅ Fallback #2 successful (using pip instead of UV)!")
                    print("   Note: Container will use pip for dependency management")
                    # Don't return here, continue to run the container
                else:
                    print("❌ Fallback #2 also failed")
                    if pip_result.stderr:
                        print("   Error:", pip_result.stderr.split('\n')[0])
            
            # All fallbacks failed
            print("\n❌ All container build methods failed")
            print("🛠️ Alternative options:")
            print("1. Run directly: python MistHelper.py")
            print("2. Check network connectivity")
            print("3. Try Docker instead of Podman")
            print("4. Verify Podman installation: podman --version")
            return False
        else:
            print("\n🛠️ General troubleshooting:")
            print("1. Check Podman installation: podman --version")
            print("2. Try direct execution: python MistHelper.py")
            print("3. Verify .env file exists")
            return False
    else:
        print("✅ Podman image built successfully!")
    
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
