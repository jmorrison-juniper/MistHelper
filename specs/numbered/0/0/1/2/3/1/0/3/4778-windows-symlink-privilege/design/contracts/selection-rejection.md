# Contract: Rejected feature selection

This contract describes the output of `check-prerequisites.ps1` when the selected path is a reparse point. The guard test checks this output.

## Command

```text
pwsh -NoProfile -File .specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireSpec
```

Run the command from the temporary repository root. Set these environment variables for the command:

- `SPECIFY_INIT_DIR` names the temporary repository root.
- `SPECIFY_FEATURE_DIRECTORY` names the selection link.

These values match `SpecCommandFixture.run` in `tests/guardrails/test_spec_route_contract.py` (lines 170-182).

## Input

- A selection link that is a symlink or a junction.
- The link points to a valid record that holds `spec.md`, `plan.md`, and `tasks.md`.

## Expected output

| Field | Expected value | Source |
|-------|----------------|--------|
| Exit code | Not zero | Test line 299 |
| Standard error | Contains `Examined` | Test line 300 |
| Standard error | Contains `Unsafe selected feature path`, the link path, and `Examined 1 parents.` | `common.ps1` line 259 |
| Temporary tree | Unchanged | Test line 301 |
| `.specify/feature.json` | Unchanged | Read-only commands must not change this file (`.github/copilot-instructions.md`, section Architecture and conventions) |

## Notes

- The exact message text comes from `common.ps1` line 259. This run did not execute the command. Unverified item U-2 covers the result on the Windows host.
