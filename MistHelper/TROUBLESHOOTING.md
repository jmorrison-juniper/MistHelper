# MistHelper Troubleshooting Guide

## Common Issues and Solutions

### 1. Authentication and API Issues

#### Problem: "Authentication failed" or "401 Unauthorized"
**Symptoms:**
- Error message: "Authentication failed"
- HTTP 401 responses
- Unable to access any API endpoints

**Solutions:**
1. **Verify API Token**
   ```bash
   # Check .env file
   cat .env | grep MIST_APITOKEN
   
   # Test token validity
   curl -H "Authorization: Token YOUR_TOKEN" https://api.mist.com/api/v1/self
   ```

2. **Check Token Permissions**
   - Login to Mist dashboard
   - Go to Organization → API Tokens
   - Ensure token has required permissions
   - Regenerate token if necessary

3. **Verify Organization ID**
   ```bash
   # List available organizations
   python MistHelper.py --menu 1
   
   # Check .env file
   cat .env | grep org_id
   ```

#### Problem: "403 Forbidden" or "Insufficient permissions"
**Symptoms:**
- Can authenticate but cannot access specific endpoints
- Some menu options work, others fail

**Solutions:**
1. **Check Token Scope**
   - Ensure API token has "Organization Admin" or appropriate permissions
   - Contact organization admin to verify access rights

2. **Verify Organization Membership**
   - Confirm user account is member of target organization
   - Check for multiple organization access

### 2. Installation and Dependency Issues

#### Problem: "ModuleNotFoundError: No module named 'mistapi'"
**Symptoms:**
- Import errors on startup
- Missing module errors

**Solutions:**
1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Check Virtual Environment**
   ```bash
   # Activate virtual environment
   source .venv/bin/activate  # Linux/macOS
   .venv\Scripts\activate     # Windows
   
   # Verify installation
   pip list | grep mistapi
   ```

3. **Update pip and setuptools**
   ```bash
   pip install --upgrade pip setuptools
   pip install -r requirements.txt
   ```

#### Problem: "Python version compatibility issues"
**Symptoms:**
- Syntax errors on startup
- Module incompatibility warnings

**Solutions:**
1. **Check Python Version**
   ```bash
   python --version
   # Should be 3.7 or higher
   ```

2. **Use Python 3 Explicitly**
   ```bash
   python3 MistHelper.py
   ```

3. **Install Python 3.7+**
   - Windows: Download from python.org
   - macOS: `brew install python@3.9`
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
