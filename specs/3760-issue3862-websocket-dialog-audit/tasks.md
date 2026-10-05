# Tasks: Issue 3862 WebSocket Dialog Audit

**Input**: Design documents in `specs/3760-issue3862-websocket-dialog-audit/`

**Prerequisites**: `plan.md`, `spec.md`, `design/research.md`, `design/data-model.md`, `design/contracts/audit-contract.md`, and `design/quickstart.md`.

**Scope and safety**: Build the independent harness under `tests/e2e/websockets_tab/dialog_audit/` and update relevant specification documents. Keep production files and the branch unchanged. The parent installed the environment and started the user-authorized normal portal on loopback8055. This session does not change containers or read credentials. Default inspection permits reviewed GET reads only. The separate user-authorized `live-readonly` mode permits one exact `site.stats.devices` observation lifecycle and only its own returned session's reads/local stop. Other starts, streams, utilities, captures, shell, and remote mutations remain prohibited. Preserve initial unavailability as historical evidence. The parent handles authorized GitHub updates/publication after checks and ownership clearance. This session does not commit or push.

**Organization**: Tasks are grouped by the four user stories in `spec.md`. Live capability blockers do not prevent isolated harness work and must remain separate from passed results.

## Phase 1: Setup

**Purpose**: Create the independent harness boundary without installing dependencies, starting services, or changing repository-wide test configuration.

- [X] T001 Create the audit support package initializer in `tests/e2e/websockets_tab/dialog_audit/support/__init__.py`; keep the audit directory to the planned five direct entries and do not add files outside it.
- [X] T002 Add audit-only pytest options, default-isolated mode, explicit live opt-in, URL/artifact-path validation, and a fixture that never starts or restarts a portal in `tests/e2e/websockets_tab/dialog_audit/conftest.py`.

## Phase 2: Foundational

**Purpose**: Establish a shared fail-closed browser and egress policy before any story-specific journey.

- [X] T003 Implement default-deny browser request handling and the isolated server-egress boundary in `tests/e2e/websockets_tab/dialog_audit/support/policy.py`; block service workers, unknown endpoints/origins, redirects, unsolicited WebSockets, operation starts, utility/shell/capture/mutation paths, and unowned session controls before transmission.

**Checkpoint**: Audit tests can use the real portal assets in isolated mode, while live execution remains opt-in and denied unless a later per-operation decision permits it.

## Phase 3: User Story 1 - Understand an Operation and Select Its Target (Priority: P1) 🎯 MVP

**Goal**: Inspect real operation catalog entries and forms as a normal user, compare their purpose and selectors to an independent behavior oracle, and prove that inspection or cancellation cannot start an operation.

**Independent Test**: Run the isolated inventory and dialog tests against the actual catalog, template, and browser assets. Reconcile every visible operation, verify purpose/fields/dependencies/empty states/cancellation, and assert that unknown or unsafe actions produce zero transmissions. Do not claim live coverage.

### Tests for User Story 1

- [X] T004 [P] [US1] Add isolated real-catalog reconciliation tests, including missing, duplicate, extra, locked, and unverified keys, in `tests/e2e/websockets_tab/dialog_audit/test_inventory.py`.
- [ ] T005 [P] [US1] Add real-asset Playwright dialog tests for purpose, scope, labels, required selectors, dependent choices, empty/failure states, stale responses, abandonment, and cancellation without operation submission in `tests/e2e/websockets_tab/dialog_audit/test_dialogs.py`.

### Implementation for User Story 1

- [ ] T006 [US1] Implement `InventoryBuilder` and `OperationOracle` using the selected revision's real catalog, source definitions, SDK signatures, and runner paths in `tests/e2e/websockets_tab/dialog_audit/support/inventory.py`; never use display names or safety badges as proof of behavior.
- [X] T007 [US1] Implement `DialogInspector` against the real rendered page and controls in `tests/e2e/websockets_tab/dialog_audit/support/journeys.py`; report the absence of a supported operation-cancel path rather than treating terminal-paste cancellation or navigation as a pass.
- [X] T008 [US1] Run and refine the isolated Story 1 suite in `tests/e2e/websockets_tab/dialog_audit/test_inventory.py` and `tests/e2e/websockets_tab/dialog_audit/test_dialogs.py`; retain every operation in the denominator and report blockers or exclusions explicitly.

## Phase 4: User Story 2 - Observe and Stop a Verified Read-Only Stream (Priority: P1)

**Goal**: Permit only a specifically verified, read-only subscription through an authenticated, available portal; otherwise produce a precise blocked outcome without transmitting a start request.

**Independent Test**: Run GET-only inspection across returned sites/maps. Then select the distinct `live-readonly` exact-key lifecycle test after the parent verifies container/base revision. Choose a populated site through the actual UI, start only `site.stats.devices`, observe bounded state/data/no-data, stop only the returned own session, and verify stopped. Isolated traps reject arbitrary starts and foreign session controls before transmission. No live result follows from isolated evidence.

### Tests for User Story 2

- [ ] T009 [US2] Add opt-in live-gate and synthetic negative tests for unreachable portal, missing authentication, unverified operations, forbidden requests, bounded timeouts, and zero forbidden transmissions in `tests/e2e/websockets_tab/dialog_audit/test_live.py`; keep live cases out of ordinary collection.

### Implementation for User Story 2

- [X] T010 [US2] Implement the bounded exact-key policy in `support/policy.py`: verified channel/SDK path, populated returned site, exact JSON body, one start attempt, response-issued ownership, bounded own message reads and one local stop. No generalized permission/expiry framework or whole-server guard is required by the authorized scope.
- [X] T011 [US2] Implement the normal-user serial `TestReadonlyLive` journey in `test_live.py`: actual site UI, exact `site.stats.devices`, 15-second selection/connection, five-second observation and stop verification, 120-second test bound, only own-session cleanup.
- [X] T012 [US2] Run and verify the distinct exact-key live lifecycle after the parent's deployed/base revision check. Corrected run verifies subscribed/live, bounded no-data observation, one own stop and stopped. Historical localhost unavailability stays historical.

## Phase 5: User Story 3 - Record Coverage and Distinct Defects (Priority: P2)

**Goal**: Produce restricted, sanitized audit records that distinguish evidence modes and terminal statuses, and track only confirmed distinct defects under issue #3862.

**Independent Test**: Validate a report with passed, failed, blocked, skipped, no-data, and isolated results. Confirm that every inventory item has a result or blocker, the known portal outage is BLOCKED, raw evidence stays local, and no blocked/skipped result contributes to pass totals. For confirmed defects, verify a distinct linked issue per defect; an environment blocker must not create an issue.

### Tests for User Story 3

- [ ] T013 [US3] Add report-schema, status-total, redaction, restricted-artifact, incomplete-inventory, and cause-based defect-deduplication tests in `tests/e2e/websockets_tab/dialog_audit/test_inventory.py`.

### Implementation for User Story 3

- [ ] T014 [US3] Implement `AuditReportWriter` and `DefectRegistry` for restricted JSON and sanitized Markdown, including exact sanitized command, duration, evidence mode, revision, status, stage outcome, and blocker fields in `tests/e2e/websockets_tab/dialog_audit/support/reporting.py`.
- [ ] T015 [US3] Emit separate inventory, isolated-inspection, live-inspection, and live-subscription totals in `tests/e2e/websockets_tab/dialog_audit/support/reporting.py`; preserve the known portal-unreachable preflight as BLOCKED in `test-artifacts/websocket-dialog-audit/report.json` and `test-artifacts/websocket-dialog-audit/report.md`, and never overwrite it with a pass or treat isolated evidence as live evidence.
- [ ] T016 [US3] For each confirmed distinct defect, reuse a matching issue or create exactly one repair issue linked to parent issue #3862, with sanitized reproduction and acceptance criteria; record the issue link in `tests/e2e/websockets_tab/dialog_audit/support/reporting.py`, and do not create issues for blockers or unverified suspicions.

## Phase 6: User Story 4 - Repair a Confirmed Defect Without Changing Operation Meaning (Priority: P3)

**Goal**: Hand each proven defect into its own authorized, ownership-cleared repair workflow; validate and track any repair through GitHub without broadening this audit into portal production changes.

**Independent Test**: For each confirmed defect, verify the unique linked issue and separate repair specification (when code repair is needed), a failing-before/passing-after isolated regression, unique release note, exact gate results, and an authorized GitHub PR. Do not commit, push, or merge before the required explicit authorization, ownership clearance, review, and passing current checks.

### Implementation for User Story 4

- [ ] T017 [US4] For each confirmed defect requiring a repair, create a separate SpecKit repair specification at `specs/<repair-issue>-<short-slug>/spec.md`, linked to its unique issue under #3862; do not invent a repair for an unconfirmed defect or treat an environment blocker as a defect.
- [ ] T018 [US4] Before a repair touches an owned file, record ownership coordination for `src/mist/realtime/websocket_streams/web/static/websockets.js` and `tests/e2e/websockets_tab/test_websockets_page.py`; do not modify either while PR #3814 owns them.
- [ ] T019 [US4] Implement only the approved repair-spec scope in its own repair worktree and add its isolated before/after regression in `tests/<approved-repair-test-path>.py` as identified by `specs/<repair-issue>-<short-slug>/plan.md`; preserve operation meaning and prohibit utility, shell, capture, mutation, production-start, and production-restart behavior.
- [ ] T020 [US4] Add one unique user-visible release-note fragment per repair at `changelog.d/<repair-issue>-<short-slug>.md`, linked to the corresponding issue and repair specification.
- [ ] T021 [US4] Run each repair's isolated regression plus applicable repository syntax, lint, format, type, complexity, security, SDK, browser, and test-quality gates; record exact commands, outcomes, durations, and current revision in the associated GitHub repair PR using `.github/PULL_REQUEST_TEMPLATE.md`.
- [ ] T022 [US4] The parent publishes authorized repairs only after ownership clearance and passing local gates, using `.github/PULL_REQUEST_TEMPLATE.md`; record the commit, CI checks, and review against that repair issue without altering the current audit branch.
- [ ] T023 [US4] Merge a repair PR only after its current required checks pass, review and ownership clearance are recorded, the `.github/PULL_REQUEST_TEMPLATE.md` is complete, and merge authority is explicit; otherwise leave it open and report the exact blocker on the associated GitHub issue/PR.

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Validate the complete bounded harness without changing portal production code or converting blockers into success.

- [ ] T024 Run the documented isolated inventory/dialog suite and policy/report checks with the exact command recorded in `test-artifacts/websocket-dialog-audit/report.json`; verify ordinary collection cannot execute live cases, live work remains explicitly gated, protected PR #3814 files remain untouched, and the unreachable-portal result remains BLOCKED in `test-artifacts/websocket-dialog-audit/report.md`.

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: T001 precedes T002. No environment bootstrap, dependency installation, portal start, or branch change is part of this feature's setup.
- **Foundational (Phase 2)**: T003 depends on T002 and blocks all user-story browser journeys.
- **User Stories**: Story 1 can proceed after the foundation. Story 2 depends on Story 1's real inventory/dialog inspection and the safety foundation. Story 3 depends on the Story 1/2 evidence contracts. Story 4 depends on a confirmed defect recorded by Story 3.
- **Polish**: T024 follows the isolated harness implementation and report validation. A blocked live prerequisite remains a blocker; it is not a reason to start a service or weaken policy.

### User Story Dependencies

- **US1 (P1)**: Depends on Setup and Foundational phases; independently testable with isolated real assets.
- **US2 (P1)**: Depends on US1 inventory/dialog coverage and the policy foundation. Live subscription is additionally blocked until all operation-specific evidence and capabilities are verified.
- **US3 (P2)**: Depends on US1 and US2 result contracts; isolated report validation can use synthetic records.
- **US4 (P3)**: Depends on a confirmed, deduplicated US3 defect with its own issue and ownership clearance. Each repair is a separate SpecKit workflow.

### Within Each User Story

- Story tests precede their implementation where those tests exercise the implementation.
- Inventory/oracle precedes dialog inspection; safety decision verification precedes a subscription journey.
- Defect issue creation follows reproducible evidence and verified cause. A repair cannot begin before its unique issue and, when required, separate repair specification exist.
- Release-note, test, commit, PR, and merge work is per repair, not shared across unrelated defects.

## Parallel Opportunities

- **Setup**: None; the support package must exist before the audit-only pytest options are added.
- **Foundational**: The fail-closed policy is a prerequisite for both browser stories and is not parallel to them.
- **US1**: T004 and T005 can be implemented in parallel because they create different test files. T006 follows T004; T007 follows T005 and the inventory model; T008 validates both.
- **US2**: Live-gate tests precede permission and journey changes. Per-operation live journeys are serial; do not parallelize work against a shared live organization or session.
- **US3**: Report contract tests precede reporting code. Different confirmed defects can be triaged independently only after evidence and ownership boundaries are established.
- **US4**: Distinct approved repairs may proceed independently in separate worktrees after their separate specs and ownership clearance. Each issue's regression, release note, checks, PR, and merge remain individually gated.

## Parallel Example: User Story 1

```text
After T003, run these independent test-authoring tasks in parallel:
T004: real inventory reconciliation tests in tests/e2e/websockets_tab/dialog_audit/test_inventory.py
T005: real dialog inspection tests in tests/e2e/websockets_tab/dialog_audit/test_dialogs.py

Then complete T006 before T007, and run T008 as the independent Story 1 acceptance check.
```

## Implementation Strategy

### Bounded implementation record (2026-10-04)

The executable harness covers real catalog/forms, SDK-linked UX review, and serial live selector inspection.
Checked tasks record their actual completed scope. Other task markers remain unchecked.
Checklist markers remain unchanged. A target-selection pass is not complete UX acceptance.

- T005 and T006 have partial implementations. Tests cover the real catalog, purpose,
  required controls, labels, multiplicity, family filtering, empty/error choices,
  delayed map replies, and abandonment. SDK signatures and server path placeholders
  form the independent requirements oracle. Capture input aliases follow the
  actual runner body builder. Utilities are not verified for execution.
- T008 is complete. The parent installed the environment and Chromium.
  Isolated browser validation measured 72 forms. The explicit regression selection passes.
  No manifests changed. Nonempty measured coverage is asserted.
- T009 is partly complete; T012's bounded exact-key lifecycle is complete. Real GET inspection visits all four returned sites and maps.
  All 72 forms have rendered evidence. Historical refusal remains a separate capability record.
  Synthetic tests cover HTTP 4xx/5xx, malformed JSON, empty body, scope drift, redirects, and prohibited traffic.
- T010 and T011 now implement the separately authorized exact-key read-only lifecycle.
  Source and executable regressions verify `StartRequestChecker`, channel dispatch,
  `/sites/{site_id}/stats/devices`, observation SUBSCRIBE, and local close.
  The installed SDK has the same device-stats subscription path.
  No generalized permission framework, utility runner, capture, or shell is added.
  T012 live execution completed after the parent's container/base revision check.
- T013 through T015 have a small restricted report writer and partial contract tests.
  Reports include complete inventory records, duration, SDK version, source revision,
  sanitized process command, separate statuses, and explicit live blockers.
  The report writer does not claim full model compliance or a successful pytest exit.
  Separate restricted isolated and live reports now exist.
  They include SDK/DOM client-input observations, shared Cancel gaps, and all-parent choice counts.
- T016 and T017 through T023 belong to the parent or a separately authorized repair.
  No GitHub issue, repair specification, production edit, commit, push, or merge occurred.
  Four optional UX enhancements and one shared Cancel user-story gap have measured evidence.
  No executed-operation functional defect is claimed.

The isolated boundary fulfills real rendered HTML and exact tracked assets locally.
It never starts a Flask listener or dispatches a production route handler.
Socket guards cover Python catalog discovery. Browser routing precedes page creation.
Every unapproved request is aborted before transmission.
Isolated mode has no forwarding branch.
Live mode forwards only approved GETs with redirects and retries disabled.
Independent traps test both boundaries.

The harness has five direct entries. Its support package has five files.
It uses absolute namespace imports instead of adding a sixth package initializer.
Pytest hook and fixture functions are required entrypoints, not application wrappers.
The harness implements one explicit observation lifecycle, not generalized subscription or defect-tracking frameworks.
Deployed backend attestation, the full failure matrix, and complete field-limit/default checks remain incomplete.
SDK/DOM utility purpose and optional client-targeting review now exist.
Do not claim a complete audit or passed cancellation.

Validation performed:

- Python 3.13 AST parsing passed for all nine harness files.
- Initial size checks passed before later browser/UX traversal changes.
  Those checks are historical, not evidence that every current function meets the initial size target.
- Eleven direct default-deny decisions and a sanitized-report smoke check passed.
  These checks used only the standard library. They are not pytest or browser evidence.
- The actual route handler aborted a synthetic start and fulfilled a local page.
  An independent forwarding trap observed zero forwarding calls.
- Protected PR #3814 files have no diff against HEAD.
- The branch remains `jmorrison-juniper-websocket-dialog-testing`.
- The prescribed Python prerequisite script is absent.
- `.gitignore` already excludes `test-artifacts/`, Python caches, and virtual environments.
  `.dockerignore` already contains the relevant existing technology patterns.
  No repository-wide ignore or tool configuration was changed.

The optional pre/post commit hooks were displayed and skipped as requested.
Ruby's YAML parser successfully read the post-hook configuration.
The mandatory companion hook was dispatched with:
`rtk proxy specify event run speckit.companion.after-implement after_implement`.
The dispatcher returned `Event command 'speckit.companion.after-implement' not found`.
Its zero exit code does not indicate hook success.
Companion journaling remains blocked. No companion state was synthesized.

### MVP First (User Story 1 Only)

1. Complete Setup and the fail-closed policy foundation.
2. Build real-catalog reconciliation and real-asset dialog inspection.
3. Run Story 1 independently in isolated mode, with no operation submissions.
4. Stop and validate purpose, scope, selector dependencies, empty/failure outcomes, and cancellation. Do not claim live success.

### Incremental Delivery

1. Preserve historical capability blockers. Keep current all-site/map GET inspection separate from subscription work.
2. Add Story 3's restricted report and one-issue-per-confirmed-defect tracking.
3. For each confirmed defect, start a separate Story 4 repair specification/workflow, followed by its own regression, release note, authorized PR, checks, review, and merge gate.
4. Run final isolated validation and local quality gates. The parent handles authorized publication after checks and ownership clearance.

### Current all-parent coverage and quality

The live traversal checks all four returned sites, not only the first.
The fourth site exposes three maps. SDK-client inspection checks all three serially.
Family-filtered device choices exist on later sites.
Parent selection changes trigger child refresh. Unchanged selections do not require a new response.
Approved selector responses are reused in memory within one context to avoid repeated Mist reads.
The complete audit uses a 120-second test bound and a shared traversal deadline.

The latest live report measured 72 forms and 315 selector-scope observations.
Target availability: 69 passed, three blocked, zero failed.
The remaining blockers are `mxedge.orgRemotePcap`, `mxedge.siteRemotePcap`, and `diag.sdkclient`.
Their required choices are empty across all returned applicable scopes.
No unknown requests or read errors occurred.
The shared Cancel gap and four optional client-choice enhancements remain separate UX findings.

Required guide preflight passed.
The explicit-file test-quality gate checked three harness test files with zero new findings.
No baseline or repository-wide analyzer setting changed.
Post-commit changed-base and full-release gates remain the parent's responsibility.

### Exact-key authorized observation extension

The original user read-only scope includes verified observation subscriptions.
The separate `live-readonly` option permits `site.stats.devices` only.
This is not another approval requirement and does not require a whole-server egress framework.
The parent verifies that the running `2900f56` container matches the local reviewed base before running it.
The default modes remain no-start/no-write.
Local lifecycle POSTs dispatch the reviewed observation runner and close its owned transport;
they do not call a remote Mist mutation endpoint.

The new rejection regressions cover changed keys/kinds/targets/parameters, extra fields,
malformed and empty start bodies, redirects, foreign origin, query/fragment aliases,
second starts, foreign stops/reads, deletes/downloads/input, HTTP refusals, and malformed JSON responses.
Source regressions run the actual request checker, channel source mapper, runner selection,
SUBSCRIBE send logic on a synthetic socket, and local stop without starting a thread.
Reports distinguish actual site-source data from local lifecycle notices.
The exact-key report never overwrites all-form isolated/live inspection reports.

Extension validation:

- All previous isolated tests remain passing. The final explicit selection has 84 passing tests in 15.16 seconds.
- A real-HTML/unchanged-JS browser regression runs the exact form/start/observe/Stop journey against
  an independent zero-network synthetic response boundary.
  It verifies one exact UI start, one own stop, `State: Live` then `State: Stopped`,
  and zero remote-data count despite a local lifecycle notice.
- Black, Ruff and targeted explicit-file mypy pass for all nine harness files.
- Guide preflight passes with six input validations and three guide checks.
- Targeted analyzer inspects three test files with zero parse errors and zero new findings.
- Local reviewed base remains `2900f56f5943eca4011dae3f11d16ad42ce03cde`.
- Historical extension checkpoint: the command had not yet run; the parent then verified deployed/local base equality.
  The later corrected live result below supersedes that not-run state.
- Earlier all-parent live inspection evidence remains 72 forms, 315 selector observations,
  69 target passes and three empty-everywhere blockers; it does not imply subscription success.

Final validation:

- Ruff and Black check: passed for all nine harness files.
- Targeted explicit-file mypy: passed, nine source files.
- Isolated plus local HTTP-response regressions: 57 passed in 12.84 seconds.
- Guide preflight: one passed in 0.70 seconds; six input validations and three guide checks.
- Analyzer: three explicit test files inspected, zero parse errors, zero new findings.
  Two irrelevant detector scopes were skipped; the failure, assertion, tautology, and untested detectors inspected the tests.
- Live file: seven local response regressions passed; the real live test returned BLOCKED as intended.
  Its 72-form inspection took 16.948 seconds and made 52 approved GET attempts.
  The whole file completed in 18.69 seconds. No operation was submitted.
- An earlier rerun timed out waiting for the initial site GET under a three-second UI wait.
  The harness readiness wait now matches the 15-second guarded GET bound.
  The later measured run recovered full form coverage without retrying failed live responses.
- Protected PR #3814 files, analyzer baseline/configuration, and branch remain unchanged.
- No credential file read, container change, GitHub mutation, commit, push, or merge occurred in this session.

### Final live lifecycle correction and publication evidence

The parent's first exact-key run failed in 20.49 seconds with a harness response-contract error.
Cause: `SessionBuilder.build` emits `secrets.token_hex(8)` (16 lowercase hex characters);
the harness incorrectly required a UUID. This was not a remote stream failure.
The internal session-list check found that earlier matching session already stopped.
No foreign or unrelated session was stopped.

The guard now validates the actual 16-hex contract and preserves the response-issued own ID
before later channel/state validation, allowing exact own-session cleanup on validation failure.
Fixed allowlisted error reasons distinguish contract failures without exposing IDs or raw errors.
Regression tests cover production hex IDs, rejection of UUID-shaped session IDs,
and cleanup ownership retained after unexpected state response.
Remote stream failure, harness validation failure, and subscribed/no-data are separate report fields.

Final exact-key run: one passed in 12.14 seconds; measured journey 10.416 seconds.
States: connecting, live, stopping, stopped.
Remote stream: subscribed. Harness validation: passed.
Five-second observation: no-data, zero remote site-source events.
Eight owned message reads, one own stop, stopped verified, zero lifecycle errors.
The local connection-opened notice does not count as remote data.
Final internal check: three retained matching channel sessions, all stopped, none live.

Current full-form live run: 72 measured forms, 315 selector observations, 69 target passes,
zero failed forms and three genuine empty-everywhere blockers.
The report still returns BLOCKED, not whole-audit success.
The run made 52 approved GET attempts, no read errors or denied request categories,
and measured 16.138 seconds (17.91 seconds pytest).

Final isolated/local selection: 86 passed in 17.00 seconds.
Ruff, Black, targeted mypy, guide preflight and explicit-file analyzer pass.
Analyzer: three test files, zero parse errors, zero new findings. Baseline unchanged.

Tracked UX work:
- #3888: explicit operation-form cancellation; open, repair work retains exclusive production JS ownership.
- #3889: optional client-choice assistance; open.
- #3890: explain DHCP targets/MAC filters; closed after merged PR #3891.
The reports link these existing issues. Wording observations remain evidence against unchanged
container/local base `2900f56`, not claims that merged PR #3891 is defective.
The repaired main revision is not deployed or tested here.
Parent performs final analyze/publication; no commit/push/GitHub mutation occurred in this session.

### Support coverage publication follow-up

All previous 86 tests remain passing. Seventeen additional isolated cases exercise:
all-site/map form traversal with genuine empty-everywhere target records; expired deadlines;
missing/misconfigured controls; source-purpose mismatches; absent optional client controls;
device-family mismatches; sanitized browser exceptions; malformed scope responses;
nonorigin URLs; unsolicited WebSocket rejection; and real owner-only restricted report writing.
The writer regression restores existing report bytes rather than replacing measured evidence with synthetic results.
No network/live operation is used by these tests.

Exact parent-supplied no-omit branch coverage command appears in `design/quickstart.md`.
Final result: 103 passed in 23.72 seconds; measured total support coverage 81.22%.
The 80% support gate passes without suppressions, exclusions or repository configuration changes.
Per-module figures remain explicit: journeys 60%, policy 92%, inventory 95%, reporting 100%.
Ruff, Black, explicit-file mypy and guide preflight pass.
The analyzer inspected three test files with zero parse errors and zero NEW findings; baseline unchanged.

The plan tree now reflects the actual root `conftest.py` and support-only initializer.
Original phase-only constraints and missing environment remain historical, not current prohibitions.
The obsolete whole-server guard condition is removed from current evidence.
All-parent traversal uses a 90-second shared deadline inside the 120-second outer test bound.
No additional live run occurred; the accepted 12.14-second real lifecycle evidence is preserved.
Parent retains ownership of final publication checklist, metadata and manifests.

### PR #3892 browser CI placement correction

CI failure tracking: [#3895](https://github.com/jmorrison-juniper/MistHelper/issues/3895).
This repair moves browser-dependent tests into the existing Chromium-equipped e2e job.

Moved the entire nine-file harness with `git mv` into
`tests/e2e/websockets_tab/dialog_audit/`, the existing Chromium-equipped browser job.
The root-and-contracts shard excludes this tree; no workflow/browser-install workaround or
missing-browser skip was added. Updated namespace imports, repository-root parent offsets,
feature manifest/tree, task paths, contract paths and quickstart commands.

Post-migration validation:
- Explicit-directory collection recognizes local CLI options: 96 offline tests, live module excluded.
- Ordinary full e2e collection: 811 tests, including the same 96 offline audit tests, live module excluded.
  Collection is not a claim that the full e2e suite was executed.
- Follow-up ordinary collection with CI-style `--base-url=http://127.0.0.1:9600 --timeout=180`
  and no `--ws-audit-*` flags: 811 collected, 96 audit items, live module excluded.
  The audit's local options are registered during normal recursive collection.
- Default audit-directory execution with those same CI options and no audit flags:
  96 passed in 22.05 seconds. The inherited e2e fixtures do not replace `audit_page`:
  it uses a separately guarded browser context, real local rendered assets at `https://audit.invalid`,
  and Python socket denial, without requesting the parent's Flask `client`/`flask_app` fixtures.
  The generic base URL does not become an audit destination. The inherited timeout hook adds
  the existing 120-second per-item mark despite the CI command's 180-second global timeout.
- Explicit isolated/local response selection: 103 passed in 24.16 seconds;
  total support branch-aware coverage 81.22%, exceeding the unchanged 80% gate.
- Ruff passed; Black check leaves all nine files unchanged.
- Supplemental relaxed explicit-file mypy passed for nine files; exact flags are in quickstart.
  This is not strict typing and does not change repository configuration.
- Required guide preflight: one passed in 0.59 seconds; six input validations, three guide checks.
- Targeted analyzer: three test files checked, zero findings, zero NEW, zero parse errors;
  two detector scopes skipped. Baseline unchanged, quality artifacts owner-only.
- No old harness-path references remain in tracked file contents; `git diff --check` passed.

No live runs were repeated. Accepted `2900f56` live evidence remains historical and unchanged.
No production, sibling browser, workflow, baseline or credential files were edited.
No commit, push or GitHub change was performed; parent retains publication ownership.
