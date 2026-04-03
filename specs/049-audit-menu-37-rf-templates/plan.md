Plan for Menu #37:

1. Add unit test similar to Menu #36 but for RF templates.
2. Patch mistapi.api.v1.orgs.rftemplates.listOrgRfTemplates to return test payload.
3. Patch DataExporter.write_with_format_selection to capture the api_function_name argument.
4. Assert 'listOrgRfTemplates' is passed through.

Rationale: Maintain parity with other OrgExportUtils exports and ensure correct SQLite schema and upsert behavior.