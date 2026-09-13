# Phase 1 Data Model: Resolve the open clear-text logging alerts

**Feature**: 1034-codeql-cleartext-logging

**Date**: 2026-08-05

This feature adds no database table and no API payload. The entities below describe
documents and one small code object. The contract files in `contracts/` state the binding
format for each one.

---

## E-001: Alert

One CodeQL result for the query `py/clear-text-logging-sensitive-data`.

| Field | Type | Source | Rule |
| - | - | - | - |
| `alert_number` | integer | GitHub code scanning API | Unique. The range is 173 to 191 |
| `file_path` | string | GitHub code scanning API | A repository-relative path |
| `line_number` | integer | GitHub code scanning API | Informational. The value drifts |
| `anchor` | string | The author | See E-004. The anchor survives a line move |
| `rule_id` | string | GitHub code scanning API | Always `py/clear-text-logging-sensitive-data` |
| `severity` | string | GitHub code scanning API | Always `high` for this set |
| `tracking_issue` | integer | The author | One of 1733, 1734, 1735, 1736, 1737 |

**Relationship**: One alert holds exactly one verdict.

**State**: The GitHub security tab holds the state. The values are `open`, `dismissed`, and
`fixed`. The register does not copy the state, because a copy goes stale.

---

## E-002: Verdict

The recorded decision for one alert.

| Field | Type | Rule |
| - | - | - |
| `verdict` | enumeration | One of `fixed`, `false_positive`, `accepted_with_rationale` |
| `reason` | string | A written sentence. The field must not be empty |
| `author` | string | The GitHub user name of the decision owner |
| `decision_date` | date | The ISO date of the decision |
| `review_date` | date | Required when the verdict is not `fixed` |
| `next_review_trigger` | string | Required when the verdict is not `fixed` |

**Validation rules**:

- A row holds exactly one verdict value. A blank verdict fails the review.
- A verdict of `false_positive` states the evidence that the query misreads the value.
  Requirement FR-005 forbids a bare claim.
- A verdict of `fixed` needs no review date, because the code change removes the alert.
- A verdict of `accepted_with_rationale` names a concrete trigger. An example trigger is
  issue #886.

**State transitions**:

```text
(no row) --> proposed --> recorded --> dismissed        [false_positive]
(no row) --> proposed --> recorded --> dismissed        [accepted_with_rationale]
(no row) --> proposed --> recorded --> closed by scan   [fixed]
recorded --> reopened   [a later scan raises the same alert again]
```

The transition `recorded --> reopened` uses the anchor, not the line number. A reopened row
keeps its history and gains a new decision date.

---

## E-003: Verdict register

The single table that holds one verdict record for each alert.

**Location**: `specs/1034-codeql-cleartext-logging/verdict-register.md`

**Shape**: One Markdown table. The columns join E-001 and E-002.

| Column | Entity |
| - | - |
| `Alert` | E-001 `alert_number` |
| `Issue` | E-001 `tracking_issue` |
| `File` | E-001 `file_path` |
| `Line` | E-001 `line_number` |
| `Anchor` | E-001 `anchor` |
| `Verdict` | E-002 `verdict` |
| `Reason` | E-002 `reason` |
| `Author` | E-002 `author` |
| `Decided` | E-002 `decision_date` |
| `Review` | E-002 `review_date` |
| `Trigger` | E-002 `next_review_trigger` |

**Invariants**:

- INV-1: The row count equals 19.
- INV-2: Every `Alert` value appears once.
- INV-3: Every row holds a non-empty `Reason`.
- INV-4: A row with a verdict other than `fixed` holds a `Review` value and a `Trigger`
  value.
- INV-5: The `Reason` text of a dismissed row equals the `dismissed_comment` of the matching
  alert in the GitHub security tab.

---

## E-004: Stable anchor

A textual key that identifies a log call site after a line move.

**Format**:

```text
<file_path>::<qualified_symbol> :: "<log template fragment>"
```

**Example**:

```text
src/ssh/ssh_runner_manager.py::SSHRunnerManager._echo_plan :: "!? Target hosts: %s"
```

**Rules**:

- The qualified symbol names the class and the method. A module-level call names the module.
- The template fragment quotes the literal format string. The fragment never quotes a value.
- The anchor holds no personal data and no credential.
- A reviewer finds the row with one text search on the fragment.

---

## E-005: Suppression justification

The written note that accompanies a suppression marker in the source.

| Field | Type | Rule |
| - | - | - |
| `alert_number` | integer | Names one alert. FR-008 forbids a file-wide marker |
| `reason` | string | Matches the register `Reason` text |
| `review_date` | date | The ISO date of the next review |
| `next_review_trigger` | string | The event that forces the review |

**Placement**: The note sits in an inline comment beside the suppressed line.

**Template**:

```python
# CodeQL alert <number> dismissed as <verdict>. <reason>
# Review by <review_date>. Trigger: <next_review_trigger>.
```

This feature adds no new `# noqa` marker and no new `# nosec` marker. The dismissal lives in
the GitHub security tab, and the comment records the reason beside the code.

---

## E-006: Credential reveal request

The small code object that carries a secret to the operator screen.

**Owner**: `CredentialConsole` in `src/utils/console.py`.

| Field | Type | Rule |
| - | - | - |
| `label` | string | A non-secret name such as `ZTP Password` |
| `secret` | string | The credential. The object never logs this field |

**Behavior**:

| Destination | Action |
| - | - |
| An interactive terminal | Write the label, write the secret, write the recording warning |
| Any other destination | Write the label, write the withhold notice, write the reason |

**Logging rule**: The class logs the event and never logs the `secret` field. The log line
names the label and the outcome. The outcome is `revealed` or `withheld`.

The contract file `contracts/credential_console.md` states the full clause list.
