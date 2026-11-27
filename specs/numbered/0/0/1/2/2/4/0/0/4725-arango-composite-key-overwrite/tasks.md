# Tasks: ArangoDB Identity Keys for Declared Multi-Field Primary Keys

**Input**: Numeric record `specs\numbered\0\0\1\2\2\4\0\0\4725-arango-composite-key-overwrite`, with `plan.md`, `spec.md`, and `design/`.

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design/research.md`, `design/data-model.md`, `design/contracts/`.

**Format**: `[ID] [P?] Description`. `[P]` marks a task that may run in parallel with other `[P]` tasks, because it touches a different file. Each task names its requirement IDs, its exact paths, its acceptance statement, one verification command, and its status.

**Status values**: `open` (process not started), `absent` (artifact missing on main), `partial` (some behavior exists on main), `verified-present` (artifact exists on main and was checked).

**Verification note**: `.github/copilot-instructions.md` lists the local gates. No local gate covers ownership, operator census, backup, policy, issue drafts, or pull request steps. Those tasks name the nearest command and say so.

## Phase 1: Gates and Ownership

- [ ] T001 Confirm file ownership and record the handoffs.
  - Requirements: FR-013, D-9.
  - Files: none (GitHub read only).
  - Acceptance: Issue comments record a handoff from each owner of `src/foundation/persistence/db/writers/arango_writer.py` and of the preserved local branch. A fresh open pull request check finds no overlap.
  - Verification: `gh pr list -R jmorrison-juniper/MistHelper --state open --json number,headRefName,files` (no local gate covers ownership).
  - Status: open.

- [ ] T002 Write the identity audit rows for the 121 affected entries.
  - Requirements: FR-009, FR-015, SC-005.
  - Files: `design/contracts/identity-audit-format.md` (in the record).
  - Acceptance: One row for each affected entry gives the collection, declared fields, OpenAPI evidence, and verdict. Verdicts use the four values in the contract.
  - Verification: `python -m pytest tests/unit/config/standalone/foundation/persistence/arango_writer/test_arango_composite_keys.py` (runs tests 15 and 16).
  - Status: absent.

## Phase 2: Writer Change

- [ ] T003 [P] Add class `CompositeKeyIdentity`.
  - Requirements: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-009.
  - Files: `src/foundation/persistence/db/writers/composite_key_identity.py` (add).
  - Acceptance: The class exposes `applies`, `derive`, and the exemption set. Every executable line has an inline comment. Each function has five parameters or fewer and 25 lines or fewer.
  - Verification: `python -m ruff check .` (expected `All checks passed`).
  - Status: absent.

- [ ] T004 Route `_compute_key` through the identity rule.
  - Requirements: FR-001, FR-007, FR-008, FR-010, FR-011.
  - Files: `src/foundation/persistence/db/writers/arango_writer.py` (`write` at line 3987, `_prepare_document` at line 4047, `_compute_key` at line 4058).
  - Acceptance: The SLE checks (lines 4061 to 4064) run first. The identity rule runs next. Single-field and exempt entries keep the legacy branch. `_batch_import` keeps `on_duplicate="replace"` (line 4034).
  - Verification: `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` (expected `Success`).
  - Status: partial (SLE and legacy branches are verified-present on main. The identity branch is absent.)

- [ ] T005 Add batch action logging and the fallback count.
  - Requirements: FR-006, FR-014.
  - Files: `src/foundation/persistence/db/writers/arango_writer.py` (`write`, lines 3987 to 4006).
  - Acceptance: An info line runs before key derivation. A debug line runs after it. A warning line names the collection and the fallback count when the count exceeds zero. All log text is ASCII.
  - Verification: `python -m pytest tests/unit/config/standalone/foundation/persistence/arango_writer/test_arango_composite_keys.py` (runs test 17).
  - Status: partial (main logs `batch_import` events but no key derivation events).

## Phase 3: Tests

- [ ] T006 Add the distinct-record and idempotency tests.
  - Requirements: FR-001, FR-002, FR-003, SC-001, SC-002.
  - Files: `tests/unit/config/standalone/foundation/persistence/arango_writer/test_arango_composite_keys.py` (add, tests 1 to 4).
  - Acceptance: Tests 1 to 3 fail on main and pass after T004. Test 4 passes on both versions.
  - Verification: `python -m pytest tests/unit/config/standalone/foundation/persistence/arango_writer/test_arango_composite_keys.py`.
  - Status: absent.

- [ ] T007 Add the normalization and fallback tests.
  - Requirements: FR-004, FR-005, FR-006.
  - Files: `tests/unit/config/standalone/foundation/persistence/arango_writer/test_arango_composite_keys.py` (tests 5 to 9).
  - Acceptance: Integer and float timestamps share one key. Strings and numbers stay distinct. IPv6 neighbor keys match the ASCII rule. Missing, empty, null, NaN, and list values use the UUID fallback.
  - Verification: `python -m pytest tests/unit/config/standalone/foundation/persistence/arango_writer/test_arango_composite_keys.py`.
  - Status: absent.

- [ ] T008 Add the single-field and SLE golden tests.
  - Requirements: FR-007, FR-008, SC-003.
  - Files: `tests/unit/config/standalone/foundation/persistence/arango_writer/test_arango_composite_keys.py` (tests 10 and 11).
  - Acceptance: Single-field keys equal the legacy values. SLE keys equal the values from `SleTrendIdentity.key` and `SleWindowIdentity.key`.
  - Verification: `python -m pytest tests/unit/config/standalone/foundation/persistence/arango_writer/test_arango_composite_keys.py`.
  - Status: absent.

- [ ] T009 Add the preservation tests.
  - Requirements: FR-010, FR-011, FR-012, SC-004.
  - Files: `tests/unit/config/standalone/foundation/persistence/arango_writer/test_arango_composite_keys.py` (tests 13 and 14).
  - Acceptance: The collection handle receives only `import_bulk` calls. Legacy documents keep their keys and content. The import kwargs equal `{"on_duplicate": "replace"}`.
  - Verification: `python -m pytest tests/unit/config/standalone/foundation/persistence/arango_writer/test_arango_composite_keys.py`.
  - Status: absent.

- [ ] T010 [P] Update the `searchOrgDeviceEvents` preservation expectation.
  - Requirements: FR-011, D-10.
  - Files: `tests/unit/config/foundation/persistence/storage/arango_indexes/test_preservation.py` (line 36).
  - Acceptance: The expected key for `searchOrgDeviceEvents` equals the identity key of the record. Other parametrized cases keep their expected keys. The file gains no test function.
  - Verification: `python -m pytest tests/unit/config/foundation/persistence/storage/arango_indexes/test_preservation.py`.
  - Status: partial (test exists on main and pins the legacy key `record-1`).

- [ ] T011 Add the identity-audit guard tests.
  - Requirements: FR-013, FR-015, SC-005.
  - Files: `tests/unit/config/standalone/foundation/persistence/arango_writer/test_arango_composite_keys.py` (tests 15 and 16).
  - Acceptance: The guard prints the examined count. It reports zero unclassified entries. It fails when its input is empty.
  - Verification: `python -m pytest tests/unit/config/standalone/foundation/persistence/arango_writer/test_arango_composite_keys.py`.
  - Status: absent.

- [ ] T012 Run the existing SLE and guard tests without edits.
  - Requirements: FR-008.
  - Files: `tests/unit/db/sle_window_summary/test_export_identity.py`, `tests/unit/db/sle_window_summary/test_backend_preservation.py`, `tests/guardrails/test_endpoint_catalog.py` (unchanged).
  - Acceptance: All tests pass with no edit to these three files.
  - Verification: `python -m pytest tests/unit/db/sle_window_summary/test_export_identity.py` (repeat for `test_backend_preservation.py` and `tests/guardrails/test_endpoint_catalog.py`).
  - Status: verified-present.

## Phase 4: Documentation and Changelog

- [ ] T013 [P] Update the database strategy document.
  - Requirements: FR-016, D-13.
  - Files: `documentation/diagrams/core/database-strategy.md` (Source of Truth, lines 173 to 177).
  - Acceptance: The section states the ArangoDB document key rule, the exemption table, and the legacy-document behavior. No other section changes.
  - Verification: `python -m black --check .` (repository format gate. No local gate covers this Markdown file.)
  - Status: partial (the section names the router mapping and does not name the key rule).

- [ ] T014 [P] Add the changelog fragment.
  - Requirements: FR-016.
  - Files: `changelog.d/issue-4725-arango-composite-key-overwrite.md` (add).
  - Acceptance: The file has one `###` heading and one `Fixed` bullet that names issue #4725. The file name follows the rule for an issue without a pull request (RC-21). The name stays after the pull request opens (RC-22).
  - Verification: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py` (existing guard, RC-122).
  - Status: absent.

## Phase 5: Operator Gates (Migration Path, Gated by D-7)

- [ ] T015 Take a read-only census of the affected collections.
  - Requirements: FR-012, SC-004.
  - Files: none in the repository. Output stays under `data/`.
  - Acceptance: The census lists the document count and the legacy-key count for each affected collection. It changes no document.
  - Verification: No local gate covers an operator census. When a container is used, follow `documentation/container-deployment.md` Rule 1 (RC-34).
  - Status: open.

- [ ] T016 Create verified backups of the affected collections.
  - Requirements: FR-012.
  - Files: none in the repository. Backups stay outside the repository.
  - Acceptance: Each affected collection has a verified backup. The backup record names the collection, the document count, and the UTC time.
  - Verification: No local gate covers backups. Compare the counts with T015.
  - Status: open (blocked by D-7).

- [ ] T017 Record the approved legacy-document policy.
  - Requirements: FR-012, D-7.
  - Files: issue comment (no repository file).
  - Acceptance: The operator records one policy: keep, merge, or remove the legacy documents. The record names the approver and the UTC date.
  - Verification: No local gate covers a policy decision.
  - Status: open.

- [ ] T018 Prepare the follow-up issues and the remediation action.
  - Requirements: out-of-scope list in `spec.md`, and plan Complexity Tracking.
  - Files: none in the repository.
  - Acceptance: Drafts exist for: (a) duplicate strategy names, RC-70 and RC-76. (b) the BGP graph key `id`, RC-48 and RC-59. (c) timestamp-only identities, RC-74. (d) the structural split of `arango_writer.py`, remediation action R-1. The orchestrator files them.
  - Verification: No local gate covers issue drafts.
  - Status: open.

## Phase 6: Delivery

- [ ] T-LOCAL-GATES Run each applicable local gate.
  - Requirements: all FR items, and SC-006.
  - Files: the changed files from T003 to T014.
  - Acceptance: Each applicable gate reports the expected result in the local gates table. The pull request body lists each gate, its result, and the reason for each gate that does not apply.
  - Verification: the commands in `design/quickstart.md`, section 3.
  - Status: open.

- [ ] T-PR Commit, push, and open the pull request.
  - Requirements: FR-016.
  - Files: the changed files and the record folder `specs\numbered\0\0\1\2\2\4\0\0\4725-arango-composite-key-overwrite`.
  - Acceptance: The commit subject is `fix(persistence): derive ArangoDB identity keys from declared key fields`. The body contains `Closes #4725`. The branch is `fix/4725-arango-composite-key-overwrite`. The pull request body lists the gate results. No `auto-merge` label is set.
  - Verification: `python -m py_compile MistHelper.py` (compile gate, run before every commit).
  - Status: open.

- [ ] T-REMOTE-CI Watch the remote checks.
  - Requirements: FR-016, and constitution Principle IV step 8.
  - Files: none.
  - Acceptance: Each required check reports success on the latest commit. A failure opens a new issue before any fix.
  - Verification: `gh pr checks <number> --watch`. The local form of the CI full test gate is `pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal`.
  - Status: open.

- [ ] T-MERGE Merge after authorization, then verify the build.
  - Requirements: constitution Principle IV steps 9 to 11.
  - Files: none.
  - Acceptance: The orchestrator authorizes the merge. Auto-merge starts only after remote CI passes. After the squash merge, `container-build.yml` runs on the merged commit, and the image revision label equals the merged commit SHA. Deployment and health checks follow as operator tasks.
  - Verification: `symbol-diff --base origin/main src/foundation/persistence/db/writers/arango_writer.py` (expected `no module-level name changed`, exit code 0).
  - Status: open.

## Dependencies and Execution Order

- T001 must finish before T004 and T005 edit `arango_writer.py`.
- T002 must finish before T011 can pass, because test 15 reads the audit rows.
- T003 must finish before T004 and T006 to T009.
- T004 must finish before T006 to T008 can pass. T006 tests 1 to 3 fail on main first, as the proof that the test can fail.
- T010 and T013 and T014 may run in parallel with the writer tasks, because they touch other files.
- T015 to T017 wait for the D-7 decision. They do not block T-LOCAL-GATES for the code change.
- T-PR waits for T-LOCAL-GATES. T-MERGE waits for T-REMOTE-CI and the orchestrator authorization.

## Parallel Example

```text
T003 composite_key_identity.py (new module)
T010 test_preservation.py (one expectation)
T013 database-strategy.md (one section)
T014 changelog fragment (new file)
```
