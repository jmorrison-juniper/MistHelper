# Quickstart: SpecKit Task Audit Link and Legend Classification

**Date**: 2026-11-26

This guide gives the exact commands for issue 4703. Each `gh` command runs read-only. Run the commands from the repository root unless a step says otherwise.

## Prerequisites

- PowerShell 7 on Windows 11, with the GitHub CLI installed.
- Read access to `jmorrison-juniper/MistHelper` and `jmorrison-juniper/misthelper-devtools`.
- The Python environment in `.venv` for the local gates in QS-07.

Warning: Do not print the value of a token variable. A printed token cannot be recalled.

## Account setup for each gh command

Run these two lines before each `gh` command in a new shell. The lines set the account from an existing variable. They print no value.

```powershell
$env:GH_HOST = 'github.com'
$env:GH_TOKEN = $env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
```

## QS-01. Read the issue facts

```powershell
gh issue view 4703 -R jmorrison-juniper/MistHelper --json number,title,state,labels,updatedAt
```

Expected: state `OPEN`, labels `bug`, `ci`, and `in-progress`.

## QS-02. Verify the devtools pin on main

```powershell
$json = gh api 'repos/jmorrison-juniper/MistHelper/contents/requirements-dev.txt?ref=main' --jq '.content'
$text = [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String(($json -replace '\s', '')))
$text -split "`n" | Select-Object -Index 196
```

Expected: `misthelper-devtools @ git+https://github.com/jmorrison-juniper/misthelper-devtools.git@2239e7bd468fd27e40c43f2b87fcd35a2e49672b` (RC-11).

## QS-03. Reproduce the defect from the CI log (Mode A)

```powershell
gh run view 42589635262 -R jmorrison-juniper/MistHelper --job 129067813179 --log
```

Expected: the summary line ends with `36 malformed.` The lines `specs/001-mist-ops-platform/tasks.md:363` and `specs/3300-selective-insight-definitions/tasks.md:707` do not appear, because the issue-time report names no file or line.

## QS-04. Read the current audit report on main

```powershell
gh run view 45774119357 -R jmorrison-juniper/MistHelper --job 139753527621 --log
```

Expected: the summary line ends with `0 malformed.`

## QS-05. Reproduce the second failure mode (Mode B)

```powershell
gh run view 45064243269 -R jmorrison-juniper/MistHelper --log-failed
```

Expected: the lines `ERROR: Cannot install -r requirements-dev.txt (line 365) and mando==0.8.2` and `ResolutionImpossible`. The step fails before the audit runs.

## QS-06. Verify the upstream repair is in the pinned history

```powershell
gh api 'repos/jmorrison-juniper/misthelper-devtools/compare/da96d6e57a9bba7c7824f703c7cd722732010655...2239e7bd468fd27e40c43f2b87fcd35a2e49672b' --jq '[.status, .ahead_by, .behind_by] | @tsv'
```

Expected: `ahead` with `2` and `0`.

## QS-07. Run the local gates after the change

Run each command from the repository root. Use the gate map in `plan.md` for the full list and the expected results.

```powershell
python -m ruff check .
python -m black --check .
python -m pytest tests/guardrails/test_process_folder_structure.py -q
python -m pytest tests/guardrails/test_changelog_fragment_policy.py -q
python -m pytest tests/guardrails -q
check-citations src tests
bandit -c pyproject.toml -r .
symbol-diff --base origin/main tests/guardrails/test_process_folder_structure.py
speckit-task-audit
ste-linter --config .ste-linter.toml --min-score 80 documentation/quality-gates.md changelog.d/issue-4703-speckit-audit-markdown-links.md specs/numbered/0/0/1/2/2/3/0/3/4703-speckit-audit-markdown-links/spec.md specs/numbered/0/0/1/2/2/3/0/3/4703-speckit-audit-markdown-links/plan.md specs/numbered/0/0/1/2/2/3/0/3/4703-speckit-audit-markdown-links/tasks.md specs/numbered/0/0/1/2/2/3/0/3/4703-speckit-audit-markdown-links/analysis.md
```

Expected results:

- Ruff prints `All checks passed`.
- Black reports that no file needs a change.
- Each pytest command reports zero failures.
- `symbol-diff` prints `no module-level name changed` and exits with code 0.
- `speckit-task-audit` reports zero malformed markers in the repository.
- `ste-linter` reports a score of 80 or above for each file.

Run the test quality procedure in `.github/copilot-instructions.md`, section Test quality ratchet, on the changed test file. Its gate must report zero new findings.

## QS-08. Confirm the record layout

```powershell
Get-ChildItem -LiteralPath 'specs/numbered/0/0/1/2/2/3/0/3/4703-speckit-audit-markdown-links' -Recurse -File | Select-Object -ExpandProperty FullName
```

Expected: `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, `design/research.md`, `design/data-model.md`, `design/quickstart.md`, `design/contracts/speckit-audit-report.md`, `design/checklists/requirements.md`, and `design/checklists/evidence.md`.
