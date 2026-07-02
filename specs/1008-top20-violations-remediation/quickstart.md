# Quickstart: Executing One Remediation PR

**Feature**: Top-20 Compliance Violations Remediation
**Audience**: The developer or agent executing a single file's remediation.
**Prerequisite**: The previous rank's PR is already squash-merged to `main` with CI
green. No other refactor PR against any of the twenty target files is currently open.

This runbook reproduces the exact workflow used successfully by PRs #578-#583. Follow
it verbatim.

## Step 0 - Sync main

```powershell
git checkout main
git pull --ff-only
git status  # Expect clean tree.
```

## Step 1 - Capture the baseline analyzer output

```powershell
# Replace <path> with the target file's repo-relative path.
python -m tools.compliance_analyzer <path> > "$env:TEMP\pre_analyzer.txt"
Get-Content "$env:TEMP\pre_analyzer.txt"
```

Confirm the score matches the baseline recorded in `data-model.md` for this rank. If
the baseline has drifted (someone landed changes to this file since 2026-07-02), that
is fine - use the current score as the "before" figure in the PR title. The A+/>=95.0
target does not move.

## Step 2 - Create the refactor branch

```powershell
# Use two-digit rank and kebab-cased basename.
git checkout -b refactor/compliance-<rank>-<slug>
# Example:
# git checkout -b refactor/compliance-01-maps-manager
```

## Step 3 - Refactor the file

Apply the class-of-fix template appropriate to the file's dominant violation
categories. See `research.md` for per-file predictions. Common moves:

- **Decompose functions** >25 LOC or >5 blocks into helpers on a semantically-named
  class. Do not create standalone wrapper functions - move logic onto a class.
- **Reduce complexity**: extract early-return guards; flatten nested `if/elif` into
  dictionary dispatch or `match` when ranges are enumerable.
- **Add inline WHY comments** on every touched line and every adjacent uncommented
  line in the same block (Constitution VI).
- **Add action logging** (`logging.info` before, `logging.debug` after) around
  every meaningful action in a touched function (Constitution VII).
- **Convert f-string log calls to `%` formatting**: `logging.info("x=%d", x)`.
- **Update callsites** in other files if a symbol had to move to a new home. Change
  them to hit the real destination - do not leave a forwarder at the old location.
- **Split the module** if it stays >500 LOC after decomposition AND a natural
  responsibility boundary exists AND the split does not require a wrapper.

Do NOT do any of the following:

- Add `# noqa`, `# type: ignore`, `# pragma: no cover`, `# pylint: disable`,
  `# ruff: noqa`, `# mypy: ignore`, `# flake8: noqa`, or `# nosec`.
- Modify `tools/compliance_analyzer/scoring.py`,
  `tools/compliance_analyzer/models.py`, `tools/compliance_analyzer/analyzers.py`,
  `tools/check_compliance.py`, or related config.
- Change public function signatures, class names, module-level exports, exception
  types raised, CLI flags, or observable side effects.
- Leave a wrapper/delegator/alias/shim at the old location of a moved symbol.

## Step 4 - Local gates

```powershell
# Syntax first (Constitution IV).
python -m py_compile <path>

# Formatting must not regress.
black --check <path>

# Lint must be clean.
ruff check <path>

# Strict types where applicable.
mypy --strict <path>  # Skip only if the file is not currently under strict.

# Compliance analyzer MUST report >=95.0 / A+.
python -m tools.compliance_analyzer <path> > "$env:TEMP\post_analyzer.txt"
Get-Content "$env:TEMP\post_analyzer.txt"
```

If the analyzer reports <95.0 or grade below A+, iterate on the refactor. Do not
proceed to Step 5 until the analyzer is happy.

## Step 5 - Behavior verification

```powershell
# Full unit-test suite must pass.
pytest tests/

# For CLI files (starlink_dashboard.py, scripts/*.py), smoke-test --help.
python <path> --help

# For the codemod (tools/codemod_logging_lazy.py), run the round-trip regression:
#   1. checkout the codemod at main
#   2. run it against a corpus, save output as expected.txt
#   3. checkout the refactored branch
#   4. run the codemod again, save output as actual.txt
#   5. diff expected.txt actual.txt  -- MUST be empty
```

## Step 6 - Commit

```powershell
git add <touched-files>
git status  # Confirm no unrelated files staged.

# Commit message must match the campaign format.
git commit -m "refactor: <file-slug> compliance <old-grade>/<old-score> -> A+/<new-score>"
# Example: 
#   refactor: maps_manager compliance F/54.0 -> A+/100.0
```

## Step 7 - Push and open the PR

```powershell
git push -u origin refactor/compliance-<rank>-<slug>

# Open the PR with pre + post analyzer output in the body.
gh pr create `
  --base main `
  --title "refactor: <file-slug> compliance <old-grade>/<old-score> -> A+/<new-score>" `
  --body @"
## Summary

<one-sentence description of what changed structurally>

## Pre-refactor analyzer output

``````
$(Get-Content $env:TEMP\pre_analyzer.txt)
``````

## Post-refactor analyzer output

``````
$(Get-Content $env:TEMP\post_analyzer.txt)
``````

## Structural change description

- <helpers extracted, e.g., ExtractedProgressReporter class in <new-module>>
- <module boundaries moved, e.g., large data literals moved to _data.py>
- <complexity reductions, e.g., 3 nested if/elif chains flattened to dict dispatch>

Closes #<issue-number-if-any>
"@ `
  --label refactor `
  --label compliance
```

## Step 8 - Wait for all 234+ required CI checks

```powershell
# Watch checks until every one is pass.
gh pr checks <pr-number> --watch

# If any check fails, diagnose. Do NOT mark checks optional or skip. Fix in-branch.
```

## Step 9 - Squash-merge

```powershell
# Only when every required check is pass.
gh pr merge <pr-number> --squash --delete-branch

# Verify main.
git checkout main
git pull --ff-only
python -m tools.compliance_analyzer <path>  # Confirms A+/>=95.0 on merged main.
```

## Step 10 - Update the campaign tracker (optional but recommended)

Add a row to `specs/1008-top20-violations-remediation/tasks.md` (or wherever the
running tracker lives) showing rank, PR number, merge SHA, and final score. This
makes the sequential progression easy to audit.

## Failure modes and recovery

| Symptom | Response |
|---------|----------|
| Analyzer stays <95.0 despite refactor | Iterate. If unresolvable without a wrapper or behavior change, escalate to human review (spec Edge Case). Do not add a suppression. |
| Required CI check fails on unrelated flake | Rerun the specific job. If reproducible on `main`, file an issue and pause the PR until the flake is fixed. Do not mark the check optional. |
| Another file's compliance regresses due to this PR | Do not merge. Fix the collateral regression in the same PR, or split and rework. |
| Merge conflict on `main` | Rebase, re-run local gates, re-push. Analyzer output stays valid as long as no line count / structure changes. |
| The file cannot reach 95.0 without a wrapper | Stop. Document in PR body. Escalate. Defer the file rather than accept the wrapper. |
