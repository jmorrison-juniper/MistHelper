#!/usr/bin/env python3
"""
Cross-platform Podman detection and PATH management utility
Handles Podman installation detection across Windows, macOS, and Linux
"""

import os
import sys
import platform
import subprocess
from pathlib import Path

def detect_podman_executable():
    """
    Detect Podman executable across different platforms and installation methods.
    Returns the full path to podman executable or None if not found.
    """
    system = platform.system().lower()
    
    # Common Podman installation paths by platform
    common_paths = {
        'windows': [
            r'C:\Program Files\RedHat\Podman\podman.exe',
            r'C:\Program Files (x86)\RedHat\Podman\podman.exe',
            r'C:\ProgramData\chocolatey\bin\podman.exe',
            os.path.expanduser(r'~\AppData\Local\Podman\podman.exe'),
        ],
        'darwin': [  # macOS
            '/usr/local/bin/podman',
            '/opt/homebrew/bin/podman',
            '/usr/bin/podman',
            os.path.expanduser('~/bin/podman'),
        ],
        'linux': [
            '/usr/bin/podman',
            '/usr/local/bin/podman',
            '/opt/podman/bin/podman',
            os.path.expanduser('~/bin/podman'),
            os.path.expanduser('~/.local/bin/podman'),
        ]
    }
    
    # First, try to find podman in PATH
    try:
        result = subprocess.run(['podman', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            # Get the actual path
            which_cmd = 'where' if system == 'windows' else 'which'
            which_result = subprocess.run([which_cmd, 'podman'], 
                                        capture_output=True, text=True, timeout=5)
            if which_result.returncode == 0:
                return which_result.stdout.strip().split('\n')[0]
            return 'podman'  # It's in PATH but we can't determine exact location
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    # If not in PATH, check common installation locations
    paths_to_check = common_paths.get(system, [])
    
    for path in paths_to_check:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            try:
                # Verify it actually works
                result = subprocess.run([path, '--version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return path
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                continue
    
    return None

def add_podman_to_path_instructions():
    """
    Provide platform-specific instructions for adding Podman to PATH.
    """
    system = platform.system().lower()
    
    instructions = {
        'windows': """
To add Podman to your Windows PATH:

1. **Windows 10/11 (Settings UI):**
   - Press Win + I to open Settings
   - Go to System → About → Advanced system settings
   - Click "Environment Variables"
   - Under "System variables", find and select "Path"
   - Click "Edit" → "New"
   - Add: C:\\Program Files\\RedHat\\Podman
   - Click OK on all dialogs

2. **PowerShell (Temporary for current session):**
   $env:PATH += ";C:\\Program Files\\RedHat\\Podman"

3. **PowerShell (Permanent):**
   [Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\\Program Files\\RedHat\\Podman", "User")

4. **Command Prompt (Temporary):**
   set PATH=%PATH%;C:\\Program Files\\RedHat\\Podman
""",
        'darwin': """
To add Podman to your macOS PATH:

1. **For Homebrew installation:**
   echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
   source ~/.zshrc

2. **For manual installation:**
   echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.zshrc
   source ~/.zshrc

3. **Verify installation:**
   podman --version
""",
        'linux': """
To add Podman to your Linux PATH:

1. **For package manager installation (usually automatic):**
   - Ubuntu/Debian: sudo apt install podman
   - RHEL/CentOS/Fedora: sudo dnf install podman
   - Arch: sudo pacman -S podman

2. **For manual installation:**
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
   source ~/.bashrc

3. **Verify installation:**
   podman --version
"""
    }
    
    return instructions.get(system, "Platform-specific instructions not available.")

def generate_cross_platform_script():
    """
    Generate a cross-platform wrapper script that handles Podman detection.
    """
    podman_path = detect_podman_executable()
    
    if not podman_path:
        print("❌ Podman not found!")
        print("\n" + add_podman_to_path_instructions())
        return False
    
    print(f"✅ Podman found at: {podman_path}")
    
    # Generate Python wrapper script
    wrapper_content = f'''#!/usr/bin/env python3
"""
Cross-platform MistHelper Podman wrapper
Auto-generated with detected Podman path: {podman_path.replace(chr(92), chr(92) + chr(92))}
"""

import sys
import subprocess
import os
from pathlib import Path

PODMAN_EXECUTABLE = r"{podman_path.replace(chr(92), chr(92) + chr(92))}"

def run_misthelper(output_format="sqlite", menu="11"):
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
    print(f"📊 Output format: {{output_format}}")
    print(f"📋 Menu option: {{menu}}")
    
    run_cmd = [
        PODMAN_EXECUTABLE, "run", "--rm", "-it",
        "-v", f"{{os.getcwd()}}/data:/app/data:Z",
        "-v", f"{{os.getcwd()}}/.env:/app/.env:Z",
        "misthelper",
        "python", "MistHelper.py",
        "--output-format", output_format,
        "--menu", menu
    ]
    
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
    parser.add_argument("--output-format", default="sqlite", choices=["csv", "sqlite"],
                       help="Output format (default: sqlite)")
    parser.add_argument("--menu", default="11", 
                       help="Menu option to execute (default: 11)")
    
    args = parser.parse_args()
    
    success = run_misthelper(args.output_format, args.menu)
    sys.exit(0 if success else 1)
'''
    
    # Write the wrapper script
    with open("run-misthelper.py", "w", encoding="utf-8") as f:
        f.write(wrapper_content)
    
    # Make it executable on Unix-like systems
    if platform.system() != "Windows":
        os.chmod("run-misthelper.py", 0o755)
    
    print("✅ Generated cross-platform wrapper: run-misthelper.py")
    print("\nUsage examples:")
    print("  python run-misthelper.py")
    print("  python run-misthelper.py --output-format csv --menu 12")
    
    return True

if __name__ == "__main__":
    print("🔍 Detecting Podman installation...")
    generate_cross_platform_script()
