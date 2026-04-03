Plan for implementing audit fixes for Menu 23 (Guest Users Export)

Assumptions
- The Mist API endpoint mistapi.api.v1.orgs.guests.searchOrgGuestAuthorization returns records containing at least 'id' and a timestamp-like field; if no stable timestamp exists, 'id' alone will be used.
- DataExporter.write_with_format_selection accepts api_function_name and will use ENDPOINT_PRIMARY_KEY_STRATEGIES to determine SQL schema and upsert behavior.

High-level steps
1. Add ENDPOINT_PRIMARY_KEY_STRATEGIES entry
   - Key: "searchOrgGuestAuthorization"
   - Type: composite_pk (recommended)
   - primary_key: ["id", "org_id", "timestamp"] or at minimum ["id"].
   - indexes: ["org_id", "site_id", "timestamp", "client_mac"] (if available)
   - Document the choice and rationale in the dict.

2. Update OrgSiteExporter.current_guests() and historical_guests()
   - Replace DataExporter.save_data_to_output(...) with DataExporter.write_with_format_selection(guests, filename, api_function_name="searchOrgGuestAuthorization")
   - Keep DataProcessingUtils.flatten_nested_fields and escape_multiline processing before calling exporter.
   - Add a small unit-testable wrapper if needed to reduce side effects (but avoid large refactors).

3. Add unit tests
   - Create tests/test_exports_guest.py
   - Mock ConfigUtils.get_cached_or_prompted_org_id to return a fixed org id
   - Mock mistapi.api.v1.orgs.guests.searchOrgGuestAuthorization to return a MagicMock response and mistapi.get_all to return sample guest records
   - Monkeypatch DataExporter.write_with_format_selection to capture calls and assert api_function_name and filename
   - Cover both current_guests and historical_guests (time-window behavior can be asserted by checking that searchOrgGuestAuthorization was called with start and end parameters for historical_guests)

4. Run validation
   - python -m py_compile MistHelper.py
   - pytest -q
   - Fix any lint or type errors surfaced by tests

5. Documentation and changelog
   - Update README menu count if required
   - Add a short changelog entry noting SQL export compliance for guest endpoints

Rollback / Backwards compatibility
- Keep file names unchanged (OrgCurrentGuests.csv and OrgHistoricalGuests.csv)
- The SQL behavior changes only when OUTPUT_FORMAT is sqlite; CSV behavior remains identical.

Estimated effort: 1-2 hours (code change + tests + run).