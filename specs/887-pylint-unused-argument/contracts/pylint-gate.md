# Contract: The pylint gate configuration

**Feature Directory**: `specs/887-pylint-unused-argument/`

**Date**: 2026-07-29

This file records the gate that the feature changes. The gate is the interface
between the source tree and the continuous integration job. The change is one
line plus a comment block.

---

## 1. The configuration today

**File**: `pyproject.toml`

```toml
[tool.pylint.main]
fail-under = 9.5

[tool.pylint."messages control"]
# ... comment block ...
disable = ["C0114", "C0115", "C0116", "W0613", "W0718"]
```

**File**: `.github/workflows/ci.yml`, job `pylint`

```yaml
- name: Run Pylint
  run: pylint ${{ env.SRC_PATH }} --fail-under=${{ env.PYLINT_THRESHOLD }} --ignore=maps,ssh,ui
```

The environment variable `PYLINT_THRESHOLD` holds `9.5`. The runner is
`ubuntu-latest`.

---

## 2. The configuration after the change

```toml
disable = ["C0114", "C0115", "C0116", "W0718"]
```

The entry `"W0613"` is absent. Every other entry keeps its position.

The comment block above the list must no longer state that `W0613` is disabled.
The replacement text must state three facts.

1. `W0613` is enforced from this change onward.
2. The audit record sits at `specs/887-pylint-unused-argument/research.md`.
3. Six sites hold a site-local disable, and each one carries a reason.

---

## 3. What must not change

FR-027, FR-028, and FR-029 forbid these changes.

| Item | Rule |
| - | - |
| `"W0718"` in the `disable` list | Must stay. It is a separate slice of issue #887. |
| `"C0114"`, `"C0115"`, `"C0116"` | Must stay. Another tool enforces docstrings. |
| `fail-under = 9.5` | Must stay. FR-024 forbids a lower threshold. |
| `--ignore=maps,ssh,ui` | Must stay. Issue #891 owns that flag. |
| The mypy `src.db` override | Must stay. It is a separate slice of issue #887. |

---

## 4. Ordering rule

FR-019 makes the `disable` list edit the **final** source change.

Rationale: The moment the entry leaves the list, every open branch inherits the
new gate. A branch that still holds an unused argument then fails. The team must
resolve all 21 findings first.

Sequence:

1. Resolve every Outcome A site and every cascade level.
2. Add every Outcome B comment and the Outcome C comment.
3. Confirm that `pylint src/ --disable=all --enable=W0613` reports zero findings.
4. Only then edit `pyproject.toml`.

---

## 5. Acceptance commands

Run each command from the repository root.

| Purpose | Command | Expected result |
| - | - | - |
| Count the findings (FR-021) | `.venv\Scripts\python.exe -m pylint src/ --disable=all --enable=W0613 --score=n` | No output. Zero findings. |
| Reproduce the gate locally | `.venv\Scripts\python.exe -m pylint src/ --fail-under=9.5 --ignore=maps,ssh,ui` | Exit code 0. |
| Confirm the ignored packages (FR-004) | `.venv\Scripts\python.exe -m pylint src/maps src/ssh --disable=all --enable=W0613 --score=n` | No output. Zero findings. |

The third command is the manual scan that the spec assumptions require. The gate
cannot prove those files, because the `--ignore` flag hides them.

---

## 6. Proof of the gate result (FR-022, FR-023)

Warning: A local Windows run is not proof. Issue #891 measured 9.71 on Windows
and 9.41 on the `ubuntu-latest` runner for the same commit. The Linux run
failed the 9.5 threshold.

The only accepted proof is a continuous integration run on the pushed branch.
Read the result of the job named "Pylint (score gate)".

Measured estimate from the current tree, for information only:

| Condition | Local Windows score |
| - | - |
| Today | 9.77 |
| With `W0613` enabled | 9.77 |

The delta is smaller than the reported resolution of 0.01.

---

## 7. Rollback position

If the Linux score falls below 9.5, take these steps in order.

1. Read the runner log. List every message type that the run reports, with a
   count for each type.
2. Confirm that the drop comes from `W0613`. Compare the count of `W0613`
   messages against zero. FR-021 requires zero.
3. If any `W0613` message remains, fix that site. The audit missed it. This is
   the expected cause, because the measured delta is near zero.
4. If zero `W0613` messages remain, the drop comes from another message type on
   Linux. That is a platform difference, not a regression from this feature.
   Record the message types and open a separate issue.
5. Do not lower `fail-under`. FR-024 forbids it.
6. Do not restore `"W0613"` to the `disable` list. FR-024 forbids it.
7. If the score cannot reach 9.5 in this feature, revert the `pyproject.toml`
   commit only. Keep every source fix and keep the triage record. The source
   tree stays clean, and the gate change waits for a follow-up branch.

Step 7 is the safe stopping point. The source work holds its value without the
gate change.
