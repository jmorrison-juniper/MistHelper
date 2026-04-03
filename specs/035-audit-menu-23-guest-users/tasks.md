tasks:

- id: audit-23-add-primary-key-strategy
  title: Add ENDPOINT_PRIMARY_KEY_STRATEGIES entry for guest authorizations
  description: |
    Add a named strategy for "searchOrgGuestAuthorization" to ENDPOINT_PRIMARY_KEY_STRATEGIES in MistHelper.py. Use composite_pk with primary_key ["id", "org_id", "timestamp"] if timestamp is present, otherwise fallback to ["id"]. Add indexes for org_id, site_id, client_mac if those fields are in the API.
  estimate_minutes: 20
  status: pending

- id: audit-23-update-export-methods
  title: Use DataExporter.write_with_format_selection in guest export methods
  description: |
    Update OrgSiteExporter.current_guests() and historical_guests() to call DataExporter.write_with_format_selection(guests, filename, api_function_name="searchOrgGuestAuthorization") so SQL export backends can apply the primary key strategy and indexes.
  estimate_minutes: 30
  status: pending

- id: audit-23-add-unit-tests
  title: Add unit tests for guest exports
  description: |
    Create tests/test_exports_guest.py. Mock API calls and mistapi.get_all. Assert DataExporter.write_with_format_selection was called with correct arguments and that historical_guests supplies start/end params to the search API.
  estimate_minutes: 45
  status: pending

- id: audit-23-validate-and-run-tests
  title: Validate syntax and run tests
  description: |
    Run python -m py_compile MistHelper.py and pytest -q. Fix any failures. Ensure no regressions in existing export tests.
  estimate_minutes: 25
  status: pending

- id: audit-23-document-changelog
  title: Update README/changelog
  description: |
    Add a changelog entry describing SQL export compliance for guest exports and note tests added.
  estimate_minutes: 10
  status: pending
