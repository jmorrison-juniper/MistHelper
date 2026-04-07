# Tasks for Export Site Zones (menu_id:52)

- task:spec/01 - Finalize spec files
  - description: Place spec_md and example schema under specs/101-audit-menu-52-site-zones and commit.
  - deps: []

- task:discover/01 - Verify API contract
  - description: Inspect SiteConfigExporter.zones implementation or provider to confirm response fields, id name (id/zone_id), pagination details, and error modes.
  - deps: ["task:spec/01"]

- task:impl/01 - Implement exporter integration
  - description: Add or update code that calls SiteConfigExporter.zones, normalizes fields to the example schema, and includes raw_json.
  - deps: ["task:discover/01"]

- task:db/01 - Register primary key strategy
  - description: Add entry for `site_zones` to ENDPOINT_PRIMARY_KEY_STRATEGIES with type natural_pk and primary_key ["site_id","zone_id"], add indexes.
  - deps: ["task:impl/01"]

- task:exporter/01 - Wire DataExporter output
  - description: Ensure CSV and SQLite exporters use the normalized schema, column order, and include raw_json column.
  - deps: ["task:impl/01","task:db/01"]

- task:tests/01 - Unit tests
  - description: Add unit tests for normalization function and exporter behavior using fixtures (empty, single, multi, malformed).
  - deps: ["task:impl/01"]

- task:tests/02 - Integration test
  - description: Run menu operation against a recorded fixture set; assert CSV/SQLite outputs, PK uniqueness, and indexing.
  - deps: ["task:exporter/01","task:tests/01"]

- task:docs/01 - README/menu update
  - description: Add operation description to README/menu index, increment operation count if applicable, and add changelog entry.
  - deps: ["task:impl/01","task:tests/02"]

- task:ci/01 - CI validation
  - description: Run python -m py_compile, existing linters/tests, and ensure no regressions. Update CI artifacts if needed.
  - deps: ["task:tests/02","task:docs/01"]

- task:release/01 - Commit & push
  - description: Commit changes with UTC version tag message, include Co-authored-by trailer. Push and create PR per repo workflow.
  - deps: ["task:ci/01"]

Notes:
- Keep each task small and testable. Implementation should be idempotent and non-destructive.
- If API lacks stable zone UUID, add a subtask to design and document stable synthetic key generation and associated caveats.
