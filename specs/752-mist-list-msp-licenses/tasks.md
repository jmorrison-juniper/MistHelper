# Tasks: listMspLicenses

**Spec**: `specs/752-mist-list-msp-licenses/spec.md`
**Issue**: #1260

## Phase 1: Discovery

- [X] T001 Resolve `listMspLicenses` against the installed SDK, not the spec text.
      The module `mistapi.api.v1.msps.licenses` exists and the signature is
      `(mist_session, msp_id)`.
- [X] T002 Read the response schema in `documentation/mist-api-openapi31json.json`.
      The endpoint returns one aggregate object, not a list, so the exporter
      cannot run `mistapi.get_all`.
- [X] T003 Confirm `listMspLicenses` has no call site in first-party code and no
      entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

## Phase 2: Design

- [X] T004 Choose two output files over one wide row. One row would hold one
      column for each subscription field, so the column count would change every
      time the MSP buys or retires a subscription.
- [X] T005 Choose a natural primary key for each file, so a repeat run upserts.
      The summary keys on `msp_id`. The detail keys on the record `id`.
- [X] T006 Choose one detail file for both record arrays. A subscription record
      and an amendment record share their field names, so a `record_type` column
      separates them.

## Phase 3: Implementation

- [X] T007 Add `src/export/msp_license_exporter.py` with `MSPLicenseExporter`.
- [X] T008 Add `InputUtils.prompt_msp_id`, the shared prompt. It calls
      `safe_input` and rejects an empty answer, so the menu survives an EOF in an
      SSH or a container session. `CountExporter` held the only copy, and a
      second copy made Pylint report duplicate code, so menu 237 now calls the
      shared method and `CountExporter._prompt_msp_id` is deleted.
- [X] T009 Add `_fetch`, which reads `response.data` and returns an empty dict
      for a non-dict body.
- [X] T010 Add `_build_summary_row`, which keeps the counter maps and drops the
      record arrays.
- [X] T011 Add `_build_detail_rows`, which skips a non-list field and a non-dict
      entry instead of raising.
- [X] T012 Add `_persist`, which routes each write through
      `DataExporter.write_with_format_selection`.
- [X] T013 Add `licenses`, the menu entry point that holds the error handler.

## Phase 4: Wiring

- [X] T014 Import `MSPLicenseExporter` in `MistHelper.py`.
- [X] T015 Register menu 238 in `menu_actions`.
- [X] T016 Mark menu 238 `interactive_safe` in the operation registry.
- [X] T017 Add the `listMspLicenses` and `listMspLicensesDetails` primary key
      strategies.

## Phase 5: Verification

- [X] T018 Add 22 unit tests in `tests/unit/export/test_msp_license_exporter.py`
      and 4 more in `tests/unit/utils/test_input_utils_wave9.py`.
- [X] T019 Run menu 238 end to end with a stubbed SDK. Read both output files,
      confirm the EOF path makes no API call, and confirm an SDK error writes no
      file and raises nothing into the menu loop.
- [X] T020 Run py_compile, ruff, black, mypy, pydocstyle, interrogate, radon,
      vulture, bandit, and pylint.
- [X] T021 Run the export suite and the guardrail suite. 1215 tests pass.
- [X] T022 Regenerate the menu reference documentation.
- [X] T023 Correct the README operation counts, which were stale at menu 234.
- [X] T024 Add the CHANGELOG entry.
