# HTTP 4xx test findings

## Problem

Issue #2746 reports 71 `missing_fm_http_4xx` findings. Commit `799a0c2cf`
reports 38 findings. The baseline contains the same 38 finding identities.

PR #4067 owned `tests/unit/test_rate_limiting.py` during the repair. PR #4076
owns `tests/unit/org/test_org_config_migration_workflow.py`. This change does
not edit either file while its ownership restriction applies.

PR #4076 repairs the false Mist SDK exception behavior. Its positional status
helper call can remain a separate analyzer finding until the call names the
status argument.

## Requirements

1. Repair each available `missing_fm_http_4xx` finding.
2. Use a returned response object for a Mist SDK HTTP status.
3. Assert a specific operator signal or return value.
4. Do not use a `mistapi` exception to model an HTTP status.
5. Keep issue #2747 outside this change.
6. Update the baseline only from the measured repaired tree.
7. State the stale issue count in the pull request.

## Acceptance criteria

- The analyzer reports no available issue #2746 finding.
- The baseline matches the remaining live finding identities.
- Each changed test passes.
- The test-quality preflight passes.
- The changed-from analyzer reports no new finding.

