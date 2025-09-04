# MistHelper Installation and Configuration Guide

## System Requirements

### Operating System Support
- **Windows**: Windows 10 build 1809 or later, Windows Server 2019 or later
- **macOS**: macOS 10.14 Mojave or later
- **Linux**: Ubuntu 18.04 LTS, CentOS 7, RHEL 8, or equivalent distributions

### Runtime Requirements
- **Python**: Version 3.8 or higher (3.9+ recommended for optimal performance)
- **Memory**: 512MB RAM minimum, 1GB recommended for large datasets
- **Storage**: 100MB for application files, additional space for data storage based on organization size
- **Network**: Internet connectivity for Mist API access (HTTPS to api.mist.com)

### API Prerequisites
- **Juniper Mist Account**: Active subscription with API access enabled
- **API Token**: Organization-level API token with appropriate permissions
- **Organization ID**: Mist organization identifier (UUID format)

## Installation Methods

### Method 1: Standard Python Installation

1. **Repository Setup**
   ```bash
   git clone <repository-url>
   cd MistHelper
   ```

2. **Virtual Environment Setup** (Recommended)
   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate.bat

   # macOS/Linux
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Dependency Installation**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   ```bash
   cp documentation/sample.env .env
   # Configure .env with API credentials
   ```

5. **Installation Verification**
   ```bash
   python MistHelper.py --help
   ```

### Method 2: Container Deployment

#### Podman Deployment (Recommended for Production)

1. **Podman Installation**
   - **Windows**: Install Podman Desktop from https://podman-desktop.io/
   - **macOS**: `brew install podman`
   - **Linux**: Distribution package manager (e.g., `dnf install podman`, `apt install podman`)

2. **Environment Setup**
   ```bash
   git clone <repository-url>
   cd MistHelper
   cp documentation/sample.env .env
   # Configure API credentials in .env
   ```

3. **Automated Container Setup**
   ```bash
   python setup-podman.py
   python run-misthelper.py --output-format sqlite --menu 1
   ```

#### Docker Deployment

1. **Docker Installation**
   - **Windows/macOS**: Docker Desktop from https://www.docker.com/products/docker-desktop
   - **Linux**: Distribution package manager or Docker's official installation script

2. **Container Setup**
   ```bash
   git clone <repository-url>
   cd MistHelper
   cp documentation/sample.env .env
   # Configure API credentials in .env
   ```

3. **Container Build and Execution**
   ```bash
   docker build -t misthelper .
   docker run -it -v ./data:/app/data -v ./.env:/app/.env:ro misthelper
   ```

## Configuration

### Environment Configuration File

Create a `.env` file in the project root directory with the following parameters:

```env
# Mist API Configuration (Required)
MIST_HOST=api.mist.com
MIST_APITOKEN=your_api_token_here
MIST_USERNAME=your_username@example.com  # Legacy authentication (optional)
MIST_PASSWORD=your_password              # Legacy authentication (optional)

# Organization Configuration
org_id=your_organization_id              # Optional, will prompt if not provided

# Application Configuration
CSV_FRESHNESS_MINUTES=15                 # Data cache duration
OUTPUT_FORMAT=csv                        # Default output format

# Auto-Upgrade Configuration (Optional)
AUTO_UPGRADE_UV=true                     # Enable UV package manager auto-upgrade
AUTO_UPGRADE_DEPENDENCIES=true           # Enable dependency auto-upgrade
UPGRADE_CHECK_TIMEOUT=60                 # Upgrade operation timeout (seconds)
```

### API Token Generation

1. **Access Mist Dashboard**
   - Navigate to https://manage.mist.com
   - Authenticate with administrative credentials

2. **Token Creation**
   - Go to Organization Settings → API Tokens
   - Click "Create Token"
   - Configure appropriate permissions:
     - **Read-only operations**: Organization Read permissions
     - **Full functionality**: Organization Admin permissions
   - Copy the generated token value

3. **Organization ID Retrieval**
   - Organization ID is displayed in the dashboard URL:
   ```
   https://manage.mist.com/admin/?org_id=12345678-1234-1234-1234-123456789abc
   ```

### File Permissions and Security

Set appropriate file permissions for credential security:

```bash
# Restrict .env file access (Unix-like systems)
chmod 600 .env

# Set script execution permissions
chmod +x setup-podman.py run-misthelper.py
```

## Initial Operation

### First-Time Setup

1. **Application Launch**
   ```bash
   python MistHelper.py
   ```

2. **Organization Selection**
   - If `org_id` is not configured in `.env`, the application will display available organizations
   - Select the appropriate organization from the list

3. **Connectivity Testing**
   ```bash
   # Test basic API connectivity with site list export
   python MistHelper.py --output-format csv --menu 11

   # Test SQLite database functionality
   python MistHelper.py --output-format sqlite --menu 11
   ```

### Output Verification

**CSV Output Verification:**
```bash
# Check generated CSV files
ls -la *.csv

# Examine sample data structure
head -20 SiteList.csv
```

**SQLite Database Verification:**
```bash
# Verify database creation
ls -la data/mist_data.db

# Examine database structure and contents
sqlite3 data/mist_data.db ".tables"
sqlite3 data/mist_data.db "SELECT * FROM SiteList LIMIT 5;"
```

## Troubleshooting

### Authentication Issues

#### API Token Authentication Failure
```
Error: HTTP 401 Unauthorized
```
**Resolution Steps:**
- Verify API token value in `.env` file
- Check token permissions in Mist dashboard
- Confirm organization ID matches token scope
- Validate token expiration status

#### Organization Access Denied
```
Error: HTTP 403 Forbidden
```
**Resolution Steps:**
- Confirm API token has Organization-level permissions
- Verify organization ID is correct
- Check if organization is active and accessible

### Dependency Installation Issues

#### Module Import Errors
```
ModuleNotFoundError: No module named 'mistapi'
```
**Resolution Steps:**
- Activate virtual environment if configured
- Execute: `pip install -r requirements.txt`
- Verify Python version compatibility: `python --version`
- Check pip installation: `pip --version`

#### UV Package Manager Issues
```
Command 'uv' not found
```
**Resolution Steps:**
- UV installation is optional; application will fall back to pip
- Manual UV installation: `pip install uv`
- Bypass UV check: `python MistHelper.py --skip-deps`

### Container Runtime Issues

#### Volume Mount Permission Errors
```
Permission denied: /app/data
```
**Resolution Steps:**
- Create data directory: `mkdir -p data`
- Set directory permissions: `chmod 755 data`
- Use SELinux-compatible volume flags: `:Z` for Podman/Docker on RHEL-based systems

#### Container Build Failures
```
Error building container image
```
**Resolution Steps:**
- Verify container runtime installation: `podman --version` or `docker --version`
- Check system resources (disk space, memory)
- Rebuild with verbose output: `podman build --verbose -t misthelper .`

### Unicode and Encoding Issues (Windows-Specific)

#### Character Encoding Errors
```
UnicodeEncodeError: 'charmap' codec can't encode character
```
**Resolution Steps:**
- Use PowerShell instead of Command Prompt
- Set environment variable: `set PYTHONIOENCODING=utf-8`
- Consider container deployment for consistent environment

### API Rate Limiting

#### Rate Limit Exceeded
```
HTTP 429: Too Many Requests
```
**Resolution Steps:**
- MistHelper includes automatic rate limiting
- Increase delay between operations if needed
- Use SQLite output format for better performance
- Monitor API usage in Mist dashboard

## Performance Optimization

### Output Format Selection

1. **SQLite for Large Datasets**
   ```bash
   python MistHelper.py --output-format sqlite
   ```
   - More efficient for large data volumes
   - Enables SQL queries and joins
   - Single file storage

2. **CSV for Data Export**
   ```bash
   python MistHelper.py --output-format csv
   ```
   - Direct Excel compatibility
   - Easy data sharing
   - Human-readable format

### Data Freshness Management

Configure cache duration to balance performance and data currency:
```env
CSV_FRESHNESS_MINUTES=15  # Adjust based on operational requirements
```

### API Usage Monitoring

Monitor API consumption through:
- `script.log` for rate limiting messages
- Mist dashboard API usage statistics
- Selective menu option usage for specific data requirements

## Platform-Specific Considerations

### Windows Deployment
- PowerShell recommended over Command Prompt for Unicode support
- Windows Terminal provides enhanced console experience
- Container deployment resolves most environment consistency issues

### macOS Deployment
- May require developer certificate acceptance for unsigned binaries
- Homebrew provides convenient dependency management
- Docker Desktop integration works seamlessly

### Linux Deployment
- SELinux-enabled systems require `:Z` volume mount flags
- Multiple package managers supported (apt, yum, dnf, zypper)
- Rootless container execution recommended for security

## Advanced Configuration

### Custom Output Locations

Modify configuration variables in MistHelper.py for custom output paths:

```python
# Custom database location
DATABASE_PATH = "/custom/path/mist_data.db"

# Custom CSV output directory
CSV_OUTPUT_DIR = "/custom/csv/output/"
```

### API Rate Limiting Configuration

Adjust rate limiting parameters for specific environments:

```python
# API timing configuration in MistHelper.py
API_DELAY_SECONDS = 0.75  # Base delay between API calls
MAX_RETRIES = 3           # Retry attempts on failures
TIMEOUT_SECONDS = 30      # Request timeout duration
```

### Logging Configuration

Configure logging verbosity for operational requirements:

```python
# Logging level configuration
logging.basicConfig(level=logging.DEBUG)    # Detailed debugging information
logging.basicConfig(level=logging.INFO)     # Standard operational logging
logging.basicConfig(level=logging.WARNING)  # Errors and warnings only
```

## Validation and Testing

### Comprehensive Test Suite

Execute the complete test suite to verify installation:

```bash
python test_misthelper.py
```

Expected output confirms successful installation:
```
MistHelper Comprehensive Test Suite
==================================================
...
----------------------------------------------------------------------
Ran 19 tests in 25.565s

OK
```

### Database Integrity Verification

Validate database structure and content:

```bash
python verify_db.py
```

### API Connectivity Testing

Verify API access and basic functionality:

```bash
python MistHelper.py --menu 1  # Test with organization alarms
```

## Security Configuration

### Credential Protection

1. **Environment File Security**
   - Never commit `.env` files to version control systems
   - Set restrictive file permissions (600) on credential files
   - Implement regular API token rotation

2. **Container Security**
   - Use rootless containers when possible
   - Keep base container images updated
   - Limit container network access to required endpoints

3. **Data Protection**
   - Implement encryption for sensitive data at rest
   - Use secure backup strategies for database files
   - Monitor access to output files containing network information

## Support and Documentation References

- **Primary Documentation**: README.md for comprehensive usage information
- **Container Deployment**: PODMAN_SETUP.md for containerization details
- **Technical Architecture**: IMPLEMENTATION-SUMMARY.md for implementation details
- **Project Structure**: FILE-VERIFICATION.md for file organization

This installation guide provides comprehensive setup procedures for all supported deployment methods and platforms. Select the method that best aligns with your operational environment and security requirements.
