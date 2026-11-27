# Quickstart: Upgrade Portal Session Recovery

This guide gives the exact commands for the defect, the feature checks, and the local gates. Run the commands from the repository root in PowerShell. Each command occupies one line.

## Prepare a Worktree

1. Install Python 3.15.2 and bootstrap the environment, as `.github/copilot-instructions.md` (section "Language and environment") describes.

```powershell
uv python install 3.15.2
uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py
.venv\Scripts\Activate.ps1
```

2. Confirm that the worktree is on a branch named `fix/3714-upgrade-portal-session-recovery`, or on a new branch created from `main`.

## Reproduce the Defect on Main

Run the existing defect check. The check asserts the loss of the session after a worker replacement.

```powershell
python -B -m pytest -p no:cacheprovider -q tests\unit\upgrade_portal\test_identity.py::test_current_session_returns_none_after_a_worker_restart
```

Expected result before implementation: 1 passed. The check replaces its assertion in task T012. After T012, the same name no longer exists.

The issue proof command names `tests/contract/upgrade_portal/session_signing/test_restart.py`. That file is absent on main (RC-38). Do not run the issue command. Use the replacement contract in task T013 instead.

## Verify Each Task

| Task | Command | Expected result |
| - | - | - |
| T006 | `python -B -m pytest -p no:cacheprovider -q tests\unit\upgrade_portal\test_config.py` | All tests pass |
| T007 | `python -B -m pytest -p no:cacheprovider -q tests\unit\upgrade_portal\test_factory_route_registration.py` | All tests pass |
| T008 | `python -B -m pytest -p no:cacheprovider -q tests\guardrails\test_container_policy_docs.py` | All tests pass |
| T009 and T012 | `python -B -m pytest -p no:cacheprovider -q tests\unit\upgrade_portal\test_identity.py` | All tests pass |
| T010 and T013 | `python -B -m pytest -p no:cacheprovider -q tests\contract\upgrade_portal\test_auth.py` | All tests pass |
| T011 | `git diff --name-only origin/main -- src/interfaces/portals/upgrade_portal/app/routes container/scripts/start.sh` | Only `src/interfaces/portals/upgrade_portal/app/routes/auth.py` appears. No change to `container/scripts/start.sh`. |
| T014 and T015 | `python -B -m pytest -p no:cacheprovider -q tests\contract\upgrade_portal\test_security.py` | All tests pass |
| T016 | `ste-linter --config .ste-linter.toml --min-score 80 documentation\upgrade_capture_portal.md` | The file scores 80 or above |
| T016 | `markdown-link-check --root . documentation\upgrade_capture_portal.md` | 0 broken links |
| T017 | `python -B -m pytest -p no:cacheprovider -q tests\guardrails\test_changelog_fragment_policy.py` | All tests pass |
| T004 | `git -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper" grep -c "@identity.require_session" -- src/interfaces/portals/upgrade_portal/app/routes` | The counts sum to 51 |

## Gate Commands

Run each command against the changed files. The file list comes from `git diff --name-only origin/main`. The expected results come from the local gates table in `.github/copilot-instructions.md:50`.

### Lint, format, and types

```powershell
python -m ruff check src\interfaces\portals\upgrade_portal\persistence\session_store.py src\interfaces\portals\upgrade_portal\runtime\identity.py src\interfaces\portals\upgrade_portal\app\config.py src\interfaces\portals\upgrade_portal\app\factory.py src\interfaces\portals\upgrade_portal\app\routes\auth.py tests\unit\upgrade_portal\test_identity.py tests\unit\upgrade_portal\test_config.py tests\contract\upgrade_portal\test_auth.py tests\contract\upgrade_portal\test_security.py
```

Expected result: `All checks passed`.

```powershell
python -m black --check src\interfaces\portals\upgrade_portal\persistence\session_store.py src\interfaces\portals\upgrade_portal\runtime\identity.py src\interfaces\portals\upgrade_portal\app\config.py src\interfaces\portals\upgrade_portal\app\factory.py src\interfaces\portals\upgrade_portal\app\routes\auth.py tests\unit\upgrade_portal\test_identity.py tests\unit\upgrade_portal\test_config.py tests\contract\upgrade_portal\test_auth.py tests\contract\upgrade_portal\test_security.py
```

Expected result: `No file needs a change`.

```powershell
python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml
```

Expected result: `Success`. The path list comes from `MYPY_PATHS` (`.github/workflows/ci.yml:93`).

### Tests

```powershell
pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal
```

```powershell
pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\contract tests\guardrails tests\integration --split tests\contract\upgrade_portal --split tests\integration\upgrade_portal
```

Expected result: one summary line for each shard, with every test passed.

```powershell
python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=
```

Expected result: coverage of 80 percent or above.

```powershell
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/main" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
```

Expected result: `gate: 0 new findings vs baseline`.

### Complexity, security, and quality

```powershell
radon cc src\interfaces\portals\upgrade_portal -j | complexity-gate --max 10
```

Expected result: no block above cyclomatic complexity 10.

```powershell
bandit -c pyproject.toml -r src\interfaces\portals\upgrade_portal -q
```

Expected result: no finding at any severity.

```powershell
pylint src/ --fail-under=9.5
```

Expected result: a score of 9.5 or above.

```powershell
vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70
```

Expected result: no finding. The path list comes from `VULTURE_PATHS` (`.github/workflows/ci.yml:101`).

```powershell
pydocstyle src/ wsgi.py web_portal
```

Expected result: no violation. The path list comes from `PYDOCSTYLE_PATHS` (`.github/workflows/ci.yml:104`).

```powershell
interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90
```

Expected result: coverage of 90 percent or above. The path list comes from `INTERROGATE_PATHS` (`.github/workflows/ci.yml:107`).

```powershell
symbol-diff --base origin/main src\interfaces\portals\upgrade_portal\runtime\identity.py
```

Expected result: `no module-level name changed`, with exit code 0. Run the same command for each changed Python module.

### Documentation

```powershell
ste-linter --config .ste-linter.toml --min-score 80 documentation\upgrade_capture_portal.md
```

Expected result: each file scores 80 or above. Run the same command for each changed Markdown file, including the record files under `specs/numbered/0/0/1/0/4/3/2/4/3714-upgrade-portal-session-recovery/`.

### Diff check (TP-28)

```powershell
git diff --name-only origin/main
```

Expected result: each listed path appears in the change map in `plan.md`. The list excludes `tests/contract/upgrade_portal/test_no_credential_leak.py`.

## Gates That Do Not Apply

| Gate | Reason |
| - | - |
| Compile of `MistHelper.py` | The change does not edit `MistHelper.py`. |
| Dependency audit (`pip-audit -r requirements.txt`) | `requirements.txt` stays unchanged. |
| Safe sweep (`python MistHelper.py --test`) | The change adds no menu operation. |
| Menu reference drift | The change adds no menu operation. |
| Ops portal and ops platform gates | The change edits no file under `ops-portal/` or `mist-ops-platform/`. |
| Playwright end-to-end gate | The change edits no file under `tests/e2e/`. The Playwright gate runs when a change touches `tests/e2e/`. |
