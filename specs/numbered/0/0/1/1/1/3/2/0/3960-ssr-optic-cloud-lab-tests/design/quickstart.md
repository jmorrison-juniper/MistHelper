# Quickstart: SSR optic and Mist cloud path lab tests

This file gives the exact reproduction steps and the exact verification commands for issue #3960. Run each command on its own line. Do not print the value of any environment variable.

## Prerequisites

- GitHub CLI reads. Set `GH_HOST` to `github.com`. Set `GH_TOKEN` from the account variable `COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper`.
- A checkout of the repository on main for reads. A separate worktree for the implementer's branch.
- The development environment with `.venv\Scripts\ste-linter.exe` and the markdown-link-check command from the misthelper-devtools package.
- For the owner: one lab SSR that runs SSR 7.0.x and one lab SSR that runs SSR 7.1.0-50r1 or later. The owner reaches each console by the owner's own method.

## Reproduction steps

1. Read the issue state (RB-3).
2. Read the section 14 subsection from main (RB-1).
3. Read the open pull requests for file overlap (RB-2).
4. The owner runs each owner-only step in the order that tasks.md gives.
5. The implementer applies the outputs (T012 to T014) and runs the local gates (T-LOCAL-GATES).

## Read-back commands

### RB-1 Read the runbook from main

```powershell
$env:GH_HOST = 'github.com'
$env:GH_TOKEN = $env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
$item = gh api "repos/jmorrison-juniper/MistHelper/contents/documentation/noc-runbooks/SSR_CONSOLE_HEALTH_CHECK.md?ref=main" | ConvertFrom-Json
$item.sha
$lines = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($item.content)) -split "`n"
$lines[346..365]
```

Expected: the blob SHA is 4fe23574f2f66792139b4c84132a85a21f3dda03 before the change. The output shows the subsection and the six rows.

### RB-2 Check open pull requests for file overlap

```powershell
$open = gh pr list --state open --limit 100 --json number,headRefName,files | ConvertFrom-Json
foreach ($pull in $open) {
  foreach ($file in $pull.files) {
    if ($file.path -match 'SSR_CONSOLE_HEALTH_CHECK|issue-3960|verify_ssr_commands') {
      "$($pull.number) $($file.path)"
    }
  }
}
```

Expected: no line. Any line names a pull request that changes a planned file. Stop and coordinate before an edit.

### RB-3 Read the issue state and labels

```powershell
gh issue view 3960 --json state,labels
```

Expected before the claim: the issue is OPEN. After T002: the labels include in-progress.

## Local gate commands (run in the worktree)

### TEST-01 STE gate on the runbook

```powershell
.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 documentation\noc-runbooks\SSR_CONSOLE_HEALTH_CHECK.md
```

Expected: the file scores 80 or above.

### TEST-02 STE gate on the fragment

```powershell
.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 changelog.d\issue-3960-ssr-lab-results.md
```

Expected: the file scores 80 or above.

### TEST-03 Link check on the runbook

```powershell
markdown-link-check documentation\noc-runbooks\SSR_CONSOLE_HEALTH_CHECK.md
```

Expected: no broken link. This record did not confirm the flags of markdown-link-check. Use the flags from the misthelper-devtools package.

### TEST-04 Link check on the fragment

```powershell
markdown-link-check changelog.d\issue-3960-ssr-lab-results.md
```

Expected: no broken link.

### TEST-05 Changelog guard test

```powershell
python -m pytest tests\guardrails\test_changelog_fragment_policy.py
```

Expected: all tests pass. The guard reads a base reference (line 104 of the test file), so fetch origin main in the worktree first.

### TEST-06 Diff scope and sanitization scan

```powershell
git diff --name-only origin/main
$added = git diff --unified=0 origin/main | Where-Object { $_ -match '^\+[^+]' }
$added | Select-String -Pattern '(\d{1,3}\.){3}\d{1,3}|([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}|password|secret|token'
```

Expected: the name list holds only the two planned paths. The scan finds no address except 8.8.8.8 and 1.1.1.1, no MAC address, and no credential word. Review each other match before the commit.

### TEST-07 Count of Not run cells

```powershell
$runbook = Get-Content -LiteralPath 'documentation\noc-runbooks\SSR_CONSOLE_HEALTH_CHECK.md'
$runbook[359..364] | Select-String -Pattern 'Not run'
```

Expected: no output when the final pull request opens. Before that, each line names a row that still waits for an output.

## Owner read-backs for the lab steps

The owner runs each command in the lab. Then the owner reads the target line in the runbook. Line numbers refer to main at blob 4fe23574f2f66792139b4c84132a85a21f3dda03.

### TEST-08 H-1 (line 245, row 360)

Run on SSR 7.0.x:

```text
show device-interface <name> optics-statistics
```

Read back:

```powershell
$runbook = Get-Content -LiteralPath 'documentation\noc-runbooks\SSR_CONSOLE_HEALTH_CHECK.md'
$runbook[244]
$runbook[359]
```

### TEST-09 H-2 (new section 11 row, row 361)

Run on SSR 7.0.x:

```text
show device-interface name <name> optics-statistics
```

Read back:

```powershell
$runbook | Select-String -SimpleMatch -Pattern 'show device-interface name <name> optics-statistics'
$runbook[360]
```

### TEST-10 H-3 (line 117, row 362)

Run on SSR 7.0.x:

```text
show device-interface name <name>
```

Read back:

```powershell
$runbook[116]
$runbook[361]
```

### TEST-11 H-4 (line 104, row 363)

Run on a fiber port on SSR 7.1.0-50r1 or later:

```text
show device-interface name <name> optics-statistics
```

Read back:

```powershell
$runbook[103]
$runbook[362]
```

### TEST-12 H-5 (line 141, row 364)

Run on the lab SSR:

```text
show mist detail
```

Read back:

```powershell
$runbook[140]
$runbook[363]
```

### TEST-13 H-6 (line 166, row 365)

Run on one lab router only. The owner types `BLOCK-443` followed by the lab router name before the block. Block TCP port 443 to the Mist cloud. Test the Testing Tools in the Mist portal. Remove the block rule. Run `show mist detail` again and confirm that Connection reads up.

Read back:

```powershell
$runbook[165]
$runbook[364]
```

### TEST-14 H-7 (line 149)

Read back:

```powershell
$runbook[148]
```

Expected: the line holds a source link, or the sentence no longer appears.

## Remote and post-merge checks

### TEST-15 Remote checks

```powershell
gh pr checks --watch
```

Expected: no required check fails. The auto-merge label is added only after this result.

### TEST-16 Post-merge read-back of main

Run RB-1 again. Expected: the blob SHA differs from 4fe23574f2f66792139b4c84132a85a21f3dda03, and the lines hold the recorded results.

### TEST-17 Claim, overlap, issue state, and closing keyword

```powershell
gh issue view 3960 --json state,labels
gh pr view --json title,body
```

Expected: the issue carries in-progress at T002. RB-2 shows no overlap. The body holds `Refs #3960` until six outputs exist. The body holds `Closes #3960` only after that.

### TEST-18 Record self-review

Read design/checklists/requirements.md and analysis.md. Expected: each FR maps to a task and a test. The remote check count is 69 in design/research.md, in STATUS.json, and in summary.md.

### TEST-19 Local cleanup (owner)

In the worktree folder, run `git status --short`. Expected: the command prints no line. In the main checkout, run `git branch --list agents/kms-optic-health-ping-commands`. Expected: no output after the owner removes the branch.
