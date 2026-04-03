Objective:
Validate Menu #45 exports licenses correctly, ensure SQL exports use correct PK strategy, and add tests.

Plan:
1. Inspect OrgAdminExporter.licenses implementation and confirm where DataExporter.save_data_to_output is called.
2. If api_function_name not passed, update call in a future PR (not required in this audit) to include "getOrgLicensesSummary".
3. Create unit tests that mock mistapi responses and assert DataExporter.save_data_to_output called with api_function_name.
4. Run test suite and document results.

Assumptions:
- No code change requested now; this plan documents follow-ups.
