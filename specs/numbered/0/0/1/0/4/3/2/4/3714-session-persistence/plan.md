# Implementation Plan: Upgrade Portal Session Persistence

**Branch**: `3714-session-persistence` | **Date**: 2026-10-06 |
**Spec**: [spec.md](spec.md)

**Input**: Issue #3714 and the confirmed assessment comment

## Summary

Replace the process-local upgrade portal session registry with a shared,
encrypted, expiring session recovery boundary. Preserve the existing
organization and site ownership rules. Migrate active sessions without a mass
logout. Repair the defect-asserting identity test so it proves recovery rather
than session loss.

The work uses seven implementation batches. Each batch has one exact file set
and must become one issue, one branch, and one pull request.

## Baseline and constraints

- Base revision: `f1505203d1d5ec845c94cb54f55118d613cf4e49`.
- Measured assessment revision: `d82f715436f295711ed5ac01ab9242118c03fee0`.
- Route reading method: `git show origin/main:src/interfaces/portals/upgrade_portal/app/routes/upgrade.py`.
- Protected handlers: 51 across 13 route blobs.
- The working-copy `upgrade.py` is a hot file owned by another worker.
- This specification branch changes no file under `src/`, `web_portal/`, or `tests/`.
- The issue body path `src/upgrade_portal/` is stale.

## Constitution check

### Five-item rule

**PASS for planning.** The plan divides the work by ownership and keeps each
implementation batch small. The implementation must preserve the existing
project hierarchy and function-size rules.

### Security boundary

**REQUIRED.** The shared store must hold encrypted values with expiry,
revocation, owner binding, and explicit failure behavior. No raw credential
or token may enter a cookie, log, response, trace, or unencrypted store value.

### Operational safety

**REQUIRED.** The deployment must preserve active sessions that migrate before
worker drain. It must not force logout during a running upgrade.

### Test correction

**REQUIRED.** The implementation must replace the test at
`tests/unit/upgrade_portal/test_identity.py:1505-1520`. The current test proves
the defect by asserting `current_session() is None`.

## Design decisions

### Use Redis as the shared store

Use the existing Redis service with a dedicated prefix and ACL. Do not add a
second store. The shared store must be authoritative after the migration
window. A local cache may reduce reads but cannot authorize a recovery.

### Encrypt the recovery record

Encrypt and authenticate the minimum recovery data before storage. Keep the
active key and one previous key in deployment-managed secret settings during
rotation. Re-encrypt a record after recovery with the active key.

### Preserve live sessions during staged migration

Write a shared record for each valid local session before its worker drains.
Keep the local record usable during the migration window. Reject a session that
cannot be verified after worker replacement. Do not use an unverified fallback.

### Keep route authorization common

Do not add separate session checks to the 51 routes. The identity boundary
must return the same recovered operator and organization context to all
protected handlers.

## Batch ownership and dependency order

### Batch 1: Shared session store foundation

**Proposed issue**: `3714-session-store-foundation`

**Purpose**: Define the encrypted record, key handling, expiry, revocation,
Redis access, and explicit failure contract.

**Exact file set**

- `src/interfaces/portals/upgrade_portal/runtime/session_store.py`
- `src/interfaces/portals/upgrade_portal/app/config.py`
- `src/interfaces/portals/upgrade_portal/app/factory.py`
- `compose.yml`
- `deploy/.env.example`

**Dependencies**: None.

### Batch 2: Identity recovery and authentication persistence

**Proposed issue**: `3714-identity-recovery`

**Purpose**: Connect the identity boundary and sign-in flows to the shared
store. Write records for valid local sessions before worker drain.

**Exact file set**

- `src/interfaces/portals/upgrade_portal/runtime/identity.py`
- `src/interfaces/portals/upgrade_portal/app/routes/auth.py`

**Dependencies**: Batch 1.

### Batch 3: Upgrade execution and organization controls

**Proposed issue**: `3714-upgrade-control-recovery`

**Purpose**: Verify recovered identity and organization ownership for the
highest-blast-radius handlers before control actions execute.

**Exact file set**

- `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py`
- `src/interfaces/portals/upgrade_portal/app/routes/upgrade.py`
- `src/interfaces/portals/upgrade_portal/app/routes/org_controls.py`

**Dependencies**: Batch 2.

**Ownership note**: `upgrade.py` is a hot file. The implementing worker must
read its committed baseline with `git show origin/main:<path>` and coordinate
file ownership before editing it.

### Batch 4: Organization selection, pre-check, and site locks

**Proposed issue**: `3714-selection-and-lock-recovery`

**Purpose**: Preserve organization scope, site selection, pre-check identity,
and lock ownership after recovery.

**Exact file set**

- `src/interfaces/portals/upgrade_portal/app/routes/select.py`
- `src/interfaces/portals/upgrade_portal/app/routes/org_precheck.py`

**Dependencies**: Batch 2.

### Batch 5: Capture recovery

**Proposed issue**: `3714-capture-session-recovery`

**Purpose**: Restore identity before capture creation, status reads, downloads,
and pre-upgrade evidence access.

**Exact file set**

- `src/interfaces/portals/upgrade_portal/app/routes/capture.py`

**Dependencies**: Batch 2.

### Batch 6: Review and history recovery

**Proposed issue**: `3714-review-session-recovery`

**Purpose**: Preserve organization ownership for comparisons, downloads, and
capture and run history.

**Exact file set**

- `src/interfaces/portals/upgrade_portal/app/routes/review.py`

**Dependencies**: Batch 2.

### Batch 7: Test, deployment, and security contracts

**Proposed issue**: `3714-session-persistence-contracts`

**Purpose**: Prove restart recovery, migration, expiry, revocation, ownership,
redaction, and deployment configuration.

**Exact file set**

- `tests/unit/upgrade_portal/test_session_store.py`
- `tests/unit/upgrade_portal/test_identity.py`
- `tests/integration/upgrade_portal/test_session_persistence.py`
- `tests/contract/upgrade_portal/test_auth.py`
- `tests/contract/upgrade_portal/test_no_credential_leak.py`
- `tests/contract/upgrade_portal/test_log_redaction.py`

**Dependencies**: Batches 1 through 6.

## Validation plan

Run the smallest focused checks for each batch, then run the combined portal
tests and security checks:

```text
python -B -m pytest -p no:cacheprovider -q tests\unit\upgrade_portal\test_session_store.py tests\unit\upgrade_portal\test_identity.py
```

```text
python -B -m pytest -p no:cacheprovider -q tests\integration\upgrade_portal\test_session_persistence.py tests\contract\upgrade_portal\test_auth.py tests\contract\upgrade_portal\test_no_credential_leak.py tests\contract\upgrade_portal\test_log_redaction.py
```

```text
python -m ruff check src\interfaces\portals\upgrade_portal tests\unit\upgrade_portal tests\integration\upgrade_portal tests\contract\upgrade_portal
```

```text
bandit -c pyproject.toml -r src\interfaces\portals\upgrade_portal -q
```

The restart test must create application A, sign in with synthetic cloud
transport, retain the browser cookie, clear process-local records, create
application B with the same signing key and shared store, and prove that a
protected request succeeds. It must then remove the shared record and prove
that the protected request returns `401 not_authenticated`.

## Deployment sequence

1. Provision the shared store ACL, key, and lifetime settings.
2. Deploy the shared-store-aware code while the current worker remains active.
3. Migrate valid local sessions when they reach the new identity boundary.
4. Drain workers only after the migration window completes.
5. Monitor recovery failures, sign-outs, key failures, and upgrade control
   requests without logging secret values.
6. Remove the previous encryption key only after the rotation window ends.

## Rejected alternatives

- Keep one Gunicorn worker. This hides the defect and does not provide recovery.
- Put raw provider tokens in Redis. This creates a credential disclosure risk.
- Put the session token in the browser cookie. This enlarges replay impact.
- Return a local session when Redis fails. This creates an unverified fallback.
- Force logout every operator. This can interrupt production firmware upgrades.
- Add 51 different recovery implementations. This creates inconsistent access
  rules and makes later review unsafe.
