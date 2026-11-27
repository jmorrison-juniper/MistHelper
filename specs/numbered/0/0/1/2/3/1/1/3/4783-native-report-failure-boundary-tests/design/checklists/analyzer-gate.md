# Analyzer Gate Checklist: Native Report Failure-Boundary Tests

**Purpose**: Check that the test-quality gate evidence in this record is complete and honest.
**Created**: 2026-11-26
**Feature**: `plan.md` and `tasks.md`

## Command and Scope

- [x] CHK001 The changed-scope command matches the job at `.github/workflows/ci.yml` line 632. (`research.md`, R07)
- [x] CHK002 The full-suite command matches the procedure in `.github/copilot-instructions.md` lines 142 to 146. (`quickstart.md`, Scenario 4, step 10)
- [x] CHK003 Both scopes name the two required output lines, `gate_scope` and `gate: K new findings vs baseline`. (`quickstart.md`, Scenario 4)
- [x] CHK004 The changed scope includes the four changed test modules and no product file. (`plan.md`, File-by-File Change Map)

## Evidence Boundaries

- [x] CHK005 The record states that the analyzer did not run in this research. (`research.md`, Method, and U1)
- [x] CHK006 The predicted clearance of the two `test_report.py` findings is marked as a prediction. (`research.md`, U1)
- [x] CHK007 The owner comment figures are marked as unverified. (`research.md`, U11)

## Detector Rules

- [x] CHK008 The empty-body and malformed-JSON markers are literal text in the detector. (`research.md`, R37 and R38)
- [x] CHK009 Marker-only code is prohibited by FR-002, with the chain-tip lines that show the defect. (`research.md`, R17 and R18)
- [x] CHK010 The bridge rule for source-driving helpers is named with its line. (`research.md`, R35)
- [x] CHK011 The bare-assert rule ID and the settings key both appear, with their different names. (`research.md`, R41 and R42)

## Protected Files

- [x] CHK012 The baseline and the settings file keep the blob SHAs that main holds. (`research.md`, R04 and R05, and `tasks.md`, T012)
- [x] CHK013 No rule changes the settings file or the baseline. (`spec.md`, FR-009)

## Symbol Check

- [x] CHK014 The symbol-diff exit codes and output lines are named. (`research.md`, R43 and R44)
- [x] CHK015 The rename output for a base that holds the file is named, with the expected exit code 1. (`quickstart.md`, Scenario 4, step 11)
- [x] CHK016 CI has no symbol job, so the symbol output is evidence for the pull request body only. (`plan.md`, Risks and Mitigations)

## Not Applicable Gates

- [x] CHK017 Each not-applicable gate names the scope line that excludes the tests. (`tasks.md`, T-LOCAL-GATES, and `research.md`, R08, R09, R10)
- [x] CHK018 The Principle IV exception names the trigger line of `container-build.yml`. (`research.md`, R46)
