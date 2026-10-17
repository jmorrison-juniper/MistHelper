# Validation Guide: Bounded live timestamp records

## Planning Checks

Use the worktree virtual environment.
Set command-scoped selection without writing `.specify/feature.json`.

```bash
export SPECIFY_FEATURE_DIRECTORY=specs/numbered/0/0/1/1/4/0/2/3/4263-spec-live-root-capacity
.venv/bin/python -B -m pytest -p no:cacheprovider -q -s tests/guardrails/test_process_folder_structure.py tests/guardrails/test_spec_route_contract.py
find "$SPECIFY_FEATURE_DIRECTORY" -type f -name '*.md' -print0 | xargs -0 .venv/bin/ste-linter --config .ste-linter.toml --min-score 80
.venv/bin/markdown-link-check --root . "$SPECIFY_FEATURE_DIRECTORY"
git diff --check
```

The process and route tests must pass.
PowerShell must be on PATH for the executable tests.
This session uses verified PowerShell 7.6.7 from its session artifact directory.
An absent executable fails the new contracts rather than providing a successful skip.
The prose score must reach 80 for each artifact.
The link checker must scan all ten planning files and report zero broken links.
Stage the explicit feature paths before the tracked-file link check.

Inspect the complete new directory tree separately.
Verify five children or fewer at every new level.
Verify the numeric route against independent base-5 arithmetic.
Verify unique sequential task IDs and coverage for FR-001 through FR-011.
Verify no changed paths overlap an open PR.

## Future Implementation Checks

Run these only after implementation authorization and owner handovers.
Use isolated temporary trees, not production records, for failure tests.

```bash
.venv/bin/python -B -m pytest -p no:cacheprovider -q -s tests/guardrails/test_process_folder_structure.py tests/guardrails/test_spec_route_contract.py
.venv/bin/speckit-task-audit --verbose
```

Selection and context fixtures reside in the route-contract test file.
The shared task audit must first include the canonical recursive-discovery release.
Run it against isolated fixtures that prove a failing grouped record is detected.
Then run the repository audit and resolve or report unrelated findings without changing their owners' records.

With PowerShell available, inspect each supported selection fixture:

```powershell
$env:SPECIFY_FEATURE_DIRECTORY = "<isolated-feature-directory>"
pwsh -NoProfile -File .specify/scripts/powershell/check-prerequisites.ps1 -Json -PathsOnly
pwsh -NoProfile -File .specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireSpec -RequireTasks -IncludeTasks
```

The second command requires the implementation's non-persisting selection behavior.
Do not run current setup commands against the tracked selector to bypass that requirement.
Test plan setup, task setup, and context generation in isolated fixtures.
Verify returned supporting-artifact paths for both established and bounded layouts.

## Preservation Checks

Compare every moved file against the approved manifest.
Check exact approved reference patches separately from unchanged file hashes.
Verify the inventory contains every original file and no duplicate feature.
Run link checks on every moved record and every changed reference document.
Report actual record, directory, and task counts.

After the process implementation merges, the Redis owner repeats these checks on its rebased PR.
This guide does not authorize another relocation.
