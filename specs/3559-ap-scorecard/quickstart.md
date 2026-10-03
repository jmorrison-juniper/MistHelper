# Quickstart: Organization Access Point Scorecard

## Prerequisites

- Use the worktree for issue `#3559`.
- Use the worktree Python at `.venv\Scripts\python.exe`.
- Keep source and test edits for implementation under `src/mist/intelligence/reports/ap_scorecard/` and `tests/unit/reports/ap_scorecard/`.
- Keep shared wiring changes deferred to [wiring.md](wiring.md).

## Validate the design artifacts

Run this command from the repository root:

```powershell
Get-ChildItem -LiteralPath specs\3559-ap-scorecard
```

Expected result:

- `plan.md` exists.
- `research.md` exists.
- `data-model.md` exists.
- `quickstart.md` exists.
- `wiring.md` exists.
- `contracts\export-contract.md` exists.

## Validate the future implementation

Run the unit tests after implementation:

```powershell
.venv\Scripts\python.exe -m pytest tests\unit\reports\ap_scorecard -q --timeout=120
```

Expected result:

- The tests pass.
- No test calls the Mist cloud.
- The tests prove color bands at `98.5`, between `80` and `98.5`, and `80`.
- The tests prove AP redundancy counts `1`, `2`, and `3`.
- The tests prove no exception occurs when `lldp_stat` is missing.

## Validate the future menu operation

Run the safe test path after shared wiring lands:

```powershell
.venv\Scripts\python.exe MistHelper.py --test
```

Expected result:

- The operation for menu `278` runs with no prompt.
- `data\ApScorecard.csv` exists.
- `data\ApScorecardBySite.csv` exists.
- The console summary prints organization-wide percentages for all five tiles.

## Validate the future export contract

Check `data\ApScorecard.csv`.

Expected result:

- The file has one data row for each AP in the test payload.
- Each row includes site, AP identity, model, version, compliance, status, VLAN, redundancy, power, stale configuration, certificate, and uptime fields.

Check `data\ApScorecardBySite.csv`.

Expected result:

- The file has one row for each site with APs in the test payload.
- Each row includes all five tile percentages and color bands.
- Each row includes no-redundancy, good-redundancy, and excellent-redundancy AP counts.

## Local quality gates for implementation

Run these commands before the implementation commit:

```powershell
.venv\Scripts\python.exe -m py_compile src\mist\intelligence\reports\ap_scorecard\__init__.py src\mist\intelligence\reports\ap_scorecard\client.py src\mist\intelligence\reports\ap_scorecard\model.py src\mist\intelligence\reports\ap_scorecard\operation.py
.venv\Scripts\python.exe -m ruff check src\mist\intelligence\reports\ap_scorecard tests\unit\reports\ap_scorecard
.venv\Scripts\python.exe -m black --check src\mist\intelligence\reports\ap_scorecard tests\unit\reports\ap_scorecard
.venv\Scripts\python.exe -m mypy src\mist\intelligence\reports\ap_scorecard --config-file pyproject.toml
.venv\Scripts\python.exe -m pydocstyle src\mist\intelligence\reports\ap_scorecard
.venv\Scripts\python.exe -m pytest tests\unit\reports\ap_scorecard -q --timeout=120
```
