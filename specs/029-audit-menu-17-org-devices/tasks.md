Actionable Fix Tasks

1) Add ENDPOINT_PRIMARY_KEY_STRATEGIES Entry
- Add a new key to MistHelper.py at the ENDPOINT_PRIMARY_KEY_STRATEGIES mapping:
  "listOrgDevices": {
      "type": "natural_pk",
      "primary_key": ["id"],
      "indexes": ["org_id", "site_id", "mac", "serial", "model", "type"],
      "unique_constraints": [],
      "description": "Organization devices with stable UUID identifiers (listOrgDevices)",
  }
- Rationale: Matches API function name emitted by mistapi, ensures SQLite writes get correct PKs.
- Tests: Update tests/unit/test_pk_strategies.py duplicate mapping if necessary.

2) Add Unit Test for Pipeline Wiring
- Create tests/unit/test_menu_17_devices.py with tests:
  a) Mock mistapi.api.v1.orgs.devices.listOrgDevices to return sample list of device dicts.
  b) Monkeypatch APIDataFetcher._fetch_api_data to set rawdata and skip live API calls.
  c) Mock DataExporter.write_with_format_selection and assert it was called with api_function_name="listOrgDevices" and filename containing "OrgDevices.csv".

3) Add Integration Test (Mocked SQLite)
- Create tests/integration/test_menu_17_sqlite.py:
  - Set OUTPUT_FORMAT to "sqlite" via monkeypatch/env.
  - Mock API to return sample devices.
  - Run OrgInventoryExporter.devices()
  - Assert a table named OrgDevices (or appropriate table name) exists in data/mist_data.db and primary key column "id" exists.
  - Clean up DB after test.

4) Documentation & README
- Update README.md dual-output operations list if needed and mention new ENDPOINT_PRIMARY_KEY_STRATEGIES key.

Notes
- Do NOT change OrgInventoryExporter.devices() implementation; it already uses APIDataFetcher which supplies api_function_name correctly. The minimal change is adding the ENDPOINT_PRIMARY_KEY_STRATEGIES entry and tests.
- After implementing changes, run unit tests and ensure tests/unit/test_pk_strategies.py still pass.
