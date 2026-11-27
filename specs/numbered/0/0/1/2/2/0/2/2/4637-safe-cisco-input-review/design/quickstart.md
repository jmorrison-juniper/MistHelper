# Quickstart: Safe Cisco Input and Structured Review

Use this guide to reproduce the current behavior and to verify this change. Run the commands in the repository worktree after issue 4636 merges and after task T004 completes. The drafting pass ran none of these commands.

## Prerequisites

Create the worktree environment as `.github/copilot-instructions.md` describes in section Language and environment.

```powershell
uv python install 3.15.2
uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py
.venv\Scripts\Activate.ps1
```

Confirm that the intake module exists before task T004 starts. It is `src\interfaces\portals\cisco_config_converter\state\intake.py`. Task T001 checks the same path.

## Reproduce the current DNS behavior

```powershell
python -m pytest tests/integration/web_portal/cisco_config_converter/test_routes.py tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py -q
```

Expected result: every test passes. This is task T002.

## Reproduce the file-name gap (defect E-01)

Run this command before task T007. The module path is `models` before task T004. It is `state.intake.source` after task T004.

```powershell
python -c "print(__import__('src.interfaces.portals.cisco_config_converter.models', fromlist=['SourceConfiguration']).SourceConfiguration.read('a\x00.cfg', b'ip name-server 192.0.2.1', 'Branch', 'spoke').name)"
```

Expected result before task T007: the command prints `Branch`. The file name holds a null character, and the code accepts it.

Expected result after task T007: the command raises `ValueError`. The message refuses control characters in a file name.

## Verify the byte limit

```powershell
python -m pytest tests/integration/web_portal/cisco_config_converter/input/test_input_contract.py -q -k "exact_size_limit or extra_byte"
```

Expected result: two tests pass. Together they prove success SC-001.

## Verify the stored-input and route behavior

```powershell
python -m pytest tests/integration/web_portal/cisco_config_converter/input -q
```

Expected result: 38 tests pass in the four input modules.

## Verify the zero-call rule

```powershell
python -m pytest tests/integration/web_portal/cisco_config_converter/input/test_observations.py -q -k "socket or cloud"
```

Expected result: the tests pass. The run records zero socket attempts and zero Mist calls.

## Verify the browser journey

```powershell
$env:UPGRADE_PORTAL_E2E_STRICT = "1"
python -m pytest tests/e2e/web_portal/test_portal_smoke.py -k Cisco -q
```

Expected result: the existing Cisco tests and the two new functions pass. The strict variable turns a missing browser package into a failure, not a skip.

## Verify the shared files are unchanged

```powershell
git diff --name-only origin/main -- web_portal/app.py web_portal/templates/base.html
```

Expected result: the command prints nothing.

## Verify that Git ignores the stored folder

```powershell
git check-ignore -v data/cisco_config_converter/input/example.cfg
```

Expected result: the command names the `data/` rule in `.gitignore` at line 95.

## Clean up

Test runs write only to `tmp_path` folders. Check that no product folder exists after the tests.

```powershell
Test-Path data\cisco_config_converter
```

Expected result: `False`. Production retention stays disabled, so the folder should not exist.

Warning: Removing `data\cisco_config_converter` deletes every stored input in it. Confirm that no stored input is needed before you remove the folder.

## Gates

Run each command in the applicable gate list of `tasks.md`, task T-LOCAL-GATES. Record each exact result in the pull request body.
