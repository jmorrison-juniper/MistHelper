# Research: Each isolation check of the browser test portal can fail

**Issue**: #3501 | **Spec**: [spec.md](spec.md)

## R1: Remove each trap, or give each trap a reader

**Decision**: Remove the four traps, their configuration keys, their fields,
their counters, and their response headers.

**Reason**: No portal code builds a connector from the configuration. A
search of `src/` and `wsgi_capture.py` finds each of the four keys in
`src/upgrade_portal/api/run_controls/models.py` only. A reader for each trap
would add a production code path that exists only to serve a test.

The real isolation of the connectors is already in place. The function
`build_child_environment` points ArangoDB at `http://127.0.0.1:1`, and it
points Redis at `127.0.0.1` port 1. A real connector call therefore fails at
once, and the page of the test then shows an error. The unit test
`test_child_environment_scrubs_credentials_paths_and_uses_sentinels` proves
the three addresses.

**Alternative**: Keep the traps and add a reader in each production
connector. Rejected, because the change would touch the production
connectors of ArangoDB, Redis, Mist, and the record files for a test value.

## R2: The audit store and the audit reader

**Decision**: Remove the keys `E2E_AUDIT_STORE` and `AUDIT_READER`, their
fields, and the class `AuditRecordStore`.

**Reason**: The lock module writes each lock action to a file through the
function `_write_lock_action`. The review route finds its reader through the
names of `AUDIT_READER_ATTRIBUTES` on a module. It never reads the
configuration key. The audit store therefore holds no row in any run.

Pull request #3502 moves the trail file of the test portal into the artifact
directory of the run. Its session guard counts the checkout trail.

The class `AuditTrailIsolation` stays in the same module.

## R3: The access store

**Decision**: Remove the key `E2E_ACCESS_STORE` and its field.

**Reason**: No portal code reads the key. The access decisions come from
`AUTHORIZATION_READER`, which is the method `authorization` of the portal
record store. That key stays.

## R4: The capture store

**Decision**: Keep the key `CAPTURE_STORE`.

**Reason**: The stand-in capture runner in
`tests/e2e/upgrade_portal/conftest.py` calls `write_capture` on
`flask.current_app.config["CAPTURE_STORE"]`. The issue table counted readers
in `src/` only, so it listed this key by mistake.

## R5: The persistence headers and their session guard

**Decision**: Remove the three persistence headers, the session fixture
`persistent_store_baseline`, and its helper `_persistent_baseline`.

**Reason**: The factory writes the fixed text "0" into each of the three
headers. The fixture compares 0 before the run with 0 after the run, so it
cannot fail. The runs and the actions of the test portal live in the stores
of the child process, and the child process ends with the run. The trail
guard of #3498 measures the one file that the lock module writes.

## R6: The owner check

**Decision**: Add the class `RunOwnerHeaderCheck` in
`tests/support/upgrade_portal_e2e/owner.py`. The conftest builds one check
for its run, and each page fixture calls it.

**Reason**: The helper `_assert_isolated_headers` in the conftest is the only
check that can fail today, and no direct test covers it. A class with direct
tests proves each failure case with no browser.

The check lowers each header name before it compares. A Playwright response
gives lowercase names, and a `urllib` response keeps the case of the server.
The check raises `AssertionError` with a message that names the header, the
found value, and the expected value. The pytest runner then reports the
failure in the test or the fixture that called the check.

## R7: The proof that the change removes the dead values

**Decision**: Add two direct tests that fail on the code of today.

1. A contract test builds the test application, reads `/healthz`, and
   requires exactly one header whose name starts with `X-MistHelper-E2E-`.
   The code of today sends eight such headers.
2. A unit test requires the exact set of the kept configuration keys. The
   code of today holds eight more keys. The test names only the kept keys, so
   the search of SC-001 finds no removed key in the test tree.

**Reason**: The browser test of SC-003 needs a running portal. The contract
test gives the same proof through the Flask test client, with no browser and
no network.

## R8: The accepted findings of the quality ratchet

**Decision**: Repair the five accepted findings of
`tests/e2e/upgrade_portal/test_run_controls/test_isolation.py`. Remove their
five baseline entries only if the full gate passes on this computer.

**Reason**: The ratchet matches a finding by its category, its rule, its file,
its line, and its text. The change moves each line of the file, so each
accepted finding would become a new finding. Four findings are the check
`is not None` on the box of an element. A helper that returns the box or
fails the test repairs them. The fifth finding is a test with no `assert`
statement. A final `assert` that the first tab keeps its selection repairs
it, and it also proves the second half of the test docstring.

A change of the baseline file makes CI run the full gate. The full gate on
this computer shows whether that run can pass.

## R9: The deploy

**Decision**: After the merge, copy `models.py` and `factory.py` into the
production container of port 8056. Then send the hang-up signal to the
Gunicorn master of that portal only.

**Reason**: The production portal builds no test value, so its behavior does
not change. The copy keeps each file of the container equal to `main`.
Before the signal, confirm that no upgrade run is active.

## R10: The run key of the configuration map

**Decision**: Remove the key `E2E_TEST_RUN_ID` from the configuration map.

**Reason**: A search of the whole worktree finds the key in `models.py`
only, where the map writes it. The factory writes the run owner header from
the field `test_run_id` of the dependency set, and it never reads the key.
The issue table did not list the key, because the key is not a field of a
group. FR-001 covers the key, because no code reads it.

The key `E2E_OVERRIDES_ACTIVE` stays. The factory reads it.
