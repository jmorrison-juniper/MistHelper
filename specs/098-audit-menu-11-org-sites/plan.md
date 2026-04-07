# High-level approach

1. Discover and document required Mist API fields and pagination behavior.
2. Implement a deterministic flatten() helper for site objects respecting the project flattening conventions.
3. Add/verify ENDPOINT_PRIMARY_KEY_STRATEGIES entry for the operation (natural_pk on `id`).
4. Implement OrgSiteExporter.sites wrapper that: calls API, paginates, flattens, and calls DataExporter.write_with_format_selection for CSV/SQLite.
5. Add unit and integration tests; update README/specs.

## Deliverables

- New/updated spec markdown under specs/098-audit-menu-11-org-sites
- Code: exporter method + flatten helpers + endpoint strategy entry
- Tests: unit tests for flattening and SQL upsert; integration smoke that writes CSV+SQLite to repo-local data/ for verification
- Documentation: README snippet + changelog entry

## Milestones

1. Design & discovery (API fields, schema) — 1 day
2. Implementation (code + strategy) — 1–2 days
3. Tests & local verification — 1 day
4. Documentation & PR — 0.5 day

## People / Roles

- Single engineer: implements, tests, documents, opens PR and fixes review comments.

## Verification plan

Manual checks:
- Run OrgSiteExporter.sites against a test org (or recorded sample) and confirm CSV contents and SQLite table structure.
- Re-run export and confirm no duplicate rows; assert upsert behavior via `SELECT COUNT(*)` and `SELECT changes()`.

Automated tests to add later:
- Unit: flattening with varied site payloads (missing/extra fields)
- Unit: SQL upsert logic produces idempotent results
- Integration: mocked API pagination and transient failures (retries)

Stop before IMPLEMENT — this plan covers design and verification steps only.