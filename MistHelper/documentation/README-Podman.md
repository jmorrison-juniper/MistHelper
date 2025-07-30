# DEPRECATED: MistHelper with Podman - Setup Guide

> **⚠️ NOTICE: This file is deprecated**
> 
> This documentation has been consolidated into **PODMAN_SETUP.md** for better organization and maintenance.
> Please refer to [PODMAN_SETUP.md](PODMAN_SETUP.md) for current Podman setup instructions.
>
> This file will be removed in a future release.

## Migration Notice

All information from this file has been merged into `PODMAN_SETUP.md`, which provides:
- More comprehensive setup instructions
- Updated troubleshooting information
- Better cross-platform guidance
- Integration with the automatic setup scripts

For the most current and complete Podman setup information, please use:
```bash
# View the current setup guide
cat PODMAN_SETUP.md

# Use automatic setup
python setup-podman.py
python run-misthelper.py
```
sudo dnf install podman podman-compose

# Ubuntu/Debian  
sudo apt install podman podman-compose
```

**macOS:**
```bash
brew install podman podman-compose
```

## Updated Scripts

### PowerShell Script (run-docker.ps1)
The script has been updated with these changes:
- `docker` → `podman` in all commands
- Added `:Z` flags to volume mounts
- Updated error messages to reference Podman Desktop
- Modified database access command

### Batch Script (run-podman.bat)
New Podman-specific batch file:
- Native Podman commands
- Proper Windows path handling with `:Z` flags
- Podman-specific error messages

### Compose File (podman-compose.yml)
Podman-specific compose file:
- Removed unnecessary network definitions
- Added `:Z` flags to volume mounts
- Podman-specific comments

## Usage Examples

### Basic Commands

```bash
# Build image
podman build -t misthelper:latest .

# Run interactively
podman run -it --rm \
  -v "./data:/app/data:Z" \
  -v "./.env:/app/.env:ro,Z" \
  misthelper:latest

# Run specific menu item
podman run --rm \
  -v "./data:/app/data:Z" \
  -v "./.env:/app/.env:ro,Z" \
  misthelper:latest python MistHelper.py --menu 1

# Access database
podman run --rm -it \
  -v "./data:/app/data:Z" \
  misthelper:latest sqlite3 /app/data/mist_data.db
```

### Windows PowerShell

```powershell
# Updated script
.\run-docker.ps1

# Manual commands
podman build -t misthelper:latest .
podman run -it --rm -v "${PWD}/data:/app/data:Z" -v "${PWD}/.env:/app/.env:ro,Z" misthelper:latest
```

### Using Podman Compose

```bash
# Install podman-compose if not available
pip install podman-compose

# Use the Podman-specific compose file
podman-compose -f podman-compose.yml up --build

# Run specific commands
podman-compose -f podman-compose.yml run --rm misthelper python MistHelper.py --menu 11
```

## Troubleshooting Podman Issues

### 1. Permission Denied Errors

**Problem:** Volume mount permission issues
**Solution:** Use `:Z` flag for SELinux labeling
```bash
-v "./data:/app/data:Z"
```

### 2. Podman Machine Not Running (Windows/macOS)

**Problem:** "cannot connect to Podman socket"
**Solution:**
```bash
podman machine start
podman machine list  # Verify running
```

### 3. WSL2 Issues (Windows)

**Problem:** Podman fails to start on Windows
**Solution:**
- Ensure WSL2 is installed and updated
- Restart Podman Desktop
- Try: `wsl --update`

### 4. Container Won't Start

**Problem:** Container exits immediately
**Solution:**
```bash
# Check logs
podman logs misthelper-interactive

# Run with debug
podman run -it --rm -v "./data:/app/data:Z" misthelper:latest python MistHelper.py --debug --menu 1
```

### 5. Database File Not Persistent

**Problem:** Database doesn't persist between runs
**Solution:**
- Ensure data directory exists: `mkdir data`
- Check volume mount syntax includes `:Z`
- Verify permissions: `ls -la data/`

## Performance Considerations

### Podman Advantages
- **Rootless:** More secure by default
- **No Daemon:** Lower resource usage
- **SELinux:** Better security integration on RHEL/Fedora
- **Compatibility:** Drop-in replacement for most Docker commands

### Podman Considerations
- **Windows:** Requires WSL2 (additional overhead)
- **Compose:** May need separate podman-compose installation
- **Learning Curve:** Slight differences in volume handling

## Migration Checklist

- [ ] Install Podman Desktop (Windows) or podman package (Linux)
- [ ] Replace `docker` with `podman` in all commands
- [ ] Add `:Z` flags to volume mounts
- [ ] Update scripts to use `podman` commands
- [ ] Test container build: `podman build -t misthelper:latest .`
- [ ] Test container run with volume mount
- [ ] Verify database persistence
- [ ] Test interactive mode
- [ ] Update documentation and scripts

## Files Changed for Podman

1. **run-docker.ps1** → Updated with Podman commands
2. **run-podman.bat** → New Podman-specific batch file  
3. **podman-compose.yml** → New Podman-specific compose file
4. **README-Podman.md** → This documentation

The original Docker files remain unchanged, so you can use either Docker or Podman depending on your preference and environment.
