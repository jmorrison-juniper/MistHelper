# Quickstart: W0706 try-except-raise handlers in MistHelper.py

Use these steps to reproduce the finding and to verify the change. Run each command from the worktree root on branch `chore/4132-w0706-try-except-raise`.

## 1. Reproduce the finding before the change

```powershell
.venv\Scripts\python.exe -m pylint MistHelper.py
```

Expected: seven `W0706` messages at lines 1820, 6610, 6654, 6666, 7811, 8094, and 8343. The message text is `The except handler raises immediately`. The column is not verified, as `research.md` records.

## 2. Run the new tests

```powershell
python -m pytest tests/unit/test_issue_1709_narrow_except.py -k "reraise or stop_propagates or ordinary or main_block or touched"
```

Expected before the change: four failed cases and fourteen passed cases. The failed cases are `test_misthelper_has_no_reraise_first_handler`, `test_main_block_keeps_keyboard_interrupt_and_finally`, and the two cases of `test_touched_fast_mode_readers_log_before_and_after`.

Expected after the change: eighteen passed cases and no failure.

## 3. Confirm that no suppression entered the change

```powershell
git diff origin/main -- MistHelper.py | Select-String -Pattern "pylint: disable|noqa|type: ignore"
```

Expected: no output.

## 4. Confirm the symbol and menu gates

```powershell
symbol-diff --base origin/main MistHelper.py
python scripts/generate_menu_wiki.py
python -m scripts.menu_api_map --check
git status --porcelain
```

Expected: `symbol-diff` prints `no module-level name changed` and exits with code 0. The two menu commands change no tracked file. The `git status` output lists only the files of this change.

## 5. Run the changelog and folder guards

```powershell
python -m pytest tests/guardrails/test_changelog_fragment_policy.py
python -m pytest tests/guardrails/test_process_folder_structure.py
```

Expected: both files pass. The folder guard prints the number of directories that it examined.

## 6. Run the STE gate on each new Markdown file

```powershell
ste-linter --config .ste-linter.toml --min-score 80 changelog.d/issue-4132-w0706-try-except-raise.md specs/numbered/0/0/1/1/3/0/1/2/4132-w0706-try-except-raise/spec.md specs/numbered/0/0/1/1/3/0/1/2/4132-w0706-try-except-raise/plan.md specs/numbered/0/0/1/1/3/0/1/2/4132-w0706-try-except-raise/tasks.md specs/numbered/0/0/1/1/3/0/1/2/4132-w0706-try-except-raise/analysis.md specs/numbered/0/0/1/1/3/0/1/2/4132-w0706-try-except-raise/design/research.md specs/numbered/0/0/1/1/3/0/1/2/4132-w0706-try-except-raise/design/data-model.md specs/numbered/0/0/1/1/3/0/1/2/4132-w0706-try-except-raise/design/quickstart.md specs/numbered/0/0/1/1/3/0/1/2/4132-w0706-try-except-raise/design/checklists/requirements.md
```

Expected: each named file scores 80 or above. Name each file. Do not pass a directory.

## 7. Run the safe sweep

```powershell
python MistHelper.py --test
```

Expected: each safe operation completes. Without a Mist token, the Mist API checks skip with a credential reason. Do not print a token value.

## 8. Remove the worktree after the merge

Keep the worktree until T-MERGE completes. Remove it only after the squash commit reaches `main`.
