Plan to remediate Menu #31 (SiteDevices):

1. Code change
   - Edit SiteDeviceExporter.devices in MistHelper.py to call:
     DataExporter.write_with_format_selection(sanitized_data, filename, api_function_name="listSiteDevices")
   - Ensure filename remains: SiteDevices_{SiteName}.csv

2. ENDPOINT_PRIMARY_KEY_STRATEGIES
   - No change required; entry for "listSiteDevices" exists and is correct (natural_pk ['id']).

3. Tests
   - Add a unit test that mocks mistapi response and DataExporter.write_with_format_selection, asserting it is called with api_function_name="listSiteDevices" and data preserved.
   - Add an integration test that runs exporter with a sample payload and asserts both CSV and SQLite table (data/mist_data.db) include expected PK column and rows.

4. Validation
   - Run existing test suite: pytest
   - Run python -m py_compile MistHelper.py to validate syntax

5. Docs
   - Update README dual-output list to document Menu #31 uses listSiteDevices for SQLite upserts.