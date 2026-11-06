# Quickstart: Stable SLE summary window keys

## Prerequisites

- Use the repository's Python 3.13+ environment with `pytest` installed.
- Do not provide Mist credentials. These checks use fake API responses.
- Use a temporary directory for SQLite fixtures and the existing Arango fake.
- Do not connect to live Mist, Redis, ArangoDB, or production SQLite.

## Offline Acceptance Checks

The implementation phase will add the focused tests under
`tests/unit/db/sle_window_summary/`. Run them with:

```sh
python -m pytest tests/unit/db/sle_window_summary -q
```

Expected result: both endpoint identities validate exactly; empty impact
`classifier`/`failure` strings remain valid; invalid or incomplete response
identity fails before writes; repeated same-window exports replace only the
new keyed record; changed identity values produce separate records; and legacy
SQLite rows and Arango UUID documents remain unchanged.

The test fixtures must demonstrate:

- A fake SDK/API response for each endpoint, with only the required path
  arguments passed to the existing SDK method.
- Response `start` and `end` used as the actual window boundaries even if the
  request was relative or the response's source dimensions conflict with
  selected path identifiers.
- Changed measurements/labels/groupings replacing content for the same
  identity, with no identity change.
- All four empty/nonempty combinations of impact `classifier` and `failure`.
- Missing and non-string classifier/failure values, invalid source dimensions,
  invalid boundaries, reversed boundaries, and a valid response row adjacent
  to an invalid row causing zero partial writes.
- A temporary SQLite database seeded with duplicate legacy rows and a later
  repeated keyed export; compare original identifiers and values byte-for-byte
  or field-for-field before and after.
- An Arango fake seeded with legacy UUID documents; verify their keys/content
  remain identical and the new deterministic document is the only one updated
  on repeat exports.
- The existing endpoint strategy retains its Arango-only routing behavior and
  does not add a RedisJSON write.

## Targeted Regression Checks

Run the new tests alongside the existing SLE exporter, SQLite writer, Arango
preservation, and strategy tests:

```sh
python -m pytest \
  tests/unit/db/sle_window_summary \
  tests/unit/export/test_endpoint_family_exporter.py \
  tests/unit/refactors/test_sqlite_database_writer.py \
  tests/unit/arango_indexes/test_preservation.py \
  tests/unit/db/test_database_schema_utils.py -q
```

Expected result: new cases pass and existing trend behavior and unrelated
endpoint strategy assertions remain unchanged.

## Scope and Safety Check

Before any implementation validation, confirm the new test paths remain
separate from open PR #4358's `tests/unit/config/...` paths. PR #4208 grants a
scoped README handover for the SLE paragraph. Preserve the WAN paragraph owned
by PR #4619. Do not run live API probes, production store checks, migrations,
data cleanup, issue edits, branch changes, or PR operations during local
validation.

See [data-model.md](data-model.md) for exact identities and
[research.md](research.md) for the contract and implementation evidence.
