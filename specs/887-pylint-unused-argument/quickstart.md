# Quickstart: Validate the W0613 narrowing

**Feature Directory**: `specs/887-pylint-unused-argument/`

**Date**: 2026-07-29

This guide shows how to validate the feature. It covers the checks that prove
each user story. It does not hold implementation code. The signature changes sit
in `contracts/signature-changes.md`. The outcomes sit in `research.md`.

---

## Prerequisites

1. Open a PowerShell prompt at the repository root.
2. Use `.venv\Scripts\python.exe` for every Python command. The global Python
   interpreter on this machine is broken, and the virtual environment holds no
   `pip`.
3. Confirm the tool version. The baseline used pylint 4.0.6 and astroid 4.0.4.

```powershell
.venv\Scripts\python.exe -m pylint --version
```

If the version differs, re-measure the baseline before you start. A version
change can add or remove findings.

---

## Step 1. Validate User Story 1, the triage record

No code change is needed for this step.

1. Open `research.md`.
2. Read section 5.
3. Confirm that the table holds 21 rows.
4. Confirm that every row holds a file, a line, a function, a parameter, an
   outcome, and a justification.
5. Confirm that no cell in the outcome column reads "To triage".

**Expected result**: 15 rows hold Outcome A. 5 rows hold Outcome B. 1 row holds
Outcome C. The total is 21.

This satisfies SC-001.

---

## Step 2. Re-measure the baseline

Run this command before you change any code.

```powershell
.venv\Scripts\python.exe -m pylint src/ --disable=all --enable=W0613 --score=n
```

**Expected result**: 21 findings. Every file and line matches the table in
`research.md`.

If the count differs, other work landed on `main`. Add each new finding to the
triage record and assign an outcome before you continue. FR-003 requires this
step.

---

## Step 3. Validate User Story 2, the source tree

Run this command after every task that changes code.

```powershell
.venv\Scripts\python.exe -m pylint src/ --disable=all --enable=W0613 --score=n
```

**Expected result during the work**: The count falls after each task. The count
never rises.

Caution: A rise means a cascade. You removed a parameter at one level and left
the caller unchanged. Read section 3 of `research.md`, then finish the thread.

**Expected result at the end**: No output. Zero findings. This satisfies FR-021
and SC-002.

---

## Step 4. Validate the ignored packages

The gate hides `src/maps` and `src/ssh`. Four findings sit there. Prove them by
hand.

```powershell
.venv\Scripts\python.exe -m pylint src/maps src/ssh --disable=all --enable=W0613 --score=n
```

**Expected result**: No output. Zero findings.

This satisfies FR-004.

---

## Step 5. Confirm that no suppression is too wide

```powershell
.venv\Scripts\python.exe -m tools.ste_linter --help
Select-String -Path "pyproject.toml","setup.cfg" -Pattern "W0613" -ErrorAction SilentlyContinue
Get-ChildItem -Path src -Recurse -Filter *.py | Select-String -Pattern "pylint: disable=.*W0613"
```

**Expected result for the second command**: No match after Step 8. A match
before Step 8 is normal.

**Expected result for the third command**: Exactly six matches. Five belong to
Outcome B. One belongs to Outcome C. Each match sits on a parameter line or on
the line above it.

Read each of the six lines. Confirm that the reason names a library, a
back-compat promise, or an issue number. A generic phrase fails FR-013 and
SC-006.

This satisfies FR-011 and FR-012.

---

## Step 6. Run the quality gates

Run each command exactly as the continuous integration job runs it. Scope the
run to the whole repository where the job does, not to the changed files only.

```powershell
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m black --check .
.venv\Scripts\python.exe -m mypy src/ --config-file pyproject.toml
.venv\Scripts\python.exe -m radon cc src/ -nc
.venv\Scripts\python.exe -m pytest
```

**Expected result**: Every command exits with code 0. The radon command must
report no block above complexity 10.

Caution: Removing a parameter lowers the parameter count. It does not raise
complexity. A radon failure therefore points at an unrelated edit.

This satisfies FR-026 and SC-005.

---

## Step 7. Confirm the test count

Record the test count before the work and after the work.

```powershell
.venv\Scripts\python.exe -m pytest -q
```

**Expected result**: The pass count matches the count before the change. The
feature updates 24 test call sites, but it adds no test and removes no test.

This satisfies SC-005.

---

## Step 8. Change the gate, last

Do not start this step until Step 3 reports zero findings.

1. Open `pyproject.toml`.
2. Remove `"W0613"` from the `disable` list under
   `[tool.pylint."messages control"]`.
3. Update the comment block above the list. See section 2 of
   `contracts/pylint-gate.md` for the three facts that the new text must state.

Reproduce the gate locally.

```powershell
.venv\Scripts\python.exe -m pylint src/ --fail-under=9.5 --ignore=maps,ssh,ui
```

**Expected result**: Exit code 0. The reported score is near 9.77 on Windows.

Warning: This local result is not proof. Go to Step 9.

---

## Step 9. Validate User Story 3, the runner result

1. Push the branch.
2. Open the continuous integration run for the branch.
3. Read the job named "Pylint (score gate)".
4. Confirm that the job passed.
5. Record the score from the job log in the pull request body.

**Expected result**: The job passes at the 9.5 threshold on `ubuntu-latest`.

Warning: Do not add the `auto-merge` label until this job and CodeQL both pass.

If the job fails, follow section 7 of `contracts/pylint-gate.md`. That section
holds the rollback position.

This satisfies FR-022, FR-023, and SC-004.

---

## Step 10. Confirm the companion issues

1. Open the three issues that section 7 of `research.md` names.
2. Confirm that each issue holds a type label and a scope label.
3. Confirm that the triage record links the Outcome C issue by number.
4. Confirm that the Outcome C comment in the source names the same number.

This satisfies FR-017 and SC-007.

---

## Step 11. Prove the gate reports a new defect

This step proves SC-008. Do not commit the temporary change.

1. Add an unused parameter to any function under `src/`.
2. Run the gate command from Step 8.
3. Confirm that pylint reports a `W0613` message for the new parameter.
4. Undo the temporary change.
5. Run the gate command again and confirm that it passes.

---

## Step 12. Check the prose

Run the linter on every document that the feature writes or changes.

```powershell
.venv\Scripts\python.exe -m tools.ste_linter --min-score 80 specs/887-pylint-unused-argument/plan.md
.venv\Scripts\python.exe -m tools.ste_linter --min-score 80 specs/887-pylint-unused-argument/research.md
.venv\Scripts\python.exe -m tools.ste_linter --min-score 80 specs/887-pylint-unused-argument/data-model.md
.venv\Scripts\python.exe -m tools.ste_linter --min-score 80 specs/887-pylint-unused-argument/quickstart.md
.venv\Scripts\python.exe -m tools.ste_linter --min-score 80 specs/887-pylint-unused-argument/contracts/signature-changes.md
.venv\Scripts\python.exe -m tools.ste_linter --min-score 80 specs/887-pylint-unused-argument/contracts/pylint-gate.md
```

**Expected result**: Every file scores 80 or higher.

Run the linter on the pull request body and on each issue body too. FR-031
covers all prose.

---

## Validation summary

| Story | Step | Success criterion |
| - | - | - |
| User Story 1 | Step 1 | SC-001 |
| User Story 2 | Steps 3, 4, 5, 6, 7 | SC-002, SC-005, SC-006, SC-009 |
| User Story 3 | Steps 8, 9, 11 | SC-003, SC-004, SC-008 |
| Companion work | Step 10 | SC-007 |
