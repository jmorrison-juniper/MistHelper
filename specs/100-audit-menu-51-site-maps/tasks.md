# Tasks (ordered with dependencies)

- [ ] task: add-spec-entry
  - description: Add spec files to specs/100-audit-menu-51-site-maps (this artifact + metadata JSON)

- [ ] task: add-primary-key-strategy
  - description: Add ENDPOINT_PRIMARY_KEY_STRATEGIES['listSiteMaps'] = {type:'natural_pk', primary_key:['id'], indexes:['site_id','name','floor']}
  - depends_on: add-spec-entry

- [ ] task: implement-exporter
  - description: Implement SiteConfigExporter.maps calling mistapi, flattening records, validation, CSV + SQLite export, idempotent upsert
  - depends_on: add-primary-key-strategy

- [ ] task: write-unit-tests
  - description: Unit tests for flattening, required-field checks, CSV writer, SQLite upsert behavior (use in-memory DB)
  - depends_on: implement-exporter

- [ ] task: write-integration-tests
  - description: Integration tests using mocked API fixtures (pagination, missing optional fields, tags array) and assert outputs
  - depends_on: write-unit-tests

- [ ] task: docs-and-readme
  - description: Update README menu table, add usage example for Export Site Maps, document fields and units
  - depends_on: implement-exporter

- [ ] task: code-review-and-merge
  - description: Create PR, request review, address feedback, merge to main
  - depends_on: write-integration-tests, docs-and-readme

- [ ] task: ci-validation
  - description: Ensure CI runs tests and validates syntax; fix issues if any
  - depends_on: code-review-and-merge

Notes:
- Keep tasks small and self-contained. Use feature branch `feature/menu-51-site-maps`.
- Target: idempotent runs and clear release note entry when merged.