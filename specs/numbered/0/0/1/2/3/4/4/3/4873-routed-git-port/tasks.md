# Tasks: Port the routed core to Spec Kit 1.4.3

**Input**: `spec.md` and `plan.md` in this directory.

## Phase 1: Port

- [x] T001 Port the `-LiteralPath` hardening to `Test-FileExists` and `Test-DirHasFiles`. (delivered: .specify/scripts/powershell/common.ps1)
- [x] T002 Add `SPECIFY_FEATURE_NO_PERSIST` to `Get-FeaturePathsEnv`. (delivered: .specify/scripts/powershell/common.ps1)
- [x] T003 Port the `-LiteralPath` scan, `Set-Location`, and `ConvertTo-AsciiJson` to the routed `create-new-feature.ps1`. (delivered: .specify/scripts/powershell/create-new-feature.ps1)

## Phase 2: Verify

- [x] T004 Run the routed dry run and the four setup scripts. The pointer stays unchanged.
- [ ] T005 Add `tests/guardrails/test_routed_core_port.py`.
- [ ] T006 Run the guardrail tests and record the counts.
- [ ] T007 Add the changelog fragment.
- [ ] T008 Open the pull request.
