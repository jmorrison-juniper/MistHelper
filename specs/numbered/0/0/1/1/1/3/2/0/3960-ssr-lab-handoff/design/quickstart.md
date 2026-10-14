# Validation Guide: SSR lab runbook validation

## Current Assignment

Create and analyze artifacts only.
Do not connect to an SSR, block connectivity, execute implementation tasks, or create a pull request.
The [observation contract](contracts/lab-evidence.md) defines the later human lab work.

## Local Prerequisites

Run commands from the repository worktree.
Use its bootstrapped `.venv` and PowerShell.
Set `SPECIFY_FEATURE_DIRECTORY` to `specs/numbered/0/0/1/1/1/3/2/0/3960-ssr-lab-handoff`.
The checked-in `.specify/feature.json` selects the same directory.

## Artifact Checks

Run the writing check on each Markdown file in this feature directory:

```text
ste-linter --config .ste-linter.toml --min-score 80 <each-feature-Markdown-file>
```

Run the local link check:

```text
markdown-link-check specs/numbered/0/0/1/1/1/3/2/0/3960-ssr-lab-handoff
```

Run the route guard and prerequisite check:

```text
python -m pytest -q tests/guardrails/test_spec_route_contract.py
pwsh -NoProfile -File .specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireSpec -RequireTasks -IncludeTasks
git diff --check
```

The expected results are writing scores of at least 80, zero broken local links, passing route tests, and all three core artifacts present.
If link discovery excludes untracked files, stage only the explicit artifact manifest before the link check.
Confirm twelve functional requirements map to tasks and all six physical observations remain unchecked.
Confirm the feature root has five children and no design directory has more than five.
These checks do not prove any SSR command result.

## Later Human Lab Validation

The human must supply authorized lab access, the required releases, a fiber port, and an independent console.
Use the [evidence model](data-model.md) and contract for OBS-01 through OBS-06.
Check privacy before recording any output in an issue or the repository.

Review the first four observations as the independent US1 result.
Review detailed Mist-state fields as the independent US2 result.
Review approval, confirmed cloud loss, portal results, and recovery together as the independent US3 result.

An absent field, unexpected command result, non-fiber port, ineffective block, or failed recovery must produce a visible limitation.
Do not mark an observation complete because a command reference describes it.

## Later Publication Checks

After accepted evidence changes the runbook, run STE and `markdown-link-check` on every changed Markdown file.
Review section 11, step C2, the fallback optic procedure, step D7, the cloud-path conclusion, and all six verification rows.
Use the repository pull request template and applicable publication gates only after separate authorization to implement.
The current assignment performs none of those publication actions.
