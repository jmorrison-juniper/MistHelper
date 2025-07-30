# MistHelper Installation and Setup Guide

## Prerequisites

### System Requirements
- **Operating System**: Windows 10+, macOS 10.14+, or Linux (Ubuntu 18.04+, CentOS 7+, RHEL 8+)
- **Python**: Version 3.7 or higher
- **Memory**: 512MB RAM minimum, 1GB recommended
- **Storage**: 100MB for application, additional space for data storage
- **Network**: Internet connection for Mist API access

### API Access Requirements
- **Juniper Mist Account**: Active subscription with API access
- **API Token**: Generated from Mist dashboard
- **Organization ID**: Your Mist organization identifier

## Installation Methods

### Method 1: Local Python Installation (Recommended for Development)

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd MistHelper
   ```

2. **Create Virtual Environment** (Recommended)
   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate

   # macOS/Linux
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment**
   ```bash
   cp sample.env .env
   # Edit .env with your API credentials
   ```

5. **Verify Installation**
   ```bash
   python MistHelper.py --help
   ```

### Method 2: Container Deployment (Recommended for Production)

#### Option A: Podman (Recommended)

1. **Install Podman**
   - **Windows**: Download from [Podman Desktop](https://podman-desktop.io/)
   - **macOS**: `brew install podman`
   - **Linux**: Use your package manager (e.g., `dnf install podman`)

2. **Setup MistHelper**
   ```bash
   git clone <repository-url>
   cd MistHelper
   cp sample.env .env
   # Edit .env with your API credentials
   ```

3. **Auto-Setup and Run**
   ```bash
   python setup-podman.py
   python run-misthelper.py --output-format sqlite --menu 1
   ```

#### Option B: Docker

1. **Install Docker**
   - **Windows**: Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop)
   - **macOS**: Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop)
   - **Linux**: Use your package manager or Docker's official installation script

2. **Setup MistHelper**
   ```bash
   git clone <repository-url>
   cd MistHelper
   cp sample.env .env
   # Edit .env with your API credentials
   ```

3. **Build and Run**
   ```bash
   docker build -t misthelper .
   docker run -it -v ./data:/app/data -v ./.env:/app/.env:ro misthelper
   ```

## Configuration

### Environment Variables (.env file)

Create a `.env` file in the project root with the following configuration:

```env
# Mist API Configuration
MIST_HOST=api.mist.com
MIST_APITOKEN=your_api_token_here
MIST_USERNAME=your_username@example.com
MIST_PASSWORD=your_password

# Organization ID (optional - will prompt if not provided)
org_id=your_organization_id

# Application Settings
CSV_FRESHNESS_MINUTES=15
OUTPUT_FORMAT=csv
```

### API Token Generation

1. **Login to Mist Dashboard**
   - Go to [manage.mist.com](https://manage.mist.com)
   - Login with your credentials

2. **Generate API Token**
   - Navigate to Organization → API Tokens
   - Click "Create Token"
   - Set appropriate permissions
   - Copy the generated token

3. **Get Organization ID**
   - In the Mist dashboard, the organization ID is visible in the URL
   - Or use the MistHelper menu option to list organizations

### File Permissions

Ensure proper file permissions for security:

```bash
# Make .env file readable only by owner
chmod 600 .env

# Make scripts executable (macOS/Linux)
chmod +x setup-podman.py run-misthelper.py
```

## First Run

### Initial Setup

1. **Start MistHelper**
   ```bash
   python MistHelper.py
   ```

2. **Organization Selection**
   - If `org_id` is not in `.env`, you'll be prompted to select an organization
   - Choose your organization from the displayed list

3. **Test Basic Functionality**
   ```bash
   # Test with site list export
   python MistHelper.py --output-format csv --menu 1

   # Test with SQLite output
   python MistHelper.py --output-format sqlite --menu 1
   ```

### Data Output Verification

After running your first export:

**CSV Output:**
```bash
# Check CSV files in project directory
ls -la *.csv

# View sample data
head -20 SiteList.csv
```

**SQLite Output:**
```bash
# Check database creation
ls -la data/mist_data.db

# View database contents
sqlite3 data/mist_data.db ".tables"
sqlite3 data/mist_data.db "SELECT * FROM SiteList LIMIT 5;"
```

## Troubleshooting

### Common Issues

#### 1. API Authentication Errors
```
Error: Authentication failed
```
**Solution:**
- Verify API token in `.env` file
- Check token permissions in Mist dashboard
- Ensure organization ID is correct

#### 2. Python Module Import Errors
```
ModuleNotFoundError: No module named 'mistapi'
```
**Solution:**
- Activate virtual environment if using one
- Install dependencies: `pip install -r requirements.txt`
- Check Python version: `python --version`

#### 3. Container Permission Issues
```
Permission denied: /app/data
```
**Solution:**
- Ensure data directory exists: `mkdir -p data`
- Fix permissions: `chmod 755 data`
- Use proper volume mounting flags (`:Z` for SELinux)

#### 4. Unicode Encoding Issues (Windows)
```
UnicodeEncodeError: 'charmap' codec can't encode character
```
**Solution:**
- Run from PowerShell instead of Command Prompt
- Use container deployment for consistency
- Set environment variable: `set PYTHONIOENCODING=utf-8`

#### 5. Rate Limiting
```
HTTP 429: Too Many Requests
```
**Solution:**
- MistHelper automatically handles rate limiting
- Increase delays between operations if needed
- Use SQLite output for better performance

### Performance Optimization

1. **Use SQLite for Large Datasets**
   ```bash
   python MistHelper.py --output-format sqlite
   ```

2. **Enable CSV Freshness Checking**
   ```env
   CSV_FRESHNESS_MINUTES=15
   ```

3. **Monitor API Usage**
   - Check script.log for rate limiting messages
   - Use menu options to fetch only needed data

### Platform-Specific Notes

#### Windows
- Use PowerShell for best Unicode support
- Consider Windows Terminal for better experience
- Container deployment recommended for consistency

#### macOS
- May require accepting developer certificates
- Use Homebrew for easy dependency installation
- Container deployment works well with Docker Desktop

#### Linux
- SELinux systems need `:Z` flags for volume mounting
- Various package managers supported
- Rootless containers recommended

## Advanced Configuration

### Custom Output Locations

Modify the following variables in MistHelper.py if needed:

```python
# Custom database location
DATABASE_PATH = "/custom/path/mist_data.db"

# Custom CSV output directory
CSV_OUTPUT_DIR = "/custom/csv/output/"
```

### API Rate Limiting Tuning

Adjust rate limiting parameters:

```python
# In MistHelper.py
API_DELAY_SECONDS = 0.75  # Increase for slower API calls
MAX_RETRIES = 3           # Retry attempts on failures
```

### Logging Configuration

Enable different logging levels:

```python
# Set logging level
logging.basicConfig(level=logging.DEBUG)  # For detailed debugging
logging.basicConfig(level=logging.INFO)   # For normal operation
logging.basicConfig(level=logging.WARNING) # For minimal output
```

## Verification

### Test Suite

Run the comprehensive test suite:

```bash
python test_misthelper.py
```

Expected output:
```
🧪 MistHelper Comprehensive Test Suite
==================================================
...
----------------------------------------------------------------------
Ran 19 tests in 25.565s

OK
```

### Database Verification

Check database integrity:

```bash
python verify_db.py
```

### API Connection Test

Test API connectivity:

```bash
python MistHelper.py --menu 1
```

## Next Steps

1. **Explore Menu Options**: Try different menu options to understand available data
2. **Set Up Automation**: Use menu numbers for automated data collection
3. **Database Queries**: Learn SQLite queries for data analysis
4. **Integration**: Consider integrating with other monitoring tools

## Support and Resources

- **Documentation**: See README.md for comprehensive usage guide
- **Container Setup**: See PODMAN_SETUP.md for container deployment details
- **Implementation Details**: See IMPLEMENTATION-SUMMARY.md for technical information
- **File Structure**: See FILE-VERIFICATION.md for project organization

## Security Considerations

1. **Credential Security**
   - Never commit `.env` files to version control
   - Use proper file permissions (600) for `.env`
   - Rotate API tokens regularly

2. **Container Security**
   - Use rootless containers when possible
   - Keep container images updated
   - Limit container network access

3. **Data Protection**
   - Encrypt sensitive data at rest
   - Use secure database passwords
   - Implement proper backup strategies

This installation guide provides comprehensive setup instructions for all supported platforms and deployment methods. Follow the method that best fits your environment and use case.
