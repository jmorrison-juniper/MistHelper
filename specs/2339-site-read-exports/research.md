<!-- site-read-handoff:02-research-and-clarifications -->
# Artifact 02: research.md and clarification decisions

## Research baseline and evidence limits

The published manifest records the audited remote commit and the exact local SDK definitions. The local checkout lagged remote `main`, so remote references and the menu tail were checked separately. No application source, tests, dependency files, or active SpecKit metadata were changed during planning.

The CLI authenticated as `jmorrison-juniper`, with repository `ADMIN` permission. The inventory contained 386 open issues at the refreshed audit. No open pull requests remained at the selection check. Active coordination issues still existed, so ownership must be checked again before implementation.

### What was verified

1. All twenty source issues were open. Their comment lists were empty at selection.
2. Every selected operation has a real definition in the installed `mistapi` 0.63.3 source.
3. The committed OpenAPI 3.0 document declares an array response for each selected GET operation.
4. All twenty operations already have primary-key strategy entries.
5. Remote source references occur only in storage metadata and three metrics help strings. None provides the selected callable export integration.
6. An isolated probe compiled each existing SDK function and invoked it with a recording fake session. All twenty accepted the planned arguments. Every function issued exactly one GET. No network client existed in the probe.

### What was not verified

A normal `import mistapi` failed in the existing virtual environment with `ImportError: cannot import name 'JSONDecodeError' from 'simplejson' (unknown location)`. The isolated probes do not prove that the full SDK package imports. A new worktree must build its own environment and pass the import check before tests.

No live Mist request, full test suite, container build, database migration, or application implementation ran during planning. Do not convert these unrun checks into green checkboxes.

## Selection decisions

- Exclude active work: #1708, #1771, #1899, #1948, #2049, #2050, #2051, #2088, and the other claimed repairs.
- Exclude organization list issues that already run through `src/org_data_collector.py`. Its `Operation` rows hold callable references, not direct calls.
- Exclude #1316. `src/firmware/upgrade_service.py` already resolves `listSiteAvailableDeviceVersions` dynamically. The SDK also does not accept `type="all"` for that function.
- Exclude the map-stack issue because its operationId did not match the audited OpenAPI document.
- Exclude object-response and multi-identifier endpoints from this batch. They require different contracts.
- Do not close excluded issues automatically. Some need a focused export UX or evidence reconciliation rather than new SDK calls.

## R01: Use one bounded family

Decision: Implement one site-read family with twenty explicit metadata rows. Reference `src/export/count_exporter.py` for the choice UX only. Do not copy its `MistHelper` imports, error handling, or unchecked persistence.

Reason: #1807 documents the cost of one menu row per endpoint. A shared fetch and storage contract makes nineteen later rows inexpensive after the foundation passes.

Rejected: Twenty standalone wrappers. They duplicate prompts, retries, pagination, tests, and menu maintenance.

## R02: Inject runtime dependencies

Decision: Pass the live SDK session, organization selector, site selector, adaptive pacing callable, and page limit from the menu composition point.

Evidence: `src/utils/rate_limiting.py` contains `AdaptivePacer.pace`. `src/utils/input_utils.py` contains the canonical EOF-safe prompt. `DataExporter` owns output format selection.

Do not create an `APISession` inside the exporter. Do not add a new lazy or static import of `MistHelper` under `src/export/site_read/`.

## R03: Validate every page

Evidence: `.venv/Lib/site-packages/mistapi/__pagination.py:get_all` appends payloads without checking HTTP status. `get_next` sends `response.next` through the same session.

Decision: A small class-owned fetch loop uses SDK `get_next`, checks every response, bounds continuation, and returns records only after completion. This is pagination, not another retry implementation.

Rejected: `APIDataFetcher.execute`. It resolves organization context, retains legacy back-references, and has partial-save recovery semantics that do not match FR-006.

## R04: Keep natural identity, scope physical keys

Evidence: `src/db/arango_writer.py:ArangoDBWriter._compute_key` reads only `primary_keys[0]`. `RedisJSONWriter._build_key` reads every configured primary-key field. Per-site SQLite table names already separate sites.

Decision: Add the explicit strategy field `storage_key_fields` to these twenty entries. It contains `site_id` followed by the existing business-key fields. Keep `primary_key` and `type` unchanged. Add an opt-in key encoder to the ArangoDB and Redis JSON paths. Leave unselected strategies byte-compatible.

This prevents the new endpoints from exposing existing composite-key limitations. It is not a repository-wide storage migration. Never write an artificial API `id`, replace an upstream `id`, or use random UUIDs for a missing business key.

## R05: Redact before flattening and mirroring

Evidence: `src/security/credential_redaction.py:CredentialRedactor.redact_records` deep-copies and redacts nested values. `DataExporter._emit_rows` logs sample rows. `ExportBackendOptions.raw_data` bypasses the flattened payload for database mirrors.

Decision: Redact the copied raw records first. Then use the safe copy for both flattening and `raw_data`. Extend exact credential-key handling for `keywrap_kek`, `keywrap_mack`, and `magic` when the endpoint schemas contain them. Add tests for those fields.

The existing redactor treats a bare `key` as sensitive. Retain that policy. Do not claim multiline escaping provides credential redaction or spreadsheet-formula protection.

## R06: Preserve backend truth

Evidence: `DataExporter.write_with_format_selection` returns the primary CSV/SQLite boolean. It separately warns when a polyglot mirror fails or writes no database records.

Decision: A false primary result returns an error. A true primary result permits a saved outcome, but the message must say primary output. Do not say all backends succeeded. Preserve the canonical warnings.

## R07: Handle missing identifiers explicitly

Some derived-profile schema examples omit `id`. The schema example is not proof that production always omits it.

Decision: Reject a nonempty row without the required identity fields before any output write. Report the operation and row position, not the payload. Test this path. If an authorized live check proves the API never supplies the required identity, stop and request a reviewed business-key amendment. Do not invent `name`, an index, a hash of the body, or a timestamp as a substitute.

## R08: Resolve planning and workflow conflicts

The supplied workspace git-flow instructions require issue-first worktrees, PRs against `main`, and local validation. Older constitution text still describes direct pushes and deployment after every change. Follow the supplied authoritative git-flow instructions. Record this conflict in `analysis.md`. Do not push directly to `main` or rewrite the constitution in this batch.

The task template says tests are optional. This specification explicitly requires them, so they are mandatory here.

## Planning method

The specification, clarification decisions, research, design, plan, tasks, checklists, and analysis were authored as complete issue artifacts. Raw slash commands were not invoked. `.specify/extensions.yml` enables automatic git hooks, which would create branches or commits in the shared checkout.

This distinction is deliberate. Do not report that `/speckit.analyze` executed against materialized files. The supplied analysis is a pre-implementation document review. The implementer must materialize the artifacts in its own worktree and repeat the native prerequisite and analysis checks there.

## R09: SDK continuation probe

An isolated execution of the existing APIResponse._check_next method used X-Page-Total=1001, X-Page-Limit=1000, and X-Page-Page=1. It produced a relative /api/v1/sites/.../assets path with page=2. This confirms the C03 path contract for array pagination in SDK 0.63.3. Reject an unexpected absolute continuation rather than forwarding credentials to it.

## 2026-09-16 verification update

Issue #2339 was rechecked against `mistapi` 0.64.0 and OpenAPI 2607.1.1. All twenty SDK functions exist. All planned parameter names still match. All OpenAPI paths still match. All twenty endpoint plans name a primary-key strategy and scoped storage fields. No live Mist request occurred. Keep implementation stopped until the user assigns it. See `verification.md` for the table.
