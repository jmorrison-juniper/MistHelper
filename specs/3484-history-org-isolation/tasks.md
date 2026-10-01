# Tasks: History Organization Isolation

**Issue**: #3484.

**Feature directory**: `specs/3484-history-org-isolation`.

**Branch**: `jmorrison-juniper-history-organization-isolation`.

**Inspected revision**: `b14078edd41cb0fe70437ae9ac6f2ec6e8882272`.

**Parent session**: `af274df3-bdff-4d8d-9603-ef1494e1b8c0`.

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md), [data-model.md](data-model.md), [history-scope.md](contracts/history-scope.md), and [quickstart.md](quickstart.md).

**Governance**: [Constitution 1.5.0](../../.specify/memory/constitution.md).

**Tests**: Required. Write direct synthetic regressions before production repair. Do not add a browser journey.

**Organization**: All four stories have P1 priority. Their repair order is US2, US4, US1, then US3.
US2 supplies the refusal and adapter boundary.
US4 supplies the required audit scope.
US1 joins the four scoped cards.
US3 verifies the site intersection and preserved controls.

## Execution Boundary

The task-generation step wrote only this document.
Checkboxes now record implementation and validation evidence.
No implementation or acceptance test ran during task generation.

The explicit task instructions control branch naming, test placement, and README ownership.
Use the existing app-managed branch and approved test paths.
Keep the README reserved for the other session.
Document the behavior in the feature contract and Security fragment.
Do not change the constitution or shared instructions.

Use the current exclusive worktree and existing app-managed branch.
Set `SPECIFY_FEATURE_DIRECTORY=specs/3484-history-org-isolation`.
Do not resolve another feature from shared context.
Do not create or switch a branch, inspect another checkout, or delegate.

The parent checked the six fixture migrations for open-PR overlap.
The parent must record those claims before implementation edits.
Do not repeat that check through GitHub or add another file.

Use only synthetic readers, synthetic records, and temporary audit trails.
Use the existing isolated `.venv` with Python 3.13.13.
Do not load credentials, `.env`, production configuration, or production stores.
Do not make API or cloud calls.
Do not start containers, servers, or browsers.
Do not install dependencies or run bootstrap scripts.

### Approved Implementation Files

| File | Purpose |
| --- | --- |
| `src/upgrade_portal/app/routes/review.py` | Refusals, scoped real adapters, validated section scope, and run-control context. |
| `src/upgrade_portal/compare/lock_audit.py` | Required organization, matching before inference, and existing limit semantics. |
| `tests/contract/upgrade_portal/test_issue_3484_history_org_isolation.py` | New direct contracts for all request forms and real query paths. |
| `tests/unit/upgrade_portal/test_issue_3484_audit_org_isolation.py` | New audit contracts with independent expected events. |
| `changelog.d/issue-3484-history-org-isolation.md` | One Security release-note fragment. |
| `tests/contract/upgrade_portal/test_history_routes.py` | Explicit selection and isolated unused operation reads. |
| `tests/contract/upgrade_portal/test_history_device_type.py` | Explicit selection without changing device-type expectations. |
| `tests/contract/upgrade_portal/test_upgrade_routes/test_stale_views.py` | Explicit selection without changing stale-run expectations. |
| `tests/contract/upgrade_portal/test_history_operations.py` | Missing-selection refusal and zero-read expectations. |
| `tests/unit/upgrade_portal/test_review_store_seams.py` | Selected request contexts and the existing query's organization field. |
| `tests/contract/upgrade_portal/test_lock_audit_log.py` | Explicit organization at 14 existing audit-reader calls. |

Keep `capture/store.py`, `app/routes/select.py`, `runtime/identity.py`, `app/seam_shapes.py`, and `upgrade/org_history.py` read-only.
These files supply existing queries, authorities, and interfaces.
Create no production wrapper, class, or module.
Create no schema, database-key, lock-key, or dependency change.

Keep shared fixtures and instruction files unchanged.
Keep `.specify/feature.json`, `.spec-context.json`, and feature context files unchanged.
Keep `.github/test-quality-config.toml` and `.github/test-quality-baseline.json` unchanged.
Add no suppression or baseline update.

Do not edit `README.md`, `portal.js`, `org_upgrade.py`, `upgrade/options.py`, `upgrade/gate.py`, or `CHANGELOG.md`.
Do not edit `tests/support/upgrade_portal_e2e/environment.py`, bootstrap files, or `requirements-dev.txt`.
Do not edit git-flow instructions, Dependabot configuration, or title guards.

### Checklist Rules

- Each task uses `- [ ] TNNN`, an optional `[P]`, and a concrete file path.
- Story phases require `[US1]`, `[US2]`, `[US3]`, or `[US4]`.
- Setup, foundational, and polish tasks have no story label.
- `[P]` identifies independent work. It does not authorize delegation or another worktree.
- Check a task only after verification. Append an evidence note, such as `(delivered: src/upgrade_portal/app/routes/review.py)`.

For a read-only check, record the command, exit status, checked count, and result.
Store validation reports outside the repository.
If a prerequisite fails, keep dependent tasks unchecked.
If repair requires an unclaimed file, report the blocker to the parent.
Do not widen the file list.

### Execution Stages

Task IDs define execution order.
Story sections group related tasks, not complete execution stages.
Complete every story's red contract before any production repair.
Use this stage table and the explicit prerequisites below.

| Stage | Tasks | Work |
| --- | --- | --- |
| A | T001 through T005 | Safe setup, coupled baseline, and explicit validation-scope decisions. |
| B | T006 through T007 | Shared synthetic fixtures. |
| C | T008 through T012 | Story-specific red contracts across all four story sections. |
| D | T013 | Shared behavioral red gate. |
| E | T014 through T024 | Refusal/adapter repair, then audit repair and verification. |
| F | T025 through T028 | Complete organization-page integration. |
| G | T029 through T032 | Site verification and preserved controls. |
| H | T033 through T045 | Local gates, mandatory analysis, and parent report. |

## Phase 1: Setup

**Goal**: Confirm ownership, preserve the environment, and record the unrepaired baseline.

- [X] T001 Confirm the worktree, branch, and parent-recorded migration claims against `specs/3484-history-org-isolation/plan.md`. (Verified the current worktree and branch. The parent supplied claim comment `5920009353`.)
- [X] T002 Prepare credential-free validation with the existing `.venv/bin/python` and `specs/3484-history-org-isolation/quickstart.md`. (Python 3.13.13. No install or shared-context write. PowerShell is absent. Read-only prerequisite checks passed for two required files. All 16 checklist items passed.)
- [X] T003 Record the coupled baseline for `tests/contract/upgrade_portal/test_history_routes.py` and the other files in command B1. (B1: exit 0, 226 collected and passed, no failures or skips. Evidence: session artifact `issue-3484-baseline.txt`.)
- [X] T004 [P] Record that the broader unit baseline is outside the coordinator-approved local scope. (The original B2 command did not run. The coupled pre-repair baseline supplies genuine unit evidence.)
- [X] T005 [P] Record that the broader contract, guardrail, and integration baseline is outside the coordinator-approved local scope. (The original B3 command did not run. No post-repair result substitutes for that missing baseline.)

T001 does not create a claim file.
It requires the parent's recorded ownership confirmation.
T002 does not install or bootstrap anything.
Record baseline failures and skip reasons without changing production code.

The latest coordinator instruction limits validation to the feature and its coupled regressions.
T004 and T005 record that decision, not passing full-suite results.
T036 through T039 cover applicable changed-file gates with unchanged configuration.
T042 and T043 compare focused regressions with the genuine coupled baseline.
The parent retains analysis reconciliation, review, commit, queue, and delivery work.
All required remote checks remain mandatory during protected delivery.

**Checkpoint**: The local boundary is safe, and baseline counts exist before any test or production edit.

## Phase 2: Foundational Synthetic Fixtures

**Goal**: Build shared synthetic fixtures before story-specific tests.

These two files support all four stories.
Keep their common fixtures here.
Each story phase owns its test tasks.
Stage C builds the complete matrix across those phases.
Stage D proves the defect before Stage E changes production.

- [X] T006 [P] Create synthetic session and database fixtures in `tests/contract/upgrade_portal/test_issue_3484_history_org_isolation.py`. (Real adapters, real query types, actual-clause AQL evaluation, two organizations, two selected sites, and isolated connections passed final contracts.)
- [X] T007 [P] Create synthetic trails and independent event expectations in `tests/unit/upgrade_portal/test_issue_3484_audit_org_isolation.py`. (Temporary JSONL and independent event tables passed bounded, full, inference, and legacy-slice contracts.)

### Shared Fixture Requirements

Use Organization A with Sites A1 and A2.
Use Organization B with Site B1.
Include a session permitted for both organizations and another permitted for A only.
Use distinct stored identifiers, labels, counts, moments, account labels, operator labels, and digests.
Include missing, empty, and mismatched organization attribution.
Give audit addresses separate sentinels from capture and run operator labels.

Use class-owned synthetic fixtures and grouped test classes.
Keep support code inside the two named regression files.
Do not create a support module or edit `conftest.py`.
Keep new methods within the five-parameter, five-block, five-operation, and 25-line limits.

In the contract file, use these behavior groups:

| Group | Story | Required cases |
| --- | --- | --- |
| `TestSelectedOrgHistory` | US1 | Complete cards, exact counts, all selected sites, empty history, foreign changes, and ownership links. |
| `TestHistoryOrgRefusals` | US2 | Refused selections, zero reads, current privileges, accepted environment-token policy, and direct adapters. |
| `TestHistorySiteScope` | US3 | Site intersections, page windows, source availability, picker compatibility, and lock-free reads. |

In the audit file, use `TestAuditReadScope`, `TestAuditInference`, and `TestAuditLegacyLimits`.
These groups supply US4 evidence.
Their reader-scope checks also support the US1 Audit log card.

### Real Query Evidence: T006, T008, and T012

Do not inject `CAPTURE_LISTER` or `RUN_LISTER` for isolation evidence.
Call the real route fallback adapters.
Use real `CaptureQuery`, `RunQuery`, `OperationQuery`, and store readers.
Replace `store.connect_database` with an in-memory synthetic database.
Reset the store connection cache around each case.
Keep all unused readers synthetic.

The synthetic `aql.execute` must evaluate the actual query text and bind values.
Apply only filters present in that text.
Do not insert a missing organization restriction inside the synthetic reader.
Evaluate capture and run counts before their sorted page windows.
Evaluate operation organization and site membership before its limit.
Preserve the run query's aggregate-operation exclusion and device-count projection.

Inspect `org_id` binds in both count and page calls.
Inspect optional `site_id` binds in both calls.
Require organization and site filters before `COLLECT` and `LIMIT`.
Use explicit expected identifiers and totals, not canned query answers.
Do not derive complete expected results from production shapers.

Exercise the two real adapters directly inside selected Flask request contexts.
For refused selections, require zero database and query calls.
Include unavailable readers to prove refusal precedes reader resolution.
Preserve both site-only and site-and-window injected call forms.
Preserve the comparison picker's site-only capture call and default window.

### Complete Response Evidence: T008

Inspect the full rendered HTML and decoded JSON.
Do not inspect only visible table cells.
Check attributes, links, embedded values, totals, operator content, account content, moments, and audit digests.
Check each HTML card independently.
Require the exact selected records and order.

Cover populated A with populated B.
Cover empty A with populated B.
Cover A1 and A2 together without a site restriction.
Cover successive pages and offsets beyond the matching total.
Add, remove, and reorder newer foreign records.
Require unchanged matching rows, totals, and page boundaries.
Exclude unattributed records, even when their site matches.

Use real operation queries.
Require the selected organization and optional site membership.
Keep another session's matching operation visible without its owner-only progress link.
Require absence of owner keys.
Keep the audit default limit independent of the capture page limit.

### Refusal Evidence: T009

Exercise `/history`, `/history?site_id=...`, and both site-history APIs.
Count capture, run, operation, and audit reads separately.
Each refused request must record four zero counts.
Repeat refusal cases with empty and unavailable sources.

| Selection or session | Expected result |
| --- | --- |
| Missing, `None`, empty, whitespace-only, or incorrectly typed selection | `400 org_not_chosen`. |
| Stale, removed, unknown, or excluded selection with known privileges | `403 org_not_permitted`. |
| Explicit selection with known empty privileges | `403 org_not_permitted`. |
| No active sign-in with default or JSON preference | Existing `401 not_authenticated` envelope. |
| No active sign-in with HTML preference | Existing sign-in redirect. |
| Explicit A selection with unavailable environment-token privileges | Existing policy accepts A. Reads remain scoped to A. |

Keep refusal codes, messages, and envelope fields unchanged.
Verify padded valid selections normalize to A.
Verify another request-supplied organization cannot replace signed A.
Change privileges between page requests.
Require refusal before reads on the next request.
Never choose the first permitted organization.

In `TestHistoryOrgRefusals`, check accepted environment-token policy through both site APIs and direct adapters.
Put complete accepted HTML checks in `TestSelectedOrgHistory`.
Include padded valid selections and caller-supplied organization conflicts in those complete checks.
This split lets T017 verify refusals before audit integration.

### Site Evidence: T010

Exercise `/history?site_id=A1` and both A1 history APIs.
Require A1 records only, with exact ordering and totals.
Require A1 membership for operations and A1 scope for audit rows.

Under selected A, request B1 and an unknown site.
Require successful empty intersections and zero capture and run totals.
Exclude foreign stored content and foreign existence details.
Keep the requested site in existing request-scope attributes.
Do not mistake reflected request context for returned stored history.

Verify default limit 25, limit bounds 1 through 200, and nonnumeric defaults.
Verify default offset zero and offset bounds zero through 1,000,000.
Verify clamping, later pages, beyond-end pages, and site-preserving links.
Repeat reads while another operator holds the site lock.
Require no lock lookup or typed confirmation.
If a source is unavailable, preserve its current response without an unrestricted retry.

### Audit Evidence: T007 and T011

Use temporary JSONL trails in stored order.
Interleave both organizations, A1, A2, and reused site text across organizations.
Use explicit expected event order and attribution.
Do not construct the complete expected answer with `audit_row` or `mark_expiries`.

Require the keyword-only organization argument.
Require invalid organizations to fail before opening or reading the trail.
Cover bounded reads and legacy limits `0`, negative values, and `None`.
Require a bounded result to equal the newest matching rows from the full scoped result.
Add enough newer foreign events to exceed a bounded limit.
Require foreign events to consume no result positions.

Cover a take after an unreleased take and a take after an unreleased takeover.
Require exactly one inferred expiry immediately before the later take.
Require the earlier hold's organization, site, and actor digest.
Require the later take's moment.
Include older matching holds outside the visible window.

Cover release and explicit expiry closure.
Cover takeover replacement without an immediate inferred expiry.
Cover legacy missing actions and existing other closing actions.
Require other sites, foreign actions, and unattributed rows to change no matching hold.
Call unchanged `mark_expiries(rows)` with mixed organizations and reused site text.
This direct case must prove independent holder keys.

Cover missing files, blank lines, damaged lines, and non-record JSON values.
Preserve current handling without widening scope.
Require actual and inferred public rows to retain digests without stored audit addresses.
Check the rendered Audit log card for the same address exclusion.

### Red Gate: T013

Run command R1 before editing either production file.
Record collected, passed, failed, and skipped counts.
Require a real-route content or count failure.
Also require an unchanged-API inference or source-read failure.
A proposed keyword-only argument's `TypeError` alone does not prove the defect.
Do not weaken expectations, add signature fallbacks, or suppress failures.

**Checkpoint**: Shared fixtures exist. Complete T008 through T013 across the story sections before any production repair.

## Phase 3: User Story 2 - Refuse an Invalid Organization Selection

**Priority**: P1.

**Goal**: Refuse before any source read and preserve the existing identity policy.

**Independent test**: Run `TestHistoryOrgRefusals` with all four request forms.
Each refusal records zero capture, run, operation, and audit reads.
Accepted environment-token cases use scoped real queries.
The complete accepted-response matrix also runs in T028 and T031.

**Tests before repair**: T009 and T012 supply the direct contracts. T013 records the red result.

- [X] T009 [US2] Add all-form refusal and identity-policy contracts in `tests/contract/upgrade_portal/test_issue_3484_history_org_isolation.py`. (All four forms, invalid selections, known privileges, sign-in, and four zero-read counters passed.)
- [X] T012 [US2] Add direct-adapter and unchanged-picker contracts in `tests/contract/upgrade_portal/test_issue_3484_history_org_isolation.py`. (Real direct adapters refused before module resolution. Site-only and windowed seam calls and picker defaults passed.)
- [X] T013 [US2] Prove behavioral red failures in both `tests/contract/upgrade_portal/test_issue_3484_history_org_isolation.py` and `tests/unit/upgrade_portal/test_issue_3484_audit_org_isolation.py`. (R1 before production repair: exit 1, 260 collected, 252 failed, 8 passed, 0 errors or skips. Real HTML foreign content, JSON total 8 instead of 3, missing-selection status 200 instead of 400, and foreign-moment inference failed. Evidence: session artifacts `issue-3484-red.txt` and `issue-3484-red.xml`.)

**Implementation after the red gate**:

- [X] T014 [US2] Add early selection refusals to all three history handlers in `src/upgrade_portal/app/routes/review.py`. (The existing sign-in guard remains first. Normalized signed selection and existing refusals precede all sources.)
- [X] T015 [P] [US2] Independently authorize and scope both real adapters in `src/upgrade_portal/app/routes/review.py`. (Both queries receive validated org_id, site_id, limit, and offset. Refusals use the authoritative Flask response.)
- [X] T016 [P] [US2] Migrate the missing-selection contract to refusal and zero reads in `tests/contract/upgrade_portal/test_history_operations.py`. (400 org_not_chosen and four zero-read checks passed.)
- [X] T017 [US2] Verify refusal, privilege, and direct-adapter contracts in `tests/contract/upgrade_portal/test_issue_3484_history_org_isolation.py`. (Final R1: 276 passed, 0 failed, 0 skipped. Evidence: session `issue-3484-green.xml`.)

In T014, preserve `identity.require_session` on `capture_history`, `run_history`, and `history_page`.
Use `(select.resolve_org(None) or "").strip()`.
Call `select.org_refusal(chosen)` before resolving or invoking any history reader.
Return the existing refusal directly.
Update touched return annotations if needed.
Do not use `select.read_chosen_org` or request-supplied organization values.
Do not change identity policy.

In T015, keep `store_capture_rows(site_id, limit, offset)` and `store_run_rows(site_id, limit, offset)` unchanged.
Each adapter repeats signed-selection normalization and refusal before source access.
If refused, abort with the existing response through `current_app.make_response(refusal)`.
Do not convert refusal into successful empty history.
Build the existing query with `org_id=chosen`, `site_id`, `limit`, and `offset`.
Keep `call_lister`, `read_store_page`, and seam metadata unchanged.
Do not introduce a signature retry or site-only real-store fallback.

In T016, change `test_no_selected_organization_reads_nothing`.
Require `400 org_not_chosen`, the existing envelope, and no source calls.
Do not render a successful missing-selection card.

**Checkpoint**: Refusals and trusted adapter scope pass independently.
Remaining successful-page integration still requires US4 and US1.
Do not release an intermediate repair.

## Phase 4: User Story 4 - Read Correctly Scoped Audit Events

**Priority**: P1.

**Goal**: Match organization and optional site before inference and result limits.

**Independent test**: Run the three new audit groups against synthetic trails.
Require exact ordered events, bounded/full equivalence, legacy slices, and correct expiry attribution.

**Tests before repair**: T007 supplies shared trails. T011 supplies audit contracts. T013 records the red result.

- [X] T011 [P] [US4] Add scope, inference, digest, and legacy-limit contracts in `tests/unit/upgrade_portal/test_issue_3484_audit_org_isolation.py`. (Both reader paths and unchanged direct inference passed. Added 16 typed-attribution cases after a separate behavioral red check.)

**Implementation after the red gate**:

- [X] T018 [US4] Require keyword-only `org_id` and early scope validation in `src/upgrade_portal/compare/lock_audit.py`. (Invalid organizations log and raise before any trail open or read.)
- [X] T019 [US4] Filter before bounded inference and deque updates in `src/upgrade_portal/compare/lock_audit.py`. (Foreign events affect no matching hold or visible position. Older matching context remains available.)
- [X] T020 [US4] Preserve scoped legacy slices and organization/site holder keys in `src/upgrade_portal/compare/lock_audit.py`. (Zero, negative, and None slices passed. Direct inference also isolates incorrectly typed attribution.)
- [X] T021 [US4] Remove obsolete `_keep_in_scope` and correct touched comments and logs in `src/upgrade_portal/compare/lock_audit.py`. (No alias, new production wrapper, suppression, raw-address log, or schema change.)
- [X] T022 [P] [US4] Pass the validated organization through the audit helper and route call in `src/upgrade_portal/app/routes/review.py`. (Audit receives chosen and optional site, but not the capture page limit.)
- [X] T023 [P] [US4] Supply `org_id=ORG_ID` at all 14 existing reader calls in `tests/contract/upgrade_portal/test_lock_audit_log.py`. (AST verified 14 calls and 14 explicit organization keywords. Existing matching assertions passed.)
- [X] T024 [US4] Verify audit contracts in `tests/unit/upgrade_portal/test_issue_3484_audit_org_isolation.py` and `tests/contract/upgrade_portal/test_lock_audit_log.py`. (All cases passed in the final 754-test scoped regression.)

In T018, use `read_audit_rows(limit=DEFAULT_AUDIT_LIMIT, path=None, site_id="", *, org_id)`.
Preserve the existing positional argument order.
Reject empty, blank, and incorrectly typed organizations before trail access.
Extend the existing `_row_in_scope` to match organization and optional site.
Migrate private call sites directly.
Add no unrestricted default or compatibility overload.

In T019, scan the complete trail in order.
Skip nonmatching rows before any inference state change.
Use `(org_id, site_id)` holder keys.
Append only matching actual and inferred rows to the bounded deque.
Retain older matching context outside the visible result.
Keep bounded memory proportional to matching open holds and the result limit.

In T020, filter the complete input before `mark_expiries`.
Keep `mark_expiries(rows)` callable with its unchanged signature.
Use organization/site tuples in its holder map.
Preserve newest-first output and the final `shaped[:limit]`.
Do not redefine zero, negative, or `None` limits.
Keep `expiry_row`, `audit_row`, and damaged-line behavior unchanged.

In T021, remove `_keep_in_scope` after all callers append already scoped rows.
Add explanatory inline comments throughout touched executable blocks.
Add safe information logs before reads and debug summaries afterward.
Use ASCII and `%s` formatting.
Do not log audit addresses, credentials, owner keys, or complete rows.

In T022, give `audit_history_rows` an explicit organization parameter.
Pass the route's validated `chosen` into its single history call.
Call `read_audit_rows(org_id=chosen, site_id=site_id)`.
Do not pass the capture page limit into this call.
Preserve `moment_text` and existing audit fields.

In T023, preserve successful assertions and limit arguments.
Correct comments that claim inference needs foreign or out-of-site events.
Do not change the expected digest representation.

**Checkpoint**: Both audit paths and the required production caller pass.
Audit reads remain independent of stores and locks.

## Phase 5: User Story 1 - Read the Selected Organization's History

**Priority**: P1.

**Goal**: Render all four cards for one validated organization across its sites.

**Independent test**: Run `TestSelectedOrgHistory` against the real query paths.
Require A1 and A2 content only, exact scoped totals, stable pages, and existing empty states.
Inspect the complete HTML and JSON.

**Tests before repair**: T008 supplies the direct contracts. T013 records the red result.
T015 supplies shared real-query scope.
T018 through T022 supply shared audit scope.

- [X] T008 [US1] Add complete-response organization and real-query contracts in `tests/contract/upgrade_portal/test_issue_3484_history_org_isolation.py`. (Full HTML and JSON, four cards, exact totals, two selected sites, page membership, foreign mutations, and owner-only links passed.)

**Implementation after US2 and US4**:

- [X] T025 [US1] Pass validated `chosen` into operation history and run-control context in `src/upgrade_portal/app/routes/review.py`. (Both use the same normalized validated organization. Owner keys remain server-only.)
- [X] T026 [P] [US1] Add explicit selection and synthetic unused operation reads in `tests/contract/upgrade_portal/test_history_routes.py`. (All existing formatting and window assertions passed with no real operation read.)
- [X] T027 [P] [US1] Add selected request contexts and `FakeQuery.org_id` assertions in `tests/unit/upgrade_portal/test_review_store_seams.py`. (Known permitted local scope and all four exact query fields passed.)
- [X] T028 [US1] Verify all cards, totals, pages, and accepted policy cases in `tests/contract/upgrade_portal/test_issue_3484_history_org_isolation.py`. (Final R1 passed, including padded selection, query conflicts, and unavailable environment-token privileges.)

In T025, give `operation_history_section` the validated organization explicitly.
Update its single history call directly.
Do not read the saved selection again inside that helper.
Use the same `chosen` for `run_control_org_id`.
Keep the operation lister and `OrgOperationHistory` unchanged.
Preserve owner-only progress links and server-only owner keys.

In T026, give `signed_in_client` an explicit authorized selection.
Keep all injected lister signatures and page expectations unchanged.
Replace unused operation reads with an in-memory stand-in.
Do not activate a real operation store through the new selection.

In T027, use local Flask request contexts with explicit authorized selection.
Add `org_id` to the existing three-field `FakeQuery`.
Assert the selected organization in both successful adapter queries.
Keep site, limit, offset, and unavailable-reader expectations.

In T028, rerun the same complete-response cases used for red evidence.
Include accepted unavailable-privilege sessions and padded valid selections.
Require exact capture/run counts before page windows.
Require scoped operation and audit content.
Verify the validated run-control organization.
Do not change templates, JavaScript, firmware controls, or unrelated text.

**Checkpoint**: The smallest secure no-site history increment passes.
US2 and US4 are prerequisites, not optional MVP omissions.

## Phase 6: User Story 3 - Preserve History for One Authorized Site

**Priority**: P1.

**Goal**: Keep the site restriction inside the selected organization.

**Independent test**: Run `TestHistorySiteScope` for A1, B1, and an unknown site.
Require exact A1 rows and totals.
Require successful empty intersections for B1 and the unknown site.
Verify page bounds, retained site links, and lock-free access.

**Tests before repair**: T010 and T012 supply the site contracts. T013 records the red result.
The earlier query and audit repairs must already preserve the optional site.
Add no site-discovery call or duplicate scope layer.

- [X] T010 [US3] Add site, window, availability, and lock-free contracts in `tests/contract/upgrade_portal/test_issue_3484_history_org_isolation.py`. (Selected, foreign, and unknown sites, all window bounds, source outages, and another holder's lock passed.)

**Migration and verification after shared repair**:

- [X] T029 [P] [US3] Add explicit selection and isolated operation reads in `tests/contract/upgrade_portal/test_history_device_type.py`. (All six existing device-type cases passed unchanged.)
- [X] T030 [P] [US3] Add `ORG_ID` selection and isolated operation reads in `tests/contract/upgrade_portal/test_upgrade_routes/test_stale_views.py`. (All three stale, terminal, and malformed-time cases passed unchanged.)
- [X] T031 [US3] Verify site intersections, windows, picker compatibility, and availability in `tests/contract/upgrade_portal/test_issue_3484_history_org_isolation.py`. (Full final R1: 276 passed. Every request uses current authorization.)
- [X] T032 [US3] Run preserved history, scope, lock-free, and control regressions starting with `tests/contract/upgrade_portal/test_lock_free_reads.py`. (B1 repeat: 226 passed. P1: 200 passed. Supplied eight-file repeat: 118 passed. Final scoped regression: 754 passed, 0 skips, audit guard 0 to 0.)

In T029, update only `signed_in_client` and its unused operation stand-in.
Keep device-type cells and assertions unchanged.

In T030, update only `stale_client` and its unused operation stand-in.
Keep stale, terminal, and malformed-time assertions unchanged.

In T031, run the site group and then both complete new regression files.
Require current authorization on every later page request.
Do not remove legitimate request-site attributes.
Do not require a lock or a confirmation word.

In T032, run B1 again and run command P1.
Keep `test_lock_free_reads.py`, the #3482 tests, and the #3486 tests unchanged.
Keep firmware and bulk-control regressions unchanged.

**Checkpoint**: All four story matrices pass with the six necessary fixture migrations only.

## Phase 7: Polish and Cross-Cutting Concerns

**Goal**: Complete local evidence without entering queued delivery.

- [X] T033 [P] Write the Security release note in `changelog.d/issue-3484-history-org-isolation.md`. (One Security fragment ends with Issue #3484. No version or CHANGELOG.md edit.)
- [X] T034 Review structural limits, comments, safe logging, and suppressions in `src/upgrade_portal/app/routes/review.py` and `src/upgrade_portal/compare/lock_audit.py`. (Direct source review passed. No new production child or wrapper. AST checked 66 new methods and 16 classes within limits, with no executable-statement comment gap. New suppressions: 0.)
- [X] T035 Compile every changed Python file and `MistHelper.py` with command Q1. (Exit 0, 11 files compiled. Cache output stayed in the session artifact directory.)
- [X] T036 [P] Run Ruff on all changed Python files and `MistHelper.py` using unchanged `pyproject.toml` with command Q2. (Parent verification: all 11 files pass. No configuration change.)
- [X] T037 [P] Run Black on all changed Python files and `MistHelper.py` using unchanged `pyproject.toml` with command Q3. (Parent verification: all 11 files remain unchanged.)
- [X] T038 [P] Run strict mypy on both changed source files with command Q4. Preserve the full CI `MYPY_PATHS` scope. (Parent verification: no issues in 2 source files. The full CI scope remains unchanged.)
- [X] T039 [P] Run local Bandit on both changed source files and check repository exclusions with command Q5. (Parent verification: 0 findings across 1,797 lines. No skipped files or new suppressions. Exclusion separator check passes.)
- [X] T040 Require at least 80% scoped coverage for each changed production module, including `src/upgrade_portal/app/routes/review.py`. (Final parent verification: review.py covers 635/665 statements, 95.49%. lock_audit.py covers 95/95, 100%. Combined coverage is 96.05%. All 787 focused cases pass. Both full-module percentages exceed 80% without configuration or exclusion changes.)
- [X] T041 [P] Run the test-quality ratchet against unchanged `.github/test-quality-config.toml` and `.github/test-quality-baseline.json` with command Q7. (Final parent verification checks all 8 changed test files. Exit 0, 0 findings, 0 new findings, 0 parse errors. Two broader-root notices do not exclude a changed test. No suppression or baseline change.)
- [X] T042 [P] Verify focused unit, audit, store, and history regressions in the combined scoped run. (All 787 cases pass with 0 failures, errors, skips, or deselections. The audit guard checks one checkout trail, 0 lines before and after.)
- [X] T043 [P] Verify focused route, authorization, comparison, firmware, and bulk-control regressions against the genuine coupled baseline. (The original 118-case baseline and its repeat both pass. The final focused run adds 309 isolation cases and retains 478 coupled cases. No whole-repository baseline result is claimed.)
- [X] T044 Run mandatory read-only `/speckit.analyze` against `specs/3484-history-org-isolation/spec.md`, `specs/3484-history-org-isolation/plan.md`, and `specs/3484-history-org-isolation/tasks.md` after local repair. (Analysis checks 24 requirements and 45 tasks. Parent review resolves the explicit task-boundary conflicts, reconciles validation dependencies, and updates the queue. The existing contract file now covers excluded selections with populated, empty, and unavailable sources. It also covers no-site valid-to-revoked authorization. All affected gates pass. No code or requirement inconsistency remains.)
- [X] T045 Verify the approved file boundary and prepare local completion evidence from `specs/3484-history-org-isolation/tasks.md` for the parent. (Direct parent review verifies all owned files, all 45 reconciled tasks, exact local results, and unchanged protected files. Local delivery evidence is ready. Commit and queued remote delivery remain separate authorized steps.)

### Bounded Local Result

The implementation agent completed 35 of the 45 original tasks.
The parent reconciled validation scope and dependencies with the latest coordinator instruction.
T004 and T005 now document unexecuted broad baselines.
No broad result is claimed as passed.
All 45 reconciled local tasks are complete.
The final focused run passes 787 cases, including 309 new isolation cases.
The new cases comprise 233 route contracts and 76 audit contracts.
The original red evidence records 252 failed and eight passed cases on the defective source.
Additional typed-attribution red evidence records 16 failed and eight passed cases before its repair.
The parent added 33 focused matrix cases after analysis.
The code uses only the 12 approved implementation paths.
Full exact commands and results are saved in the session artifact directory:
`/Users/jmorrison/.copilot/session-state/5f8a6a1d-655b-4b00-adfc-421c15726914/files/`.
Read `issue-3484-red.txt`, `issue-3484-typed-attribution-red.txt`, `issue-3484-green.txt`, and `issue-3484-local-validation.txt`.
The parent owns analysis, review, commit, queue, delivery, merge, and the exact merged-tree test.
The parent completed analysis and local review.
The implementation agent created no commit, push, PR, workflow, container, server, browser, or delegated agent.
The parent will commit after the final boundary and documentation checks.
The mandatory companion post-hook was dispatched with the explicit feature directory.
It returned exit 127 because `speckit.companion.after-implement` is unavailable.
The hook did not complete or write `.spec-context.json`.
PowerShell is also unavailable, as recorded in T002.
The explicit feature artifacts preserve the required specification, plan, tasks, implementation, and analysis evidence.
Do not install missing hook tools or perform prohibited shared-context writes.
Full hook automation completion is not claimed.
These workflow limits do not change the passing local implementation evidence.

In T033, use the format in `changelog.d/README.md`.
Write one change heading and a `**Security**` bullet ending with Issue #3484.
Use STE and do not add a version.
Do not edit `CHANGELOG.md`.

In T034, retain only the existing structural exceptions recorded in `plan.md`.
Add no production child, wrapper, class, or module.
Check explanatory inline comments and before/after action logs throughout each touched block.
Fix findings only inside the approved files.
Rerun affected contracts after any correction.

In T040, run Q6.
Check each module's coverage independently.
A combined percentage alone does not satisfy this task.
Add relevant tests only in the two named new regression files if needed.
Do not lower the scoped floor, add exclusions, or update a baseline.

In T041, include feature-owned untracked tests.
Do not use a committed-diff filter that omits them.
Do not use `--write-baseline`, `--prune-baseline`, rule overrides, or replacement configuration.

In T042 and T043, compare coupled cases with the recorded T003 baseline.
Account for the added regression cases.
Record every failure, deselection, skip reason, and final runner summary.
Do not call an unexecuted or unexpectedly skipped test passed.

In T044, use the explicit feature directory.
Use the explicitly requested `speckit.analyze` workflow without optional commit hooks or shared-context writes.
Require no unresolved critical or high-severity inconsistency.
If a correction changes code or tests, rerun every affected local gate.
If a correction needs another file, report the blocker rather than widening scope.

In T045, report exact changed files, red/green counts, gate results, and both module coverage values.
Confirm instruction files, feature context, quality configuration, and quality baseline remain unchanged.
Confirm no API call, production read, credential use, container, branch switch, push, or PR occurred before the queue release.
Complete the local implementation checklist without marking queued delivery done.

**Checkpoint**: Local implementation and analysis are complete. The parent owns the next delivery decision.

## Local Command Reference

Run commands from this worktree root.
Use RTK for every executable command.
Keep output reports in the temporary validation directory.
These commands are instructions for later implementation, not task-generation actions.

Each shell tool call starts a fresh process.
Repeat the environment exports in each call.
Reuse the recorded absolute `VALIDATION_DIR` instead of creating another directory.
Do not assume an earlier call's exports persist.

### Environment: T002

Use a credential-free shell.
Do not print environment values or load `.env`.

```bash
export PATH="$PWD/.venv/bin:$PATH"
export SPECIFY_FEATURE_DIRECTORY=specs/3484-history-org-isolation
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$PWD"
export MISTHELPER_STANDALONE=true
export VALIDATION_DIR="$(rtk proxy .venv/bin/python -B -c 'import tempfile; print(tempfile.mkdtemp(prefix="issue-3484-validation-"))')"
export COVERAGE_FILE="$VALIDATION_DIR/.coverage"
export PYTHONPYCACHEPREFIX="$VALIDATION_DIR/pycache"
export RUFF_CACHE_DIR="$VALIDATION_DIR/ruff-cache"
export BLACK_CACHE_DIR="$VALIDATION_DIR/black-cache"
export MYPY_CACHE_DIR="$VALIDATION_DIR/mypy-cache"
export PYTEST_ADDOPTS="-p no:cacheprovider -m 'not integration'"
rtk proxy .venv/bin/python --version
rtk proxy .venv/bin/python -c 'import os; print("Validation directory:", os.environ["VALIDATION_DIR"])'
GIT_OPTIONAL_LOCKS=0 rtk git status --short --branch
```

The existing `integration` marker identifies live Mist API tests.
Record those deselections explicitly.
All feature cases must remain collected and synthetic.
The marker does not replace synthetic fixture isolation.
Use unique pytest temporary directories for concurrent processes.

### B1: Coupled Baseline and Regression

```bash
rtk proxy .venv/bin/python -m pytest --timeout=120 \
  tests/contract/upgrade_portal/test_history_routes.py \
  tests/contract/upgrade_portal/test_history_device_type.py \
  tests/contract/upgrade_portal/test_history_operations.py \
  tests/contract/upgrade_portal/test_lock_audit_log.py \
  tests/contract/upgrade_portal/test_lock_free_reads.py \
  tests/contract/upgrade_portal/test_upgrade_routes/test_stale_views.py \
  tests/unit/upgrade_portal/test_review_store_seams.py \
  tests/unit/upgrade_portal/test_store.py \
  tests/unit/upgrade_portal/test_store_history.py \
  tests/unit/upgrade_portal/test_org_history.py
```

### B2 and B3: Historical Broad Baselines

The original full unit and contract/guardrail/integration baseline commands did not run.
The latest coordinator instruction excludes them from local acceptance prerequisites.
T004 and T005 record that scope decision only.
Use B1, R1, P1, and the combined focused coverage run for T042 and T043.
Do not describe a later run as a pre-repair baseline.

### R1: Red and Green Regression Files

```bash
rtk proxy .venv/bin/python -m pytest --timeout=120 \
  tests/contract/upgrade_portal/test_issue_3484_history_org_isolation.py \
  tests/unit/upgrade_portal/test_issue_3484_audit_org_isolation.py
```

Use the same command before and after production repair.
For a story-only check, select its named class from the shared fixture requirements.
Run the full files again in T031.

### P1: Preserved Presentation and Controls

```bash
rtk proxy .venv/bin/python -m pytest --timeout=120 \
  tests/unit/upgrade_portal/test_issue_3482_history_scope.py \
  tests/unit/upgrade_portal/test_issue_3486_history_site_column.py \
  tests/contract/upgrade_portal/test_upgrade_options.py \
  tests/contract/upgrade_portal/test_org_advanced_options.py \
  tests/contract/upgrade_portal/test_upgrade_start.py \
  tests/contract/upgrade_portal/test_upgrade_routes/test_bulk_preview.py \
  tests/contract/upgrade_portal/test_upgrade_routes/test_bulk_actions.py
```

### Q1: Compile

```bash
rtk proxy .venv/bin/python -m py_compile \
  MistHelper.py \
  src/upgrade_portal/app/routes/review.py \
  src/upgrade_portal/compare/lock_audit.py \
  tests/contract/upgrade_portal/test_issue_3484_history_org_isolation.py \
  tests/unit/upgrade_portal/test_issue_3484_audit_org_isolation.py \
  tests/contract/upgrade_portal/test_history_routes.py \
  tests/contract/upgrade_portal/test_history_device_type.py \
  tests/contract/upgrade_portal/test_upgrade_routes/test_stale_views.py \
  tests/contract/upgrade_portal/test_history_operations.py \
  tests/unit/upgrade_portal/test_review_store_seams.py \
  tests/contract/upgrade_portal/test_lock_audit_log.py
```

`PYTHONPYCACHEPREFIX` keeps explicit compile output outside the repository.

### Q2 and Q3: Lint and Format

```bash
rtk proxy .venv/bin/python -m ruff check MistHelper.py \
  src/upgrade_portal/app/routes/review.py src/upgrade_portal/compare/lock_audit.py \
  tests/contract/upgrade_portal/test_issue_3484_history_org_isolation.py \
  tests/unit/upgrade_portal/test_issue_3484_audit_org_isolation.py \
  tests/contract/upgrade_portal/test_history_routes.py \
  tests/contract/upgrade_portal/test_history_device_type.py \
  tests/contract/upgrade_portal/test_history_operations.py \
  tests/contract/upgrade_portal/test_lock_audit_log.py \
  tests/contract/upgrade_portal/test_upgrade_routes/test_stale_views.py \
  tests/unit/upgrade_portal/test_review_store_seams.py
rtk proxy .venv/bin/python -m black --check --diff MistHelper.py \
  src/upgrade_portal/app/routes/review.py src/upgrade_portal/compare/lock_audit.py \
  tests/contract/upgrade_portal/test_issue_3484_history_org_isolation.py \
  tests/unit/upgrade_portal/test_issue_3484_audit_org_isolation.py \
  tests/contract/upgrade_portal/test_history_routes.py \
  tests/contract/upgrade_portal/test_history_device_type.py \
  tests/contract/upgrade_portal/test_history_operations.py \
  tests/contract/upgrade_portal/test_lock_audit_log.py \
  tests/contract/upgrade_portal/test_upgrade_routes/test_stale_views.py \
  tests/unit/upgrade_portal/test_review_store_seams.py
```

### Q4: Strict Types

The full CI scope remains authoritative and unchanged.
Local strict typing covers both changed source files.

```bash
rtk proxy .venv/bin/python -m mypy src/upgrade_portal/app/routes/review.py \
  src/upgrade_portal/compare/lock_audit.py --config-file pyproject.toml
```

### Q5: Local Security

```bash
rtk proxy .venv/bin/bandit-exclude-check
rtk proxy .venv/bin/python -m bandit -c pyproject.toml \
  src/upgrade_portal/app/routes/review.py src/upgrade_portal/compare/lock_audit.py
```

Do not add online dependency audits or cloud security checks to this local-only workflow.
Keep existing exclusions unchanged.
Fix real findings rather than suppressing them.

### Q6: Scoped Coverage

```bash
rtk proxy .venv/bin/python -m pytest --timeout=120 \
  tests/contract/upgrade_portal/test_issue_3484_history_org_isolation.py \
  tests/unit/upgrade_portal/test_issue_3484_audit_org_isolation.py \
  tests/contract/upgrade_portal/test_history_routes.py \
  tests/contract/upgrade_portal/test_history_device_type.py \
  tests/contract/upgrade_portal/test_history_operations.py \
  tests/contract/upgrade_portal/test_lock_audit_log.py \
  tests/contract/upgrade_portal/test_lock_free_reads.py \
  tests/contract/upgrade_portal/test_upgrade_routes/test_stale_views.py \
  tests/unit/upgrade_portal/test_review_store_seams.py \
  tests/unit/upgrade_portal/test_store.py \
  tests/unit/upgrade_portal/test_store_history.py \
  tests/unit/upgrade_portal/test_org_history.py \
  tests/contract/upgrade_portal/test_comparison.py \
  tests/contract/upgrade_portal/test_comparison_errors.py \
  tests/contract/upgrade_portal/test_comparison_export.py \
  tests/contract/upgrade_portal/test_compare_picker_moment.py \
  --cov=src.upgrade_portal.app.routes.review \
  --cov=src.upgrade_portal.compare.lock_audit \
  --cov-report=term-missing --cov-fail-under=80
rtk proxy .venv/bin/python -m coverage json \
  --fail-under=80 -o "$VALIDATION_DIR/coverage.json"
rtk proxy .venv/bin/python -c 'import json, os; from pathlib import Path; report=json.loads((Path(os.environ["VALIDATION_DIR"])/"coverage.json").read_text()); paths=("src/upgrade_portal/app/routes/review.py", "src/upgrade_portal/compare/lock_audit.py"); scores={path: report["files"][path]["summary"]["percent_covered"] for path in paths}; print("Checked", len(scores), "modules:", scores); assert all(score >= 80 for score in scores.values()), "Each changed module must reach 80%"'
```

The command-line floor applies to this approved two-module scope.
Do not change the repository coverage configuration or claim a broader coverage result.

### Q7: Unchanged Test-Quality Ratchet

```bash
rtk proxy .venv/bin/test-quality-analyzer --gate \
  --config .github/test-quality-config.toml \
  --baseline .github/test-quality-baseline.json \
  --roots tests/contract/upgrade_portal/test_issue_3484_history_org_isolation.py \
  tests/unit/upgrade_portal/test_issue_3484_audit_org_isolation.py \
  tests/contract/upgrade_portal/test_history_routes.py \
  tests/contract/upgrade_portal/test_history_device_type.py \
  tests/contract/upgrade_portal/test_upgrade_routes/test_stale_views.py \
  tests/contract/upgrade_portal/test_history_operations.py \
  tests/unit/upgrade_portal/test_review_store_seams.py \
  tests/contract/upgrade_portal/test_lock_audit_log.py \
  --report "$VALIDATION_DIR/test-quality-report.json" \
  --summary "$VALIDATION_DIR/test-quality-summary.md"
```

Require no new finding against the unchanged baseline.
Include the two new files even while they are untracked.

## Dependencies and Execution Order

### Completion Graph

```text
Setup T001-T003 and scope decisions T004-T005
       |
Shared fixtures T006-T007
       |
Story-specific red contracts T008-T012
       |
Behavioral red gate T013
       |
       +--> US2 refusals/adapters T014-T017 --+
       |                                   |
       +--> US4 audit scope T018-T024 ------+
                                           |
                              US1 all cards T025-T028
                                           |
                              US3 site checks T029-T032
                                           |
                              Local gates/analyze T033-T045
                                           |
                              STOP: parent delivery hold
```

The two repair streams share `review.py`.
Serialize every edit to that file.
Audit-only work can start after T013.
Its route integration also requires T014.

### Explicit Task Prerequisites

| Task or tasks | Required completed tasks |
| --- | --- |
| T001 | None. |
| T002 | T001. |
| T003 | T002. |
| T004, T005 | T003. |
| T006, T007 | T003. |
| T008 | T006. |
| T009 | T008. |
| T010 | T009. |
| T011 | T007. |
| T012 | T010. |
| T013 | T011 and T012. |
| T014 | T013. |
| T015, T016 | T014. |
| T017 | T015 and T016. |
| T018 | T013. |
| T019 | T018. |
| T020 | T019. |
| T021 | T020. |
| T022 | T014 and T021. |
| T023 | T021. |
| T024 | T022 and T023. |
| T025 | T017 and T024. |
| T026 | T025. |
| T027 | T015. |
| T028 | T025, T026, and T027. |
| T029, T030 | T014. |
| T031 | T028, T029, and T030. |
| T032 | T017, T024, T028, and T031. |
| T033, T034 | T032. |
| T035 through T043 | T034. |
| T044 | T033 and T035 through T043. |
| T045 | T044. |

T008, T009, T010, and T012 serialize edits to the shared contract file.
T018 through T021 serialize edits to the audit module.
No production task may start before T013.
Use numeric task order across story sections, not a complete-story-first sequence.
Do not declare overall completion before T045.

## Parallel Execution Examples

Parallel work is optional.
It does not authorize delegation or concurrent edits to one file.
Use separate temporary outputs for concurrent checks.

### User Story 2

After T014, T015 and T016 touch different files.
T015 changes the real adapters in `review.py`.
T016 changes the missing-selection operation contract.
Run T017 after both complete.

### User Story 4

After T021 and T014, T022 and T023 touch different files.
T022 updates the production audit caller.
T023 migrates the 14 legacy test calls.
Do not overlap T022 with another `review.py` edit.

### User Story 1

After T025, T026 and T027 touch different test files.
T026 updates the history fixture.
T027 updates direct adapter query assertions.
Run T028 after both complete.

### User Story 3

After T014, T029 and T030 touch different fixture files.
Keep their successful assertions unchanged.
Run T031 after both migrations and T028 complete.

### Shared Work

T004 and T005 record scope decisions without another pytest process.
T006 and T007 create different regression files.
T011 can proceed beside contract-file work after T007.
After T034, read-only lint, format, type, security, ratchet, and bounded regression checks can run independently.
Run only one scoped coverage writer.

## Requirement Traceability

| Requirements | Evidence and repair |
| --- | --- |
| FR-001 through FR-004, SC-002 | T009, T012, T014 through T017, and accepted-session checks in T028. |
| FR-005 through FR-007, FR-010, FR-011, SC-001, SC-003 | T006, T008, T012, T015, and T025 through T028. |
| FR-008, FR-009, SC-004 | T010, T029 through T032. |
| FR-012 through FR-015, SC-005 | T007, T011, T018 through T024, and complete audit rendering in T028. |
| FR-016 | T008, T016, T025, and T028. |
| FR-017 | T009, T010, T012, T015, and T031. |
| FR-018, FR-019 | T010, T026 through T032, B1, and P1. |
| Constitution comments, logging, structure, and quality | T021, T034 through T044, and the existing exceptions recorded in `plan.md`. |

## Implementation Strategy

### Secure MVP

The MVP is US1 with its US2 and US4 prerequisites.
It includes all four cards, exact scoped totals, early refusal, and scoped audit reads.
Do not omit refusal or audit protection to deliver US1 sooner.
All four stories remain P1 requirements for final local handoff.

### Incremental Local Work

1. Record safe baselines and build the complete synthetic regression matrix.
2. Prove the defect before any production repair.
3. Repair refusals and adapters, then audit scope, then validated page composition.
4. Complete the six fixture migrations and rerun site and preserved-behavior contracts.
5. Complete local quality gates and mandatory analysis, then report to the parent.

Use the smallest direct change inside the approved files.
Reuse existing authorities, query fields, row shapers, and operation ownership rules.
Do not add a second scope service or compatibility layer.
Keep every validation result tied to a concrete command and checked count.

## Delivery Hold: Outside Implementation Tasks

Implementation can finish after T045.
It does not depend on a queue release, remote operation, or merged-tree check.
There are no delivery checkboxes in this document.

The parent owns the authorized local commit after validation.
The parent must include the required Copilot trailer.
This task-generation workflow does not commit.

The original queue position 7 is historical.
The latest coordinator order places #3305 after #3398 and before #3484.
Unfinished parent issue #3399 follows #3484.
Coordinator session `6d71fd26-57c2-48c0-abc8-607af98f75d0` must supply the queue release and stable main SHA.
Until then, do not push or open a PR.
Do not invent a main SHA or move branches.

Later rebase validation, PR checks, protected squash, and merged-tree checks remain parent/coordinator delivery work.
Keep those actions outside implementation completion.
Report local readiness without claiming queued delivery complete.
