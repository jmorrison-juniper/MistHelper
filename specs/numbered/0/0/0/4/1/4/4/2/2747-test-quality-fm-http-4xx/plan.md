# Implementation Plan: Test quality: repair remaining missing_fm_http_4xx findings

**Branch**: `chore/2747-fm-http-4xx` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification from `specs/numbered/0/0/0/4/1/4/4/2/2747-test-quality-fm-http-4xx/spec.md`.

`spec.md`, `plan.md`, `tasks.md`, and `analysis.md` stay at the feature root. Research, data model, and quickstart stay under `design/`.

## Summary

The baseline holds 38 `missing_fm_http_4xx` entries (`.github/test-quality-baseline.json`, research R-17). Remote evidence shows that most entries come from detector behavior, not from missing tests. Twenty-six test modules already hold 4xx status literals, yet the baseline still lists them. Twelve test modules hold no 4xx status literal. Their source imports trigger applicability risk. Static reading finds no real missing 4xx refusal path before the census.

The plan therefore repairs the detector in misthelper-devtools, pins a released commit, runs the census, and writes the baseline with stale 4xx entries removed. A native 4xx test is added in MistHelper only when the census shows a real gap (family F1).

## Technical Context

**Language/Version**: Python 3.15 (`pyproject.toml` requires `>=3.15`).

**Primary Dependencies**: `mistapi` 0.64.x (installed 0.64.1 in `.venv`), pytest, and `misthelper-devtools`. The pin is commit `2239e7bd468fd27e40c43f2b87fcd35a2e49672b` (`requirements-dev.txt` line 197).

**Storage**: Git-tracked baseline JSON (`.github/test-quality-baseline.json`). Census output goes to `test-artifacts/2747/`, which Git ignores.

**Testing**: `test-quality-analyzer` census and gate, pytest for each changed test module, ruff, black, py_compile, mypy, and symbol-diff.

**Target Platform**: Windows 11, macOS, and Linux.

**Project Type**: Test-quality chore across two repositories: MistHelper and misthelper-devtools.

**Performance Goals**: The `test_quality_gate` job has a 10-minute timeout (`.github/workflows/ci.yml`, R-13). The census must finish inside that limit.

**Constraints**: No live Mist call. No production credential in a test. No suppression marker. No baseline edit that hides a new finding.

**Scale/Scope**: 38 baseline 4xx entries, each on a separate test module (research R-23 to R-60).

## Constitution Check

*Gate: passes before research and again after design.*

| Rule | Result | Reason |
|------|--------|--------|
| I. Five-item rule | Pass | The record uses the managed route `specs/numbered/0/0/0/4/1/4/4/2/`. Each route folder holds one child. No direct child enters `specs/`. Each record folder holds five children or fewer. |
| II. Class-based architecture | Pass | The plan adds no standalone function. Detector changes stay inside the existing classes of misthelper-devtools. |
| III. Safety first | Pass | No destructive operation runs. The plan reads no secret. The census writes only under `test-artifacts/`. |
| IV. Full deployment pipeline | Pass | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE cover steps 1 to 9. Steps 10 to 12 belong to the container workflow and stay with the owner. |
| V. Observability and logging | Pass | New test code adds no log statement. The tests assert existing ASCII log records (D-5). |
| VI. Inline comments | Pass | FR-011 requires an inline comment on each executable line of new test code. Task T013 checks the changed files. |
| VII. Action logging | Pass with decision D-5 | Principle VII governs operational code. The change touches no operational code path. The tests assert the existing action logs of the source under test. |
| Mist transport (`mistapi` only) | Pass | Tests use native `requests.Response` and `mistapi.APIResponse` objects with mocked boundaries. The plan adds no direct HTTP request. |
| Output backends and database keys | Not applicable | The change writes no export and defines no primary key. |
| Data directory | Pass | Census output goes to `test-artifacts/2747/`. No product output changes. |
| Container runtime | Not applicable | The change adds no container, port, or compose entry. |
| File paths | Pass | Scripts use `pathlib` or analyzer path helpers. Records use forward slashes for repository paths. |
| Security findings | Pass | No suppression comment is added (FR-007). |
| Documentation | Pass | No repository documentation changes. The analyzer documentation lives in misthelper-devtools and changes there (T006 and T007). |
| Changelog fragment | Pass with decision D-8 | The constitution Documentation rule requires one fragment for each change (R-83). The plan adds `changelog.d/issue-2747-fm-http-4xx.md`. |
| SpecKit escalation | Pass | The change touches 38 test modules across two repositories. This record is the specification. |
| Labels and issue first | Pass | Issue #2747 carries `chore`, `tests`, and `in-progress`. No label change is required. |
| Hot files | Pass | The plan does not change `MistHelper.py`. |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/0/4/1/4/4/2/2747-test-quality-fm-http-4xx/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    checklists/
      requirements.md
```

The folder `design/contracts/` is omitted. No new interface exists. The analyzer report format belongs to misthelper-devtools. Its schema is `report.schema.json` in the installed package.

### Source Code (repository root and misthelper-devtools)

| Path | Action | Task | Repository |
|------|--------|------|------------|
| `specs/numbered/0/0/0/4/1/4/4/2/2747-test-quality-fm-http-4xx/` | Add | T-PR | MistHelper |
| `requirements-dev.txt` (line 197, devtools pin) | Modify | T009 | MistHelper |
| `.github/test-quality-baseline.json` | Modify by the documented write command, then restore non-4xx entries | T012 | MistHelper |
| `changelog.d/issue-2747-fm-http-4xx.md` | Add. One `### Changed` heading and one bullet that names issue #2747 (D-8). | T-PR | MistHelper |
| `test-artifacts/2747/` | Add. Git ignores it. Never commit it. | T003 | MistHelper |
| Each test module that a census row in family F1 names | Modify. Add one native 4xx test. The census decides the list. Expected list before the census: none. | T011 | MistHelper |
| `src/misthelper_devtools/test_quality_analyzer/detection/missing_failure_mode.py` (`FailureModeApplicabilityInferer`, `SourceDrivenCoverageSlicer`) | Modify | T006 and T007 | misthelper-devtools |
| `tests/` of misthelper-devtools (`testpaths` at `pyproject.toml` line 81) | Add regression cases. Planned count: 7 (4 for F2, 3 for F3). | T006 and T007 | misthelper-devtools |

The plan does not change `MistHelper.py`, `src/`, `documentation/`, `README.md`, or `CHANGELOG.md`. It adds one fragment under `changelog.d/`.

### Analyzer Path Through the Detector

```text
test module (remote main)
  -> FailureModeApplicabilityInferer: is HTTP status risk present?        (missing_failure_mode.py lines 283-437)
  -> SourceDrivenCoverageSlicer: which test functions drive source?        (lines 438-622)
  -> HttpStatusCoverageInferer: is a 4xx literal in a status context?      (lines 84-282)
  -> _findings_for_coverage: emit missing_fm_http_4xx                      (lines 676-742)
  -> test-quality-analyzer: compare the finding with the baseline          (package __main__.py)
```

## Dependencies

- A misthelper-devtools release that holds the applicability and coverage repairs. Issue `jmorrison-juniper/misthelper-devtools#67` is open. Commits `b15d4f913030f984d07088e85f99bddf44ce7d4a` and `66449a34a3f875be4a605a8c7236ac58bd2fb485` exist in that repository. The MistHelper pin does not name either commit (research R-61 to R-68).
- A Python 3.15 environment with `requirements-dev.txt` installed in the implementing environment.
- GitHub CLI for pull request reads and checks. Use the account rule from the brief in each command.

## Complexity Tracking

| Item | Kind | Reason | Remediation |
|------|------|--------|-------------|
| 38 baseline 4xx entries, most stale or caused by the detector | Existing debt | The baseline predates the scoped detector and later repairs. The baseline is not pruned after those repairs. | T003 to T012 |
| The pin names a commit without the repairs | Existing debt | The upstream release has not happened. | T006 to T009 |

The plan adds no new debt.

## Risks and Mitigations

- **The upstream release is delayed.** Mitigation: the pin and the baseline stay unchanged. The record stays blocked on T008.
- **The census differs from the pre-census triage.** Mitigation: T005 updates the triage table from the census before any repair. SC-001 checks the row count.
- **A repair hides a real gap.** Mitigation: family F1 requires a failing mutation test (FR-004). Upstream regression cases in T006 and T007 keep detector positives for real status literals.
- **A baseline write hides a new finding.** Mitigation: T012 requires zero added entries. T012 restores each removed non-4xx entry.
- **A held file conflicts with PR #4208.** Mitigation: FR-013 and T011 skip the held file.
- **A pinned commit fails to install.** Mitigation: T010 installs the pin and runs the census before any pull request.
- **Test code action logs are disputed.** Mitigation: D-5 records the decision. A reviewer can reject D-5 in the pull request.

## Rollback

1. Close the pull request before merge. After merge, revert the squash commit on `main` with `git revert`.
2. Restore the earlier devtools pin line in `requirements-dev.txt`. The earlier commit is `2239e7bd468fd27e40c43f2b87fcd35a2e49672b`.
3. Restore the earlier `.github/test-quality-baseline.json` from the commit before the squash merge.
4. Run `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json`. The output must report zero new findings.

Caution: a revert restores the stale entries. The census then reports the same count as before the change.
