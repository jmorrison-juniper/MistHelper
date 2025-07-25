# MistHelper Troubleshooting Guide

## Quick Diagnostics

### Health Check Commands
```bash
# Test basic functionality
python MistHelper.py --help

# Verify API connectivity
python MistHelper.py --menu 11 --debug

# Run systematic tests
python MistHelper.py --test

# Check environment configuration
python -c "import os; print('API Token:', 'SET' if os.getenv('MIST_APITOKEN') else 'NOT SET')"
```

## Common Issues and Solutions

### 1. Authentication and API Issues

#### Problem: "Authentication failed" or "401 Unauthorized"
**Symptoms:**
- Error message: "Authentication failed"
- HTTP 401 responses
- Unable to access any API endpoints

**Root Causes:**
- Invalid or expired API token
- Incorrect organization ID
- Token permissions insufficient

**Solutions:**
1. **Verify API Token**
   ```bash
   # Check .env file exists and contains token
   cat .env | grep MIST_APITOKEN
   
   # Test token validity directly
   curl -H "Authorization: Token YOUR_TOKEN" https://api.mist.com/api/v1/self
   ```

2. **Generate New Token**
   - Login to Mist dashboard → Organization → API Tokens
   - Create new token with "Organization Admin" permissions
   - Update `.env` file with new token

3. **Verify Organization ID**
   ```bash
   # List available organizations
   curl -H "Authorization: Token YOUR_TOKEN" https://api.mist.com/api/v1/orgs
   
   # Test with specific org ID
   python MistHelper.py --org YOUR_ORG_ID --menu 11
   ```

#### Problem: "403 Forbidden" or "Insufficient permissions"
**Symptoms:**
- Can authenticate but cannot access specific endpoints
- Some menu options work, others fail
- Permission denied errors

**Solutions:**
1. **Check Token Scope**
   - Ensure API token has "Organization Admin" or appropriate permissions
   - Contact organization admin to verify access rights
   - Some endpoints require specific permission levels

2. **Verify Organization Membership**
   - Confirm user account is member of target organization
   - Check for multiple organization access conflicts
   - Verify user role within organization

### 2. Installation and Dependency Issues

#### Problem: "ModuleNotFoundError: No module named 'mistapi'"
**Symptoms:**
- Import errors on startup
- Missing module errors
- Application fails to start

**Solutions:**
1. **Install Dependencies**
   ```bash
   # Standard installation
   pip install -r requirements.txt
   
   # Force reinstall if corrupted
   pip install --force-reinstall -r requirements.txt
   
   # Update specific package
   pip install --upgrade mistapi
   ```

2. **Virtual Environment Issues**
   ```bash
   # Create fresh virtual environment
   python -m venv .venv
   
   # Windows
   .venv\Scripts\activate
   pip install -r requirements.txt
   
   # Linux/macOS
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Python Version Compatibility**
   ```bash
   # Check Python version
   python --version
   # Should be 3.7 or higher
   
   # Use specific Python version
   python3.9 -m pip install -r requirements.txt
   python3.9 MistHelper.py
   ```

#### Problem: "Python version compatibility issues"
**Symptoms:**
- Syntax errors on startup
- Module incompatibility warnings
- Feature unavailability

**Solutions:**
1. **Upgrade Python**
   - **Windows**: Download from python.org
   - **macOS**: `brew install python@3.9`
   - **Linux**: `sudo apt install python3.9` or equivalent

2. **Use Containers for Consistency**
   ```bash
   # Podman (recommended)
   python setup-podman.py
   python run-misthelper.py
   
   # Docker
   docker build -t misthelper .
   docker run -it misthelper
   ```

### 3. Container and Deployment Issues

#### Problem: Container won't start or build
**Symptoms:**
- Build failures with error messages
- Container startup errors
- Permission denied in containers

**Solutions:**
1. **Check Container Runtime**
   ```bash
   # Podman diagnostics
   podman --version
   podman machine start  # Windows/macOS only
   podman system info
   
   # Docker diagnostics
   docker --version
   docker system info
   ```

2. **Fix File Permissions**
   ```bash
   # Set correct .env permissions
   chmod 600 .env
   
   # Create and set data directory permissions
   mkdir -p data
   chmod 755 data
   
   # Fix ownership if needed
   sudo chown -R $USER:$USER data .env
   ```

3. **SELinux Issues (Linux)**
   ```bash
   # Use proper SELinux labels for Podman
   podman run -it \
     -v ./data:/app/data:Z \
     -v ./.env:/app/.env:ro,Z \
     misthelper
   
   # Check SELinux status
   getenforce
   
   # Temporary disable if needed (not recommended for production)
   sudo setenforce 0
   ```

#### Problem: "Permission denied" in container
**Symptoms:**
- Cannot write to data directory
- Database creation failures
- File access errors

**Solutions:**
1. **Volume Mounting**
   ```bash
   # Correct Podman syntax with labels
   podman run -it \
     -v ./data:/app/data:Z \
     -v ./.env:/app/.env:ro,Z \
     misthelper
   
   # Docker syntax
   docker run -it \
     -v ./data:/app/data \
     -v ./.env:/app/.env:ro \
     misthelper
   ```

2. **Directory Preparation**
   ```bash
   # Create directories with correct permissions
   mkdir -p data
   chmod 755 data
   
   # For rootless containers
   podman unshare chown 0:0 data
   ```

### 4. Network and Connectivity Issues

#### Problem: "Connection timeout" or "Network unreachable"
**Symptoms:**
- API calls fail with timeout
- Cannot reach api.mist.com
- Network-related errors

**Solutions:**
1. **Basic Connectivity**
   ```bash
   # Test DNS resolution
   nslookup api.mist.com
   dig api.mist.com
   
   # Test HTTP connectivity
   curl -I https://api.mist.com
   ping api.mist.com
   ```

2. **Proxy Configuration**
   ```bash
   # Check proxy settings
   env | grep -i proxy
   
   # Test without proxy
   curl --noproxy "*" https://api.mist.com
   
   # Configure proxy in .env if needed
   echo "HTTPS_PROXY=http://proxy.company.com:8080" >> .env
   ```

3. **Corporate Firewall**
   - Contact IT to whitelist api.mist.com
   - Ensure HTTPS (443) traffic allowed
   - Check for SSL certificate inspection issues

### 5. Data Processing and Output Issues

#### Problem: "UnicodeEncodeError" or encoding issues
**Symptoms:**
- Character encoding errors
- Unicode-related crashes
- Windows-specific encoding problems

**Solutions:**
1. **Environment Variables**
   ```bash
   # Windows Command Prompt
   set PYTHONIOENCODING=utf-8
   set LANG=en_US.UTF-8
   
   # Windows PowerShell
   $env:PYTHONIOENCODING="utf-8"
   
   # Linux/macOS
   export PYTHONIOENCODING=utf-8
   export LANG=en_US.UTF-8
   ```

2. **Terminal Configuration**
   ```bash
   # Windows - use PowerShell instead of CMD
   powershell
   
   # Set console encoding
   chcp 65001
   
   # Use UTF-8 compatible terminal
   # Windows Terminal, PowerShell 7, or container deployment
   ```

3. **Container Solution**
   ```bash
   # Containers provide consistent Unicode handling
   python run-misthelper.py --output-format sqlite --menu 11
   ```

#### Problem: Empty or malformed CSV files
**Symptoms:**
- Zero-byte CSV files
- Corrupted CSV data
- Missing headers or data

**Solutions:**
1. **Debug Data Collection**
   ```bash
   # Enable debug logging
   python MistHelper.py --menu 11 --debug
   
   # Check log for API responses
   tail -f script.log
   ```

2. **Verify API Response**
   ```bash
   # Test specific endpoint manually
   curl -H "Authorization: Token YOUR_TOKEN" \
        "https://api.mist.com/api/v1/orgs/YOUR_ORG_ID/sites"
   ```

3. **Check File Permissions**
   ```bash
   # Verify write permissions
   ls -la *.csv
   
   # Fix permissions if needed
   chmod 644 *.csv
   
   # Check disk space
   df -h .
   ```

### 6. Database Issues

#### Problem: SQLite database not created or corrupted
**Symptoms:**
- Database file missing
- SQLite errors
- Empty database tables

**Solutions:**
1. **Database Diagnostics**
   ```bash
   # Check database file
   ls -la data/
   file data/mist_data.db
   
   # Test database integrity
   sqlite3 data/mist_data.db "PRAGMA integrity_check;"
   
   # List tables
   sqlite3 data/mist_data.db ".tables"
   ```

2. **Recreate Database**
   ```bash
   # Remove corrupted database
   rm data/mist_data.db
   
   # Create fresh database
   python MistHelper.py --output-format sqlite --menu 11
   ```

3. **Permission Issues**
   ```bash
   # Check directory permissions
   ls -ld data/
   
   # Fix permissions
   chmod 755 data/
   chmod 644 data/mist_data.db
   ```

### 7. Performance Issues

#### Problem: Slow API responses or timeouts
**Symptoms:**
- Operations taking excessive time
- Frequent timeout errors
- Rate limiting messages

**Solutions:**
1. **Rate Limiting Adjustment**
   ```bash
   # Increase delay between API calls
   python MistHelper.py --delay 2.0 --menu 13
   
   # Check rate limiting in logs
   grep -i "rate" script.log
   ```

2. **Network Optimization**
   ```bash
   # Test network latency
   ping api.mist.com
   
   # Use fast mode for smaller datasets
   python MistHelper.py --fast --menu 11
   ```

3. **Memory Management**
   ```bash
   # Monitor memory usage
   top -p $(pgrep -f MistHelper.py)
   
   # Use smaller batch operations
   python MistHelper.py --menu 11  # Instead of bulk operations
   ```

## Platform-Specific Issues

### Windows

#### PowerShell Execution Policy
```powershell
# Check current policy
Get-ExecutionPolicy

# Allow script execution (if needed)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### PATH Issues
```cmd
# Add Python to PATH permanently
setx PATH "%PATH%;C:\Python39;C:\Python39\Scripts"

# Temporary PATH fix
set PATH=%PATH%;C:\Python39;C:\Python39\Scripts
```

### macOS

#### Homebrew Issues
```bash
# Update Homebrew
brew update && brew upgrade

# Install Python via Homebrew
brew install python@3.9

# Fix PATH for Homebrew Python
echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

#### Permission Issues
```bash
# Fix pip permissions
python3 -m pip install --user -r requirements.txt

# Use virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Linux

#### Package Dependencies
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv sqlite3

# RHEL/CentOS/Fedora
sudo dnf install python3 python3-pip sqlite

# Install from source if needed
wget https://www.python.org/ftp/python/3.9.16/Python-3.9.16.tgz
```

#### SELinux Considerations
```bash
# Check SELinux status
getenforce

# Use proper container labels
podman run -v ./data:/app/data:Z misthelper

# Create SELinux policy if needed
audit2allow -a -M misthelper
semodule -i misthelper.pp
```

## Debugging Techniques

### Enable Comprehensive Logging
```bash
# Maximum debug output
python MistHelper.py --debug --menu 11 2>&1 | tee debug.log

# API call tracing
export PYTHONPATH=.:$PYTHONPATH
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
import mistapi
# Your MistHelper operations here
"
```

### Performance Monitoring
```bash
# Time operations
time python MistHelper.py --menu 11

# Memory profiling
python -m memory_profiler MistHelper.py --menu 11

# Network monitoring
netstat -i  # Before and after operations
```

### API Response Analysis
```bash
# Capture API responses
tcpdump -i any -w api_capture.pcap host api.mist.com

# Analyze with curl
curl -v -H "Authorization: Token TOKEN" \
     "https://api.mist.com/api/v1/orgs/ORG_ID/sites" \
     > api_response.json 2>api_headers.txt
```

## Getting Help

### Information to Provide
When seeking help, include:

1. **Environment Information**
   ```bash
   python --version
   pip list | grep mistapi
   uname -a  # Linux/macOS
   systeminfo | findstr "OS"  # Windows
   ```

2. **Error Details**
   - Complete error message
   - Steps to reproduce
   - Contents of script.log
   - Environment configuration (without sensitive data)

3. **System Configuration**
   - Operating system and version
   - Python version and installation method
   - Container runtime (if applicable)
   - Network configuration (proxy, firewall)

### Support Channels
- **Issues**: GitHub repository issues
- **Documentation**: README.md and related documentation files
- **Community**: Project discussions and forums
- **Enterprise**: Contact support through official channels

### Self-Diagnostic Tools
```bash
# Comprehensive system check
python MistHelper.py --test --debug 2>&1 | tee full_diagnostic.log

# Environment validation
python -c "
import sys, os, mistapi
print(f'Python: {sys.version}')
print(f'MistAPI: {mistapi.__version__}')
print(f'API Token: {\"SET\" if os.getenv(\"MIST_APITOKEN\") else \"NOT SET\"}')
print(f'Org ID: {os.getenv(\"org_id\", \"NOT SET\")}')
"
```

This troubleshooting guide covers the most common issues and their solutions. For complex problems, use the diagnostic tools and information gathering techniques to provide detailed information when seeking help.
   - Linux: `sudo apt install python3.9`

### 3. Container and Deployment Issues

#### Problem: Container won't start or build
**Symptoms:**
- Build failures
- Container startup errors
- Permission denied messages

**Solutions:**
1. **Check Container Runtime**
   ```bash
   # For Podman
   podman --version
   podman machine start
   
   # For Docker
   docker --version
   docker ps
   ```

2. **Verify File Permissions**
   ```bash
   # Fix .env permissions
   chmod 600 .env
   
   # Fix data directory
   mkdir -p data
   chmod 755 data
   ```

3. **SELinux Issues (Linux)**
   ```bash
   # Use proper SELinux labels
   podman run -it -v ./data:/app/data:Z -v ./.env:/app/.env:ro misthelper
   ```

4. **Container Build Issues**
   ```bash
   # Clean build
   podman build --no-cache -t misthelper .
   
   # Check Containerfile syntax
   podman build --dry-run -t misthelper .
   ```

#### Problem: "Permission denied" in container
**Symptoms:**
- Cannot write to data directory
- Database creation failures

**Solutions:**
1. **Check Volume Mounting**
   ```bash
   # Ensure proper volume syntax
   -v ./data:/app/data:Z
   ```

2. **Fix Host Directory Permissions**
   ```bash
   sudo chown -R $USER:$USER data
   chmod 755 data
   ```

3. **Run as Root (if necessary)**
   ```bash
   podman run --user root -it misthelper
   ```

### 4. Network and Connectivity Issues

#### Problem: "Connection timeout" or "Network unreachable"
**Symptoms:**
- API calls fail with timeout
- Cannot reach api.mist.com
- Network-related errors

**Solutions:**
1. **Check Internet Connection**
   ```bash
   ping api.mist.com
   curl -I https://api.mist.com
   ```

2. **Verify DNS Resolution**
   ```bash
   nslookup api.mist.com
   dig api.mist.com
   ```

3. **Check Firewall/Proxy Settings**
   ```bash
   # Check proxy settings
   env | grep -i proxy
   
   # Test direct connection
   curl --noproxy "*" https://api.mist.com
   ```

4. **Corporate Network Issues**
   - Contact IT about API access
   - Check for SSL certificate issues
   - Verify allowed domains list

### 5. Data Processing and Output Issues

#### Problem: "UnicodeEncodeError" or encoding issues
**Symptoms:**
- Character encoding errors
- Unicode-related crashes
- Windows-specific encoding problems

**Solutions:**
1. **Set Environment Variables**
   ```bash
   # Windows
   set PYTHONIOENCODING=utf-8
   
   # Linux/macOS
   export PYTHONIOENCODING=utf-8
   ```

2. **Use Container Deployment**
   ```bash
   # More consistent encoding
   python run-misthelper.py
   ```

3. **Check Terminal Encoding**
   ```bash
   # Windows - use PowerShell
   powershell
   
   # Set console encoding
   chcp 65001
   ```

#### Problem: Empty or malformed CSV files
**Symptoms:**
- Zero-byte CSV files
- Corrupted CSV data
- Missing headers

**Solutions:**
1. **Check API Response**
   ```bash
   # Enable debug logging
   python MistHelper.py --menu 1 2>&1 | grep -i error
   ```

2. **Verify Data Processing**
   ```python
   # Test data processing functions
   python test_misthelper.py
   ```

3. **Check File Permissions**
   ```bash
   ls -la *.csv
   chmod 644 *.csv
   ```

### 6. Database Issues

#### Problem: SQLite database not created or corrupted
**Symptoms:**
- Database file missing
- SQLite errors
- Empty database tables

**Solutions:**
1. **Check Database Path**
   ```bash
   ls -la data/
   file data/mist_data.db
   ```

2. **Verify Database Integrity**
   ```bash
   sqlite3 data/mist_data.db "PRAGMA integrity_check;"
   ```

3. **Recreate Database**
   ```bash
   rm data/mist_data.db
   python MistHelper.py --output-format sqlite --menu 1
   ```

4. **Check Database Permissions**
   ```bash
   chmod 644 data/mist_data.db
   ```

#### Problem: Database queries fail
**Symptoms:**
- SQL syntax errors
- Table not found errors
- Data type issues

**Solutions:**
1. **Check Table Structure**
   ```sql
   sqlite3 data/mist_data.db ".schema"
   ```

2. **Verify Data Types**
   ```sql
   sqlite3 data/mist_data.db "PRAGMA table_info(SiteList);"
   ```

3. **Test Database Connectivity**
   ```bash
   python verify_db.py
   ```

### 7. Performance Issues

#### Problem: Slow API responses or timeouts
**Symptoms:**
- Long wait times
- Timeout errors
- Incomplete data retrieval

**Solutions:**
1. **Check Rate Limiting**
   ```bash
   # Monitor logs for rate limit messages
   tail -f script.log | grep -i rate
   ```

2. **Adjust Request Timing**
   ```python
   # In MistHelper.py, increase delay
   time.sleep(1.0)  # Instead of 0.75
   ```

3. **Use Incremental Updates**
   ```bash
   # Use freshness checking
   CSV_FRESHNESS_MINUTES=30
   ```

4. **Optimize Menu Selection**
   ```bash
   # Use specific menu options instead of broad queries
   python MistHelper.py --menu 1  # Sites only
   ```

### 8. Testing and Validation Issues

#### Problem: Test failures
**Symptoms:**
- Test suite fails
- Import errors in tests
- Timeout issues in tests

**Solutions:**
1. **Run Individual Tests**
   ```bash
   python -m unittest test_misthelper.TestMistHelperUtils.test_flatten_dict_recursively
   ```

2. **Check Test Dependencies**
   ```bash
   python -c "import unittest, tempfile, subprocess; print('OK')"
   ```

3. **Verify Mock Environment**
   ```bash
   # Tests should not require actual API access
   python test_misthelper.py  # Should work without .env
   ```

## Platform-Specific Issues

### Windows

#### Problem: PowerShell execution policy
**Symptoms:**
- "Execution of scripts is disabled on this system"
- Cannot run .ps1 scripts

**Solutions:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Problem: PATH issues with containers
**Symptoms:**
- "podman is not recognized"
- "docker is not recognized"

**Solutions:**
1. **Auto-detection setup**
   ```bash
   python setup-podman.py
   ```

2. **Manual PATH setup**
   ```powershell
   $env:PATH += ";C:\Program Files\RedHat\Podman"
   ```

### macOS

#### Problem: Homebrew vs manual installation conflicts
**Symptoms:**
- Multiple Python versions
- Package conflicts

**Solutions:**
1. **Use Homebrew consistently**
   ```bash
   brew install python@3.9 podman
   ```

2. **Check Python path**
   ```bash
   which python3
   /usr/local/bin/python3 --version
   ```

### Linux

#### Problem: SELinux denials
**Symptoms:**
- Permission denied in containers
- AVC denial messages

**Solutions:**
1. **Check SELinux status**
   ```bash
   getenforce
   ```

2. **Use proper labels**
   ```bash
   podman run -v ./data:/app/data:Z misthelper
   ```

3. **Check audit logs**
   ```bash
   sudo ausearch -m avc -ts recent
   ```

## Debugging Techniques

### Enable Debug Logging

1. **Application Debug Mode**
   ```python
   # In MistHelper.py
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **API Debug Mode**
   ```bash
   # Set environment variable
   export MIST_DEBUG=1
   ```

### Check Log Files

1. **Application Logs**
   ```bash
   tail -f script.log
   ```

2. **Container Logs**
   ```bash
   podman logs misthelper
   ```

### Test Individual Components

1. **Test API Connection**
   ```python
   import mistapi
   session = mistapi.APISession(env_file=".env")
   session.login()
   ```

2. **Test Data Processing**
   ```python
   from MistHelper import flatten_dict_recursively
   test_data = {"a": {"b": {"c": 1}}}
   result = flatten_dict_recursively(test_data)
   print(result)
   ```

### Performance Monitoring

1. **Monitor API Usage**
   ```bash
   grep -i "rate\|delay\|timeout" script.log
   ```

2. **Check Memory Usage**
   ```bash
   ps aux | grep python
   htop
   ```

## Getting Help

### Information to Collect

When reporting issues, please include:

1. **System Information**
   ```bash
   python --version
   uname -a  # Linux/macOS
   systeminfo  # Windows
   ```

2. **Application State**
   ```bash
   ls -la
   cat requirements.txt
   head -20 script.log
   ```

3. **Error Messages**
   ```bash
   python MistHelper.py --help 2>&1
   ```

4. **Configuration**
   ```bash
   cat .env | grep -v TOKEN | grep -v PASSWORD
   ```

### Support Resources

1. **Documentation**
   - README.md - Main documentation
   - API-REFERENCE.md - API details
   - INSTALLATION-GUIDE.md - Setup instructions

2. **Test Suite**
   - Run comprehensive tests: `python test_misthelper.py`
   - Check specific functionality

3. **Community**
   - Check existing issues
   - Provide detailed problem descriptions
   - Include reproduction steps

This troubleshooting guide covers the most common issues encountered with MistHelper. For complex issues, refer to the comprehensive test suite and detailed logging output for additional debugging information.
