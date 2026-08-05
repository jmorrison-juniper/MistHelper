# Contract: The verdict register

**Feature**: 1034-codeql-cleartext-logging

**Artifact**: `specs/1034-codeql-cleartext-logging/verdict-register.md`

**Date**: 2026-08-05

This contract states the binding format of the verdict register. A reviewer checks a
register against the clauses below. A register that breaks any clause fails the review.

---

## C-1: The register holds one table with eleven columns

The header row reads as follows.

```markdown
| Alert | Issue | File | Line | Anchor | Verdict | Reason | Author | Decided | Review | Trigger |
| - | - | - | - | - | - | - | - | - | - | - |
```

The column order is fixed. A reader compares two revisions of the register with a plain
text difference, so a column move breaks the comparison.

---

## C-2: The register holds nineteen data rows

The row count equals the alert count. The count is 19. The `Alert` values run from 173
through 191 with no gap and no repeat.

A reviewer counts the rows with the command below.

```bash
grep -c '^| 1[78][0-9] |' specs/1034-codeql-cleartext-logging/verdict-register.md
```

The expected output is `19`.

---

## C-3: The `Verdict` column holds one of three values

The allowed values are `fixed`, `false_positive`, and `accepted_with_rationale`. No other
value passes the review. A blank cell fails the review.

---

## C-4: The `Reason` column holds a written sentence

The sentence states why the verdict is correct. The sentence follows the Simplified
Technical English rules. The cell is never blank and never reads `see above`.

A row with the verdict `false_positive` states the evidence that the query misreads the
value. A bare claim of a false positive fails the review, because requirement FR-005 makes a
code fix the default action.

---

## C-5: A non-fixed row holds a review date and a trigger

A row with the verdict `false_positive` or `accepted_with_rationale` fills the `Review`
column and the `Trigger` column. Requirement FR-007 requires both fields.

The `Review` value is an ISO date. The `Trigger` value names a concrete event. An example
event is the merge of issue #886.

A row with the verdict `fixed` writes `-` in both columns, because the code change removes
the alert.

---

## C-6: The `Anchor` column survives a line move

The anchor format follows entity E-004 in `data-model.md`.

```text
<file_path>::<qualified_symbol> :: "<log template fragment>"
```

The anchor holds no street address, no coordinate, no MAC address, and no credential. The
anchor quotes the format string only.

---

## C-7: A dismissal reason matches the register reason

The team dismisses each alert with the verdict `false_positive` or
`accepted_with_rationale`. The dismissal comment repeats the register `Reason` text.

The dismissal command follows.

```bash
gh api -X PATCH "repos/:owner/:repo/code-scanning/alerts/<alert_number>" \
  -f state=dismissed \
  -f dismissed_reason="<api_reason>" \
  -f dismissed_comment="<register_reason>"
```

The `api_reason` value maps from the register verdict.

| Register verdict | `api_reason` |
| - | - |
| `false_positive` | `false positive` |
| `accepted_with_rationale` | `won't fix` |
| `fixed` | No dismissal |

---

## C-8: The reconciliation command proves clause C-7

A reviewer lists every dismissed alert and compares the output against the register.

```bash
gh api "repos/:owner/:repo/code-scanning/alerts?state=dismissed&per_page=100" \
  --jq '.[] | select(.rule.id=="py/clear-text-logging-sensitive-data")
        | "\(.number)|\(.dismissed_reason)|\(.dismissed_comment)"'
```

Each line of the output matches one register row. A line with no matching row fails the
review. A register row with no matching line fails the review.

---

## C-9: The open alert count reaches zero

The command below reports the open alert count for the query.

```bash
gh api "repos/:owner/:repo/code-scanning/alerts?state=open&per_page=100" \
  --jq '[.[] | select(.rule.id=="py/clear-text-logging-sensitive-data")] | length'
```

The expected output at the end of the feature is `0`. The command returned `19` on
2026-08-05, and that value is the baseline.

---

## C-10: The five tracking issues link to the register

Each of the issues 1733, 1734, 1735, 1736, and 1737 holds a comment with the register path.
The comment names the rows that belong to that issue. Requirement FR-003 requires the link.

---

## C-11: A reopened alert keeps its history

A later scan can raise the same alert again after a code change. The register then adds a
new row for the new alert number. The new row names the earlier alert number inside the
`Reason` text.

The team does not delete the earlier row. The register is an audit record, so the history
stays.
