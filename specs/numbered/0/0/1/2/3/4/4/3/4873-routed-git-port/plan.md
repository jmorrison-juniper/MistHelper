# Implementation Plan: Port the routed core to Spec Kit 1.4.3

**Branch**: `chore/4873-routed-git-port` | **Issue**: #4873 | **Spec**: `spec.md`

## Summary

Apply the 1.4.3 hardening and the no-persist policy to the routed core. Keep the routing rules, and record each decision.

## Changes

| File | Change |
| - | - |
| `.specify/scripts/powershell/common.ps1` | `-LiteralPath` in `Test-FileExists` and `Test-DirHasFiles`. `SPECIFY_FEATURE_NO_PERSIST` in `Get-FeaturePathsEnv`. The persist guard uses `$noPersist`. |
| `.specify/scripts/powershell/create-new-feature.ps1` | `-LiteralPath` in the recursive scan and in `Set-Location`. `ConvertTo-AsciiJson` for the JSON output. |
| `tests/guardrails/test_routed_core_port.py` | Source contract for the routing rules. |
| `changelog.d/issue-4873-routed-core-port.md` | One release-note fragment. |

## Verification

1. Parse both changed `.ps1` files. Expect zero errors.
2. Run `create-new-feature.ps1 -DryRun -Json`. Expect a path under `specs/numbered/`.
3. Run the four setup scripts with `SPECIFY_FEATURE_DIRECTORY`. Expect exit 0 and JSON.
4. Run `git status`. Expect no change to `.specify/feature.json`.
5. Run `tests/guardrails/test_spec_route_contract.py` and `tests/guardrails/test_routed_core_port.py`.

## Constitution Check

- No structural directory in the new record has more than five children.
- No secret is in any file.
- The change adds no compatibility shim.
