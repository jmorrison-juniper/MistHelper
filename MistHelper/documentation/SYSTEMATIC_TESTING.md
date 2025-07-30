# Systematic Testing Feature for MistHelper

## Overview

The `--test` flag provides a systematic way to test all safe menu options in MistHelper automatically. This feature enables comprehensive validation of the application's functionality without requiring manual intervention or risking system changes.

**Key Benefits:**
- **Continuous Integration**: Automated testing in CI/CD pipelines
- **Regression Testing**: Ensuring all functions work after code changes  
- **API Validation**: Verifying that all Mist API endpoints are accessible
- **Performance Testing**: Measuring execution time for all operations
- **Quality Assurance**: Comprehensive validation of data processing pipeline

## Usage

### Basic Systematic Test
```bash
python MistHelper.py --test
```

### Test with Debug Logging
```bash
python MistHelper.py --test --debug
```

### Test with SQLite Output Format
```bash
python MistHelper.py --test --output-format sqlite
```

### Test in Container Environment
```bash
python run-misthelper.py --test --output-format sqlite
```

### Performance Optimization
The `--test` flag automatically enables `--skip-deps` to bypass dependency checks for faster startup, reducing test execution time.

## Test Coverage

### ✅ Safe Operations (54 operations tested)

**Core Data & Diagnostics (1-10)**
- Organization alarms and device events
- Audit logs and security events
- Event and alarm definitions

**Organization-Level Data (11-28)**
- Site lists and device inventories
- Performance statistics and analytics
- Location-enriched data exports
- Template and configuration exports

**Templates & Configuration (35-59)**
- All template types (gateway, network, RF, AP, switch)
- Security monitoring and rogue detection
- License and usage information
- Organization management data

**Status & Monitoring (60-62)**
- Firmware upgrade status monitoring
- Inventory comparison utilities
- Marvis action polling

### 🚫 Unsafe Operations (28 operations skipped)

**Interactive Functions (require user input)**
- Site selection and device browsing (70-74)
- Site-specific exports requiring selection (29-34, 49-53)
- Interactive configuration viewers

**WebSocket Operations (real-time communication)**
- CLI shell access (79)
- Real-time command execution (80-83)
- Live device interaction

**Destructive Operations (POST/PUT/DELETE)**
- Device reboots and firmware upgrades (90-91)
- Configuration changes (92-93)
- System modifications

**Continuous Processes (long-running)**
- Data collection loops (75-76)
- Background monitoring processes

**Work in Progress (potentially unstable)**
- 52-week historical data exports (63-64)
- Advanced gateway configuration exports (65)

## Output and Logging

### Console Output Example
```
🧪 Starting systematic test of MistHelper menu options...
⚠️  Note: This will skip interactive, websocket, POST, and destructive operations
⏰ Test started at: 2025-07-25 10:30:15
================================================================================

📊 Found 93 total menu options
✅ 54 safe options will be tested
⚠️  39 unsafe options will be skipped

🚫 Skipping unsafe operations:
   29: Export site port statistics (Reason: Requires site selection)
   30: Export site clients (Reason: Requires site selection)
   70: Select a site (Reason: Interactive site selection)
   79: Launch CLI shell (Reason: WebSocket/interactive operation)
   90: Bulk AP firmware upgrade (Reason: Destructive POST operation)
   ...

🧪 Testing safe operations:
   [ 1/54] Testing option  1: Export all organization alarms...
   ✅ Option 1 completed successfully (2.1s)
   [ 2/54] Testing option  2: Export all device events...
   ✅ Option 2 completed successfully (3.5s)
   [ 3/54] Testing option  3: Export audit logs...
   ✅ Option 3 completed successfully (1.8s)
   ...

🧪 Systematic Test Summary:
   ✅ Successful operations: 52/54 (96.3%)
   ❌ Failed operations: 2/54 (3.7%)
   🚫 Skipped unsafe operations: 39
   📊 Total coverage: 52/93 (55.9%)
   ⏱️  Total execution time: 147.3 seconds
   
Failed operations:
   - Option 42: Export security events (API endpoint unavailable)
   - Option 58: Export license usage (Insufficient permissions)
```

### Log File Output
All test results are logged to `script.log` with detailed information:
```
2025-07-25 10:30:15 - INFO - SYSTEMATIC_TEST: Starting systematic test mode
2025-07-25 10:30:16 - INFO - SYSTEMATIC_TEST: Starting test of menu option 1: Export all organization alarms
2025-07-25 10:30:18 - INFO - SYSTEMATIC_TEST: Successfully completed menu option 1 (Duration: 2.1s)
2025-07-25 10:30:18 - INFO - SYSTEMATIC_TEST: Starting test of menu option 2: Export all device events
2025-07-25 10:30:22 - INFO - SYSTEMATIC_TEST: Successfully completed menu option 2 (Duration: 3.5s)
2025-07-25 10:30:25 - ERROR - SYSTEMATIC_TEST: Failed menu option 42: HTTP 404 - Security events endpoint not available
```

## Exit Codes and Integration

### Exit Code Behavior
- **0**: All tested operations succeeded
- **1**: One or more operations failed (check logs for details)
- **2**: Critical error preventing test execution

### Integration Examples

#### GitHub Actions CI/CD
```yaml
name: MistHelper API Test
on: [push, pull_request]

jobs:
  test-api-functions:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
          
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          
      - name: Create test environment
        run: |
          cp sample.env .env
          echo "MIST_APITOKEN=${{ secrets.MIST_API_TOKEN }}" >> .env
          echo "org_id=${{ secrets.MIST_ORG_ID }}" >> .env
          
      - name: Run systematic tests
        run: |
          python MistHelper.py --test --output-format sqlite
          
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: |
            script.log
            data/*.db
            *.csv
```

#### Jenkins Pipeline
```groovy
pipeline {
    agent any
    
    stages {
        stage('Test MistHelper Functions') {
            steps {
                script {
                    def result = sh(
                        script: 'python MistHelper.py --test --output-format csv',
                        returnStatus: true
                    )
                    
                    if (result != 0) {
                        currentBuild.result = 'UNSTABLE'
                        echo "Some API functions failed - check logs"
                    }
                }
                
                archiveArtifacts artifacts: 'script.log, *.csv', fingerprint: true
            }
        }
    }
    
    post {
        always {
            publishTestResults testResultsPattern: 'test-results.xml'
        }
    }
}
```

#### Container Testing
```bash
# Test in Podman container
python setup-podman.py
python run-misthelper.py --test --output-format sqlite

# Docker testing
docker build -t misthelper-test .
docker run --rm -v ./data:/app/data -v ./.env:/app/.env:ro \
    misthelper-test python MistHelper.py --test
```

## Test Metrics and Reporting

### Performance Metrics
- **Total Execution Time**: Complete test suite runtime
- **Individual Operation Time**: Per-function performance measurement
- **API Call Efficiency**: Request/response timing analysis
- **Memory Usage**: Peak memory consumption during testing

### Coverage Analysis
- **Function Coverage**: Percentage of menu options tested
- **API Endpoint Coverage**: Unique Mist API endpoints validated
- **Error Path Coverage**: Exception handling verification
- **Output Format Coverage**: CSV and SQLite validation

### Quality Metrics
- **Success Rate**: Percentage of operations completing successfully
- **Failure Analysis**: Categorization of failure types
- **Consistency Check**: Data format and structure validation
- **Regression Detection**: Comparison with previous test runs

## Best Practices

### Pre-Test Setup
1. **Environment Validation**: Ensure `.env` file is properly configured
2. **Network Connectivity**: Verify access to api.mist.com
3. **Permissions Check**: Confirm API token has required permissions
4. **Disk Space**: Ensure adequate space for output files

### Test Execution
1. **Isolated Environment**: Run in clean environment to avoid conflicts
2. **Rate Limiting**: Tests include built-in delays to respect API limits
3. **Error Collection**: All failures are logged with detailed context
4. **Resource Monitoring**: Monitor system resources during execution

### Post-Test Analysis
1. **Log Review**: Examine script.log for detailed execution information
2. **Output Validation**: Verify generated CSV/SQLite files are valid
3. **Performance Analysis**: Review execution times for performance regression
4. **Failure Triage**: Categorize and prioritize any test failures

## Troubleshooting

### Common Issues

#### API Authentication Failures
```bash
# Verify API token
curl -H "Authorization: Token YOUR_TOKEN" https://api.mist.com/api/v1/self

# Check organization ID
python MistHelper.py --menu 11 --output-format csv
```

#### Rate Limiting
- Tests include automatic rate limiting
- If rate limiting occurs, tests will slow down automatically
- Large organizations may need longer test execution times

#### Partial Test Failures
- Individual function failures don't stop the entire test suite
- Check script.log for specific error details
- Some failures may be due to organization-specific limitations

#### Container Issues
```bash
# Check container environment
python setup-podman.py --verify

# Test container access
python run-misthelper.py --help
```

This systematic testing framework provides comprehensive validation of MistHelper functionality while maintaining safety and reliability standards.
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run systematic test
        env:
          MIST_APITOKEN: ${{ secrets.MIST_APITOKEN }}
          org_id: ${{ secrets.MIST_ORG_ID }}
        run: python MistHelper.py --test
```

### Cron Job for Regular Testing
```bash
# Test every day at 2 AM
0 2 * * * cd /path/to/MistHelper && python MistHelper.py --test >> test_results.log 2>&1
```

### PowerShell Script for Windows
```powershell
# Run systematic test and capture results
$result = python MistHelper.py --test
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ All tests passed!" -ForegroundColor Green
} else {
    Write-Host "❌ Some tests failed!" -ForegroundColor Red
}
```

## Performance Considerations

- **API Rate Limiting**: 1-second delay between tests to respect Mist API limits
- **Dependency Skip**: Automatic `--skip-deps` for ~30 second startup time savings
- **Parallel Safety**: Tests run sequentially to avoid API conflicts
- **Memory Usage**: Each test is independent, preventing memory leaks

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   ```
   ❌ 401 Unauthorized: Invalid API token
   ```
   **Solution**: Check your `.env` file has valid `MIST_APITOKEN`

2. **Organization Not Found**
   ```
   ❌ 404 Not Found: Invalid organization ID
   ```
   **Solution**: Verify `org_id` in `.env` file

3. **Rate Limiting**
   ```
   ❌ 429 Too Many Requests: API rate limit exceeded
   ```
   **Solution**: Tests include delays, but you may need to wait and retry

4. **Network Connectivity**
   ```
   ❌ Connection timeout
   ```
   **Solution**: Check internet connection and Mist API availability

### Debug Mode
For detailed troubleshooting, run with debug logging:
```bash
python MistHelper.py --test --debug
```

This will show:
- API request details
- Response data sizes
- Error stack traces
- Function execution flow

## Test Categories

The systematic test categorizes menu options as follows:

| Category | Count | Description |
|----------|-------|-------------|
| Core Data Exports | 15 | Organization-level data (sites, devices, stats) |
| Event Definitions | 7 | Various event type definitions |
| Templates | 5 | Gateway, network, RF, AP, switch templates |
| Security & Monitoring | 8 | Alarms, security events, rogue detection |
| Configuration | 12 | Settings, WLANs, licenses, webhooks |
| Analytics | 7 | Usage statistics, applications, clients |
| **Interactive** | 5 | User input required (skipped) |
| **WebSocket** | 4 | Real-time communication (skipped) |
| **Destructive** | 1 | Device reboots (skipped) |
| **Continuous** | 2 | Long-running processes (skipped) |
| **Site-Specific** | 11 | Require site selection (skipped) |
| **Work in Progress** | 5 | Unstable functions (skipped) |

This systematic approach ensures comprehensive testing while maintaining safety and avoiding operations that could disrupt production environments.
