# Research: Each test keeps its site lock actions out of the checkout trail

**Issue**: #3503 | **Spec**: [spec.md](spec.md)

## R1: The place of the move

**Decision**: Put the move in the root file `tests/conftest.py` as one autouse fixture.

**Reason**: The lock actions come from more than one folder.
The folders are `tests/unit/upgrade_portal`, `tests/contract/upgrade_portal`, and `tests/integration/upgrade_portal`.
The file `tests/test_upgrade_portal_audit.py` sits in the root folder of the tests.
A fixture in the root file reaches each folder, and a new test file needs no action (FR-002).

**Rejected**: One fixture in each folder file.
That choice misses the root folder, and each new folder needs a copy.

## R2: The scope of the move

**Decision**: Give the move the function scope.

**Reason**: pytest sets up each fixture of a wider scope before each fixture of the function scope.
The browser guard of #3498 is a session fixture.
It therefore reads the path of the checkout trail before the first move, so the move does not blind it (FR-010).
Each test also gets an empty trail of its own (User Story 1, scenario 2).

**Rejected**: A session move.
pytest sets up an autouse fixture before the other fixtures of its scope.
A root session move would therefore run before the browser guard, and that guard would count the moved trail.

## R3: The mechanism of the guard

**Decision**: Use one autouse session fixture in `tests/conftest.py`.
It counts the trail before the first test, and it counts the trail again in its teardown.
A changed count raises an error in the teardown, and pytest reports that error as a failed run.
A hook `pytest_terminal_summary` prints the measure of the guard.

**Reason**: The browser guard of #3498 uses the same pattern, so a maintainer reads one pattern.
The error names the path and the counts in the report of the run.

**Rejected**: The hook `pytest_sessionfinish` with a changed exit status.
That hook gives no error record, and a maintainer sees only an exit code.

## R4: The place of the guard class

**Decision**: Put a new class `CheckoutTrailGuard` in the new module `tests/support/site_lock_trail.py`.
The module imports the standard library and nothing from the portal.

**Reason**: The class `AuditTrailIsolation` of #3498 lives in the package `tests/support/upgrade_portal_e2e`.
The start of that package imports the dependency groups of the portal factory.
The root file of the tests loads for each test session, so an import of that package would load the portal factory for each session.

**Rejected**: A move of `AuditTrailIsolation` into a shared module.
The browser guard would then change, and FR-010 keeps it unchanged.
The two classes share one count rule of ten lines.
A later change can join the two count rules.

## R5: The import of the lock module

**Decision**: Import the lock module inside each of the two fixtures.

**Reason**: The root file checks the environment in the hook `pytest_configure`.
An import at the top of the file runs before that check, and an absent package would then hide the repair message of #1866.
The fixture `isolate_config_utils_state` uses the same late import.

**Cost**: The root file already loads `MistHelper.py` for each session, in 7.3 seconds on this computer.
After that load, the import of the lock module took between 0.56 and 0.90 seconds in two measures.
The module `runtime/identity.py` imports the web framework of the portal, and that import holds most of the cost.
The import runs one time in each session.

**Measure**: A timing plugin read the setup time of each fixture in two sessions.
Over 1386 tests, the move took 0.09 milliseconds on average for each test.
The fixture `isolate_working_directory` took 0.34 milliseconds on average, for comparison.
The session guard took 172 milliseconds in a session with no portal test, because that session imported the lock module.
It took 0.75 milliseconds in a session of portal tests, because the collection had imported the lock module.
Both values are inside SC-005.

## R6: The directory of each test trail

**Decision**: Use the folder `site-lock-trail` inside the temporary directory of each test.

**Reason**: The fixture `tmp_data_dir` creates the folder `data` in the same directory, and that creation fails if the folder exists.
A separate name keeps the two fixtures apart.
The lock module creates the folder at the first write, so a test with no lock action sees no new folder.

## R7: The proof of the guard

**Decision**: Use two proofs.

1. Direct tests call the count, the decision, and the measure with a stand-in trail.
   They need no network and no production file.
2. A red run adds one temporary test that writes to the checkout trail of the worktree.
   The run must fail with the path and the two counts.
   The temporary test file then goes away before the commit.

**Reason**: The rule "Prove new guard behavior" accepts a direct test.
The red run also proves the wiring of the session fixture, which a direct test cannot prove.

## R8: The tests that move the trail today

**Decision**: Keep the four tests that set their own trail directory.

**Reason**: Each test reads its trail at a path that it names.
The autouse move runs first, and the setting of the test then wins (FR-003).
The test at line 917 of `tests/unit/upgrade_portal/test_lock.py` sets the relative name `data` and writes nothing.
It proves the anchor rule of the lock module, so it stays.

## R9: The production trail

**Decision**: Delete no line from any trail.

**Reason**: The owner decides about the 3031 test lines in the production trail (FR-009).
## R10: The skip when the lock module cannot import

**Decision**: If the import of the lock module raises an import error, the guard skips.
The terminal summary prints the error and names the missing capability.
The move then does nothing.

**Reason**: The lock module pulls in the web framework of the portal.
The environment guard of the root file does not require that package.
Without the skip, an environment with no such package would stop each test, and most of those tests never touch the portal.
Without the lock module, no test can write a site lock action, so the skip is safe.
The rule "Prove new guard behavior" permits a skip that prints the reason and names the missing capability.

**Rejected**: A failure of each test.
That choice stops unrelated tests for a gap that cannot cause the leak.

## R11: A nested session in the same process

**Decision**: Accept that a nested session counts the moved trail of the outer test.

**Reason**: One test in `tests/unit/org/test_org_synthetic_probes_manager.py` starts a nested session with `pytest.main`.
That nested session loads the root file again while the move of the outer test is active.
Its guard therefore counts the trail of the outer test, and each nested test gets its own move.
The guard of the outer session still counts the checkout trail, so the protection stays complete.
## Baseline: the leak before the change

**Measure**: I ran the unit, contract, and integration suites of the portal and `tests/test_upgrade_portal_audit.py` in the fresh worktree.
The trail of the worktree was absent before the run.
The run passed 5340 tests in 423 seconds.
After the run, the trail held 150 lines.
The lines came from three stand-in orgs.
The org that ends in `aa` wrote 143 lines, the org that ends in `a1` wrote 4 lines, and the org that ends in `c3` wrote 3 lines.