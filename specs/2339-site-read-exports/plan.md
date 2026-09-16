<!-- site-read-handoff:04-implementation-plan -->
# Artifact 04: plan.md

## Implementation Plan: Twenty site-read exports

**Branch after authorization:** `feat/2339-site-read-exports`.
**Base:** A fresh `origin/main`, never another feature branch.
**Spec:** The `spec.md` artifact in this issue.
**Execution model:** One owner, sequential changes, one feature concern. Do not distribute shared files across twenty agents.

## Technical Context

Use Python 3.13+, the repository's installed `mistapi`, standard-library dataclasses, typing, UUID, URL parsing, JSON, and Base64. Reuse pytest, Hypothesis, Ruff, Black, mypy, and the existing storage libraries. No new runtime dependency is necessary.

Target Windows and Linux. The user-facing interface is the existing CLI menu. The primary output is CSV or SQLite. The canonical router handles ArangoDB and Redis according to the existing strategy types.

The source set is twenty exact GET operations. Store catalog data as four groups of five entries and flatten them in manifest order. Requests are sequential and use the existing adaptive pacer. The safety limits are 1,000 pages and 1,000,000 rows per selection.

## Constitution Check and decisions

- Use semantic classes. Do not add standalone pass-through wrappers.
- Keep every new function at 25 lines or fewer and five parameters or fewer. Keep new classes and modules bounded. The new feature package has five modules.
- Add meaningful inline comments and before/after action logging to touched code blocks.
- Never log credentials. Use ASCII messages and Simplified Technical English.
- Require tests despite the task template's optional-test example.
- Preserve business IDs. The physical scoped-key encoder uses their values without changing the API `id`.
- Follow the supplied issue-first worktree and PR policy. Older direct-to-main deployment instructions conflict with that policy and must not drive this work.
- Do not refactor unrelated, already-large directories merely to reduce their child count. Record the pre-existing structural debt instead.

## New source files

| File | New symbols and ownership |
| --- | --- |
| `src/export/site_read/__init__.py` | Keep package initialization inert. A docstring is sufficient. |
| `src/export/site_read/models.py` | Own `EndpointSpec`, `SiteReadRuntime`, `SiteReadRequest`, `SiteReadOutcome`, and `SiteReadError`. |
| `src/export/site_read/catalog.py` | Own `SiteReadCatalog`. It returns explicit entries, resolves one entry, imports its callable, and builds supported initial keyword arguments. |
| `src/export/site_read/fetch.py` | Own `SiteReadFetcher` and `SiteReadPageGuard`. Separate request execution from status, continuation, and bound validation. |
| `src/export/site_read/service.py` | Own `SiteReadExporter`, `SiteReadRecords`, and `SiteReadPersistence`. Separate selection, validation/redaction, and writing. |
| `src/db/storage_keys.py` | Own `StorageKeyEncoder`. Keep it independent of Mist, database connections, and the feature package. |

Use at most five methods per new class. Extract within these modules when necessary. Do not put tests inside `src/`.

### Suggested method boundaries

`SiteReadExporter`: `__init__`, `interactive`, `run`, `_select_request`, `_report`.

`SiteReadCatalog`: `entries`, `get`, `resolve_callable`, `build_kwargs`.

`SiteReadFetcher`: `__init__`, `fetch`, `_first_page`, `_next_page`, `_accept_page`.

`SiteReadPageGuard`: `validate_response`, `validate_continuation`, `check_bounds`.

`SiteReadRecords`: `validate`, `enrich`, `redact`, `flatten`, `output_name`.

`SiteReadPersistence`: `write`. It calls the canonical writer and interprets its boolean. It does not implement another CSV or database writer.

`StorageKeyEncoder`: `values`, `encode`. It is a pure identity formatter, not a store or a fallback generator.

These boundaries describe implementation ownership. Do not create empty forwarding methods merely to match a name list.

## Existing files to modify narrowly

| File | Exact change |
| --- | --- |
| `MistHelper.py` | Add private imports and one lazy menu composition using the live `apisession`, `PromptUtils.select_site`, `ConfigUtils.get_cached_or_prompted_org_id`, `AdaptivePacer(apisession, _api_usage_cache).pace`, and `DEFAULT_API_PAGE_LIMIT`. Do not change `__all__` or existing entries. |
| `src/utils/operation_registry.py` | Register the new number as `interactive_safe` with a clear prompt-related reason. Use the actual existing registry value type. |
| `src/refactors/endpoint_primary_key_strategies.py` | Add `storage_key_fields` to the twenty existing entries only. Do not append duplicate dictionary keys. |
| `src/db/arango_writer.py` | Opt into scoped encoding in `_prepare_document`. Preserve the old path for strategies without the new field. |
| `src/db/redis_writer.py` | Carry the opt-in key mode through `RedisJSONWriter` batch operations. Preserve ordinary endpoint keys and Redis TimeSeries code. |
| `src/security/credential_redaction.py` | Extend the exact-key set for the three documented credential names. Keep deep-copy behavior and existing field rules. |
| `README.md` | Document one family menu and link its endpoint table. Do not add twenty menu numbers. |
| `CHANGELOG.md` | Add one feature entry after tests pass. Keep the repository's timestamp version format. |
| `documentation/menu_reference.md` and `documentation/wiki/Menu-Reference.md` | Regenerate both with the existing generator. Never edit only one copy. |
| The twenty `specs/.../spec.md` files named in the packets | Correct SDK modules, state family integration, and link this handoff. Keep a truthful delivery status. |

If an existing writer defect blocks a new regression test, stop and record a separate issue before expanding this file set. Do not suppress, deselect, or weaken that test.

## Existing code to read and reuse

- `src/export/count_exporter.py:CountExporter._choose` shows the numbered family-choice UX. Its other behavior is not a safe implementation template.
- `src/utils/input_utils.py:InputUtils.safe_input` returns an empty default on EOF and Ctrl+C. It does not raise in those normal cancellation paths.
- `src/utils/rate_limiting.py:AdaptivePacer.pace` carries the adaptive state and applies the delay.
- `src/data/data_processing_utils.py:DataProcessingUtils.flatten_nested_fields` normalizes nested records.
- `src/export/data_exporter.py:DataExporter.write_with_format_selection` returns the primary writer result and emits mirror warnings.
- `src/dataclasses/export_backend_options.py:ExportBackendOptions` transports safe raw data to the database router.
- `src/security/credential_redaction.py:CredentialRedactor.redact_records` protects nested credential fields without mutating the input.
- `src/db/router.py:DatabaseRouter.write` routes natural keys to ArangoDB and composite keys to the existing dual-write path.
- `src/db/arango_writer.py:ArangoDBWriter._prepare_document` is the physical-key integration point.
- `src/db/redis_writer.py:RedisJSONWriter.write` and `_build_key` are the Redis JSON identity integration points.
- `src/refactors/sqlite_database_writer.py:SQLiteDatabaseWriter.write` and `src/db/database_schema_utils.py:DatabaseSchemaUtils` own SQLite persistence and DDL.
- `scripts/generate_menu_wiki.py` regenerates both menu-reference files.

## Test layout

Create exactly five files under `tests/unit/export/site_read/`:

1. `conftest.py` supplies a fresh fake session, deterministic UUIDs, a fake pacer, safe rows, and endpoint cases.
2. `test_catalog.py` checks all twenty callables, signatures, paths, metadata, and strategy keys.
3. `test_fetch.py` checks status, pagination, limits, malformed data, and no partial writes.
4. `test_service.py` checks prompts, cancellation, context, redaction, filenames, and writer outcomes.
5. `test_storage.py` checks real temporary SQLite upserts and recording ArangoDB/Redis clients without network connections.

Extend `tests/unit/test_arango_writer.py`, `tests/unit/test_redis_writer.py`, and `tests/unit/security/test_credential_redaction.py` for shared behavior changes. Keep their previous cases passing. Add a new storage-key test module under `tests/unit/db/` if the encoder needs isolated property tests.

Use `tests/unit/refactors/test_sqlite_database_writer.py:stub_deps` as the isolation pattern, not its mock DDL as the idempotency proof. For the new proof, use the real `DatabaseSchemaUtils` and a temporary SQLite file. The example fixture's simplified DDL does not declare a primary key.

Run `tests/guardrails/test_operation_registry_menu_coverage.py`, `tests/unit/test_operation_registry_fail_closed.py`, and `tests/unit/test_no_new_legacy_facade_imports.py`. Read `tests/unit/test_exports.py` and `tests/test_exports.py` before changing public imports.

## Ordered implementation phases

1. Preflight and artifact materialization. No application edits before the interpreter, ownership, and prerequisite checks pass.
2. Foundation: models, explicit catalog shape, safe pagination, redaction, and scoped-key tests.
3. US1: Finish one paginated endpoint end to end. Use #1313 as the first proof.
4. US2: Finish cancellation and failed-page behavior before expanding the catalog.
5. US3: Finish SQLite, ArangoDB, Redis, and redaction cases before expanding the catalog.
6. Process the twenty packets in the published order. Shared files are sequential, not parallel.
7. US4: Wire the single menu entry and update generated documentation.
8. Run the full gates, review the diff, and prepare one focused PR.

A packet may be researched in parallel. It may not modify `catalog.py`, shared tests, strategy configuration, README, changelog, or the menu concurrently with another worker.

## Migration and rollback

The opt-in physical key format is new only for these endpoint collections. Verify that a deployment has no pre-existing manually imported records before enabling it. Otherwise obtain a separate reviewed migration. Do not delete an existing database or container volume.

A rollback removes the new menu integration or reverts its feature commit through review. It must not clean up data automatically. Keep logs and failed-test evidence.

## 2026-09-16 verification update

Issue #2339 was rechecked against `mistapi` 0.64.0 and OpenAPI 2607.1.1. All twenty SDK functions exist. All planned parameter names still match. All OpenAPI paths still match. All twenty endpoint plans name a primary-key strategy and scoped storage fields. No live Mist request occurred. Keep implementation stopped until the user assigns it. See `verification.md` for the table.
