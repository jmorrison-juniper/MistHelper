# Quickstart: Organization Switch Scorecard

## Prerequisites

1. Use the feature worktree.
2. Use the assigned virtual environment Python path.
3. Do not edit shared menu wiring files on this branch.

## Validate the model

```powershell
C:\Users\jmorrison\mh-fleet\3558-switch-scorecard\.venv\Scripts\python.exe -m pytest tests\unit\reports\switch_scorecard -q --timeout=120
```

Expected result: all scorecard unit tests pass.

## Validate code quality

```powershell
C:\Users\jmorrison\mh-fleet\3558-switch-scorecard\.venv\Scripts\python.exe -m py_compile src\reports\switch_scorecard\__init__.py src\reports\switch_scorecard\client.py src\reports\switch_scorecard\model.py src\reports\switch_scorecard\operation.py
C:\Users\jmorrison\mh-fleet\3558-switch-scorecard\.venv\Scripts\python.exe -m ruff check src\reports\switch_scorecard tests\unit\reports\switch_scorecard
C:\Users\jmorrison\mh-fleet\3558-switch-scorecard\.venv\Scripts\python.exe -m black --check src\reports\switch_scorecard tests\unit\reports\switch_scorecard
C:\Users\jmorrison\mh-fleet\3558-switch-scorecard\.venv\Scripts\python.exe -m mypy src\reports\switch_scorecard --config-file pyproject.toml
C:\Users\jmorrison\mh-fleet\3558-switch-scorecard\.venv\Scripts\python.exe -m pydocstyle src\reports\switch_scorecard
```

Expected result: each gate passes.

## Validate the operation seam

Run the operation through unit tests with a fake API session and fake exporter. Confirm these outcomes.

1. The client requests `listOrgDevicesStats` with `type="switch"`.
2. The model writes one detail row for each switch.
3. The site report contains each tile percentage and count.
4. A switch without `module_stat` produces empty module fields.
5. The operation writes `SwitchScorecard.csv` and `SwitchScorecardBySite.csv`.

## Deferred integration

The integration pull request applies the menu wiring from `specs/3558-switch-scorecard/wiring.md`. Do not run menu 277 from the root menu until that pull request lands.
