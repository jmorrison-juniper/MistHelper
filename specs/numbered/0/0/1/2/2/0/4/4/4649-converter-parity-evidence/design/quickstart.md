# Quickstart: Reproduce the Parity Evidence Gate

## Prerequisites

- Windows PowerShell or PowerShell 7 in the repository root.
- The GitHub CLI (`gh`), authenticated for the repository owner.
- The repository virtual environment at `.venv` for the Python commands.

## Step 1: Confirm the route

Read the base-5 digits of 4649 by repeated division.

```powershell
$value = 4649
$digits = @()
while ($value -gt 0) {
    $remainder = $value % 5
    $digits = @($remainder) + $digits
    $value = [math]::Floor($value / 5)
}
$digits -join ''
```

Expected output: `122044`. Padded to eight digits, the route is `0\0\1\2\2\0\4\4`.

## Step 2: Read the prerequisite issue states

Run these read-only commands.

```powershell
gh issue view 4635 -R jmorrison-juniper/MistHelper --json number,state,title
gh issue view 4648 -R jmorrison-juniper/MistHelper --json number,state,title
gh issue view 4649 -R jmorrison-juniper/MistHelper --json number,state,title
```

Expected at observation time: each issue reports `OPEN`. Issue #4635 is the legal prerequisite. Issue #4648 is the shared-portal prerequisite.

## Step 3: Read the main tree for the parity record

```powershell
$tree = gh api "repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1" | ConvertFrom-Json
$tree.truncated
$tree.tree | Where-Object { $_.path.StartsWith('specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/') } | ForEach-Object { $_.sha + ' ' + $_.path }
```

Expected output: `truncated` is `False`. The list shows the ten parity files. Their blob SHAs match checks R01 to R11 in `design/research.md`.

## Step 4: Decode one remote file and read a line

```powershell
$content = gh api "repos/jmorrison-juniper/MistHelper/contents/specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/spec.md?ref=main" --jq .content
$text = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String(($content -replace '\s', '')))
$lines = $text -split "`n"
$lines[6]
```

Expected output: the status line that starts with `**Status**: Specified.` This line is check R01.

## Step 5: Run the STE gate on each record file

Run the gate once for each Markdown file in the record folder.

```powershell
.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 specs\numbered\0\0\1\2\2\0\4\4\4649-converter-parity-evidence\spec.md
```

Repeat the command for each other Markdown file in the record folder, including the contracts and checklists.

Expected result: exit code 0 and a score of 80 or above for each file.

## Step 6: Run the structure guard

```powershell
python -m pytest tests/guardrails/test_process_folder_structure.py
```

Expected result: every test in the file passes.

## Step 7: Run the register audit after task T008

```powershell
python -m pytest tests/integration/web_portal/cisco_config_converter/evidence/test_register_audit.py
```

Expected result: the 13 tests pass when the audit package exists and reads the register. Before task T005, the completion test passes only when it expects a refusal.

## Expected Results Summary

| Step | Expected result |
| --- | --- |
| 1 | `122044`, which gives the route `0\0\1\2\2\0\4\4` |
| 2 | Issues #4635, #4648, and #4649 are `OPEN` |
| 3 | `truncated` is `False`. Ten parity files with the recorded blob SHAs |
| 4 | Line 7 of the parity `spec.md` is the status line |
| 5 | Exit code 0 and a score of 80 or above for each Markdown file |
| 6 | The structure guard passes |
| 7 | The 13 audit tests pass after the register refresh |

## Failure Meanings

- A different blob SHA in step 3 means that main changed. Refresh checks R01 to R11 before any edit.
- A different line in step 4 means that the line citation is stale. Correct the citation and repeat the check.
- A score below 80 in step 5 means that the prose fails the STE gate. Repair the prose and run the gate again. Do not lower the threshold.
