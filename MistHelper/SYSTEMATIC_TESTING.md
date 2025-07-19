# Systematic Testing Feature for MistHelper

## Overview

The `--test` flag provides a systematic way to test all safe menu options in MistHelper automatically. This is particularly useful for:

- **Continuous Integration**: Automated testing in CI/CD pipelines
- **Regression Testing**: Ensuring all functions work after code changes  
- **API Validation**: Verifying that all Mist API endpoints are accessible
- **Performance Testing**: Measuring execution time for all operations
- **Documentation**: Generating a comprehensive list of working vs broken functions

## Usage

### Basic Systematic Test
```bash
python MistHelper.py --test
```

### With Debug Logging
```bash
python MistHelper.py --test --debug
```

### Test with SQLite Output Format
```bash
python MistHelper.py --test --output-format sqlite
```

### Speed Optimization
The `--test` flag automatically enables `--skip-deps` to bypass dependency checks for faster startup.

## What Gets Tested

### ✅ Safe Operations (Tested)
- All organization-level GET operations (sites, devices, stats, inventory)
- Event and alarm definitions exports
- Template exports (gateway, network, RF, AP, switch)
- License and configuration exports
- Audit logs and security events
- Statistics and analytics data
- Non-interactive data exports

### 🚫 Unsafe Operations (Skipped)
- **Interactive Functions**: Require user input (options 0, 16-19)
- **WebSocket Operations**: Real-time device communication (options 34, 38-40)
- **POST/PUT/DELETE**: Device reboots, configuration changes (option 46)
- **Continuous Loops**: Background processes (options 35, 78)
- **Site-Specific**: Require site selection (options 47-52, 66-70)
- **Work in Progress**: Unstable functions marked as WIP

## Output and Logging

### Console Output
```
🧪 Starting systematic test of MistHelper menu options...
📊 Found 82 total menu options
✅ 54 safe options will be tested
⚠️  28 unsafe options will be skipped

🚫 Skipping unsafe operations:
   0: Select a site (Reason: Interactive site selection)
   16: View device inventory for a selected site (Reason: Interactive)
   ...

🧪 Testing safe operations:
   [ 1/54] Testing option  1: Export all organization alarms...
   ✅ Option 1 completed successfully
   [ 2/54] Testing option  2: Export all device events...
   ✅ Option 2 completed successfully
   ...

🧪 Systematic Test Summary:
   ✅ Successful operations: 52
   ❌ Failed operations: 2
   🚫 Skipped unsafe operations: 28
   📊 Total coverage: 52/82 (63.4%)
```

### Log File Output
All test results are logged to `script.log` with detailed error information:
```
2025-07-18 10:30:15 - INFO - SYSTEMATIC_TEST: Starting systematic test mode
2025-07-18 10:30:16 - INFO - SYSTEMATIC_TEST: Starting test of menu option 1: Export all organization alarms
2025-07-18 10:30:18 - INFO - SYSTEMATIC_TEST: Successfully completed menu option 1
```

## Exit Codes

- **0**: All tested operations succeeded
- **1**: One or more operations failed (check logs for details)

## Integration Examples

### CI/CD Pipeline (GitHub Actions)
```yaml
name: MistHelper API Test
on: [push, pull_request]
jobs:
  test:
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
