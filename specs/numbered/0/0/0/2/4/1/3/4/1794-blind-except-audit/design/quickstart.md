# Quickstart: Blind except handler audit (issue 1794)

Use this file to reproduce the baseline and to run each slice check. Run each command from the root of a clean worktree. Use `.venv\Scripts\python.exe` for each Python command (tasks.md rule 1).

Warning: Do not delete a held branch or a held commit before its merged replacement exists. Deletion can lose unmerged work (FR-028).

Caution: The record pull request body contains `Closes #1794`. When it merges, the issue closes. Reopen #1794 if the umbrella must stay open (D-12).

## Prerequisites

### Q-1 Confirm the verified commit

```
gh api repos/jmorrison-juniper/MistHelper/commits/main --jq .sha
git rev-parse HEAD
```

Expected at record time: `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` for both commands. The research rows cite blob SHAs that were read at this commit.

### Q-2 Confirm the Python version and the pinned tools

```
.venv\Scripts\python.exe --version
.venv\Scripts\python.exe -m ruff --version
.venv\Scripts\python.exe -m pylint --version
.venv\Scripts\python.exe -m pip show mistapi
```

Expected: Python 3.15, ruff 0.17.6, pylint 4.1.4, and mistapi 0.64.1 (RC-005, RC-007, RC-008, RC-018).

## Reproduce the baseline

### Q-3 Measure the ruff BLE001 count

```
.venv\Scripts\python.exe -m ruff check . --select BLE001 --statistics
.venv\Scripts\python.exe -m ruff check . --select BLE001 --ignore-noqa --statistics
```

Record both values in `design/research.md` (T001). The scope metric is the `--ignore-noqa` value (FR-005). The last reported value is 524 (issue comment 9). That value is not measured (U-1).

### Q-4 List the sites of one slice

Run the command with the paths of one slice row in `plan.md`. For slice S01, the paths are `MistHelper.py` and `wsgi.py`.

```
.venv\Scripts\python.exe -m ruff check MistHelper.py wsgi.py --select BLE001 --ignore-noqa --output-format concise
```

Each output line is one site. A slice holds at most 40 sites (FR-017).

### Q-5 Confirm the zero count

For a slice, run Q-4 again with `--statistics` in place of `--output-format concise`. The count for the slice paths must be zero after the slice merges.

For the final gate, run the repository command. The count must be zero (SC-002).

```
.venv\Scripts\python.exe -m ruff check . --select BLE001 --ignore-noqa --statistics
```

### Q-6 Run the local gates for the changed files

Run each gate that applies to the changed files. Record each result in the pull request body (T-LOCAL-GATES). Each gate command comes from the local gates table in `.github/copilot-instructions.md`. The CI forms come from `.github/workflows/ci.yml`.

```
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m black --check .
.venv\Scripts\python.exe -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml
.venv\Scripts\python.exe -m pytest <changed test files> -q
.venv\Scripts\python.exe MistHelper.py --test
.venv\Scripts\python.exe -m radon cc src/ MistHelper.py wsgi.py scripts/analyze_marvis_pcap.py scripts/probe_zscaler_endpoints.py tests/unit/utils/test_zscaler_catalogue.py -j | complexity-gate --max 10
symbol-diff --base origin/main <changed Python file>
.venv\Scripts\python.exe -m bandit -c pyproject.toml -r . -q
pip-audit -r requirements.txt
.venv\Scripts\python.exe -m pylint src/ --fail-under=9.5
.venv\Scripts\python.exe -m vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70
.venv\Scripts\python.exe -m pydocstyle src/ wsgi.py web_portal
.venv\Scripts\python.exe -m interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90 -v
ste-linter --config .ste-linter.toml --min-score 80 README.md AGENTS.md .github/copilot-instructions.md CLAUDE.md documentation/ASD-STE100_writing-guide.md
```

Notes for Q-6:
- The `<changed test files>` value lists the test files that the change touches.
- The `MistHelper.py --test` command applies only to slices that change `MistHelper.py` (S01).
- Run `symbol-diff` once for each changed Python file (copilot-instructions line 73).
- Run the test quality procedure from `.github/copilot-instructions.md` for each changed test file. The expected result is `gate: 0 new findings vs baseline`.
- The coverage command from the local gates table runs before the final gate (T031): `.venv\Scripts\python.exe -m pytest tests --ignore=tests/e2e --cov=src --cov-report=`.
- The ops portal and ops platform gates do not apply. No file under `ops-portal/` or `mist-ops-platform/` changes in this audit.

### Q-7 Measure the pylint W0718 count

```
.venv\Scripts\python.exe -m pylint src/ --disable=all --enable=W0718 --score=n
```

Count the output lines that name W0718. Record the value in `design/research.md` (T001). The recorded value of 493 is stale (RC-002, U-2).

### Q-8 Measure the text count

```
git grep -c -E "except[[:space:]]+(Exception|BaseException)[^A-Za-z0-9_]"
```

Add the counts from the output. At `f03c6c9`, the total is 827 sites in 310 files (research.md, Local evidence).

### Q-9 Reconcile the counts

Group the Q-3 output by path. Compare the groups with the Q-7 output and the Q-8 output. Each difference needs a path-level reason in `design/research.md` (T002).

```
.venv\Scripts\python.exe -m ruff check . --select BLE001 --ignore-noqa --output-format concise
```

The ruff root is the repository without the four `extend-exclude` paths (`pyproject.toml` line 206, RC-004). The pylint root is `src/` (`ci.yml` lines 78 and 529, RC-014).

### Q-10 Measure the excluded trees

```
git grep -c -E "except[[:space:]]+(Exception|BaseException)[^A-Za-z0-9_]" -- mist-ops-platform web_portal scripts src/interfaces/visualization/maps
git grep -c "noqa: BLE001" -- src/interfaces/visualization/maps
```

Expected at `f03c6c9`: 23, 26, 32, and 68 text sites in the four trees. The total is 149 sites in 49 files. The maps tree holds 16 inert `noqa` lines (research.md, Local evidence).

### Q-11 Inventory the pylint disables

```
git grep -c "pylint: disable=broad-exception-caught"
```

Expected at `f03c6c9`: 57 lines in 20 files. Each kept site that pylint flags needs one inline disable and one reason comment (D-13).

## Check each slice

### Q-12 Confirm that no slice adds a noqa directive

```
git diff --merge-base origin/main HEAD | Select-String -Pattern "^\+.*noqa"
```

Expected: no output (SC-006, FR-015).

### Q-13 Run the growth guard

```
.venv\Scripts\python.exe -m pytest tests/guardrails/test_blind_exception_handler_ratchet.py -q
```

Expected: all tests pass (FR-006). After the final gate, the stored-baseline test passes with an empty baseline (FR-026).

### Q-14 Confirm the baseline count only falls

```
git diff --merge-base origin/main HEAD -- .github/blind-exception-handler-baseline.json
```

Expected: each changed path has a lower count, and no count rises (FR-019).

### Q-15 Check the final gate configuration

```
Select-String -Path pyproject.toml -Pattern "BLE001|RUF100|W0718"
git diff --merge-base origin/main HEAD -- pyproject.toml
```

Expected for the final gate only (T031):
- `BLE001` and `RUF100` are in the ruff select list.
- `W0718` is not in the pylint disable list.
- The `extend-exclude` list is unchanged.
- The comment at lines 588 to 593 no longer states the 493-site count.

### Q-16 Run the pylint score gate

```
.venv\Scripts\python.exe -m pylint src/ --fail-under=9.5
```

Expected: exit code 0. The score is 9.5 or higher. CI recorded 9.53 before the change (RC-129).

### Q-17 Confirm the held commits

Run this block after `git fetch origin main`. Each held commit must print exit code 1 for the ancestor check and `commit` for the object type.

```
$held = @(
  "c3d0f769cda328d259d7397d2278707845b44b41",
  "8a700b2b518b9d08840087cbd30ff3fc13daa8f4",
  "ecdf3fef95b638ee52296cc1db991965cce96c70",
  "88e8bd4f1ce9e997937513cc8f415085574cf69f",
  "f35a51037b1b4f67cc7b6c53612032cda598fdbb",
  "a2641739600e6e0ee1d0aadbcac8049dd4b4b90f",
  "acdbcb0cb4892eb3220155307f80ab307863ac41",
  "0055f7080a4979fdc33b6ce71dce1c9270d01519",
  "0157ec13fb7f5eb98564fd65ea4a4b804288e06b",
  "57fd57c8c0aa6ee8407efacb62cc7e06a7bdf159",
  "54fc78c46145067f796d9391fcc49cf518b559d6",
  "f9b33748ce0c7b9039588d544f829bb64a9af380",
  "45ca06d2978a65bfe33900b74585c247cb794ee6",
  "30edc280c9d230129bf148bdd6a215703911f3dc",
  "63dd076f7c1d96eda6c68a01237e48d6d29cf59b",
  "49c665d9c1d71c65a2cb5314ae7add702886fb4b"
)
foreach ($sha in $held) {
  git merge-base --is-ancestor $sha origin/main
  Write-Output "$sha ancestor exit $LASTEXITCODE"
  git cat-file -t $sha
}
```

The list holds 16 commits (RC-104, RC-106, and RC-112 to RC-125). Before the owning slice merges, each commit stays on its remote branch with a preservation note (FR-028, SC-011).

### Q-18 Confirm the route

```
git ls-tree origin/main specs/numbered/0/0/0/2/4/1/3/4/
```

Before the record merges, the command prints nothing (RC-096). After the record merges, it prints one folder named `1794-blind-except-audit`.

### Q-19 Check the pull request keywords and outcome rows

```
gh pr view <pull request number> -R jmorrison-juniper/MistHelper --json body --jq .body
```

- The record pull request and the final gate pull request contain `Closes #1794` (D-12).
- Each slice pull request contains `Refs #1794` and one outcome row for each audited site (`contracts/outcome-table.md`, FR-018, FR-029).

### Q-20 Check the comments on changed Python lines

```
git diff -U0 --merge-base origin/main HEAD -- "*.py" | Where-Object { $_ -match '^\+[^+]' -and $_ -notmatch '#' }
```

Expected: each output line is blank, a decorator, or a closing bracket. Any other line needs an inline comment (FR-014, FR-036).

### Q-21 Check the Simplified Technical English score

Run the STE command from Q-6 and add each changed Markdown file to its list. Each file must score 80 or higher (FR-034).

### Q-22 Reproduce a masked failure

Use this check for each slice that narrows or deletes a handler (User Story 1).

1. Read the handler and its caller before you edit the code (FR-009).
2. Add a local programming error, such as `NameError`, to the guarded block. Revert this edit before the commit.
3. Run the slice test file with this command:

```
.venv\Scripts\python.exe -m pytest <slice test file> -q
```

Expected after the slice: the programming error propagates, and the propagation test passes (FR-010, FR-021). Before the slice: the handler returns the default value, and no log record names the operation.

### Q-23 Confirm the rebase

Run this check before each slice publication (FR-020):

```
git fetch origin main
git merge-base --is-ancestor origin/main HEAD
```

Expected: exit code 0. If the exit code is 1, rebase onto `origin/main` and run Q-6 again.
