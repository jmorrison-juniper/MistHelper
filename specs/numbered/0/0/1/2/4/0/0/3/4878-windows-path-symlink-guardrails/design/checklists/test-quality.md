# Test Quality Checklist: Windows Path and Symlink Guardrails

**Purpose**: Check the test changes against the structure, assertion, skip, logging, and ratchet rules before the pull request opens.

## Structure

- [x] The change adds no top-level test function or class (D-7).
- [x] The change adds no module-level name to a changed test module (D-6, symbol-diff rule S-7).
- [x] The new method joins `SpecCommandFixture`, which holds four members after the change (R-07, R-08).

## Assertions and Failure Paths

- [ ] The symlink case still asserts rejection on a host that creates symlinks. Verify with T-REMOTE-CI on Linux.
- [ ] The Git root assertion fails on a value that differs from the repository root. Verify with the one-off case in T-LOCAL-GATES.
- [ ] The missing-root assertion fails when the message wording changes. Verify with the test in T-LOCAL-GATES.
- [x] No bare truthy assertion, broad `pytest.raises`, or assertion-free test enters the change (rules listed in the test-quality configuration).

## Skips and Logs

- [x] The skip reason names the OS error text (FR-001).
- [x] The skip logs the cause at error level before it skips (D-3).
- [x] Each log line uses `%s` formatting and ASCII text (constitution Principle V, R-28).

## Suppressions and Secrets

- [x] No `# noqa`, `# type: ignore`, or `# nosec` comment enters the change (R-38).
- [x] No token, password, or account value appears in a test or a log line.

## Ratchet

- [ ] The test-quality analyzer reports zero new findings against the baseline after the commit. Verify in T-PR (R-49).
