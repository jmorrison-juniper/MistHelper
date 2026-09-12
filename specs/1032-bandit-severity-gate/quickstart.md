# Quickstart: Measure and validate the bandit severity gate work

**Feature**: `1032-bandit-severity-gate` | **Branch**: `security/889-bandit-ll` | **Date**: 2026-07-28

This guide states how to measure the findings, how to check one work group, and how to prove that the feature is complete. It holds no implementation code. The work items live in `tasks.md` after you run `/speckit.tasks`.

---

## 1. Prerequisites

| Item | Check |
| - | - |
| Branch | `git branch --show-current` returns `security/889-bandit-ll`. Do not create a branch and do not switch. |
| Python | 3.13 or newer. |
| Virtual environment | Activate it with `.venv\Scripts\Activate.ps1` on Windows. |
| bandit | Run `bandit --version`. The project venv does not hold bandit today. The global Python 3.13 install provides `bandit 1.9.4`. Install it into the venv with `pip install "bandit[toml]"` if you prefer one environment. |
| Test runner | Use `.venv\Scripts\python.exe -m pytest`. The global Python cannot import the project. |

---

## 2. Measure the baseline

Run this step before the first edit. Requirement FR-006 counts 54 findings, and the count must match before you change any line.

### Step 2.1 - Produce the report

```powershell
bandit -c pyproject.toml -r . -f json -o "$env:TEMP\bandit_1032.json" -q
```

Bandit exits with code 1 when it reports a finding. That exit code is expected here.

### Step 2.2 - Apply the two filters

A raw Windows run reports 105 findings. Two of those groups never reach CI. You must remove them by hand, because a Windows scan does not honor the `exclude_dirs` entry for the analyzer fixtures. That entry uses a forward slash and a Windows scan returns a backslash.

Filter rules:

1. Normalize each `filename` value. Replace a backslash with a forward slash. Remove a leading `./`.
2. Drop a finding when `git ls-files` does not list the normalized path.
3. Drop a finding when the normalized path starts with `tools/test_quality_analyzer/fixtures/`.

### Step 2.3 - Compare against the expected result

| Measurement | Expected value |
| - | - |
| Raw findings | 105 |
| Findings in tracked files | 96 |
| Findings in scope | 54 |
| Findings above LOW severity, in scope | 0 |

| Rule | Expected count |
| - | - |
| B101 | 18 |
| B105 | 11 |
| B107 | 1 |
| B110 | 7 |
| B404 | 4 |
| B603 | 9 |
| B606 | 1 |
| B607 | 3 |

**If a count differs**: The branch moved, or the bandit version changed. Stop. Re-derive the ledger in [data-model.md](data-model.md) before you edit any line.

### Step 2.4 - Confirm the out-of-scope findings

The filter should remove exactly these untracked findings. The specification names them as non-goals.

| Rule | Severity | Location |
| - | - | - |
| B101 | LOW | `_tr042_synthetic.py`, 8 findings |
| B104 | MEDIUM | `mist-ops-platform/src/shared/config/settings.py` line 41 |

The 42 fixture findings under `tools/test_quality_analyzer/fixtures/` also disappear. The analyzer needs that code to stay unsafe.

---

## 3. Check one work group

Run this loop after each group from A to D. See the phased approach in [plan.md](plan.md).

1. Re-run step 2.1 and step 2.2.
2. Confirm that the rule count for the finished group reads 0.
3. Confirm that **every other rule count did not change**. A changed count means that an edit moved a finding instead of clearing it.
4. Run the fast gates that read the touched files.

   ```powershell
   ruff check .
   black --check --diff .
   ```

5. Run the deeper gates when the group touched `src/`.

   ```powershell
   mypy src/ --config-file pyproject.toml
   radon cc src/ -a -nb
   vulture src/ --min-confidence 80
   pylint src/ --ignore=maps,ssh,ui
   .venv\Scripts\python.exe -m pytest tests/unit --no-cov -q
   ```

**Do not scope a gate to the changed files only.** CI runs `ruff check .` and `black --check --diff .` across the whole repository. A gate that passes on a subset can still fail in CI.

**Watch the complexity gate.** CI fails when any block in `src/` scores above 10. A narrowed `except` clause adds no branch. A converted `assert` adds one branch each. Group D2 adds 7 branches across 6 functions, so no function should cross the limit.

---

## 4. Group-by-group acceptance

| Group | Rules | Expected count after the group | Extra check |
| - | - | - | - |
| A | B404, B603, B606, B607 | 0 for each | `starlink_dashboard.py` still starts. `tools/compliance_analyzer` still reads the git ignore list. |
| B | B105, B107 | 0 for each | No value moved to the environment, unless you found a real credential. If you did, stop and raise a rotation request. |
| C | B110 | 0 | `.venv\Scripts\python.exe -m pytest tests/unit -q` keeps its pass count. No new log line appears inside `src/utils/logger_utils.py`. |
| D | B101 | 0 | `validate_template` raises `ValueError` on a bad template. Its docstring names `ValueError`, not `AssertionError`. |
| E | none | 0 in total | The bandit step holds no `-ll`. |

---

## 5. Prove the feature is complete

Map each check to a success criterion in [spec.md](spec.md).

### SC-001 - The scan is clean

```powershell
bandit -c pyproject.toml -r . -q
```

Apply the two filters from step 2.2. The in-scope count must read 0. On a Linux checkout the raw command exits with code 0 and reports zero findings, because the fixture exclusion works there.

### SC-002 - The flag is gone

```powershell
Select-String -Path .github\workflows\ci.yml -Pattern '\-ll'
```

The search must return no match inside the bandit step.

### SC-003 - The gate fails on a new finding

1. Add one `assert True` line to a tracked file in `src/`.
2. Run the scan. It must report one B101 finding and must exit with code 1.
3. Remove the line. Do not commit it.

### SC-004 and SC-005 - Every finding holds a decision, and no suppression is bare

```powershell
git diff main...HEAD -- '*.py' | Select-String -Pattern 'nosec'
```

Read every added `# nosec` line. Each line must name a rule identifier and must state a reason. Check each line against [contracts/suppression-comment.md](contracts/suppression-comment.md).

### SC-006 - No runtime guard depends on `assert`

```powershell
.venv\Scripts\python.exe -O -m pytest tests/unit -q
```

The suite must keep its pass count under the `-O` flag. That flag removes every `assert`, so a suite that still passes proves that no converted guard lost its duty.

### SC-007 - Every gate stays green

Run the full suite exactly as CI runs it.

```powershell
ruff check .
black --check --diff .
mypy src/ --config-file pyproject.toml
pylint src/ --ignore=maps,ssh,ui
radon cc src/ -a -nb
vulture src/ --min-confidence 80
.venv\Scripts\python.exe -m pytest --cov=src/ --cov-fail-under=80
bandit -c pyproject.toml -r .
pip-audit
```

### SC-008 - A reviewer understands each suppression

Ask a reviewer who did not write the change to read three added `# nosec` comments. The reviewer must state the reason for each one in under one minute.

### SC-009 - The change stays inside the scope

```powershell
git diff --name-only main...HEAD
```

The list must hold no file under `tools/test_quality_analyzer/fixtures/`. The list must hold no untracked file from step 2.4, such as `_tr042_synthetic.py` or `mist-ops-platform/src/shared/config/settings.py`.

---

## 6. Known traps

| Trap | Effect | Avoid it by |
| - | - | - |
| A `# noqa: S101` or `# noqa: S603` annotation already sits on the line. | It suppresses nothing. The root `ruff` configuration does not select the `S` rule set, and bandit ignores `# noqa`. | Add a real `# nosec` comment. Leave the old annotation in place. |
| The ledger line numbers go stale. | Group D2 converts 7 asserts into multi-line blocks, so every later line in those files moves. | Locate each finding by the anchor column in [data-model.md](data-model.md), not by the line number. |
| The comment pushes the line past the length limit. | `ruff` fails on E501. | Shorten the reason. Move the comment to another line of the same statement. Add `# noqa: E501` only as a last step. |
| A file in `mist-ops-platform` uses a different limit. | The limit is 99 characters there, not 120. | Check `mist-ops-platform/pyproject.toml` before you write a long comment. |
| The global Python runs the tests. | The import of the project fails. | Always call `.venv\Scripts\python.exe -m pytest`. |
| The workflow flip happens early. | Every push turns red while findings remain. | Keep Group E last. |
