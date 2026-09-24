# Research: Menu 270 mode 4, the closed Marvis Actions report

**Feature**: `3342-marvis-closed-report` | **Issue**: #3342

**Spec**: [spec.md](./spec.md) | **Parent research**: [3299 research](../3299-marvis-actions-bulk-resolve/research.md)

This file records the evidence for each design decision. Each item names its
source, so a reviewer can repeat the check.

## Sources

| Source | What it gives |
| - | - |
| `src/marvis/actions/model.py` at `origin/main` 3cd54e47 | The status catalog and the `is_open` rule. |
| `src/marvis/actions/selection.py` at 3cd54e47 | The mode constants, the tables, and the answer grammar. |
| `src/marvis/actions/operation.py` at 3cd54e47 | The run flow, the stop lines, and the export step. |
| `web_portal/services/operation.py` at 3cd54e47 | The six portal controls of menu 270 and the run status rules. |
| `src/refactors/sqlite_database_writer.py` at 3cd54e47 | The SQLite write mode for a `natural_pk` table. |
| `data/OrgMarvisActions.csv` of 2026-09-24T08:23:31Z | The live export of the lab organization. |

## R1. The current modes and the open rule

`selection.py` defines three modes. Mode 1 keeps every action. Modes 2 and 3
keep the open actions only, through the flag `open_only`. The operation sets
the flag with `open_only = mode != MODE_EXPORT_ALL`.

`model.py` sets `is_open` with `status in OPEN_STATUSES`. `OPEN_STATUSES` holds
`open`, `inprogress`, and `reoccured`. Every other key, known or unknown, gives
False.

Decision: mode 4 keeps the records with `is_open` False. This rule is the exact
opposite of the rule of modes 2 and 3. Modes 2 and 4 therefore split the mode 1
rows with no overlap and no gap. A property test proves the split.

## R2. The status catalog

`STATUS_NAMES` names seven keys. Four of them are closed: `resolved` (Resolved
By User), `validated` (AI Validated), `marvis_self_driven` (Marvis Self Driven),
and `expired action` (Expired Action).

The builder writes `STATUS_NAMES.get(status, status)` into `status_name`, so an
unknown key already shows its raw text.

Decision: keep the builder as it is. Add one caution line in the export step for
the unknown keys. An unknown key can be a new open status, and Mist can add a
status without a notice. The run then counts that action as closed, and the engineer
must compare it with the Mist UI.

## R3. The live data

The export of 2026-09-24T08:23:31Z holds 112 rows. Every row is closed.

| Status | Rows |
| - | - |
| AI Validated | 111 |
| Marvis Self Driven | 1 |

No row shows Resolved By User, so the `label` column and the `comment` column
are empty. A live mode 4 run on this organization must write 112 rows, the same
count as mode 1. A live mode 2 run must stop with "No open Marvis Actions exist
in this organization."

## R4. The portal answer order

The portal row of menu 270 holds six controls: mode, category, subcategory,
resolution code, comment, and confirmation. The browser sends one answer for each
control, in control order. The input queue drops the answers that the run does
not read.

Decision: add one choice to the mode control and change no control. The report
modes 1, 2, and 4 read the first three answers only. The contract test
`test_the_mode_values_are_the_three_modes` compares the choice values with
`MODES`, so the new choice and the new mode must arrive together.

## R5. The run status rules of the portal

The portal marks a run as failed when a log line holds `could not`, `failed to`,
or `error fetching`. It marks a run as a missing input when a line holds
`no value provided`. It reads a line that starts with `No ` as the reason of an
empty result.

Decision: the new stop lines start with `No closed Marvis Actions`, so the portal
reports "Operation completed with no output file". The caution line for an
unknown status holds none of the failure words.

## R6. The unattended test pass

`UnattendedInteractiveInputProvider` answers a prompt from keyword rules. The
test `test_no_prompt_holds_a_keyword_of_the_unattended_test_pass` checks every
prompt text of menu 270.

Decision: the new prompt text adds `3,` and `or 4` only. The mode table lines go
to the log, not to the prompt, so the word `closed` never reaches the provider.
The provider still takes the default mode 1.

## R7. The database write

`SqliteDatabaseWriter._determine_insert_mode` returns `INSERT OR REPLACE` for a
`natural_pk` table. `listOrgMarvisActions` uses `natural_pk` on `uuid`.

Decision: keep one table. A mode 4 run updates the closed rows and leaves the
rows of earlier runs. The spec states this, and a database reader filters on
`is_open`.

## R8. The five-item rule

`selection.py` holds five classes, and `MarvisTopicSelector` holds five public
methods. A new class or a new public method breaks the rule that the parent plan
states.

Decision: add no class and no public method. A constant table maps each mode to
the `is_open` values that it keeps. A second table maps each mode to the words
of its stop lines. The selector takes the mode instead of `open_only`.

## Alternatives that were rejected

| Alternative | Why it was rejected |
| - | - |
| Change mode 2 to ask for a status. | A new prompt shifts every portal answer by one position. |
| A new file `OrgMarvisActionsClosed.csv`. | Two tables with the same columns force a join for each audit. |
| A filter on `status_name`. | An unknown key has no fixed name, so the filter misses it. |
| An enum class for the status rule. | It adds a sixth class to `selection.py`. |
| A Closed column in mode 4 only. | A table that changes its columns by mode confuses the reader. |
