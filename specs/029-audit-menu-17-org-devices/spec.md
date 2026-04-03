Title: Audit - Menu 17: Org Inventory Exporter (OrgInventoryExporter.devices)

Current State Analysis
- Location: MistHelper.py, class OrgInventoryExporter, devices method at ~line 11782.
- Implementation: OrgInventoryExporter.devices() constructs an APIDataFetcher with api_call=mistapi.api.v1.orgs.devices.listOrgDevices and filename "OrgDevices.csv" then calls .execute().
- Export pipeline: APIDataFetcher.execute() uses DataExporter.export_with_processing(..., api_function_name=api_call.__name__), which calls DataExporter.save_data_to_output -> DataExporter.write_with_format_selection(..., api_function_name).

Issues Found
- ENDPOINT_PRIMARY_KEY_STRATEGIES contains an entry for "getOrgDevices" but NOT for "listOrgDevices". The API function name propagated at runtime is "listOrgDevices". This mismatch means SQLite exports will fall back to the "default" strategy instead of using the intended natural_pk strategy.
- No direct unit test found that asserts DataExporter.write_with_format_selection() is invoked with api_function_name="listOrgDevices" for menu #17.

SQL Export Compliance
- Non-compliant: Because ENDPOINT_PRIMARY_KEY_STRATEGIES lacks "listOrgDevices", SQLite exports (OUTPUT_FORMAT=sqlite) will use the default auto-increment strategy, losing proper primary key/index definitions for organization devices. To comply, add an entry keyed by "listOrgDevices" (or ensure APIDataFetcher supplies a matching api_function_name) mapping to the natural_pk strategy.

Test Coverage
- Unit tests exist for ENDPOINT_PRIMARY_KEY_STRATEGIES structural validation (tests/unit/test_pk_strategies.py) but they duplicate a local dict, not asserting runtime behavior of OrgInventoryExporter.devices.
- No end-to-end or unit test found that covers Menu #17 pipeline asserting api_function_name usage, CSV/SQLite outputs, or DB table schema creation.

Acceptance Criteria
- ENDPOINT_PRIMARY_KEY_STRATEGIES contains a mapping for "listOrgDevices" with type "natural_pk" and primary_key ["id"], indexes appropriate (org_id, site_id, mac, serial, model, type).
- Add unit test asserting APIDataFetcher/DataExporter pipeline passes api_function_name="listOrgDevices" and that write_with_format_selection is invoked accordingly (mocked).
- Integration test (mocked API) confirming SQLite table created/populated using the strategy when OUTPUT_FORMAT=sqlite.
