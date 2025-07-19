# MistHelper

A comprehensive Python utility for interacting with the Juniper Mist API, providing data extraction, analysis, and reporting capabilities for network infrastructure management.

## Overview

MistHelper is a command-line tool designed to help network administrators and engineers efficiently interact with Juniper Mist cloud infrastructure. It provides powerful data extraction, processing, and reporting capabilities with support for both CSV and SQLite database outputs.

## Features

- **Comprehensive Data Extraction**: Pull organization, site, device, and statistical data from Mist API
- **Flexible Output Formats**: Support for CSV files and SQLite databases
- **Interactive Device Management**: Browse and manage network devices with intuitive menus
- **Advanced Data Processing**: Automatic data flattening, sanitization, and formatting
- **Rate Limiting**: Built-in API rate limiting to prevent service disruptions
- **Containerized Deployment**: Docker and Podman support for consistent environments
- **Cross-Platform**: Runs on Windows, macOS, and Linux
- **Comprehensive Testing**: Full test suite with dependency handling

## Quick Start

### Prerequisites

- Python 3.7 or higher
- Juniper Mist API credentials
- Internet connection for API access

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd MistHelper
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API credentials**:
   ```bash
   cp sample.env .env
   # Edit .env with your Mist API credentials
   ```

4. **Run MistHelper**:
   ```bash
   python MistHelper.py
   ```

5. **Test all functions systematically**:
   ```bash
   python MistHelper.py --test
   ```

### Environment Configuration

Create a `.env` file in the project root with your Mist API credentials:

```env
# Mist API Configuration
MIST_HOST=api.mist.com
MIST_APITOKEN=your_api_token_here
MIST_USERNAME=your_username@example.com
MIST_PASSWORD=your_password

# Organization ID (optional - will prompt if not provided)
org_id=your_organization_id

# CSV File Freshness (in minutes)
CSV_FRESHNESS_MINUTES=15
```

## Usage

### Command Line Interface

```bash
# Basic usage - interactive menu
python MistHelper.py

# CSV output format (default)
python MistHelper.py --output-format csv

# SQLite database output
python MistHelper.py --output-format sqlite

# Direct menu access
python MistHelper.py --menu 1

# Show help
python MistHelper.py --help

# Systematic testing of all safe operations
python MistHelper.py --test

# Test with debug logging
python MistHelper.py --test --debug
```

### Available Menu Options

1. **Export Site List** - Get all sites in organization
2. **Export Device Inventory** - Get all devices
3. **Export Device Statistics** - Get device performance stats
4. **Export Device Port Statistics** - Get port-level statistics
5. **Export VPN Peer Statistics** - Get VPN connection data
6. **Export Audit Logs** - Get organization audit logs
7. **Export Open Alarms** - Get current active alarms
8. **Export Device Events** - Get device event logs
9. **Site Device Inventory** - Interactive site device browser
10. **Device Configuration** - Get device configuration details
11. **Device Statistics** - Get individual device stats
12. **Device Test Results** - Get synthetic test results
13. **Export Site Configurations** - Get site configuration settings
14. **Export Gateway Synthetic Tests** - Get gateway test results
15. **Export Test Results by Site** - Get all test results per site
16. **Export Event Definitions** - Get event log definitions
17. **Export Sites with Location** - Get sites with GPS coordinates
18. **Export Devices with Site Info** - Get devices with site details
19. **Merge SFP Transceiver Data** - Combine transceiver and location data

### Output Formats

#### CSV Files
- Human-readable format
- Excel-compatible
- Individual files per data type
- Automatic data flattening and sanitization

#### SQLite Database
- Structured relational data
- Efficient for large datasets
- Supports complex queries
- Single database file: `data/mist_data.db`

## Container Deployment

### Docker Support

```bash
# Build and run with Docker
docker-compose up --build

# Or run directly
docker build -t misthelper .
docker run -it -v ./data:/app/data -v ./.env:/app/.env:ro misthelper
```

### Podman Support

```bash
# Setup Podman environment
python setup-podman.py

# Run with Podman
python run-misthelper.py --output-format sqlite --menu 11
```

See [PODMAN_SETUP.md](PODMAN_SETUP.md) for detailed Podman configuration.

## Data Processing Features

### Automatic Data Flattening

MistHelper automatically flattens nested JSON structures into CSV-friendly formats:

```python
# Nested JSON structure
{
    "device": {
        "model": "AP41",
        "config": {
            "wifi": {"ssid": "corporate", "security": "WPA2"}
        }
    }
}

# Becomes flattened fields
device_model: "AP41"
device_config_wifi_ssid: "corporate"
device_config_wifi_security: "WPA2"
```

### Data Sanitization

- Multiline strings are escaped for CSV compatibility
- Special characters are handled properly
- List values are converted to comma-separated strings
- Null values are handled gracefully

### Rate Limiting

Built-in rate limiting prevents API throttling:
- Dynamic delay calculation based on API response times
- Automatic retry on rate limit errors
- Partial data saving on interruptions

## Testing

### Running Tests

```bash
# Run the comprehensive test suite
python test_misthelper.py

# Run specific test categories
python -m unittest test_misthelper.TestMistHelperUtils
python -m unittest test_misthelper.TestMistHelperCLI
python -m unittest test_misthelper.TestMistHelperFileOperations
python -m unittest test_misthelper.TestMistHelperIntegration
```

### Test Coverage

- **Unit Tests**: Core utility functions (data flattening, CSV operations)
- **Integration Tests**: CLI operations with timeout handling
- **File Operations**: CSV and SQLite file handling
- **End-to-End Tests**: Complete data processing pipelines

## Architecture

### Core Components

- **MistHelper.py**: Main application with API interaction logic
- **Data Processing**: Automatic flattening and sanitization
- **Output Handlers**: CSV and SQLite database writers
- **Rate Limiting**: API throttling management
- **Interactive CLI**: Menu-driven user interface

### Dependencies

- `mistapi`: Juniper Mist API client library
- `requests`: HTTP client for API calls
- `prettytable`: CLI table formatting
- `tqdm`: Progress bars for long operations
- `python-dotenv`: Environment variable management
- `sqlite3`: Database support (built-in)

## Development

### Project Structure

```
MistHelper/
├── MistHelper.py          # Main application
├── requirements.txt       # Python dependencies
├── test_misthelper.py     # Comprehensive test suite
├── .env                   # API credentials (create from sample.env)
├── sample.env            # Environment template
├── data/                 # Output directory
│   └── mist_data.db     # SQLite database (created automatically)
├── docs/                 # Documentation
│   ├── README.md        # This file
│   ├── PODMAN_SETUP.md  # Podman configuration
│   └── IMPLEMENTATION-SUMMARY.md  # Development notes
└── containers/           # Container configurations
    ├── Containerfile    # Container build instructions
    ├── compose.yml      # Container orchestration
    └── run-scripts/     # Platform-specific run scripts
```

### Adding New Features

1. **New API Endpoints**: Add functions following the `export_*_to_csv()` pattern
2. **Data Processing**: Extend `flatten_nested_fields_in_list()` for new data types
3. **Output Formats**: Extend `write_data_with_format_selection()` for new formats
4. **Menu Options**: Add to the main menu in `MistHelper.py`

### Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## Troubleshooting

### Common Issues

1. **API Authentication Errors**:
   - Verify `.env` file configuration
   - Check API token validity
   - Ensure organization ID is correct

2. **Rate Limiting**:
   - The tool automatically handles rate limits
   - Increase delays between calls if needed
   - Use SQLite output for better performance

3. **Unicode Encoding (Windows)**:
   - Run from PowerShell or Command Prompt
   - Ensure proper terminal encoding
   - Use container deployment for consistency

4. **Container Issues**:
   - Ensure Docker/Podman is running
   - Check volume mounts for data persistence
   - Verify SELinux settings (Linux with Podman)

### Performance Optimization

- Use SQLite output for large datasets
- Enable CSV freshness checking to avoid redundant API calls
- Use menu options to fetch only required data
- Monitor API usage with built-in rate limiting

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the test suite for examples
3. Examine the comprehensive logging output
4. Consult the Mist API documentation

## Changelog

### Latest Version
- ✅ Comprehensive test suite with dependency handling
- ✅ SQLite database support alongside CSV
- ✅ Container deployment (Docker/Podman)
- ✅ Cross-platform compatibility
- ✅ Enhanced error handling and logging
- ✅ Rate limiting and API throttling management
- ✅ Interactive device and site selection
- ✅ Automatic data processing and sanitization
