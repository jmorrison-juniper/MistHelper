Plan to remediate Menu #33 (SiteDeviceExporter.device_virtual_chassis):

1. Add PK strategy
   - Add an entry in ENDPOINT_PRIMARY_KEY_STRATEGIES in MistHelper.py for "getSiteDeviceVirtualChassis".
   - Recommended initial strategy: natural_pk with primary_key ["id"] if the API returns an 'id' in VC objects. If API does not include a stable 'id', use composite_pk with primary_key ["device_id","member_id","timestamp"] or fallback to auto_increment_with_unique with clear indexes.
   - Document the chosen strategy in the mapping comment.

2. Code change
   - Edit SiteDeviceExporter.device_virtual_chassis to call:
     DataExporter.write_with_format_selection(sanitized, filename, api_function_name="getSiteDeviceVirtualChassis")

3. Tests
   - Unit test: mock getSiteDeviceVirtualChassis response and assert DataExporter.write_with_format_selection called with correct api_function_name.
   - Integration: verify SQLite table created and columns/indexes align with chosen PK strategy.

4. Validation
   - python -m py_compile MistHelper.py
   - pytest

Notes: Inspect actual API response shape to choose the best PK columns before committing the ENDPOINT_PRIMARY_KEY_STRATEGIES entry.