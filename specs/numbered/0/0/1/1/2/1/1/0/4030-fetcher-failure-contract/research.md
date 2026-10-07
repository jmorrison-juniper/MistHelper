# Research: Fetcher Failure Contract

## Decision 1: Repair the fetcher return contract

**Decision**: Change the unresolved-site branch in
`DeviceDataFetcher.fetch()` to log the required error and return `False`.

**Rationale**: The fetcher owns site resolution. The display already suppresses
completion when the fetcher returns explicit `False`.

**Alternatives considered**:

- Change `InteractiveDisplayUtils.device_tests()`. Rejected because its
  explicit `False` contract already works.
- Change `OperationExecutor`. Rejected because the existing handled-error
  classifier already checks errors before output evidence.
- Add Menu 95 controls. Rejected because issue #4030 excludes missing controls.

## Decision 2: Use the exact handled-error text

**Decision**: Emit
`! Error fetching device data: site ID could not be resolved.`.

**Rationale**: The text is clear to the operator. The phrase `error fetching`
matches `HANDLED_ERROR_MARKERS` without a portal edit.

**Alternatives considered**:

- Reuse only the debug abort line. Rejected because debug output does not
  establish an explicit failed result.
- Use a new marker. Rejected because it would widen the production scope.
- Classify the message as missing input. Rejected because the feature requires
  the existing handled-error contract.

## Decision 3: Preserve marker coupling as a dependency

**Decision**: Record issue #3168 as the owner of the broader marker-coupling
problem.

**Rationale**: This feature intentionally relies on log text for portal failure
classification. It does not introduce a typed portal outcome.

**Alternatives considered**:

- Replace log markers with a typed result now. Rejected because it exceeds the
  strict issue scope.
- Add a Menu 95-only portal rule. Rejected because it duplicates fetcher state
  in the portal.

## Decision 4: Prove the portal result through the real path

**Decision**: Extend
`tests/unit/web_portal/test_portal_silent_completion.py` with a Menu 95
regression that uses the real display and fetcher classes.

**Rationale**: A fake fetcher result would not prove the contract between site
resolution, the display completion guard, log capture, output scanning, and the
portal verdict.

**Test wiring**:

- Register menu 95 with `InteractiveDisplayUtils.device_tests`.
- Patch both source resolver seams with one controlled resolver object.
- Keep `DeviceDataFetcher` bound to the real production class.
- Make site selection create an unrelated file, then return no site ID.
- Replace the scanner constructor with a factory for a real scanner rooted at
  `tmp_path`.
- Use a Mist endpoint mock only to prove that no request occurs.
- Run the executor operation path and inspect its final run record.

**Alternatives considered**:

- Call `_finish_successful_operation()` with prepared log entries. Rejected
  because it bypasses the real display and fetcher path.
- Put a file name directly in `run["output_files"]`. Rejected because it does
  not prove concurrent output scanning.
- Mock `DeviceDataFetcher.fetch()` to return `False`. Rejected because it hides
  the defect under test.

## Decision 5: Use a red-green proof for before and after behavior

**Decision**: Add the portal regression before the production repair. Run it
once against the current branch, then run it again after the repair.

**Rationale**: The current code returns `None`, logs display completion, and
lets unrelated output produce a completed run. The repaired code returns
`False`, logs the exact error, and produces a failed run.

**Required evidence**:

- Before repair: the new assertion expects Failed, but the observed status is
  Complete.
- After repair: the status is Failed.
- After repair: the failure reason contains the exact fetcher error.
- After repair: unrelated output remains present but cannot override failure.

**Alternatives considered**:

- Keep two production implementations in the test. Rejected because the test
  must exercise the real implementation.
- Reconstruct the old implementation in a test helper. Rejected because it
  creates a second contract that can drift.

## Decision 6: Keep non-site behavior unchanged

**Decision**: Do not change device-resolution failure, empty Mist response, or
successful output behavior.

**Rationale**: The specification limits the repair to unresolved site scope.
Existing tests cover the adjacent branches.

**Alternatives considered**:

- Convert every `None` failure to `False`. Rejected because it changes several
  established caller contracts.
- Change exception handling in `_fetch_data()`. Rejected because issue #4030
  does not cover that path.
