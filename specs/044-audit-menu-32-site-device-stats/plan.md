Plan to remediate Menu #32 (SiteDeviceExporter.device_stats):

1. Code change
   - Edit SiteDeviceExporter.device_stats in MistHelper.py to call:
     DataExporter.write_with_format_selection(sanitized_data, filename, api_function_name="listSiteDevicesStats")
   - Keep the current filename convention: SiteDeviceStats_{SiteName}.csv

2. ENDPOINT_PRIMARY_KEY_STRATEGIES
   - No change required; entry for "listSiteDevicesStats" exists (composite_pk ['device_id','timestamp']).

3. Tests
   - Unit test: mock mistapi listSiteDevicesStats and assert DataExporter.write_with_format_selection called with api_function_name.
   - Integration: verify SQLite table exists with columns matching composite PK and rows upsert correctly when duplicate timestamp/device_id pairs provided.

4. Validation
   - python -m py_compile MistHelper.py
   - pytest

5. Docs
   - Update README and release notes noting the dual-output compliance fix for Menu #32.