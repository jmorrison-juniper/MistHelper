# Data Model: Narrow the pylint W0613 unused-argument suppression

**Feature Directory**: `specs/887-pylint-unused-argument/`

**Date**: 2026-07-29

This feature stores no runtime data. It changes source code and one
configuration file. The entities below are documentation records and code
constructs. The triage record in `research.md` is the instance store.

---

## 1. Finding

One pylint `W0613` message.

| Field | Type | Rule |
| - | - | - |
| `file` | Path relative to the repository root | Required. Always inside `src/`. |
| `line` | Integer | Required. Points at the function definition. |
| `function` | Qualified name | Required. Holds the class name when the function is a method. |
| `parameter` | Identifier | Required. Names the unused argument. |
| `gate_sees_it` | Boolean | Derived. False when the file sits in `src/maps`, `src/ssh`, or `src/ui`. |
| `outcome` | Enum `A`, `B`, `C` | Required. FR-001 forbids an empty value. |
| `justification` | One sentence | Required by FR-002. |

**Cardinality**: The measured baseline holds 21 findings.

**Validation**: A finding without an outcome fails SC-001.

---

## 2. Site

One function that holds one or more findings.

| Field | Type | Rule |
| - | - | - |
| `function` | Qualified name | Required. |
| `findings` | List of Finding | One or more. |

**Cardinality**: The baseline holds 20 sites and 21 findings.

**Note**: `AppRunner._prompt_for_commands` is the only site with two findings.
The site holds the parameters `env_cmds` and `csv_cmds`.

---

## 3. Parameter thread

A chain of functions that pass the same parameter down without reading it.

| Field | Type | Rule |
| - | - | - |
| `parameter` | Identifier | Required. |
| `levels` | Ordered list of functions | The leaf comes first. |
| `stops_at` | Qualified name | Required. Names the first function that reads the parameter. |

**State transitions**: A thread moves through three states.

1. **Reported**: Pylint reports the leaf only.
2. **Partly removed**: The leaf loses the parameter. Pylint now reports the next
   level. The count of findings does not fall.
3. **Resolved**: Every level below `stops_at` loses the parameter. Pylint
   reports nothing for the thread.

**Validation rule**: A change must never leave a thread in the "partly removed"
state at the end of a task. That state adds a finding that the baseline does
not hold.

**Instances**: `research.md` section 3 lists four threads.

---

## 4. Outcome

One of three decisions. The enum is closed.

| Value | Meaning | Required action | Forbidden action |
| - | - | - | - |
| `A` | The argument is a refactor leftover. | Remove the parameter from the signature and from every call site. Update every test that calls the signature. | Leave a call site behind. |
| `B` | A contract mandates the signature. | Add a site-local `# pylint: disable=W0613` comment with a specific reason. | Add a file-wide or module-wide disable. |
| `C` | The argument should have been used. | Record the defect, file a companion issue, take the safest minimal action. | Delete the parameter. |

**Validation rule for `B`**: FR-013 rejects a generic reason. The reason must
name a library, an override contract, a documented promise, or an issue number.

---

## 5. Suppression

A `# pylint: disable=W0613` comment.

| Field | Type | Rule |
| - | - | - |
| `scope` | Enum `line`, `function` | FR-012 forbids `file`, `module`, and `repository`. |
| `position` | Enum `same line`, `line above` | FR-011 allows these two positions only. |
| `reason` | One line | Required. Names a specific contract or an issue. |

**Cardinality**: Six suppressions after the change. Five belong to Outcome B.
One belongs to Outcome C.

---

## 6. Dead ruff suppression

A `# noqa: ARG00x` comment that guards a parameter this feature removes.

| Field | Type | Rule |
| - | - | - |
| `code` | Enum `ARG001`, `ARG002`, `ARG004` | Ruff reports the unused argument under these codes. |
| `stated_reason` | Text | Recorded for the audit trail. |

**Validation rule**: When the feature removes the parameter, the feature deletes
the comment in the same change. A comment that guards a parameter that no longer
exists is dead text.

**Cardinality**: Six comments. `research.md` section 4 lists them.

---

## 7. Companion issue

A GitHub issue that records work outside this feature.

| Field | Type | Rule |
| - | - | - |
| `title` | Text | Required. States the defect or the observation. |
| `type_label` | Enum `bug`, `chore` | Required by the repository issue policy. |
| `scope_label` | Text | Required by the repository issue policy. |
| `linked_from` | Triage record row | Required by FR-017 for an Outcome C row. |

**Cardinality**: Three issues. One is mandatory under FR-017. Two record
observations that the spec names.

---

## 8. Gate configuration

The pylint settings that the continuous integration job reads.

| Field | Location | Value today | Value after the change |
| - | - | - | - |
| `disable` list | `pyproject.toml`, `[tool.pylint."messages control"]` | `["C0114", "C0115", "C0116", "W0613", "W0718"]` | `["C0114", "C0115", "C0116", "W0718"]` |
| Comment block | Directly above the `disable` list | Names `W0613` as disabled | Must not claim that `W0613` is disabled |
| `fail-under` | `pyproject.toml`, `[tool.pylint.main]` | `9.5` | `9.5`, unchanged |
| `--ignore` flag | `.github/workflows/ci.yml` | `maps,ssh,ui` | `maps,ssh,ui`, unchanged |

**Validation rule**: FR-019 makes the `disable` list edit the final source
change. FR-027 and FR-029 forbid a change to `W0718` and to the `--ignore` flag.

**State transition**: The gate holds two states.

1. **Hidden**: `W0613` sits in the `disable` list. A new unused argument passes.
2. **Enforced**: `W0613` is absent. A new unused argument lowers the score.

The move to "Enforced" is safe only when the finding count is zero. FR-021
states that rule.
