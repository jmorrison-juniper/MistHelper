# Tasks for Audit: Menu 20 - Sites with Location and Timezone

- audit-menu-20-read-code
  - Read OrgSiteExporter.sites_with_location and document current behavior (data sources, transforms, exporter call)
  - Assignee: reviewer
  - Status: pending

- audit-menu-20-check-pk-strategy
  - Verify ENDPOINT_PRIMARY_KEY_STRATEGIES includes an entry for listOrgSites (natural_pk) and document any gaps
  - Assignee: reviewer
  - Status: pending

- audit-menu-20-verify-export-call
  - Confirm whether DataExporter.write_with_format_selection is used with api_function_name and recommend change if not
  - Assignee: reviewer
  - Status: pending

- audit-menu-20-add-unit-tests
  - Create unit tests for sites_with_location: mock APICoreFetchUtils.all_sites_with_limit and assert DataExporter called appropriately; add test file tests/unit/test_org_site_exporter.py
  - Assignee: developer
  - Status: pending

- audit-menu-20-add-integration-tests
  - Add integration test to simulate OUTPUT_FORMAT=sqlite and ensure SQLite table uses PK strategy (requires test harness)
  - Assignee: developer
  - Status: pending

- audit-menu-20-docs-update
  - Update README/CHANGELOG to note audit and any behavioral changes after remediation
  - Assignee: docs
  - Status: pending
