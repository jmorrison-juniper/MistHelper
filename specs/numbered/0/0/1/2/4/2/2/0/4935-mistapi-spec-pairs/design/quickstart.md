# Quickstart: Check Every Operation Pair in the mistapi Spec Guard

Run each command from the root of the worktree. Use PowerShell. Each expected result follows its command.

## Prerequisites

1. Create the worktree from `main` for the branch `fix/4935-mistapi-spec-pairs`:

```powershell
git worktree add ..\MistHelper-fix-4935 -b fix/4935-mistapi-spec-pairs main
```

2. Prepare the Python environment in the worktree. The repository instructions name these commands:

```powershell
uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py
```

```powershell
.venv\Scripts\Activate.ps1
```

3. Confirm that the installed SDK is version 0.64.1:

```powershell
Get-ChildItem -LiteralPath ".venv\Lib\site-packages" -Filter "mistapi-*.dist-info" -Name
```

Expected result: `mistapi-0.64.1.dist-info`

## Scenario 1: Reproduce the defect on main

1. Count the operation lines in the spec file of issue 4934:

```powershell
Select-String -LiteralPath "specs\numbered\0\0\1\2\4\2\1\4\4934-mist-netcool-runbook\spec.md" -Pattern '^- \*\*operationId\*\*: `'
```

Expected result: 25 lines, from line 461 to line 557.

2. Run the guard before the change:

```powershell
python -m pytest tests/guardrails/test_mistapi_spec_modules.py -q
```

Expected result: The test passes. The old helper checks one pair for each file, so the defect is silent.

## Scenario 2: Run the guard after the change

```powershell
python -m pytest tests/guardrails/test_mistapi_spec_modules.py -q -s -k declared_sdk
```

Expected result: The output contains the line `mistapi spec module guard: examined 489 operation pairs, 0 defects.`

## Scenario 3: Prove that the wrong-first-pair fixture fails on the old logic

1. Run the fixture test on the new code:

```powershell
python -m pytest tests/guardrails/test_mistapi_spec_modules.py -q -k wrong_first_pair
```

Expected result: 1 passed.

2. In the worktree only, change `_source_fields` so that it returns only its last pair, as the old helper does. Run the same command again.

Expected result: 1 failed.

3. Caution: revert the temporary change before you commit. Run the same command again.

Expected result: 1 passed.

## Scenario 4: Check the declared absences

```powershell
python -m pytest tests/guardrails/test_mistapi_spec_modules.py -q -k declared_absence
```

Expected result: All selected tests pass.

## Scenario 5: Check the spec file 511 module line

```powershell
Select-String -LiteralPath "specs\511-mist-count-org-client-fingerprints\spec.md" -Pattern '^- \*\*mistapi SDK module\*\*: `mistapi\.api\.v1\.orgs\.insights`$'
```

Expected result: One line, at line 14.

## Scenario 6: Confirm the SDK facts

```powershell
Select-String -LiteralPath ".venv\Lib\site-packages\mistapi\api\v1\orgs\insights.py" -Pattern '^def countOrgClientFingerprints\('
```

Expected result: One line, at line 17.

```powershell
Select-String -LiteralPath ".venv\Lib\site-packages\mistapi\api\v1\orgs\ssr.py" -Pattern '^def getOrg128TRegistrationCommands\('
```

Expected result: No output. The SDK lacks the function.

## Scenario 7: Check the record for guard prefixes

After task T-PR moves the record folder into the route, run this command:

```powershell
Select-String -LiteralPath "specs\numbered\0\0\1\2\4\2\2\0\4935-mistapi-spec-pairs\spec.md" -Pattern '^- \*\*(operationId|mistapi SDK module)\*\*: `'
```

Expected result: No output.

## Scenario 8: Run the local gates

Run the gates in task T-LOCAL-GATES of `tasks.md`, in the order that the task lists. Record each command and its result in the pull request body.
