# Quickstart: Credential default audit

Run each command from the repository root in Windows PowerShell. Each command runs one check.

## Reproduce the database defaults

This command prints `True` when the field holds a value. It never prints the value.

```powershell
.venv\Scripts\python.exe -c "print(bool(__import__('src.foundation.persistence.db', fromlist=['DatabaseConfig']).DatabaseConfig().arango_password), bool(__import__('src.foundation.persistence.db', fromlist=['DatabaseConfig']).DatabaseConfig().redis_password))"
```

Expected before batch 1: `True True`. Expected after batch 1: `False False`.

## Reproduce the portal username default

This command prints `True` when the username resolves to a value. It never prints the value.

```powershell
.venv\Scripts\python.exe -c "print(bool(__import__('src.interfaces.portals.upgrade_portal.app.config', fromlist=['load_arango_settings']).load_arango_settings().username))"
```

Expected before batch 1 with `ARANGO_USERNAME` unset: `True`. After batch 1 in container runtime, loading is refused.

## Run the ratchet guard

```powershell
.venv\Scripts\python.exe -m pytest tests\guardrails\credential_default_ratchet -q -s
```

Expected: one line that starts with `credential-default-scan files=` and ends with `parse_failures=0 candidates=`. The guard passes against the baseline.

## Run the batch 1 checks

```powershell
.venv\Scripts\python.exe -m pytest tests\unit\test_standalone.py tests\unit\db_discovery\test_config.py tests\unit\upgrade_portal\test_config.py -q
.venv\Scripts\python.exe -m pytest tests\integration --collect-only -q
```

## Run the batch 2 checks

```powershell
.venv\Scripts\python.exe -m pytest tests\unit\test_credential_preflight.py -q
.venv\Scripts\python.exe -m pytest tests\unit\websocket\test_manager.py tests\unit\device\test_arp_command_manager.py tests\unit\test_routing_utils.py -q
```

## Run the backend token checks

Run these checks after T012 is decided and changed.

```powershell
mist-ops-platform\.venv\Scripts\python.exe -m pytest mist-ops-platform\tests\unit\mist\token_resolution -q
```

## Run the exception and compose guards

```powershell
.venv\Scripts\python.exe -m pytest tests\guardrails\test_blind_exception_handler_ratchet.py tests\guardrails\test_compose_database_settings.py tests\guardrails\test_changelog_fragment_policy.py -q
```

## Compile the changed entry points

```powershell
.venv\Scripts\python.exe -m py_compile MistHelper.py src\foundation\persistence\db\__init__.py
```

## Run the local gates for the changed files

Run each applicable row of the local gates table in `.github/copilot-instructions.md` lines 57 to 76. Read `MYPY_PATHS` from `.github/workflows/ci.yml` before the type check. Run the test quality procedure in lines 95 to 150 exactly as written.

## Manual prompt check for batch 2

Start the command-line entry point from a terminal with no token variables. Record where the prompt appears in the pull request. Press Ctrl+C at the prompt and record the exit status.

## Containers

Do not start a container for this record. When D-7 is decided, follow the container guide in `documentation/container-deployment.md`, section "Test and debug containers", line 141.

## Cleanup

Remove any test evidence that a run writes under `test-artifacts/`. Git ignores that folder.
