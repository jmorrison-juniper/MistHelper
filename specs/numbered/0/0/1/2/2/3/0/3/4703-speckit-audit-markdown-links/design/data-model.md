# Data Model: SpecKit Task Audit Link and Legend Classification

**Date**: 2026-11-26

This model describes the data that the SpecKit task audit reads and reports. The audit stores nothing. Each run reads the tasks files and prints a report.

## TaskMarkerLine

One line of a `tasks.md` file under a feature record.

- **Natural key**: The repository-relative path of the `tasks.md` file, plus the one-based line number.
- **Attributes**: path, line number, raw text, fence state (inside or outside a fenced code block), box text (the text between the brackets), and classification.
- **Classification states**:
  - `checked`: a line that matches a box with `x` or `X`.
  - `unchecked`: a line that matches a box with a space.
  - `malformed`: a bullet with a bracketed label that is not a link, a legend, a defined reference, or prose. It holds a task ID.
  - `not a marker`: a link line, a legend line, a reference definition, a fenced line, or prose.

The rule for `malformed` is the rule in `_is_malformed` at commit `2239e7bd` (RC-23). The rule at `e8e093d` (RC-20) counted every bracketed bullet as malformed. This change narrows the rule to the states above.

### State transitions

- `not a marker` to `malformed`: an author writes a bullet with an invalid box and a task ID. The bullet is not a link or a legend.
- `malformed` to `checked` or `unchecked`: an author repairs the box to `[x]` or `[ ]`.
- `unchecked` to `checked`: an author completes the task and cites its evidence.
- `checked` to `unchecked`: an author reopens the task.
- Any state to `not a marker`: an author changes the line to a link, a legend, or a reference definition. The audit counts the line as not a marker.

Caution: Do not change a line to a link or a legend only to remove it from the count. The change hides a real task.

## AuditTotals

The summary of one audit run. It exists only in the printed report.

- **Natural key**: The audit run, identified by the timestamp of the CI job.
- **Attributes**: feature record count, task file count, task marker count, checked count, unchecked count, malformed count, and the list of malformed line references.
- **Relationship**: Each total is the sum of the `TaskMarkerLine` classes across all `tasks.md` files in the run.

## PinnedDevtoolsCommit

The misthelper-devtools commit that supplies the audit code.

- **Natural key**: The 40-character commit SHA in `requirements-dev.txt` line 197.
- **States**:
  - `pinned without repair`: `e8e093d` (RC-12) or `79a5e459` (R2 in `design/research.md`).
  - `pinned with repair`: `2239e7bd` (RC-11), which contains commit `da96d6e` (R3 in `design/research.md`).
- **Transition**: `pinned without repair` to `pinned with repair` by one edit of `requirements-dev.txt` line 197. This record does not require that edit, because the pin already holds `2239e7bd`.

## Relationships

- `AuditTotals` aggregates `TaskMarkerLine` classes for each `tasks.md` file.
- `PinnedDevtoolsCommit` selects the classification rule that `TaskMarkerLine` uses.
- The regression tests read the classification of two fixed sample lines and one fixed marker. Each test writes its own fixture file, so the tests do not depend on the repository records.
