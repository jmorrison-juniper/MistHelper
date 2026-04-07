# Task list

- t1-discover-api: Document API responses and pagination for /orgs/{org_id}/sites. (no deps)

- t2-add-endpoint-strategy: Add an ENDPOINT_PRIMARY_KEY_STRATEGIES entry for this operation (natural_pk on `id`). (depends: t1-discover-api)

- t3-implement-flatten: Create/extend flatten_dict or site-specific flatten_site(site_obj) to output the example flattened schema. Include sanitization for nulls and list-to-text conversions. (depends: t1-discover-api)

- t4-implement-exporter: Implement OrgSiteExporter.sites wrapper that paginates, calls flatten_site, and invokes DataExporter.write_with_format_selection to write CSV and SQLite. Add retry/backoff and streaming to avoid memory spikes. (depends: t2-add-endpoint-strategy, t3-implement-flatten)

- t5-unit-tests-flatten: Write unit tests for flatten_site with sample payloads covering missing fields and lists. (depends: t3-implement-flatten)

- t6-unit-tests-sql-upsert: Write unit tests to verify SQLite upsert behavior (idempotence, indexes). Use in-repo temp DB under data/ for tests. (depends: t4-implement-exporter)

- t7-integration-mock-api: Create an integration test that mocks paginated API responses and asserts output CSV/SQLite rows equal expected. (depends: t4-implement-exporter, t5-unit-tests-flatten)

- t8-docs-update: Update README and specs/098-audit-menu-11-org-sites with usage examples and acceptance criteria. (depends: t4-implement-exporter)

- t9-ci-and-commit: Run python -m py_compile, run tests, commit changes, include version trailer in commit message. (depends: t5-unit-tests-flatten, t6-unit-tests-sql-upsert, t7-integration-mock-api)

Notes: Keep tasks small and atomic. After tasks complete, open a single PR referencing specs/098-audit-menu-11-org-sites. Stop before IMPLEMENT as requested.