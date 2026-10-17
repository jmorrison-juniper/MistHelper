# Quickstart Validation: MistDSW

## Current Planning Documents

These commands validate planning only.
Run them from the MistHelper worktree, not the main checkout.
If dependencies are missing, run `python3 scripts/bootstrap_worktree.py`.
Activate the worktree environment with `source .venv/bin/activate`.
On Windows, use `.venv\Scripts\Activate.ps1`.

Set the feature path:

```bash
FEATURE=specs/numbered/0/0/1/1/3/4/1/0/4230-mistdsw-migration
```

Run the documentation gates:

```bash
ste-linter --config .ste-linter.toml --min-score 80 "$FEATURE"/*.md "$FEATURE"/design/*.md "$FEATURE"/design/contracts/*.md "$FEATURE"/design/checklists/*.md
markdown-link-check --root . "$FEATURE"
python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/test_process_folder_structure.py tests/guardrails/test_spec_route_contract.py
git diff --check
```

STE must score every document at 80 or above.
The link check must report zero broken local targets.
The guards must report measured counts and pass their negative cases.
Inspect the changed-file list. It must contain only this feature's Markdown documents.
Check all 18 FR identifiers, eight SC identifiers, three stories, and 27 task identifiers for coverage.
No future task may be checked as implemented.

PowerShell is unavailable on the planning host.
The plan, checklist, and task setup scripts therefore cannot run here.
The equivalent direct workflow reads the resolved core templates, constitution, feature pointer, and artifact prerequisites.
No override or preset template was present.
The application-managed branch replaces the branch-creation hook's raw Git action.
Optional commit hooks are deferred until the complete artifact set passes validation.
The feature pointer is temporary and restored before commit.

The `speckit-task-audit --root` CLI expects a repository containing a direct `specs/` directory.
It does not discover this managed nested feature when given the feature directory.
Use the shared scanner and citation validator directly for this planning record:

```bash
python -c "from pathlib import Path; from misthelper_devtools.speckit_task_audit import TaskFileScanner, CitationValidator; p=Path('specs/numbered/0/0/1/1/3/4/1/0/4230-mistdsw-migration/tasks.md'); c=TaskFileScanner().scan(p); e=CitationValidator(Path('.')).find_errors(p); print(f'Task audit: 1 file, checked={c.checked}, unchecked={c.unchecked}, malformed={c.malformed}, invalid_citations={len(e)}'); raise SystemExit(0 if c.checked==0 and c.unchecked==27 and c.malformed==0 and not e else 1)"
```

Expected counts are zero checked tasks, 27 unchecked tasks, zero malformed boxes, and zero invalid citations.

## Future Implementation Validation

These tests do not exist in this planning PR.
Run them only after authorized implementation supplies the referenced files.

```bash
python -m pytest tests/unit/mistdsw tests/contract/mistdsw tests/integration/mistdsw
python -m pytest tests/e2e/web_portal/mistdsw
python -m pytest tests/unit/mistdsw tests/contract/mistdsw tests/integration/mistdsw --cov=src.operations.execution.configuration.mistdsw --cov-fail-under=80
python -m py_compile MistHelper.py
python -m ruff check MistHelper.py src/operations/execution/configuration/mistdsw tests/unit/mistdsw tests/contract/mistdsw tests/integration/mistdsw tests/e2e/web_portal/mistdsw
python -m black --check MistHelper.py src/operations/execution/configuration/mistdsw tests/unit/mistdsw tests/contract/mistdsw tests/integration/mistdsw tests/e2e/web_portal/mistdsw
python -m mypy src/operations/execution/configuration/mistdsw --config-file pyproject.toml
radon cc src/operations/execution/configuration/mistdsw -j | complexity-gate --max 10
bandit -c pyproject.toml -r src/operations/execution/configuration/mistdsw -q
```

Run the repository's configured mypy paths, docstring gates, symbol gate, and test-quality procedure before the implementation push.
Read their current selectors from `.github/workflows/ci.yml`.
Do not claim that a planning-only run passed these product gates.
If T002 changes the package root, update these selectors before implementation.

## Future Acceptance Journeys

1. Prepare two synthetic named stores and explicit gateways. Compare all CSV rows against the approved profile.
2. Submit a nonaligned address. Review its normalized `/22`, acknowledge it, and verify four consecutive `/24` networks.
3. Submit invalid, duplicate, overlapping, and partial rows. Expect row-specific errors and no ready artifact.
4. Transform synthetic switch and gateway exports. Compare preserved fields, metadata removal, LAN mapping, DHCP, and mixed tenants.
5. Generate networks and services. Expect ten networks, four services, matching references, and no cloud request.

Exercise the current portal on its existing port 8055.
Use labels, keyboard navigation, and stable selectors from the preparation contract.
Do not start a second app or database.
Store failure screenshots and traces under `test-artifacts/`.

Run ownership, secret-canary, expiration, storage-outage, and interrupted-write cases.
Measure 500 stores on a four-core, 8 GB host and record the hardware and elapsed time.
Pass means five seconds or less, excluding transfer.
Treat any unavailable measurement as unverified.

## Deployment Boundary

Manual deployment follows the source guide: site variables, networks, services, switch template, then gateway template.
Warning: manual deployment changes the Mist organization and can disrupt production networks.
The acceptance journeys stop at private downloads.
Do not send generated payloads to Mist during this workflow.
Resolve B1-B4 and obtain explicit implementation authorization before product changes.
