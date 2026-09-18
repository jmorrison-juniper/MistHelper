# Tasks: Org-wide rogue DHCP server scan

**Feature**: `2985-rogue-dhcp-scan` | **Issue**: #2985

**Input**: [spec.md](./spec.md), [plan.md](./plan.md)

Each task names its files. A task marked `[P]` can run beside another `[P]` task
in the same phase, because the two tasks touch no common file.

## Phase 1: Foundation

- [ ] **T001** Add the primary key strategy `scanOrgRogueDhcpServers` to
  `src/refactors/endpoint_primary_key_strategies.py`. Use `composite_pk` with the
  key `["record_id", "site_id", "last_seen"]` and the index list from the plan.
  The constitution requires this entry before any code writes a row.

- [ ] **T002** Create the package `src/security/rogue_dhcp/` with an `__init__.py`
  that exports `RogueDhcpScanOperation`, `RogueDhcpScanner`, `RogueDhcpFinding`,
  and `RogueDhcpSignalMatcher`. Create `tests/unit/security/rogue_dhcp/__init__.py`.

## Phase 2: User Story 1 -- the scan (P1)

### The matcher

- [ ] **T003** Write `src/security/rogue_dhcp/signals.py`. Define
  `ROGUE_ALARM_TYPES`, `ROGUE_EVENT_TYPES`, `MARVIS_CONFIG_EVENT_TYPE`,
  `MARVIS_ROGUE_REASON`, `REJECTED_DHCP_TYPES`, and `KEYWORD_PAIR`. Define the
  class `RogueDhcpSignalMatcher` with `matches`, `is_rejected`,
  `alarm_type_filter`, and `event_type_filters`. Satisfies FR-005 to FR-010.

- [ ] **T004** `[P]` Write `tests/unit/security/rogue_dhcp/test_signals.py`. Cover
  each literal accept, the Marvis reason rule, the keyword accept with an unknown
  type, the reject list, and letter case.

### The record shape

- [ ] **T005** Write `src/security/rogue_dhcp/records.py`. Define the frozen
  dataclass `RogueDhcpFinding` with the 19 columns from the plan and a
  `column_names()` class method. Define `RogueDhcpRecordNormalizer` with one
  method for each source shape, one state method, and one merge method.
  Satisfies FR-015 to FR-020.

- [ ] **T006** `[P]` Write `tests/unit/security/rogue_dhcp/test_records.py`. Cover
  the shared column set, the merge of a duplicate, the sum of the counts, the
  earliest first seen, the latest last seen, the joined source list, and the
  active and historical states.

### The scanner

- [ ] **T007** Write `src/security/rogue_dhcp/scanner.py`. Define
  `RogueDhcpScanResult` and `RogueDhcpScanner`. Implement `scan`,
  `query_organization`, `query_site`, and `resolve_site_names`. Use
  `mistapi.get_all` for paging. Wrap each site query in a try block that records
  the failure and continues. Satisfies FR-011 to FR-014 and FR-025 to FR-028.

- [ ] **T008** `[P]` Write `tests/unit/security/rogue_dhcp/test_scanner.py`. Cover
  the organization-first order, the named-site rule, the failure isolation, the
  30-day window, the failed-site count, and the empty organization.

### The operation

- [ ] **T009** Write `src/security/rogue_dhcp/operation.py`. Define
  `RogueDhcpScanOperation.run`. Resolve the organization, run the scanner, print
  the table and the per-source counts, and call
  `DataExporter.write_with_format_selection` with the endpoint name
  `scanOrgRogueDhcpServers`. Return without a write when the result is empty.
  Satisfies FR-021 to FR-024.

- [ ] **T010** `[P]` Write `tests/unit/security/rogue_dhcp/test_operation.py`.
  Cover the export call arguments, the empty-result path, the printed summary,
  and the failed-site report.

### The menu

- [ ] **T011** Add `"269": {"category": "safe"}` to
  `src/utils/operation_registry.py`. Satisfies FR-002.

- [ ] **T012** Add the `menu_actions` row for `"269"` in `MistHelper.py`. Point
  the handler at `RogueDhcpScanOperation.run`. Add the import. Satisfies FR-001.

- [ ] **T013** Raise `EXPECTED_MENU_ENTRY_COUNT` from 268 to 269 in
  `tests/unit/test_menu_entry_metadata.py`.

## Phase 3: User Story 2 -- durable output (P2)

- [ ] **T014** Confirm that the export writes the CSV file under `data/` and that
  the polyglot route receives the rows. Add the assertion to
  `tests/unit/security/rogue_dhcp/test_operation.py`.

- [ ] **T015** `[P]` Write `tests/property/test_rogue_dhcp_properties.py` with
  Hypothesis. Assert that the merge never returns a longer list than its input,
  and that the normalizer always returns the declared column set.

## Phase 4: User Story 3 -- the operations web dashboard (P3)

- [ ] **T016** Add `PORTAL_EXPLICIT_ALLOWLIST` to
  `web_portal/services/operation.py` and read it in `_is_portal_runnable`. Add the
  range `(269, 269, "Network Security Scans")` to `CATEGORY_RANGES`. Satisfies
  FR-029 and FR-030.

- [ ] **T017** Add the description row for `"269"` to
  `web_portal/menu_registry.py`, so the portal shows the operation when it starts
  without the MistHelper command line.

- [ ] **T018** `[P]` Write
  `tests/guardrails/test_rogue_dhcp_portal_exposure.py`. Prove that the gate
  admits 269, that it still refuses a destructive number, that it still refuses an
  unparseable key, and that the allowlist cannot admit an operation the registry
  does not call safe. Satisfies the guard proof rule.

- [ ] **T019** Confirm that no file under `src/upgrade_portal/` changed. Satisfies
  FR-031.

## Phase 5: Documentation and release note

- [ ] **T020** `[P]` Update the operation count and the menu table in `README.md`.

- [ ] **T021** `[P]` Run `python scripts/generate_menu_wiki.py` to regenerate
  `documentation/wiki/Menu-Reference.md`.

- [ ] **T022** `[P]` Add `changelog.d/issue-2985-rogue-dhcp-scan.md` with one
  `### Added` heading and one bullet that names issue #2985.

## Phase 6: Validation

- [ ] **T023** Run `python -m py_compile MistHelper.py` and every new module.

- [ ] **T024** Run `python -m ruff check .`. Repair every finding.

- [ ] **T025** Run `python -m black --check .`. Repair every finding.

- [ ] **T026** Run `python -m mypy` over the scope in `.github/workflows/ci.yml`.
  Repair every finding.

- [ ] **T027** Run the new tests, then the guardrail suite, then the full unit
  suite. Repair every failure and repeat until clean.

- [ ] **T028** Run `python -m pylint` on the new package. The score must reach
  9.5 or higher.

- [ ] **T029** Run `python -m bandit` on the new package. Resolve every finding.
  Never suppress one.

- [ ] **T030** Run `python -m radon cc` on the new package. No block may exceed
  complexity 10.

- [ ] **T031** Run `python -m vulture` at confidence 70, `python -m pydocstyle`,
  and `python -m interrogate`. Repair every finding.

- [ ] **T032** Run `python -m pytest --cov` on the new package. Coverage must
  reach 80 percent or more.

- [ ] **T033** Run `python -m tools.symbol_diff --base origin/main` on every
  changed file. No module-level name may be lost.

## Phase 7: Delivery

- [ ] **T034** Commit with a Conventional Commits message that names issue #2985.

- [ ] **T035** Push the branch and open the pull request with the template.

- [ ] **T036** Wait for every required check, including CodeQL.

- [ ] **T037** Merge to `main` and confirm the merge.

- [ ] **T038** Record the outcome in issue #2985 and remove the worktree.

## Dependencies

```text
T001, T002  -> everything
T003 -> T004, T005, T007
T005 -> T006, T007, T009
T007 -> T008, T009
T009 -> T010, T012, T014
T011, T012 -> T013, T016
T016 -> T018
T003..T022 -> T023..T033
T023..T033 -> T034..T038
```

## Parallel opportunities

- T004, T006, T008, T010 write four separate test files. They can run together
  once their source module exists.
- T020, T021, T022 touch three separate documentation files.
- T015 and T018 touch two separate test files.
