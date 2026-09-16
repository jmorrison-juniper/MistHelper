<!-- site-read-handoff:05-quickstart-and-tools -->
# Artifact 05: quickstart.md and implementer tool guide

## Start here

This issue is the complete handoff. Read its body and every numbered artifact comment. Each endpoint packet adds exact data to the shared specification and contracts. Reading the body alone is insufficient.

Use `rtk proxy gh issue view 2339 --repo jmorrison-juniper/MistHelper --comments` to read the thread. For complete machine-readable pagination, use `rtk proxy gh api repos/jmorrison-juniper/MistHelper/issues/2339/comments --paginate --jq '.[] | .body'`.

Do not execute implementation merely because this issue exists. Start only after the user assigns implementation to you.

## Preflight after authorization

1. Run `rtk proxy gh api user --jq .login`. Require `jmorrison-juniper`.
2. If the account differs, inspect `gh auth status` without exposing tokens. Use `rtk proxy gh auth switch --hostname github.com --user jmorrison-juniper` only if that account is available. A token environment override can defeat account switching. Ask the user to handle a secret directly, never through chat.
3. Read `agents.md`, `.github/copilot-instructions.md`, `.github/instructions/git-flow-multi-agent.instructions.md`, and `.specify/memory/constitution.md`.
4. Read issue #2295 and current agent claims. Recheck all twenty issue states. Do not assume this planning pass reserves the work.
5. Run `rtk proxy gh pr list --repo jmorrison-juniper/MistHelper --state open --json number,headRefName,files`. Inspect file overlap. If a PR owns `MistHelper.py` or another planned file, wait or coordinate.
6. Claim this handoff issue with assignment to the actual implementer and the `in-progress` label. State the planned file set. Do not assign Copilot automatically or start another model without the user's instruction.
7. Run `rtk proxy git status --short` and `rtk proxy git fetch origin main` from the main checkout. Leave existing untracked files alone.
8. Create an isolated worktree with `rtk proxy git worktree add ../MistHelper-2339-site-read -b feat/2339-site-read-exports origin/main`.
9. Change to that worktree. Do not run `git checkout` in the shared checkout.
10. Run `rtk proxy py -3.13 scripts/bootstrap_worktree.py` on Windows. The new worktree needs its own `.venv`.
11. Run `rtk proxy .venv\Scripts\python.exe -c "import sys, mistapi, requests, simplejson; print(sys.executable); print(mistapi.__file__)"`. Both paths must belong to the worktree environment.
12. If imports fail, stop. Record the environment failure. Do not delete or reinstall the user's main `.venv`, kill editor processes, change global packages, or weaken tests.

The planning checkout had a broken `simplejson` import. The source-level SDK probe passed, but it did not repair that environment. Do not confuse those two facts.

## Secret and test isolation

Do not copy the user's real `.env` into the test worktree. If a root `.env` is required, create a placeholder-only file from `deploy/.env.example` with the file editor. Do not commit it. Add no new environment variable for this feature.

Ensure test subprocesses do not inherit live Mist tokens. Do not print environment values. Use fake session methods for endpoint tests and temporary paths for file tests. Use recording database clients, not the workstation's ArangoDB or Redis containers.

Read `tests/conftest.py` before running tests. It preloads `MistHelper.py` during collection, before its temporary-directory fixture executes. The fixture alone does not prove that import-time environment loading is isolated. Do not bypass its environment guard.

Do not run `python MistHelper.py --test`, `--testinteractive`, or a real `--menu` command as the first verification step. Those are not substitutes for offline unit tests.

## Materialize the SpecKit artifacts

Use real file-edit actions in your own worktree. A chat description is not a file edit.

Create `specs/2339-site-read-exports/`. Put each section in its named file:

- Artifact 01 becomes `spec.md`.
- Artifact 02 becomes `research.md`. Copy its resolved decisions into the clarification section of `spec.md`.
- The `data-model.md` section of Artifact 03 becomes `data-model.md`.
- The `contracts/export.md` section of Artifact 03 becomes `contracts/export.md`.
- Artifact 04 becomes `plan.md`.
- Artifact 05 becomes `quickstart.md`.
- Artifact 06 becomes `tasks.md`. Insert the packet tasks at the specified point, in packet order.
- Artifact 07 becomes `checklists/requirements.md` and `analysis.md` at its section boundary.
- Each endpoint packet becomes `contracts/endpoints/ISSUE_NUMBER.md`, using the actual source issue number from its header.

The shared artifacts plus each packet are the complete specification. Do not regenerate generic boilerplate over them. Do not re-run the old endpoint catalog generator, which derived incorrect SDK module paths.

Set `.specify/feature.json` in your worktree to a JSON object whose `feature_directory` is `specs/2339-site-read-exports`. Alternatively set `$env:SPECIFY_FEATURE_DIRECTORY` to that path in this worktree's terminal. The actual resolver is `.specify/scripts/powershell/common.ps1:Get-FeaturePathsEnv`.

Run `& .\.specify\scripts\powershell\check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks` in the existing PowerShell terminal. RTK does not execute PowerShell functions or scripts directly, so this shell-native invocation is intentional. Confirm that the returned feature directory is this handoff, not an unrelated active spec.

Read `.specify/extensions.yml` before any slash command. It enables a mandatory branch hook before `speckit.specify` and optional commit hooks around later phases. Do not invoke `speckit.companion.auto`, `speckit.taskstoissues`, or a git hook on the shared checkout. Do not change the repository's global hook configuration to avoid reading it.

The planning stages already have completed content here. After materialization, use `speckit.analyze` in read-only mode, decline optional commit hooks, and resolve new critical findings before implementation. Then, and only after user authorization, use `speckit.implement` against this feature directory. Never mark `currentStep=implement` or `status=implemented` during planning.

## Tool guide for the implementer

| Need | Tool or command | Exact discipline |
| --- | --- | --- |
| Read an issue or comments | GitHub CLI `gh issue view` or `gh api` | Use the explicit repository and `jmorrison-juniper`. Paginate comments. |
| Find a source symbol | VS Code text search, or `rtk proxy git grep -n SYMBOL -- src tests` | Search the exact operationId and actual symbol names. Do not trust old line numbers. |
| Read a file | VS Code file reader | Read the relevant full function and its imports before changing it. Use absolute local paths in editor actions. |
| Change a file | VS Code patch/file-edit actions | Apply the edit, wait for success, then reread it. Do not merely narrate changes. Do not use terminal rewriting scripts for source edits. |
| Verify Python symbols | Pylance definitions, references, signature checks, and diagnostics when available | Load deferred capabilities before invoking them. Validate changed writer helper signatures at their real call sites. |
| Verify library behavior | Installed SDK source, `inspect.signature`, official documentation through the documentation tools | Resolve modules from actual definitions. Never infer `.derived` or `.stats.foo` submodules from URL paths. |
| Debug a test | Existing debugger/Pylance debug capability | Inspect values and the failing branch. Do not add temporary production prints. |
| Run tests or checks | Persistent PowerShell terminal with `rtk proxy .venv\Scripts\python.exe ...` | Use synchronous commands. Read the exit code. Do not poll, sleep, or use a global Python fallback. |
| Inspect local diagnostics | VS Code Problems diagnostics | Check every changed file after editing. Do not suppress legitimate findings. |

If an external tool is unavailable, use the listed local alternative. If the alternative cannot establish the fact, stop and state the missing fact. Do not fabricate a successful tool result.

## Focused verification after each implementation increment

Run from the new worktree root with its interpreter:

- `rtk proxy .venv\Scripts\python.exe -m pytest tests/unit/export/site_read/ -q --timeout=120`.
- `rtk proxy .venv\Scripts\python.exe -m pytest tests/unit/test_arango_writer.py tests/unit/test_redis_writer.py tests/unit/security/test_credential_redaction.py tests/unit/refactors/test_sqlite_database_writer.py -q --timeout=120`.
- `rtk proxy .venv\Scripts\python.exe -m pytest tests/guardrails/test_operation_registry_menu_coverage.py tests/unit/test_operation_registry_fail_closed.py tests/unit/test_no_new_legacy_facade_imports.py -q --timeout=120`.
- `rtk proxy .venv\Scripts\python.exe -m pytest tests/unit/export/site_read/ --cov=src/export/site_read --cov-branch --cov-fail-under=90 --timeout=120`.

An expected red test before implementation proves the missing behavior. Record it. An unexpected failure is not permission to weaken the assertion. Fix only the assigned cause, or file a separate issue and stop at the boundary.

## Full local quality gates before a PR

Read `.github/workflows/ci.yml` again. The workflow, not stale prose in the PR template, defines the gate scopes.

1. Syntax: `rtk proxy .venv\Scripts\python.exe -m py_compile MistHelper.py`, followed by every changed Python file.
2. Lint: `rtk proxy .venv\Scripts\python.exe -m ruff check .`.
3. Format: `rtk proxy .venv\Scripts\python.exe -m black --check --diff .`.
4. Types: `rtk proxy .venv\Scripts\python.exe -m mypy src/ MistHelper.py wsgi.py --config-file pyproject.toml`. Re-read `MYPY_PATHS` if CI changes.
5. Tests: In an isolated test environment, run the root CI command `rtk proxy .venv\Scripts\python.exe -m pytest --cov=src/ --cov-fail-under=80 --timeout=120`. E2E services must be disposable. A skipped service-dependent check remains unverified.
6. Security: `rtk proxy .venv\Scripts\python.exe -m bandit -c pyproject.toml -r .` and `rtk proxy .venv\Scripts\python.exe -m pip_audit -r requirements.txt`.
7. Pylint: `rtk proxy .venv\Scripts\python.exe -m pylint src/ --fail-under=9.5`. Set `PYTHONIOENCODING=utf-8` if the Windows console cannot print an existing Unicode message.
8. Complexity: Run `radon cc` against the workflow's `RADON_PATHS`, then its JSON threshold check. The current paths are `src/ MistHelper.py wsgi.py starlink_dashboard.py`. The display command alone is not a gate. Fail on any block above 10.
9. Dead code: `rtk proxy .venv\Scripts\python.exe -m vulture src/ MistHelper.py wsgi.py starlink_dashboard.py web_portal --min-confidence 70`.
10. Docstrings: `rtk proxy .venv\Scripts\python.exe -m pydocstyle src/ wsgi.py web_portal` and `rtk proxy .venv\Scripts\python.exe -m interrogate src/ MistHelper.py wsgi.py wsgi_capture.py starlink_dashboard.py web_portal tools --fail-under=90 -v`.
11. References: `rtk proxy .venv\Scripts\python.exe scripts/lint_diagram_refs.py` and `rtk proxy .venv\Scripts\python.exe -m tools.check_citations src tests`.
12. Writing: `rtk proxy .venv\Scripts\python.exe -m tools.ste_linter --min-score 80` followed by each changed Markdown and Python file.
13. Menu docs: Run `rtk proxy .venv\Scripts\python.exe scripts/generate_menu_wiki.py`. Review both generated files. Run it again and require no second change.
14. Sweep guard: If you perform an automated source sweep, run `rtk proxy .venv\Scripts\python.exe -m tools.symbol_diff --base origin/main` followed by each changed source file. Do not treat a comment sweep as harmless.

Run unaffected subproject gates if the full required workflow demands them. Do not claim npm or ops-platform tests passed merely because this feature changes root Python files. Report unrelated blockers with their exact commands and counts.

## Mocked manual journey

Use the existing test harness to invoke the actual new menu callable with a fake runtime. Select #1313's catalog entry and a deterministic fake site. Assert that the primary output contains both paginated rows. Repeat with EOF, then with a later-page 403. Assert no output on either failure path.

A real Mist smoke test is optional and requires separate permission, a read-only token, and an explicitly selected test site. Do not upgrade, reboot, run `--testinteractive` broadly, or use production containers to demonstrate a read export.

## Delivery boundary

Read `.github/PULL_REQUEST_TEMPLATE.md` before creating the PR. Complete applicable checkboxes with real evidence. Explain nonapplicable web UI and environment changes instead of falsely ticking them.

Use Conventional Commits and one focused PR against `main`. Reference this handoff and the twenty source issues. Add closing keywords only for endpoints whose acceptance checks pass. Do not close #1807 or #991 with this limited batch. Wait for required checks, including CodeQL, before adding `auto-merge`.

Do not push solely to obtain a test log. Do not deploy, remove containers, change volume permissions, or delete worktrees belonging to another agent.
