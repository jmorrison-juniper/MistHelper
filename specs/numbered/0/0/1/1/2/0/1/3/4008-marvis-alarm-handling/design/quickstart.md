# Quickstart: Isolate Marvis Alarm Handling Modules

Use these steps to reproduce the starting state, make the move, and run each local gate. Run each command from the root of the new worktree, unless a step names another folder. Keep every command on its own line.

Warning: `git clean` and `git reset --hard` discard the five unrelated edits in the shared checkout. Run neither command there.

## Prerequisites

1. Fetch main and create the worktree (task T001):

   ```powershell
   git fetch origin main
   git worktree add ..\MistHelper-4008 -b chore/4008-marvis-alarm-handling origin/main
   ```

   Expected: the worktree exists, and its `HEAD` equals the `origin/main` commit.

2. Create the environment with the worktree steps from `.github/copilot-instructions.md`:

   ```powershell
   uv python install 3.15.2
   uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py
   .venv\Scripts\Activate.ps1
   ```

   Run `uv pip show mistapi`. Expected: the output contains the line `Version: 0.64.1`.

## Scenario 1: Reproduce the starting state

3. Run the guardrails on the untouched worktree:

   ```powershell
   python -m pytest tests\guardrails -q
   ```

   Keep the list of any failing test names outside the repository. On main, the nested ratchet expects 33 violations and 236 total excess (research R19). Compare the result after the move.

4. List the actions package:

   ```powershell
   Get-ChildItem src\mist\intelligence\marvis\actions -Name
   ```

   Expected before the move: `__init__.py`, `acknowledgement.py`, `alarms.py`, `client.py`, `model.py`, `operation.py`, `selection.py`, and `__pycache__`.

## Scenario 2: Move the modules (tasks T003 and T004)

5. Create the package folder:

   ```powershell
   New-Item -ItemType Directory -Path src\mist\intelligence\marvis\actions\alarm_handling
   ```

6. Move both modules with `git mv`:

   ```powershell
   git mv src\mist\intelligence\marvis\actions\acknowledgement.py src\mist\intelligence\marvis\actions\alarm_handling\acknowledgement.py
   git mv src\mist\intelligence\marvis\actions\alarms.py src\mist\intelligence\marvis\actions\alarm_handling\alarms.py
   ```

7. Create `src\mist\intelligence\marvis\actions\alarm_handling\__init__.py` with one docstring line. Use the create tool. The line reads `"""Join and acknowledge Marvis alarms for menu 270."""`.

8. Verify the blob hashes of the moved files:

   ```powershell
   git hash-object src\mist\intelligence\marvis\actions\alarm_handling\acknowledgement.py
   git hash-object src\mist\intelligence\marvis\actions\alarm_handling\alarms.py
   ```

   Expected: `765c01070ebdf0d79580af464441f9f44e3c34fb` and `c61405c839212c6c64c5cbd8c07cd2e582cd4287`.

9. Run the import smoke test on the new path. Expected: no output.

   ```powershell
   python -c "import src.mist.intelligence.marvis.actions.alarm_handling.alarms"
   ```

10. Run the import smoke test on the old path. Expected: `ModuleNotFoundError`.

    ```powershell
    python -c "import src.mist.intelligence.marvis.actions.alarms"
    ```

Caution: a failed move can leave both paths in the index. Read the output of `git status` before the next step.

## Scenario 3: Canonical references (tasks T005 to T008)

11. Edit these lines with the edit tool:
    - `src\mist\intelligence\marvis\actions\operation.py`, lines 51 and 57, to name `alarm_handling`.
    - `src\mist\intelligence\marvis\actions\__init__.py`, lines 4 to 7, to name the `alarm_handling` package.
    - `tests\unit\marvis\actions\test_acknowledgement.py`, lines 7, 30, 43, and 58.
    - `tests\unit\marvis\actions\test_alarms.py`, lines 18 and 19. The logger check reads `alarms_module.__name__`.
    - `tests\unit\marvis\actions\test_operation.py`, line 20.
    - `tests\unit\marvis\actions\test_model.py`, line 15.
    - `tests\unit\marvis\actions\test_properties.py`, line 25.
    - `documentation\marvis-actions-api-endpoints.md`, line 1329.

12. Search for old paths. Expected: no output.

    ```powershell
    git grep -n "marvis[./]actions[./]\(alarms\|acknowledgement\)" -- . ":(exclude)specs" ":(exclude)CHANGELOG.md"
    ```

13. Compare the module-level names of the two edited source files. Expected: `no module-level name changed`, with exit code 0.

    ```powershell
    symbol-diff --base origin/main src\mist\intelligence\marvis\actions\operation.py
    symbol-diff --base origin/main src\mist\intelligence\marvis\actions\__init__.py
    ```

14. Run the focused Marvis tests. Expected: every test passes.

    ```powershell
    python -m pytest tests\unit\marvis\actions -q
    ```

## Scenario 4: Guards (tasks T009 to T011)

15. Add the structure test to `tests\guardrails\test_src_domain_structure.py`, before line 120. Name it `test_marvis_actions_has_alarm_handling_package`.

16. After the task T002 check passes, add the two `MODULE_PATHS` entries to `tests\guardrails\test_src_public_symbol_preservation.py`, after the `juniper_docs/classify/reclassifier.py` entry. Each entry maps an old module to its `alarm_handling` path.

17. Delete lines 91 to 95 of `tests\guardrails\nested_package_baseline.json`. Change line 177 of `tests\guardrails\test_nested_package_structure.py` to read `"32 violations, 235 total excess"`.

18. Stage the moved files by explicit path before the ratchet run:

    ```powershell
    git add src\mist\intelligence\marvis\actions\alarm_handling\__init__.py src\mist\intelligence\marvis\actions\alarm_handling\acknowledgement.py src\mist\intelligence\marvis\actions\alarm_handling\alarms.py
    ```

Caution: the nested ratchet reads tracked files only. Stage each moved file before the run, or the ratchet reports the old layout.

19. Run the guards. Each command expects a pass. The nested ratchet reports `32 violations, 235 total excess`.

    ```powershell
    python -m pytest tests\guardrails\test_src_domain_structure.py -q
    python -m pytest tests\guardrails\test_src_public_symbol_preservation.py -q
    python -m pytest tests\guardrails\test_nested_package_structure.py -q
    python -m pytest tests\guardrails\test_move_module_guidance.py -q
    ```

## Scenario 5: Generated references (task T012)

20. Regenerate the menu references and read the diff. Expected: no change, or only the regenerated lines.

    ```powershell
    python scripts\generate_menu_wiki.py
    git diff --stat -- documentation scripts
    ```

21. Run the CI form of the menu API map check. Expected: exit code 0 and no drift message.

    ```powershell
    python -m scripts.menu_api_map --check
    ```

## Scenario 6: Changelog fragment (task T013)

22. Create `changelog.d\issue-4008-marvis-alarm-handling.md` with the create tool. The file holds this text:

    ```markdown
    ### Refactor the Marvis alarm handling modules

    - **Changed**: The Marvis alarm acknowledgement and alarm join modules moved under `alarm_handling`. Menu 270 behavior is unchanged. Issue #4008.
    ```

23. Run the fragment guard. Expected: every test passes.

    ```powershell
    python -m pytest tests\guardrails\test_changelog_fragment_policy.py -q
    ```

## Scenario 7: Local gates (task T-LOCAL-GATES)

Run each row that applies. The expected results come from the local gates table of `.github/copilot-instructions.md`.

| Gate | Command | Expected result |
| - | - | - |
| Compile | `python -m py_compile MistHelper.py`, and each changed Python file | No output |
| Lint | `python -m ruff check .` | `All checks passed!` |
| Format | `python -m black --check .` | No file needs a change |
| Types | `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` | `Success` |
| Focused tests | `python -m pytest tests\unit\marvis\actions\test_acknowledgement.py tests\unit\marvis\actions\test_alarms.py tests\unit\marvis\actions\test_model.py tests\unit\marvis\actions\test_operation.py tests\unit\marvis\actions\test_properties.py tests\guardrails\test_src_domain_structure.py tests\guardrails\test_src_public_symbol_preservation.py tests\guardrails\test_nested_package_structure.py tests\guardrails\test_move_module_guidance.py tests\guardrails\test_marvis_actions_portal_exposure.py -q` | All pass, with 223 test functions run |
| Full tests | `pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal`, then `pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\contract tests\guardrails tests\integration --split tests\contract\upgrade_portal --split tests\integration\upgrade_portal` | One summary line for each shard, with no failure |
| Safe sweep | `python MistHelper.py --test` | Each safe operation completes. The Mist API checks skip without a token. |
| Coverage | `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=` | Coverage is 80 percent or above |
| Test quality | After the local commit, run `python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides`, then `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/main" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt` | `gate: 0 new findings vs baseline` |
| Complexity | `radon cc src -j \| complexity-gate --max 10` | No block above complexity 10 |
| Security lint | `bandit -c pyproject.toml -r src\mist\intelligence\marvis\actions -q` | No finding |
| Code quality | `pylint src/ --fail-under=9.5` | Score 9.5 or above |
| Dead code | `vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70` | No finding |
| Docstrings | `pydocstyle src/ wsgi.py web_portal`, and `interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90` | No violation, and coverage 90 percent or above |
| Menu reference | Scenario 5 commands | No changed file after the run |
| Symbols | Scenario 3, step 13, for the files that stay in place | `no module-level name changed` |
| Moved modules | Scenario 4, step 19, for the rename-aware symbol test | Pass |
| Guardrails | `python -m pytest tests\guardrails -q` | Each guard passes, and no new failure appears |

Not applicable rows, with reasons: the STE gate, because no listed file changes. The ops portal and ops platform gates, because no file in those folders changes. The dependency audit, because no dependency file changes. The browser gate, because the change adds no web interface behavior, and the issue requires no browser test.

## Commit and publication (task T-PR)

24. Create the remediation child issue under #3824 before the pull request. The issue body lists the touched-debt rows of `plan.md`. Use `gh issue create` with a body file that lies outside the repository.

25. Stage the changed paths by explicit path. Do not use `git add -A` or `git add .`.

26. Commit with the Conventional Commit subject and the closing keyword:

    ```powershell
    git commit -m "refactor(marvis): isolate alarm handling modules" -m "Closes #4008" -m "Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>"
    ```

27. Run the test quality gate from Scenario 7. Stop when it reports a new finding.

28. Rebase onto current main, rerun the affected gates, and push without force:

    ```powershell
    git push -u origin chore/4008-marvis-alarm-handling
    ```

Warning: `git push --force` replaces remote commits that other agents depend on. Push without force, and read the rejection message if the push fails.

29. Open the pull request with the same title. Pass the body text in a file that lies outside the repository, with `--body-file`. The body holds `Closes #4008`, the gate results, the logger change, the touched-debt table, the hold status, and the child issue number.

## Remote checks and merge (tasks T-REMOTE-CI and T-MERGE)

30. Watch the required checks on the pull request:

    ```powershell
    gh pr checks --watch
    ```

31. After CI passes and the orchestrator authorizes the merge, add the `auto-merge` label. Then read the container build for the merged revision:

    ```powershell
    gh run list --workflow container-build.yml --branch main --limit 1
    ```

Expected: the run succeeds, and its image revision label equals the merged commit.
