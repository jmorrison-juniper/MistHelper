# Audit: Menu #26 — Export gateway templates from the organization

Summary:
- Menu 26 maps to GatewayExportUtils.templates() which calls mistapi.api.v1.orgs.gatewaytemplates.listOrgGatewayTemplates and writes CSV via DataExporter.save_data_to_output.
- ENDPOINT_PRIMARY_KEY_STRATEGIES contains an entry for "listOrgGatewayTemplates" (type: natural_pk, primary_key: ["id"]).
- The templates() method does NOT use DataExporter.write_with_format_selection(..., api_function_name=...). It uses save_data_to_output directly; therefore SQL export (SQLite upsert/updating) behavior may be missing.
- Tests: repo contains unit tests for PK strategies (tests/unit/test_pk_strategies.py) but no explicit unit or integration test covering GatewayExportUtils.templates or SQL export compliance.

Risk/Impact:
- Without write_with_format_selection and api_function_name, exports may not support SQL upsert/indexing or PK strategy enforcement.
- Low test coverage increases risk of regressions when updating export behavior.

Recommendation:
- Update GatewayExportUtils.templates() to call DataExporter.write_with_format_selection(templates, "OrgGatewayTemplates", api_function_name="listOrgGatewayTemplates") or equivalent.
- Add unit tests verifying:
  - templates() invokes the correct API and writes via write_with_format_selection with proper api_function_name
  - SQL export produces expected table schema/PKs when writing to SQLite (integration test using temporary DB)

Assumptions:
- DataExporter.write_with_format_selection exists and implements SQL export when api_function_name is provided.
- Modifications will follow project conventions (no wrappers; use classes/staticmethods as appropriate).