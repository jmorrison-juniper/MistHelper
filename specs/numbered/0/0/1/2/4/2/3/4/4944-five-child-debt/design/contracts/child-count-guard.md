# Contract: Child-count guard

## Identity

- Test file: `tests/guardrails/test_process_folder_structure.py`. The guard cases extend this file. No new file is added.
- Baseline: the constant `DEBT_FOLDER_BASELINE` in that file. Its value is `{"scripts": 53, "tests/unit/scripts": 10, "documentation/noc-runbooks": 17}` in PR-1, and the values lower with each PR.
- Limit: five tracked children for each debt folder. The limit is documented here and checked by the final baseline values.

## Inputs

- Folder paths use forward slashes and are relative to the repository root.
- The count source is `git ls-files -- <folder>/`. The count is the number of distinct direct child names in the tracked paths.
- Untracked files, `__pycache__`, and local-only folders do not count.

## Output

Each debt folder prints one ASCII line. The guard prints the examined total as the last line.

```text
five-child debt: folder=scripts children=53 baseline=53 limit=5 status=ok
five-child debt: folder=tests/unit/scripts children=10 baseline=10 limit=5 status=ok
five-child debt: folder=documentation/noc-runbooks children=17 baseline=17 limit=5 status=ok
five-child debt: examined folders=3 children=80
```

## Pass and fail rules

- Pass: each folder count is at most its baseline.
- Fail on growth: a folder count exceeds its baseline. The failure message names the folder, the count, and the baseline. It also names the examined folder total.
- Fail on input: `git ls-files` returns an error, or it returns no output for a folder that the baseline lists. The failure message names the command. The guard never skips.
- Lowering a baseline is allowed in a group pull request. Raising a baseline needs reviewer approval and a note in the pull request body.

## Growth case

The growth case adds one name to a copy of the tracked list in memory. It expects a failure that names the folder. The case does not change any file.

## Command

```text
python -m pytest tests/guardrails/test_process_folder_structure.py -q -s
```
