# MistHelper Podman Setup Guide

This guide helps you set up and run MistHelper in a Podman container across different operating systems, avoiding common PATH issues.

## Quick Start

### Option 1: Automatic Detection (Recommended)
```bash
python setup-podman.py
python run-misthelper.py --output-format sqlite --menu 11
```

### Option 2: Platform-Specific Scripts

**Windows PowerShell:**
```powershell
.\run-podman.ps1 -OutputFormat sqlite -Menu 11
```

**Windows Batch:**
```cmd
run-podman.bat 11
```

**Cross-Platform Python:**
```bash
python run-misthelper.py --output-format sqlite --menu 11
```

## Common PATH Issues and Solutions

### Windows

**Problem:** `'podman' is not recognized as an internal or external command`

**Solutions:**

1. **Automatic Detection:** Run `python setup-podman.py` to generate a cross-platform wrapper
2. **Manual PATH Setup:**
   - Add `C:\Program Files\RedHat\Podman` to your system PATH
   - Or use the enhanced PowerShell script that auto-detects Podman location

**PowerShell PATH Fix (Temporary):**
```powershell
$env:PATH += ";C:\Program Files\RedHat\Podman"
```

**PowerShell PATH Fix (Permanent):**
```powershell
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\Program Files\RedHat\Podman", "User")
```

### macOS

**Problem:** `podman: command not found`

**Solutions:**

1. **Homebrew Installation:**
   ```bash
   brew install podman
   ```

2. **Manual PATH Setup:**
   ```bash
   echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
   source ~/.zshrc
   ```

### Linux

**Problem:** `podman: command not found`

**Solutions:**

1. **Package Manager Installation:**
   ```bash
   # Ubuntu/Debian
   sudo apt install podman
   
   # RHEL/CentOS/Fedora
   sudo dnf install podman
   
   # Arch Linux
   sudo pacman -S podman
   ```

2. **Manual Installation:**
   ```bash
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
   source ~/.bashrc
   ```

## Database Field Preservation

### ID Fields Issue
The original implementation dropped API `id` fields to avoid SQLite conflicts. We've fixed this:

**Old Behavior:** API `id` fields were discarded
**New Behavior:** API fields are preserved as:
- `id` → `api_id`
- `timestamp` → `api_timestamp`

### Verification
Check your database to see preserved ID fields:
```python
import sqlite3
conn = sqlite3.connect('./data/mist_data.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(SiteList)")
columns = cursor.fetchall()
for col in columns:
    print(f"Column: {col[1]}, Type: {col[2]}")
```

## Script Selection Guide

| Platform | Best Choice | Reason |
|----------|-------------|---------|
| Windows 10+ | `setup-podman.py` then `run-misthelper.py` | Cross-platform, auto-detection |
| Windows (Legacy) | `run-podman.bat` | No PowerShell restrictions |
| macOS | `setup-podman.py` then `run-misthelper.py` | Handles Homebrew vs manual installs |
| Linux | `setup-podman.py` then `run-misthelper.py` | Handles various package managers |

## Troubleshooting

### Container Won't Start
1. Ensure Podman Desktop is running
2. Check if `.env` file exists with proper API credentials
3. Verify data directory permissions

### Permission Issues (Linux/macOS)
```bash
# Make scripts executable
chmod +x setup-podman.py
chmod +x run-misthelper.py
```

### SELinux Issues (Linux)
The scripts use `:Z` flags for proper SELinux labeling:
```bash
-v ./data:/app/data:Z
```

### Database Not Created
1. Check container logs for errors
2. Verify menu option exists (1-47)
3. Ensure API credentials are valid

## Development

### Adding New Platforms
Extend the `common_paths` dictionary in `setup-podman.py`:
```python
'new_platform': [
    '/path/to/podman',
    '/alternative/path/podman'
]
```

### Testing Different Menu Options
```bash
# Test various menu options
python run-misthelper.py --menu 1   # Organization info
python run-misthelper.py --menu 11  # Site list
python run-misthelper.py --menu 12  # Device inventory
```

## Support

If you encounter issues:
1. Run `python setup-podman.py` for automatic detection
2. Check the generated `run-misthelper.py` script
3. Verify Podman installation with manual commands
4. Check container logs for application-specific errors
