# Implementation Plan: Organization Switch Scorecard

**Branch**: `feat/3558-switch-scorecard`  
**Spec**: `specs/3558-switch-scorecard/spec.md`  
**Issue**: `#3558`  
**Menu**: `277`  
**Status**: Planned

## Summary

Add a safe organization report that builds the Mist switch scorecard across all sites. The report reads switch runtime evidence from `listOrgDevicesStats` with `type=switch`. It writes one switch detail file and one site summary file through the shared export backend.

## Technical Context

| Item | Decision |
| - | - |
| Language | Python 3.13 or newer |
| Package | `src/reports/switch_scorecard/` |
| Test path | `tests/unit/reports/switch_scorecard/` |
| Entry class | `SwitchScorecard` |
| Handler | `SwitchScorecard.run()` |
| API source | `listOrgDevicesStats` |
| Pagination | Reuse `APIDataFetcher` behavior used by menu 15 |
| Output backend | `DataExporter.write_with_format_selection()` |
| Output files | `SwitchScorecard.csv` and `SwitchScorecardBySite.csv` |
| Environment input | `SWITCH_AP_AFFINITY_LIMIT` |

## Constitution Check

| Principle | Plan result |
| - | - |
| Five-Item Rule | The new package contains four source modules and keeps each function small. |
| Class-Based Architecture | The feature uses classes for the client, model, and operation surfaces. |
| Safety-First | The operation is safe and uses no destructive API call. |
| Full Deployment Pipeline | Local gates run before each commit and before the pull request. |
| Observability & Logging | The client and operation log before and after each action. |
| Inline Comments | New Python executable lines include inline comments. |
| Action Logging | API calls, transforms, and exports have before and after logs. |

## Project Structure

```text
src/reports/switch_scorecard/
  __init__.py
  client.py
  model.py
  operation.py
tests/unit/reports/switch_scorecard/
  __init__.py
  test_switch_scorecard_client.py
  test_switch_scorecard_model.py
  test_switch_scorecard_operation.py
specs/3558-switch-scorecard/
  contracts/
  data-model.md
  plan.md
  quickstart.md
  research.md
  tasks.md
  wiring.md
```

## Design

The client resolves the organization and uses the same `APIDataFetcher` pagination path as the existing organization device statistics export. The model converts switch statistics into normalized report rows. The operation orchestrates the client, the model, the console summary, and the two export writes.

The integration pull request wires menu `277`. This feature branch does not edit `MistHelper.py`, `OperationRegistry`, `README.md`, or generated menu references.

## Complexity Tracking

| Existing debt | New design action | Follow-up |
| - | - | - |
| `src/reports/` can contain more than five report packages in the full repository. | Use the assigned nested package and do not add a sibling outside `switch_scorecard`. | A separate structure cleanup can group report packages by domain. |
| Menu registration files are shared fleet files. | Record all required entries in `wiring.md`. | The tier integration pull request applies the wiring. |

## Quality Gates

Run these commands with the assigned Python path.

```powershell
.\.venv\Scripts\python.exe -m py_compile src\reports\switch_scorecard\__init__.py src\reports\switch_scorecard\client.py src\reports\switch_scorecard\model.py src\reports\switch_scorecard\operation.py
.\.venv\Scripts\python.exe -m ruff check src\reports\switch_scorecard tests\unit\reports\switch_scorecard
.\.venv\Scripts\python.exe -m black --check src\reports\switch_scorecard tests\unit\reports\switch_scorecard
.\.venv\Scripts\python.exe -m mypy src\reports\switch_scorecard --config-file pyproject.toml
.\.venv\Scripts\python.exe -m pydocstyle src\reports\switch_scorecard
.\.venv\Scripts\python.exe -m pytest tests\unit\reports\switch_scorecard -q --timeout=120
.\.venv\Scripts\python.exe -m vulture src\reports\switch_scorecard --min-confidence 70
.\.venv\Scripts\python.exe -m interrogate -v src\reports\switch_scorecard
```

## Phase Outputs

| Phase | Output |
| - | - |
| Phase 0 | `research.md` |
| Phase 1 | `data-model.md`, `contracts/`, `quickstart.md` |
| Phase 2 | `tasks.md` |
| Implementation | Source package, tests, wiring manifest, release note |
