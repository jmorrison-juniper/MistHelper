# Quickstart: SQLite schema context errors

Use these steps to reproduce the defect and to verify the fix. Run each command from the worktree root for branch `fix/4712-schema-context-errors`.

## Prerequisites

1. Create the branch from current `main` (task T001).
2. Create the Python 3.15.2 environment (task T002):

```text
uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py
```

3. Activate the environment. On Windows, run `.venv\Scripts\Activate.ps1`. On macOS or Linux, run `source .venv/bin/activate`.

## Reproduce the defect on the base

1. Add the three regression tests (task T005) and the updated expectation (task T006). Do not change the source file.
2. Run the regression and legacy tests:

```text
python -m pytest tests/unit/config/foundation/persistence/storage/db/test_database_schema_context_errors.py tests/unit/db/test_database_schema_utils.py
```

3. Expected result: four failures.
   - TST-1 and TST-2 report `DID NOT RAISE` for `RuntimeError` or `AttributeError`.
   - TST-3 fails its zero-connection assertion, because the writer reaches `sqlite3.connect`.
   - TST-4 reports `DID NOT RAISE` for the legacy stack inspection test.

## Apply the fix

1. Delete the `except` clause and its log call at lines 62 and 63 of `src\foundation\persistence\db\database_schema_utils.py` (task T007).
2. Run the same command as in the reproduction step.
3. Expected result: all selected tests pass.

## Verify the module-level names

```text
symbol-diff --base origin/main src\foundation\persistence\db\database_schema_utils.py
```

Expected result: `no module-level name changed`, with exit code 0.

## Verify the documents

```text
ste-linter --config .ste-linter.toml --min-score 80 README.md AGENTS.md .github/copilot-instructions.md CLAUDE.md documentation/ASD-STE100_writing-guide.md documentation/operator-guide.md changelog.d/issue-4712-schema-context-errors.md
```

Expected result: each file scores 80 or above. The full list adds each Markdown file of the record folder.

## Verify the changelog and the record

```text
python -m pytest tests/guardrails/test_changelog_fragment_policy.py
python -m pytest tests/guardrails
```

Expected result: both commands pass.

## Scope of this quickstart

No live Mist, SSH, firmware, or production database operation runs. No container starts. The full gate list appears in `tasks.md`, section Gate list for T-LOCAL-GATES.

## Cleanup

After the merge, remove the worktree and the branch (AGENTS.md, Merge). Warning: do not delete `data/mist_data.db`. The file holds the output of every run, and deletion cannot be undone.
