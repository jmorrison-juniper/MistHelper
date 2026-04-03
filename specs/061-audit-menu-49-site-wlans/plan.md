Objective:
Ensure site WLAN exports have PK strategy and test coverage.

Plan:
1. Add strategy entry for listSiteWlans to ENDPOINT_PRIMARY_KEY_STRATEGIES.
2. Update duplicated strategies in tests/unit/test_pk_strategies.py to include listSiteWlans for validation.
3. Create unit tests to mock mistapi.api.v1.sites.wlans.listSiteWlans and assert DataExporter.save_data_to_output receives api_function_name.
4. Run tests and verify SQLite schema.
