---

description: "Implementation tasks for upgrade portal session persistence"

---

# Tasks: Upgrade Portal Session Persistence

**Input**: Routed design documents from
`specs/numbered/0/0/1/0/4/3/2/4/3714-session-persistence/`

**Prerequisites**: `spec.md`, `plan.md`

**Specification-only boundary**

- This branch adds only the three routed specification files and one changelog
  fragment.
- Do not edit a file under `src/`, `web_portal/`, or `tests/`.
- Do not file the proposed batch issues.
- Do not create a pull request that changes a source file.

## Phase 1: Baseline and ownership

**Purpose**: Confirm the measured baseline and prevent hot-file conflicts.

- [ ] T001 Verify `origin/main` resolves to
  `f1505203d1d5ec845c94cb54f55118d613cf4e49`.
- [ ] T002 Verify `specs/numbered/` exists with
  `git ls-tree origin/main specs/numbered`.
- [ ] T003 Verify issue 3714 assessment comment
  `6026814949` is the source for the 51-handler count.
- [ ] T004 Verify the restricted route was read only with
  `git show origin/main:src/interfaces/portals/upgrade_portal/app/routes/upgrade.py`.
- [ ] T005 Verify no source, portal, or test file changes exist in this branch.

## Phase 2: Batch 1 - Shared session store foundation

**Purpose**: Define the shared record, encryption, expiry, revocation, and
failure contract.

**Proposed issue**: `3714-session-store-foundation`

- [ ] T006 Add `runtime/session_store.py` with an authenticated encrypted record.
- [ ] T007 Add validated session lifetime and key settings in `app/config.py`.
- [ ] T008 Construct and close the shared store in `app/factory.py`.
- [ ] T009 Add the dedicated Redis ACL and key prefix to `compose.yml`.
- [ ] T010 Document non-secret settings in `deploy/.env.example`.
- [ ] T011 Prove missing, expired, revoked, and undecryptable records fail closed.

**Exact file set**

- `src/interfaces/portals/upgrade_portal/runtime/session_store.py`
- `src/interfaces/portals/upgrade_portal/app/config.py`
- `src/interfaces/portals/upgrade_portal/app/factory.py`
- `compose.yml`
- `deploy/.env.example`

## Phase 3: Batch 2 - Identity recovery

**Purpose**: Replace process-local authorization with the shared identity
boundary and persist valid sessions before worker drain.

**Proposed issue**: `3714-identity-recovery`

- [ ] T012 Persist approved recovery data after each supported sign-in mode.
- [ ] T013 Restore a valid session in a replacement application.
- [ ] T014 Bind recovery to the operator, browser, organization, expiry, and
  revocation state.
- [ ] T015 Delete the shared record during sign-out.
- [ ] T016 Reject shared-store and key-service failures without a local fallback.

**Exact file set**

- `src/interfaces/portals/upgrade_portal/runtime/identity.py`
- `src/interfaces/portals/upgrade_portal/app/routes/auth.py`

## Phase 4: Batch 3 - Upgrade and organization controls

**Purpose**: Protect handlers with the highest blast radius.

**Proposed issue**: `3714-upgrade-control-recovery`

- [ ] T017 Verify recovered organization ownership before upgrade control.
- [ ] T018 Verify status, cancel, retry, reschedule, and stop actions.
- [ ] T019 Preserve the running upgrade control path after worker replacement.
- [ ] T020 Read the hot route baseline only with `git show` before editing.

**Exact file set**

- `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py`
- `src/interfaces/portals/upgrade_portal/app/routes/upgrade.py`
- `src/interfaces/portals/upgrade_portal/app/routes/org_controls.py`

## Phase 5: Batch 4 - Selection, pre-check, and locks

**Purpose**: Preserve organization and site ownership before upgrade actions.

**Proposed issue**: `3714-selection-and-lock-recovery`

- [ ] T021 Verify organization and site selection after recovery.
- [ ] T022 Preserve pre-check ownership after worker replacement.
- [ ] T023 Preserve lock owner identity and reject cross-session inheritance.

**Exact file set**

- `src/interfaces/portals/upgrade_portal/app/routes/select.py`
- `src/interfaces/portals/upgrade_portal/app/routes/org_precheck.py`

## Phase 6: Batch 5 - Capture recovery

**Purpose**: Protect pre-upgrade evidence and capture data.

**Proposed issue**: `3714-capture-session-recovery`

- [ ] T024 Restore identity before capture start, status, read, download, or
  page operations.
- [ ] T025 Reject capture access after expiry, revocation, or organization
  mismatch.

**Exact file set**

- `src/interfaces/portals/upgrade_portal/app/routes/capture.py`

## Phase 7: Batch 6 - Review and history recovery

**Purpose**: Protect comparison and historical organization data.

**Proposed issue**: `3714-review-session-recovery`

- [ ] T026 Restore identity before comparison, download, capture history, run
  history, or history page operations.
- [ ] T027 Reject historical data access after expiry, revocation, or mismatch.

**Exact file set**

- `src/interfaces/portals/upgrade_portal/app/routes/review.py`

## Phase 8: Batch 7 - Test and security contracts

**Purpose**: Replace the false safety assertion and prove the complete
recovery, migration, and redaction contract.

**Proposed issue**: `3714-session-persistence-contracts`

- [ ] T028 Replace the test at
  `tests/unit/upgrade_portal/test_identity.py:1505-1520`.
- [ ] T029 Assert valid shared-record recovery after process-local state clears.
- [ ] T030 Assert rejection for missing, expired, revoked, mismatched, and
  undecryptable records.
- [ ] T031 Prove replacement application recovery with synthetic cloud
  transport.
- [ ] T032 Prove supported sign-in modes persist only approved recovery data.
- [ ] T033 Prove credentials and tokens do not appear in cookies, responses,
  traces, logs, or storage.
- [ ] T034 Prove staged migration preserves sessions before worker drain.

**Exact file set**

- `tests/unit/upgrade_portal/test_session_store.py`
- `tests/unit/upgrade_portal/test_identity.py`
- `tests/integration/upgrade_portal/test_session_persistence.py`
- `tests/contract/upgrade_portal/test_auth.py`
- `tests/contract/upgrade_portal/test_no_credential_leak.py`
- `tests/contract/upgrade_portal/test_log_redaction.py`

## Phase 9: Focused validation

**Purpose**: Prove each batch before the full repository gates.

- [ ] T035 Run the focused unit tests for the shared store and identity.
- [ ] T036 Run the integration and contract tests for recovery and redaction.
- [ ] T037 Run Ruff on the affected portal and test paths.
- [ ] T038 Run Bandit on the affected portal package.
- [ ] T039 Run the full applicable repository quality gates.
- [ ] T040 Run the post-commit test-quality ratchet after each batch commit.

## Dependencies

- T006 through T011 depend on T001 through T005.
- T012 through T016 depend on T006 through T011.
- T017 through T027 depend on T012 through T016.
- T028 through T034 depend on the identity boundary and route batches.
- T035 through T040 depend on the completed batch under test.

## Completion rules

- Each batch has one issue, one branch, and one pull request.
- No batch changes a file owned by another active worker.
- No batch stores a plaintext credential or token.
- No batch adds a stale source path.
- No batch leaves the current defect assertion unchanged.
- No batch forces logout of every live operator.
