# Implementation Plan: History Organization Isolation

**Branch**: `jmorrison-juniper-history-organization-isolation`

**Date**: 2026-09-30

**Spec**: [spec.md](spec.md)

**Input**: `specs/3484-history-org-isolation/spec.md`

**Inspected revision**: `b14078edd41cb0fe70437ae9ac6f2ec6e8882272`

**Parent session**: `af274df3-bdff-4d8d-9603-ef1494e1b8c0`

## Summary

Repair issue #3484 only.
Every history request must use the selected organization from the signed session.
The current identity service must authorize that selection before any history source reads records.

Keep the capture and run lister signatures unchanged.
Their real store adapters must supply the selected organization through the existing query fields.
The store already filters rows and totals before pagination.

Require an explicit organization on audit reads.
Filter audit records before inference and result limits.
Keep inference state separate for each organization and site.
Preserve the current operation scope, progress-link ownership, history presentation, firmware behavior, and bulk confirmations.

## Technical Context

**Language/Version**: Python 3.13 or newer. The existing isolated environment uses Python 3.13.13.

**Primary Dependencies**: Existing Flask 3.x, Jinja2, python-arango, pytest, and repository development tools. No new dependency.

**Storage**: Existing capture and run collections, existing operation records, and the existing append-only JSONL lock trail.

**Testing**: Direct Flask response contracts, real query types with synthetic database readers, and synthetic audit trails.

**Target Platform**: Existing upgrade portal. Validate locally in this exclusive Darwin worktree without a server or container.

**Project Type**: Existing Python web application.

**Performance Goals**: Keep database filtering before counts and page limits. Keep bounded audit memory proportional to matching open holds and the result limit.

**Constraints**: No production data, credentials, cloud calls, schema changes, database-key changes, lock-key changes, or dependency changes.

**Scale/Scope**: Four request forms and four history sources. Two production files, two new regression files, one release-note fragment, and six coupled test migrations.

[research.md](research.md) resolves every design question.
This step does not run acceptance tests.

## Constitution Check

The applicable constitution is version 1.5.0.
The specification checklist passes all 16 items.

The explicit task and app instructions control this repair's boundary.
They require the app-managed branch and prohibit edits to the README owned by another session.
They require new isolation evidence without unrelated directory refactoring.
The repair retains the existing test locations and documents behavior in this specification and the Security fragment.
These narrow task instructions supersede conflicting repository defaults for branch naming, README edits, and new children in existing test directories.
Do not change the constitution or shared instructions.

| Gate | Design decision | Result |
| --- | --- | --- |
| I. Structural discipline | Edit existing production modules only. Add no production module, helper class, or wrapper. Record existing debt below. | Pass with bounded exceptions. |
| II. Class-based architecture | Preserve the existing route and adapter boundaries. Use class-owned synthetic readers and grouped regression tests. Add no standalone delegating wrapper. | Pass with existing debt recorded. |
| III. Safety first | Reuse the existing session and organization authorities. Refuse invalid selections before reads. Keep history independent of locks and confirmations. | Pass. |
| IV. Delivery pipeline | This step writes planning documents only. Later code delivery requires local gates, a local commit, and the coordinator's queue release. | Pass for planning. |
| V. Observability | Use ASCII logs with safe counts and decisions. Do not log credentials, audit addresses, or complete stored rows. | Pass. |
| VI. Inline comments | Add explanatory inline comments to changed executable lines and the touched block. Do not suppress this gate. | Required during implementation. |
| VII. Action logging | Add information logs before meaningful reads and debug summaries afterward. Preserve exception handling and credential redaction. | Required during implementation. |
| Technology and storage | Reuse Python 3.13+, existing packages, query types, schemas, retention, backup, and recovery rules. | Pass. |
| Quality evidence | Require a failing isolation contract, repaired contracts, scoped coverage, the unchanged quality ratchet, and regression evidence. | Required during implementation. |

**Pre-design result**: Pass for this planning-only step.
No unjustified new production structure or unresolved design question remains.

**Post-design result**: Pass for this planning-only step.
The design adds no authentication policy, external dependency, persistence write, or new public history route.
Implementation remains subject to the file-ownership hold below.

### Existing debt and separate remediation

The current route directory has 13 children.
The comparison directory has eight children.
`review.py` has 74 top-level functions and classes.
`lock_audit.py` has eight.
These existing structures exceed the five-item limit.
The repair must not add a production child to these structures.

Existing touched functions also exceed 25 physical lines:

| Existing function | Current lines |
| --- | --- |
| `review.audit_history_rows` | 33 |
| `review.history_page` | 39 |
| `lock_audit.mark_expiries` | 35 |
| `lock_audit._read_limited_audit_rows` | 32 |

Use short changed blocks and keep every new method within the project limits.
Do not add helper wrappers to reduce a line count.
A separate, coordinator-owned change can move service logic into compliant class-owned packages.
That change must migrate callers directly and remove obsolete names.
It is not part of #3484.

The existing contract and unit directories have 56 and 152 children.
The user explicitly names the two future regression files in these directories.
This plan records that test-location exception without treating it as permission for new production structure.
A separate test-organization change can consolidate these large directories after ownership review.

## Project Structure

### Documentation for this feature

This step writes exactly these files:

```text
specs/3484-history-org-isolation/
  plan.md
  research.md
  data-model.md
  quickstart.md
  contracts/history-scope.md
```

The existing `spec.md` and `checklists/requirements.md` remain unchanged.
This step does not create `tasks.md`.

### Existing source boundaries

```text
src/interfaces/portals/upgrade_portal/
  app/routes/review.py
  compare/lock_audit.py
  capture/store.py                  # Read-only dependency.
  runtime/identity.py               # Read-only authority.
  upgrade/org_history.py            # Read-only dependency.
```

`app/routes/select.py` supplies the existing selection and refusal authorities.
`app/seam_shapes.py` records the existing injected lister calls.
Neither file needs an implementation edit.

**Structure decision**: Keep the repair within the claimed production files.
Use existing selection functions, existing query types, and existing record shapers.
Do not create another service layer or compatibility path.

## Phase 0: Research

Research used the current worktree's specification, checklist, constitution, source code, tests, and validation configuration.
No delegation, external research, cloud call, or production-store read occurred.

[research.md](research.md) records these decisions:

1. Reuse the signed selection and current authorization policy.
2. Scope the real adapters without changing capture or run seam calls.
3. Require organization scope on both audit paths.
4. Preserve organization-and-site inference and existing response behavior.
5. Use direct synthetic evidence and the exact migration list.

## Phase 1: Design and Contracts

### 1. Refuse before any history read

Keep `identity.require_session` on all three registered history handlers.
These handlers implement all four request forms.

In each handler, read `select.resolve_org(None)` and normalize the returned string with `strip()`.
A missing value becomes an empty string.
The resolver already rejects incorrectly typed saved values.

Call `select.org_refusal` with the normalized value before resolving or invoking any history reader.
Return its existing refusal when present.

- Missing, blank, whitespace-only, or incorrectly typed selections produce `400 org_not_chosen`.
- Known privileges that exclude the selection produce `403 org_not_permitted`.
- A known empty privilege set excludes every selection.
- Unavailable privileges retain the existing environment-token policy.
- The existing sign-in guard still acts first.

Use only the signed organization selection.
Ignore organization values in request bodies, forms, and query parameters.
`select.read_chosen_org` reads selection submissions, not the saved selection for history.
Do not select the first permitted organization or infer one from a record.
Do not change `identity.org_is_permitted`.

### 2. Scope capture and run adapters

Keep these signatures unchanged:

- `store_capture_rows(site_id, limit, offset)`
- `store_run_rows(site_id, limit, offset)`
- `CAPTURE_LISTER` and `RUN_LISTER`

Each real adapter must read the normalized signed selection and reuse `select.org_refusal` before source access.
If refusal occurs, terminate the request with that existing response.
Flask can abort with the response produced by `current_app.make_response(refusal)`.
Do not convert a refusal into an unscoped query or a successful empty authorization result.

Construct the existing `CaptureQuery` or `RunQuery` with `org_id`, `site_id`, `limit`, and `offset`.
The existing store supplies both scoped count queries and scoped page queries.
Do not filter a page after the store calculates its total.

Keep `call_lister`, `read_store_page`, and `app/seam_shapes.py` unchanged.
The existing window introspection does not carry an organization parameter that it could discard.
The trusted real adapter supplies that scope itself.
Do not add signature retries or a site-only real-store fallback.

The comparison picker shares `CAPTURE_LISTER`.
Preserve its site-only call shape and default window.
Its real adapter must also avoid an unrestricted read when the signed selection is invalid.
Do not change comparison loading, export behavior, or comparison refusal text.

### 3. Keep one scope for operation and audit sections

Use the validated organization for `run_control_org_id`.
Pass that organization into the existing operation and audit section helpers.
Update their single route call sites directly.

Keep the operation lister contract unchanged.
`OrgOperationHistory` and `OperationQuery` already accept the organization and optional site.
Preserve operation ordering and the owner-only progress links.
Do not expose owner keys.

The audit section must call `read_audit_rows(org_id=chosen, site_id=site_id)`.
Keep the audit default limit independent of the capture and run page limit.
Preserve the existing moment shaper and audit row fields.

### 4. Make audit scope mandatory

Add a required keyword-only `org_id` to `read_audit_rows`.
Keep the existing `limit`, `path`, and `site_id` parameter order.
Reject an empty or incorrectly typed organization before opening the trail.
Do not retain a default organization or unrestricted public read path.

Apply organization-and-site matching before inference state changes and before result limits.
Records without matching organization attribution must not enter the result or influence a matching hold.

For a positive limit, scan the complete trail in order.
Retain earlier matching context even when it falls outside the visible result.
Append only matching action and inferred rows to the bounded deque.
Remove `_keep_in_scope`.
Append already scoped rows directly.
Migrate the existing private calls directly.

For the legacy non-positive or unbounded path, filter the complete input before `mark_expiries`.
Keep the existing final Python slice behavior.
Do not redefine zero, negative, or `None` limits.

Use `(org_id, site_id)` for the in-memory holder keys in both inference paths.
This tuple changes no database key or lock key.
Keep `mark_expiries(rows)` available to its current callers with the same signature.

Preserve these rules:

- A take after an unreleased take or takeover inserts one expiry.
- The expiry uses the earlier hold's attribution and the later take's moment.
- A release prevents the corresponding expiry.
- A takeover opens or replaces a hold without inserting an expiry.
- A missing action retains the legacy takeover meaning.

Keep `expiry_row`, `audit_row`, and damaged-line handling behavior unchanged.
Continue to display operator digests, not stored audit addresses.

### 5. Produce validation artifacts

- [data-model.md](data-model.md) defines the existing fields and transient scope.
- [contracts/history-scope.md](contracts/history-scope.md) defines response, adapter, and audit obligations.
- [quickstart.md](quickstart.md) defines safe, runnable validation commands.

Do not add a browser journey for this server-only design.
This design changes server-side scope and refusals only.
Direct complete-response contracts can prove the changed behavior.

### Agent context boundary

The standard setup script persists `.specify/feature.json`.
The agent-context script writes shared instruction files.
The companion post-hook targets `.spec-context.json`.
These write phases are outside the user's explicit file boundary.

PowerShell is unavailable, so the required setup invocation failed before it could run.
This step resolved paths directly from the explicit feature directory.
The core plan template supplied this document's structure.
Keep all new context in these five feature artifacts.
Do not install PowerShell, create another worktree, or update shared state.

## Phase 2: Planning Handoff

### Current claimed implementation surface

| File | Required implementation work |
| --- | --- |
| `src/interfaces/portals/upgrade_portal/app/routes/review.py` | Early refusals, scoped real queries, validated section scope, and unchanged lister signatures. |
| `src/interfaces/portals/upgrade_portal/compare/lock_audit.py` | Required organization, early filtering, independent inference, and both limit paths. |
| `tests/contract/upgrade_portal/test_issue_3484_history_org_isolation.py` | Four request forms, four cards, real adapters, exact totals, and zero-read refusals. |
| `tests/unit/upgrade_portal/test_issue_3484_audit_org_isolation.py` | Two-organization audit results, limits, inference, attribution, and digest safety. |
| `changelog.d/issue-3484-history-org-isolation.md` | One Security fragment for the exact repair. |

### Exact additional test migration list

The parent must check ownership and claim these six files before implementation edits.
They remain unchanged in this step.

| Additional file | Smallest required migration |
| --- | --- |
| `tests/contract/upgrade_portal/test_history_routes.py` | Give `signed_in_client` an explicit selected organization. Keep all existing lister signatures and page assertions. Isolate unused operation reads. |
| `tests/contract/upgrade_portal/test_history_device_type.py` | Give `signed_in_client` an explicit selected organization. Keep device-type rows and assertions unchanged. Isolate unused operation reads. |
| `tests/contract/upgrade_portal/test_upgrade_routes/test_stale_views.py` | Give `stale_client` its existing `ORG_ID` selection. Keep stale, terminal, and malformed-time assertions unchanged. Isolate unused operation reads. |
| `tests/contract/upgrade_portal/test_history_operations.py` | Change `test_no_selected_organization_reads_nothing` to assert `400 org_not_chosen` and no reads. Do not render a missing-selection card. |
| `tests/unit/upgrade_portal/test_review_store_seams.py` | Add explicit selection in local Flask request contexts. Add `org_id` to `FakeQuery` and both successful query assertions. |
| `tests/contract/upgrade_portal/test_lock_audit_log.py` | Add `org_id=ORG_ID` at all 14 direct audit-reader calls. Correct inference comments without changing successful expectations. |

Capture and run seam APIs keep their current call forms.
Keep `app/seam_shapes.py`, `test_lock_free_reads.py`, shared `conftest.py`, and the browser environment unchanged.
`test_lock_free_reads.py` already selects an organization.
The #3482 and #3486 presentation tests remain regression evidence, not edit targets.

### Acceptance evidence

Use Organization A with Sites A1 and A2, and Organization B with Site B1.
Include reused site text across organizations for audit inference.
Use distinct identifiers, labels, counts, moments, account labels, and operator digests.

The new contracts must exercise real `CaptureQuery`, `RunQuery`, `OperationQuery`, and store readers with a synthetic database.
The synthetic database must apply only filters actually present in each query.
It must not silently supply a missing organization restriction.
Check bind values and filter positions in count and page queries.

Inspect complete HTML and JSON.
Assert exact matching rows and totals, and absence of every foreign sentinel.
Cover empty selected history, populated foreign history, site intersections, later pages, and changed privileges.
Prove zero calls to all four sources for every refusal.

Audit tests must use independent expected events.
Cover both opening actions, release suppression, takeover behavior, older context, foreign events, unattributed rows, and bounded/unbounded equality.
Do not use the production shaper to construct the complete expected result.

### Validation and delivery hold

Capture a baseline before production edits.
Demonstrate a failing content or count contract on the defective source.
Rerun the same contract after the repair.

Run compile, Ruff, Black, strict mypy, Bandit, scoped coverage at 80% or higher, and the repository test-quality ratchet.
Read `MYPY_PATHS` from `.github/workflows/ci.yml`.
Keep `.github/test-quality-config.toml` and `.github/test-quality-baseline.json` unchanged.
Run the coupled regression suite and the focused history, authorization, audit, comparison, firmware, and bulk-control regressions.
The latest coordinator instruction requires focused validation, not repeated unrelated repository suites.
The full CI type scope remains unchanged and applies during protected PR checks.
Local strict mypy covers both changed source files.
Local compile, lint, and format cover every changed Python file and `MistHelper.py`.
Local Bandit covers both changed source files and retains the repository exclusion check.
The quality ratchet checks all eight changed test files against the unchanged repository configuration and baseline.
The original broad baseline commands did not run.
Do not describe a post-repair run as a pre-repair baseline.

Later implementation must complete local validation and a local commit before it enters the coordinator queue.
Report to the parent session and wait for the coordinator's release and stable main SHA.
Do not push or open a pull request before that release.
No delivery action occurs in this planning step.
The latest queue places #3305 after #3398 and before #3484.
The earlier queue position 7 is historical.

### Excluded files and actions

Do not edit `README.md`, `portal.js`, `org_upgrade.py`, `upgrade/options.py`, `upgrade/gate.py`, or `CHANGELOG.md`.
Do not edit the browser environment, bootstrap files, dependency files, or git-flow, Dependabot, and title-guard files.
Do not edit shared instruction or context files.
Do not inspect another worktree or the main checkout.
Do not implement, delegate, create or switch branches, commit, push, open a pull request, merge, or deploy.

### Planning execution record

This step generated only the five approved planning artifacts.
File-boundary, input-hash, link, sentence-length, and validation-command syntax checks passed.
STE scores were 97 or 98.
The configured dictionary was absent, so dictionary checks did not run.
No implementation or acceptance tests ran.

The setup and agent-context invocations failed because PowerShell was absent.
The companion hook dispatch failed because its local handler was absent.
No substitute state write occurred.
Optional Git hooks remained unexecuted.
The branch, revision, specification, checklist, shared context, instructions, and quality baseline remained unchanged.

## Complexity Tracking

| Existing constraint or exception | Why this repair retains it | Separate remediation |
| --- | --- | --- |
| Large production directories and module namespaces | The explicit claim permits two existing production files. The repair adds no production child. | Consolidate class-owned services in a separately claimed change. |
| Existing standalone route and adapter functions | Their names define current Flask and injected-reader boundaries. This repair adds no delegating wrapper or alternate API. | Migrate service callers directly during the separate class refactor. |
| Existing long composers and inference functions | A broad extraction would exceed this issue's scope. Keep changed blocks short and record the current lengths. | Reduce complete function size during the separate structural change. |
| Explicit new test locations in large test directories | The user names these two regression paths. The exception is limited to these tests. | Reorganize test groups under separate ownership. |
