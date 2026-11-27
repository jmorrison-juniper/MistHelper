# Quickstart: Private Configuration Backup and Verified Catalog

This guide gives the exact reproduction steps and the exact verification commands for issue 4643. The drafting pass ran none of the commands in this guide. The implementer runs them after the gates in `spec.md` open.

## Preconditions

1. Issue 4636 merged. Its `state/` package and `state/lifecycle/backup.py` exist on `main`.
2. Issue 4634 recorded the contract evidence for the three list operations (`design/contracts/mist-list-reads.md`).
3. A new worktree exists for `feat/4643-private-config-backup-catalog`, created from `main`. Use the bootstrap command from `.github/copilot-instructions.md`, section "Language and environment".
4. The `in-progress` label is set on issue 4643 before the branch starts.

Run the bootstrap commands from the worktree root, one command on each line:

```powershell
uv python install 3.15.2
uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py
.venv\Scripts\Activate.ps1
```

## Reproduce the Current State

Each command reads GitHub or the local checkout. No command writes a file.

Check that the state package is absent on `main`:

```powershell
gh api "repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1" --jq '.tree[] | select(.path | test("cisco_config_converter/state")) | .path'
```

The command prints no line before issue 4636 merges. Research row R-72 records this result.

Check that the OpenAPI file does not document the reported total header:

```powershell
Select-String -LiteralPath "documentation\mist-api-openapi31yaml.yaml" -Pattern "X-Page-Total"
```

The command prints no line. Research row R-50 records this result.

Check that the firmware collector discards the reported total. Read `src/operations/execution/firmware_policy/sdk.py` at line 219. The function `collect` follows only the `next` link (research row R-22).

## Reproduce the Exposure Gap

The gap exists until the integration pull request merges. The output scan and the data browser do not exclude the converter backup directory.

Run this read-only command. It prints `False` until the integration pull request merges:

```powershell
python -c "print('.cisco-config-converter-backups' in __import__('web_portal.services.output_scan', fromlist=['EXCLUDED_DIR_NAMES']).EXCLUDED_DIR_NAMES)"
```

The output scan module imports `EXCLUDED_DIR_NAMES` (research row R-24). It lists the firmware directory name, not the converter directory name.

## Verification Commands for the Feature Pull Request

Run each command from the worktree root. Each command maps to one row of the local gates table in `.github/copilot-instructions.md`, section "Local gates".

```powershell
python -m ruff check .
python -m black --check .
python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml
python -m pytest tests/integration/web_portal/cisco_config_converter/backup
python -m pytest tests/integration/web_portal/cisco_config_converter/test_routes.py
python -m pytest tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py
python -m pytest tests/integration/test_mistapi_sdk_compatibility.py
python -m pytest tests/guardrails/test_nested_package_structure.py
python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=
radon cc src/interfaces/portals/cisco_config_converter -j | complexity-gate --max 10
bandit -c pyproject.toml -r src/interfaces/portals/cisco_config_converter -q
pylint src/ --fail-under=9.5
vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70
pydocstyle src/ wsgi.py web_portal
interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90
symbol-diff --base origin/main src/interfaces/portals/cisco_config_converter/state/lifecycle/backup.py
check-citations src tests
```

The test-quality ratchet uses the command form from `documentation/quality-gates.md`, section "Test quality ratchet". Set the base branch first:

```powershell
$BASE_REF = "main"
git fetch --no-tags origin "+refs/heads/${BASE_REF}:refs/remotes/origin/${BASE_REF}"
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/$BASE_REF" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
```

Expected results:

- Lint prints `All checks passed`.
- Format reports no file that needs a change.
- Types print `Success`.
- Each pytest command reports zero failures and zero errors. Each skip prints its reason.
- The coverage command reports 80 percent or above for `src`.
- The complexity command reports no block above cyclomatic complexity 10.
- Bandit reports no finding.
- Pylint scores 9.5 or above.
- Vulture, pydocstyle, and interrogate report no violation, and interrogate reports 90 percent or above.
- The symbol gate reports the module-level names that changed. The pull request body lists each added name: `BackupDirectory`, `BackupCapture`, `BackupWriter`, and `BackupCatalog`.
- The test-quality gate prints `gate: 0 new findings vs baseline`.

Gates that do not apply, with the reason:

- Compile (`python -m py_compile MistHelper.py`): `MistHelper.py` does not change.
- Safe sweep (`python MistHelper.py --test`): the change adds no menu operation.
- Menu reference: the change adds no menu operation.
- STE: the feature pull request changes no file in the STE gate list.
- Ops portal and ops platform: no file under `ops-portal/` or `mist-ops-platform/` changes.
- Dependency audit (`pip-audit -r requirements.txt`): no dependency changes.
- Playwright: no UI change.
- CodeQL register: no dismissal changes.

## Container Check for the POSIX Path (U-08)

Run this check on a Linux host or on the Podman machine that the owner uses. Start the container in the compose group. Name it with the issue number. Publish no port.

```powershell
.\scripts\compose.ps1 run --rm misthelper python -m pytest tests/integration/web_portal/cisco_config_converter/backup/test_backup_directory.py
```

Record the owner and mode of the mounted `data` directory inside the container. Run each command on its own line:

```powershell
.\scripts\compose.ps1 run --rm misthelper python -c "print(__import__('os').stat('/app/data').st_uid)"
.\scripts\compose.ps1 run --rm misthelper python -c "print(oct(__import__('os').stat('/app/data').st_mode))"
```

Remove each leftover resource by its exact name. Use the cleanup list from `.github/copilot-instructions.md`, section "Containers and ports":

```powershell
podman ps -a --filter "name=misthelper-tmp-" --format "{{.Names}} {{.Status}}"
podman volume ls --filter "name=misthelper-tmp-" --format "{{.Name}}"
```

Both commands must print no line when the cleanup finishes.

Warning: do not run a `system prune` or a `volume prune` command on a shared host. Such a command removes the data of other users.

## Integration Pull Request Commands

Run these commands after the feature pull request merges and the issue 4633 handover is recorded.

```powershell
python -m pytest tests/unit/web_portal/test_output_scan_runtime_files.py
python -m pytest tests/unit/config/standalone/foundation/persistence/database/test_data_browser_path_guard.py
```

Expected results:

- `test_output_scan_prunes_converter_backup_directory` passes. `EXCLUDED_DIR_NAMES` contains `BackupDirectory.NAME`.
- `test_data_browser_refuses_converter_backup_path` passes. The data browser refuses a path that contains the converter directory name.
- Both modules report zero failures.

## Cleanup

Remove each scratch file that the reproduction created. A committed file must not appear in `data/`. Confirm with:

```powershell
git status --short
```

Review the output. Each listed path must belong to the pull request file list in `plan.md`.
