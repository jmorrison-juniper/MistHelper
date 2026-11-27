# Quickstart: WAN history replay safety

This guide gives the exact steps to reproduce issue #4793 on the candidate branch. It also gives the exact verification commands. The author of this record ran none of these commands.

## Prerequisites

- Python 3.15.2 and the bootstrap of the repository (`.github/copilot-instructions.md`, Language and environment).
- A worktree of the candidate branch. Use the commands below.
- For remote checks only, the GitHub environment. Set the host and the token from the account variable. Never print the token.

```powershell
git fetch origin jmorrison-juniper-4200-migrate-mistwanperformance
git worktree add ..\MistHelper-4793 origin/jmorrison-juniper-4200-migrate-mistwanperformance
cd ..\MistHelper-4793
uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py
.venv\Scripts\Activate.ps1
```

## Reproduction of Issue #4793

The issue reproduction used commit `15c69b1176f7ae7c24e010aba3d29915ef228610`. GitHub returns HTTP 422 for that commit (RC-62). The steps below run on the candidate branch instead. The committed test names follow the issue steps.

| Issue step | Action | Committed test location |
|------------|--------|-------------------------|
| 1 | Load the committed domain, codec, and SQLite modules | Candidate modules: `sqlite_history.py`, `record_codec.py`, and `measurement.py` (RC-30, RC-37, RC-45). |
| 2 | Create an empty temporary database and select `SQLiteHistory` | Fixture `history` in `tests/unit/wan_performance/test_history_repository.py` (line 26). |
| 3 and 4 | Create the first live API sample and call `upsert` | Line 716 and line 719 of `test_sqlite_api_sample_replay_keeps_one_original_sample`. |
| 5 and 6 | Create the second sample with a later collection time and call `upsert` | Lines 717 and 720. The second call no longer raises `IntegrityError`. |
| 7 | Read the bounded window and expect one sample | Lines 722 to 724. The expected sample is the first sample. |

## Scenario 1: SQLite replay

```powershell
python -m pytest tests/unit/wan_performance/test_history_repository.py::test_sqlite_api_sample_replay_keeps_one_original_sample -q
```

Expected result: one test passes.

## Scenario 2: SQLite changed data

```powershell
python -m pytest tests/unit/wan_performance/test_history_repository.py::test_sqlite_rejects_changed_api_sample_without_replacing_prior_rows -q
```

Expected result: one test passes.

## Scenario 3: Arango mocked replay and changed data

```powershell
python -m pytest tests/unit/wan_performance/test_history_repository.py::test_arango_api_sample_replay_is_idempotent_and_rejects_changes -q
```

Expected result: one test passes after T009 sets the mocked commit to True.

## Scenario 4: New commit and rollback tests

```powershell
python -m pytest tests/unit/wan_performance/test_history_repository.py::test_arango_upsert_rejects_unconfirmed_commit -q
python -m pytest tests/unit/wan_performance/test_history_repository.py::test_arango_rollback_failure_keeps_original_error -q
python -m pytest tests/unit/wan_performance/test_history_repository.py::test_changed_sample_error_names_source_time -q
```

Expected result before Phase 3: each test fails. Expected result after Phase 3: each test passes.

## Scenario 5: Conflicting duplicates in one response

```powershell
python -m pytest tests/unit/wan_performance/test_snapshot_records.py -q
```

Expected result before T012: `test_rate_samples_reject_conflicting_duplicate_values` fails. Expected result after T012: the file passes.

## Scenario 6: Selected-port refresh with API samples

```powershell
python -m pytest tests/unit/wan_performance/test_live_service.py -q
```

Expected result before Phase 3: both tests pass. The candidate code already keeps one row for each repeated API sample. These tests guard that behavior. Expected result after Phase 3: the file passes.

## Scenario 7: Local gates for the changed files

Run each command from the local gates table of `.github/copilot-instructions.md`.

```powershell
python -m py_compile MistHelper.py
python -m ruff check .
python -m black --check .
python -m mypy $MYPY_PATHS --config-file pyproject.toml
radon cc src/interfaces/wan_performance -j | complexity-gate --max 10
bandit -c pyproject.toml -r src/interfaces/wan_performance -q
symbol-diff --base origin/main src/interfaces/wan_performance/integration/arango_history.py
symbol-diff --base origin/main src/interfaces/wan_performance/integration/record_codec.py
symbol-diff --base origin/main src/interfaces/wan_performance/collection/snapshot_records.py
ste-linter --config .ste-linter.toml --min-score 80 documentation/wan-performance.md changelog.d/pr-4208.md
```

Read `MYPY_PATHS` and the pydocstyle paths from `.github/workflows/ci.yml` before the mypy and pydocstyle commands.

Full tests use the two `pytest-chunks` commands of the local gates table.

## Scenario 8: Remote checks

```powershell
$env:GH_HOST='github.com'
$env:GH_TOKEN=$env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
gh pr view 4208 -R jmorrison-juniper/MistHelper --json headRefOid,mergeable --jq '.headRefOid + " " + .mergeable'
gh api repos/jmorrison-juniper/MistHelper/commits/15c69b1176f7ae7c24e010aba3d29915ef228610
```

Expected result: the first command prints the head SHA and the merge state. The second command returns HTTP 422 (RC-62).
