# Data Model: Test quality: triage weak_is_not_none findings

This model tracks the baseline entries, the weak guards, the candidates, the holds, and the slices. It names each natural key and each state change.

## BaselineEntry

- **Natural key**: The five-field identity that the analyzer uses. The fields are category, rule ID, file path, line number, and explanation (installed `baseline.py` lines 48 to 55).
- **Values in this record**: Category `weak_assertion`. Rule ID `weak_is_not_none`. Explanation `assert x is not None only verifies non-None state.` File path and line number come from the baseline.
- **States**:
  - present: the line holds a weak guard.
  - repaired: the line holds one exact check. The entry leaves the baseline at the next write.
  - shifted: an edit above the line moved the finding. The baseline write records the new line.
  - held: an open reservation blocks the repair. The entry stays in the baseline.
  - stale: the line holds no weak guard. The entry leaves the baseline after analyzer confirmation.
- **Transitions by task**: T002 moves each stale entry to removed. T003 to T010 move present entries to repaired. T011 to T014 move held entries to repaired after release. T015 and T016 classify the unclassified entries.

## WeakGuard

- **Natural key**: File path and line number of the assert statement.
- **Fields**: Category (S, RC, R, H, or U). Slice (A to H, hold, or open). Statement text. Controlled wrong value. Failing-run result.
- **States**: open, then repaired (one exact check on the same line), then proven (the failing run is recorded in the pull request body), then merged.

## Candidate

- **Natural key**: Git blob SHA or commit SHA.
- **Fields**: Source (local, archive branch, or recovery branch). GitHub presence (present or absent). Use (evidence only).
- **States**: recorded (evidence only), then re-derived (a repair is made from main), or discarded (not used).
- **Rule**: A candidate never reaches a slice as a blob copy (decision D-6).

## Hold

- **Natural key**: File path and owner reference (issue or pull request number).
- **Fields**: Owner. Release condition. Status (held or released).
- **States**: held, then released (owner handoff or merge), then closed (the file leaves the campaign).

## Slice

- **Natural key**: Letter from A to H. The branch is `chore/2708-weak-is-not-none-<letter>`.
- **Fields**: Files. Lines. Pull request number. Required check result. Merge state.
- **States**: planned, then local gates passed, then pushed, then checks passed, then merged, then baseline updated.

## Relationships

- A Slice repairs one or more WeakGuard values.
- A BaselineEntry names one WeakGuard by file path and line number.
- A Hold blocks each Slice that selects its file.
- A Candidate informs a WeakGuard repair as evidence only.
