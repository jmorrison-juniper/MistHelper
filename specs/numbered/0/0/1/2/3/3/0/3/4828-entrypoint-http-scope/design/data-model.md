# Data Model: Entry-point test quality for HTTP status scope

## Entities

### Test module

- **Fields**: Repository path, import list, test case list, and state (`present` or `removed`).
- **Natural key**: Repository path in POSIX form.
- **Modules in scope**:
  - `tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_help_invocation_side_effect_free.py` (RC-01).
  - `tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_reject_unsupported_flag_variants.py` (RC-05).
  - `tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_main_entrypoint.py` (RC-11).
  - `tests/unit/refactors/test_app_context_session_state.py` (RC-13).
  - `tests/unit/config/foundation/support/refactors/runtime/console/test_fast_mode_small_seams.py` (RC-14).

### Test case

- **Fields**: Module path, class name, function name, and parameter set ID.
- **Natural key**: Module path, class name, function name, and parameter set ID.
- **Counts**: The help file holds 15 cases (T001). The reject-flag file holds 3 tests (T002). One case in `test_main_entrypoint.py` is deleted (T003).

### Baseline entry

- **Fields**: Category, rule ID, file path, line number, explanation, and severity.
- **Natural key**: Category, rule ID, file path, line number, and explanation (RC-52).
- **Entries in scope**: Four `missing_fm_http` entries for the three bootstrap modules (RC-15, RC-16, RC-17). Two stale `missing_fm_http` entries for the reject-flag module (RC-18, RC-19).

### Analyzer finding

- **Fields**: Rule ID, file path, line number, explanation, and severity.
- **Natural key**: The same key as a baseline entry (RC-52).
- **States**: `current` when a baseline entry matches. `new` when no baseline entry matches. A baseline entry without a current finding is `stale`.

### Analyzer pin

- **Fields**: Package name, commit SHA, and the three locations that name the SHA (`pyproject.toml` line 123, `requirements-dev.txt` line 197, and `uv.lock` line 1586).
- **Natural key**: Commit SHA.
- **Invariant**: All three locations name the same SHA (FR-006).

### Issue

- **Fields**: Number, state (`open` or `closed`), and labels.
- **Natural key**: Issue number.

## State Transitions

### Baseline entry

- `present` changes to `stale` when the analyzer stops reporting the finding. The two reject-flag entries are stale now (RC-18, RC-19).
- `stale` changes to `removed` when `--write-baseline` runs on the full suite (T007).
- `present` changes to `removed` when `--prune-baseline` runs for a file that no longer exists. This change does not use that path (D-4).
- A new finding never enters the baseline in this change (FR-004).

### Analyzer pin

- The current pin `2239e7bd` changes to the fixed commit after the external fix merges (T005).
- T006 verifies the pin with `uv lock --check`. T007 verifies the baseline with the full gate.
- A pin that changes only one of the three files is invalid (FR-006).

### Test case

- The duplicate argument case changes from `present` to `removed` in T003.

### Issue #4828

- The issue changes from `open` to `closed` only when the final pull request merges (FR-009, D-5).
