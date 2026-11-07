# Validation Guide

## Current Documentation Workflow

Use this isolated worktree only.
Do not open another converter implementation worktree.
Do not run commit, push, issue-state, pull-request, deployment, or cloud-write commands for this assignment.

Set the explicit record path in the shell:

```bash
FEATURE=specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity
export SPECIFY_FEATURE_DIRECTORY="$FEATURE"
```

The tracked `.specify/feature.json` is not required to select this record.
Use the loaded specify, plan, tasks, and analyze skills with this explicit path.
No scope clarification is needed. The specification records the remaining safe assumptions.
Do not execute Git hooks. Companion hooks are disabled.

PowerShell allocation and setup could not run because `pwsh` is absent.
The managed route was independently calculated and checked against the resolver's algorithm.
Do not claim that `create-new-feature.ps1`, `setup-plan.ps1`, or prerequisite scripts passed.
Use the core template contents inspected in this worktree.

The missing worktree tools were restored with:

```bash
python3 scripts/bootstrap_worktree.py
```

Result: locked dependency sync completed and the environment became ready.
The bootstrap removed zero orphaned source directories.
No tracked application file changed.

## Current Baseline Evidence

These commands test the delivered DNS component, not the future full-parity implementation:

```bash
.venv/bin/python -m pytest -q tests/unit/gateway/overrides/test_cisco_config_converter.py tests/integration/web_portal/cisco_config_converter/test_routes.py
.venv/bin/python -m pytest -q tests/e2e/web_portal/test_portal_smoke.py
```

Results: 43 tests passed in the first command. Twenty tests passed in the second command.
The converter browser tests use an isolated blueprint host.
They do not establish shared portal registration.
Existing pytest deprecation warnings remain unchanged.

The source README, guides, route list, and test categories were inspected through read-only GitHub queries.
The source application and source tests were not executed.
Installed SDK signatures were inspected without creating a cloud session.
Initial incorrect method/module candidates were corrected in [the cloud contract](contracts/mist.md).

## Documentation Gates

Run the existing STE and local-link validators on the new record:

```bash
find "$FEATURE" -name '*.md' -print0 | xargs -0 .venv/bin/ste-linter --config .ste-linter.toml --min-score 80 --quiet
.venv/bin/markdown-link-check --root . "$FEATURE"
```

Verify that the STE command examines every Markdown file.
The link checker may select tracked files only.
If it examines zero new files, use an independent read-only local-link check and record the examined count.
Do not stage files merely to make the checker discover them.

Check all 32 requirement IDs, 40 comparison rows, and remaining task references.
Require unique task IDs, valid dependencies, no cycles, and zero checked future tasks.
Check every new directory against the five-child bound.
Validate extension YAML and core template selection.
Use `git status --short` and `git diff --name-only` to verify the file boundary.
Record actual command output in [analysis](../analysis.md).

The session-local read-only audit is:

```bash
.venv/bin/python /Users/jmorrison/.copilot/session-state/94c60aae-a5ae-4559-b743-6c928d7848aa/files/cisco_spec_audit.py
```

Result: ten documents, 13 local links, 32 requirements, 40 comparison rows, and 33 unchecked tasks passed.
All dependency references were valid and the graph had zero cycles.
The audit also verified bounded directories, core templates, parsed hooks, and the documentation-only file boundary.
This audit file is session evidence, not a product file or a portable repository gate.

## Future End-to-End Acceptance

These checks require later implementation authorization and the planned test files.
They were not run during specification.

1. Run original input, parser, mapping, proposal, discovery, apply, backup, administration, and recovery tests with simulated responses.
2. Run each coverage row's positive, negative, and unsupported decision checks.
3. Run browser journeys through the real portal factory with no live credentials.
4. Verify all role/family combinations, configured themes, keyboard input, and desktop/narrow layouts.
5. Obtain legal, API, integration-owner, and cloud-owner decisions before release or cloud use.

Use the existing local gates from `.github/copilot-instructions.md` for the files later changed.
Run unit, contract, integration, and browser tests before claiming full parity.
Store future failure screenshots or traces under `test-artifacts/`.
Do not use source screenshots as comparison assets.
Do not use live credentials or cloud writes in automated tests.
No manual production test is authorized by this guide.

## Visual Evidence Plan

Use the supplied pink and charcoal theme, centered file card, structured review, and proposal and confirmation flow as design facts.
Compare each journey with the target counterpart in [the visual matrix](research.md#visual-journey-comparison).
Use original synthetic inputs and independently authored target screens.
Optional fresh captures must show only an offline target with simulated services and synthetic data.
Do not capture a live-connected portal or reuse source screenshots, assets, templates, prose, or styles.
Record viewport, target revision, theme, journey state, keyboard behavior, and owner decision for each permissible capture.
The owner must accept each journey and its missing or unsupported states.
No capture or visual approval was obtained in this discovery pass.
