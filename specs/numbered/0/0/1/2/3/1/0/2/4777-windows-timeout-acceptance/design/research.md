# Research: Native Windows Timeout Acceptance

## Decision

Use the Windows audit workflow as a pattern for action versions, dependencies, native-platform checks, read-only permissions, and JUnit results.

## Rationale

The repository already uses these controls in an optional Windows-only workflow. Reuse keeps the acceptance run consistent without changing shared CI or dependency files.

## Alternatives Considered

- Reuse the Windows audit workflow: rejected because it tests a different behavior and has its own test selection.
- Add the timeout module to shared CI: rejected because the requested acceptance must run on native Windows and remain optional.
- Mock subprocess behavior: rejected because the acceptance must exercise real process startup and teardown.

## Evidence

- `.github/workflows/windows-audit-report.yml` uses `windows-latest`, read-only contents permission, checkout without persisted credentials, action versions `checkout@v7` and `setup-python@v7`, a native Windows check, and JUnit count validation.
- `tests/guardrails/e2e_timeout_budget/test_timeout_budget.py` collects seven tests and has no parametrized cases. The full local run confirmed this count.
- The route dry run resolved issue 4777 to `specs/numbered/0/0/1/2/3/1/0/2/4777-windows-timeout-acceptance`.
- The existing `.specify/feature.json` continues to select issue 4785. Plan setup used the command-scoped `SPECIFY_FEATURE_DIRECTORY`.
