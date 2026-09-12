# Test Isolation Contract: Upgrade Portal E2E

**Feature**: `specs/2447-stale-bulk-run-controls/` | **Version**: 2

The E2E suite must not read or write a persistent local portal record.

## 1. Construction Order

The application factory accepts an explicit `E2EFactoryOverrides` object.

The factory applies the object in this order:

1. Build the Flask application and safe static configuration.
2. Validate that every required E2E override exists.
3. Install record, access, cloud, audit, and connector overrides.
4. Install the test response header.
5. Register blueprints.
6. Start no production storage bootstrap.

No route registration can occur before step 3.

Production construction uses the same factory with production dependencies.

## 2. Required Overrides

| Seam group | Test owner |
| - | - |
| Run and capture records | Process-owned record store. |
| Action records and transactions | Process-owned action store. |
| Site lock and authorization | Process-owned access store. |
| Audit records | Process-owned audit store. |
| Reconciliation cloud evidence | Scripted cloud stand-in. |
| Mist client construction | Failing cloud connector trap. |
| ArangoDB construction | Failing ArangoDB connector trap. |
| Redis construction | Failing Redis connector trap. |
| Portal record file access | Failing file trap. |

A missing override fails factory construction. No seam uses a production
fallback.

## 3. Support Package Layout

The support package has five direct children:

```text
tests/support/upgrade_portal_e2e/
├── __init__.py
├── environment.py
├── records/
├── resources.py
└── traps/
```

`environment.py` owns the credential scrub and connector sentinels.
`resources.py` owns the unique port, run identifier, artifact, log, and process
file allocation.

The records package has five direct children:

```text
records/
├── __init__.py
├── actions.py
├── audit.py
├── cloud.py
└── portal.py
```

`portal.py` owns run, capture, lock, and authorization records. The other
files own the action, audit, and scripted cloud records.

The traps package has five direct children:

```text
traps/
├── __init__.py
├── arango.py
├── files.py
├── mist.py
└── redis.py
```

## 4. Explicit Network Sentinels

The child environment uses:

```text
ARANGO_HOST=http://127.0.0.1:1
REDIS_HOST=127.0.0.1
REDIS_PORT=1
```

The child removes `MIST_APITOKEN` and `MIST_API_TOKEN`. The cloud stand-in is
the only cloud dependency.

Port 1 is an explicit unreachable sentinel. A trap must fail before code tries
that address.

## 5. Credential and Path Scrub

The child removes or replaces:

- `ARANGO_DATABASE`
- `ARANGO_USERNAME`
- `ARANGO_ROOT_PASSWORD`
- `REDIS_PASSWORD`
- `MIST_APITOKEN`
- `MIST_API_TOKEN`
- `OUTPUT_FORMAT`
- `DATABASE_PATH`
- Portal backup and export path variables

The child receives only test credentials that cannot authenticate to a real
service.

## 6. Connector and File Traps

Each trap raises a clear test failure and records the call name.

```text
E2E isolation failed: an ArangoDB connector was called.
E2E isolation failed: a Redis connector was called.
E2E isolation failed: a Mist cloud connector was called.
E2E isolation failed: a portal record file was opened.
```

The fixture resets cached ArangoDB, Redis, storage bootstrap, and readiness
state before it creates the application.

The suite asserts zero trap calls after each browser module and after the full
session.

## 7. Unique Resources

Each E2E server session receives:

- A new `test_run_id`.
- A new in-memory record graph.
- A loopback port reserved for that child only.
- A unique temporary artifact directory.
- A unique server log and process-owner file.

The fixture passes the reserved port directly to the child. It does not use a
fixed shared browser port.

No portal record file exists in the artifact directory.

## 8. Test Response Header

Each response from an E2E application includes:

```http
X-MistHelper-E2E-Run-ID: <test_run_id>
```

Production responses do not include this header.

The browser fixture rejects a missing or different value before it performs a
workflow assertion.

## 9. Store Rules

The process-owned store contains:

- Runs.
- Captures.
- Actions.
- Site locks.
- Authorization results.
- Cloud evidence scripts.
- Audit rows.

Every record carries the current `test_run_id`. The store rejects another test
run identifier.

The store has no connection string and no record file path.

## 10. Proof Order

### Unit Proof

Unit tests prove the traps, environment scrub, unique resource allocator,
header installer, and record ownership.

### Contract Proof

Contract tests construct the real application with overrides. They assert that
overrides exist before blueprint registration.

They call every route family and assert zero trap calls.

### Browser Proof

No browser command runs before the unit and contract isolation proof passes.

Then the complete command runs:

```powershell
.venv\Scripts\python.exe -m pytest tests\e2e\upgrade_portal -v
```

A targeted browser command cannot replace this proof.

### Local Store Proof

Record these values before and after the complete suite:

- Total nonfinal runs.
- Total E2E runs.
- Total E2E action records.
- Total E2E audit rows.

All values must remain unchanged.

## 11. Failure Behavior

- A connector or file call fails the test. It never becomes a skip.
- A missing override fails construction.
- A wrong response header fails before workflow assertions.
- A reused port or artifact path fails fixture setup.
- A record from another test run fails the write.
- A timeout leaves no persistent portal record.
