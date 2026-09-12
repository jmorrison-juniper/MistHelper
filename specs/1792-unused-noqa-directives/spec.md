# Feature Specification: Unused Noqa Directive Removal

**Feature Branch**: `docs/lint-debt-specs` (specification only). The implementation branch is `lint/1792-unused-noqa`.

**GitHub Issue**: [#1792](https://github.com/jmorrison-juniper/MistHelper/issues/1792) — "lint: 231 unused noqa directives claim suppressions that do not exist"

**Created**: 2026-08-05

**Status**: Specification only. No code change exists yet.

**Input**: Remove the 286 `# noqa` directives that suppress nothing. Add the `RUF100` rule to the ruff `select` list, so that the count cannot grow again.

---

## Background

A `# noqa` directive is a claim. It states that a person read a lint result, judged the result acceptable, and recorded that judgment on the line.

The repository holds 286 directives that make this claim with no basis. Ruff reports each one under rule `RUF100`, which is named `unused-noqa`. No lint result sits behind any of them. The issue title states 231, because a maintainer measured that value one day earlier.

### Why no gate reports this today

The ruff `select` list in `pyproject.toml` line 164 reads as follows.

```toml
select = ["E", "F", "W", "I", "UP", "B", "G"]
```

`RUF100` sits outside that list. The CI lint gate therefore never reports these directives. The count grows without limit and without notice.

### Measured baseline

**Correction on 2026-08-06.** A second maintainer measured the counts again at commit `08a75d2` with ruff 0.16.0. Two values changed. The correct command uses `--extend-select`, not `--select`. The correct count is 286, not 231.

```powershell
.venv\Scripts\python.exe -m ruff check . --extend-select RUF100 --statistics
```

| Measurement | Value on 2026-08-05 | Value on 2026-08-06 |
| - | - | - |
| `RUF100` results under `--extend-select` | not measured | 286 |
| `RUF100` results under `--select` | 231 | 320 |
| Files that hold at least one directive | 110 | 94 under `--extend-select` |
| Results that ruff repairs without help | 231 | 286 |

**Warning**: The `--select RUF100` form disables every other rule. Ruff then reports 34 directives that suppress a real result under the project configuration. A repair that uses that form deletes those 34 directives and breaks the lint gate. The section "The isolated select trap" states the proof.

The eight files below hold 127 of the directives.

| File | Count |
| - | - |
| src/device/ap_profile_migration_manager.py | 67 |
| src/site/address_audit/ui_geocoder.py | 10 |
| src/export/site_export_utils.py | 9 |
| src/firmware/firmware_manager.py | 9 |
| src/ssid_consolidation/_ssid_template_phase45.py | 9 |
| src/reports/e911_bssid.py | 8 |
| tests/unit/refactors/test_fast_mode_small_seams.py | 8 |
| src/ssh/batch/interactive_batch_executor.py | 7 |

The directives name 12 rule codes. The six codes below cover 259 of the named codes. One directive can name more than one code, so the code total is larger than the directive total.

| Named code | Count |
| - | - |
| BLE001 blind-except | 107 |
| T201 print | 49 |
| PLC0415 import-outside-top-level | 44 |
| E402 module-import-not-at-top-of-file | 26 |
| SLF001 private-member-access | 18 |
| E501 line-too-long | 15 |

### The isolated select trap

**Warning**: A repair with the wrong command deletes 34 live suppressions and breaks the lint gate.

Ruff decides that a directive is unused when the named code produces no result **in the current run**. The `--select RUF100` form turns off `E`, `F`, `W`, `I`, `UP`, `B`, and `G`. Ruff therefore reports every `# noqa: E501` and every `# noqa: E731` as unused, even where the directive hides a real result.

| Command | `RUF100` results |
| - | - |
| `ruff check . --select RUF100` | 320 |
| `ruff check . --extend-select RUF100` | 286 |

A maintainer compared the two result sets on 2026-08-06. The 34 extra results all name a code that the project selects. The sample below shows four of them.

| Site | Named code |
| - | - |
| src/export/org_inventory_exporter.py line 246 | E501 |
| src/export/site_anomaly_exporter.py line 182 | E731 |
| tests/maps/test_viewer_callbacks_wave_a.py line 46 | E402 |
| starlink_dashboard.py line 98 | F401 |

The repair must therefore use `--extend-select RUF100 --fix`.

### The latent suppression trap

This work must land before the team adds `BLE001` to the `select` list.

Ruff reports 412 `BLE001` results when it reads the `# noqa` directives. Ruff reports 500 results when a maintainer adds `--ignore-noqa`.

| Command | `BLE001` count |
| - | - |
| Default. Ruff reads each directive. | 412 |
| With `--ignore-noqa`. Ruff skips each directive. | 500 |

The difference is 88 lines. Each of those 88 lines carries a `# noqa: BLE001` directive **and** holds a real blind `except` block. The directive changes nothing today, because ruff does not select `BLE001`. The directive starts to work on the day the team selects the rule. Ruff then hides 88 real results, and the team never sees them.

Issue [#1794](https://github.com/jmorrison-juniper/MistHelper/issues/1794) owns the blind `except` work. That issue depends on this one.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Remove every directive that suppresses nothing (Priority: P1)

A reader opens a source file. Each `# noqa` directive that remains in that file suppresses a real lint result. No directive makes a false claim.

**Why this priority**: This story delivers the whole value of the work. Ruff repairs all 286 results without help, so the cost is low and the benefit is immediate.

**Independent Test**: A reviewer runs `ruff check . --extend-select RUF100`. The command exits with code 0 and reports zero results.

**Acceptance Scenarios**:

1. **Given** the branch holds the repair, **When** a reviewer runs `ruff check . --extend-select RUF100`, **Then** the command exits with code 0 and reports zero results.
2. **Given** the branch holds the repair, **When** a reviewer reads the difference, **Then** the difference removes comment text only and changes no line of code.
3. **Given** the branch holds the repair, **When** CI runs the full gate set, **Then** each gate stays green and the unit test suite keeps its pass count.

---

### User Story 2 - Stop the count from growing again (Priority: P2)

A contributor adds a `# noqa` directive that suppresses nothing. The CI lint gate reports the directive and stops the pull request.

**Why this priority**: This story protects the result of User Story 1. Without it, the count returns. The story cannot land first, because the gate fails while the 286 results remain.

**Independent Test**: A reviewer adds one directive that suppresses nothing to a tracked file. The lint gate fails and names `RUF100`.

**Acceptance Scenarios**:

1. **Given** the updated `select` list, **When** a reviewer searches the list, **Then** the list holds `RUF100`.
2. **Given** the updated `select` list, **When** CI runs the lint gate on the clean branch, **Then** the gate succeeds.
3. **Given** a pull request that adds one directive with no matching result, **When** CI runs the lint gate, **Then** the gate fails and the log names `RUF100` and the file.

---

### User Story 3 - Protect the blind except work from a silent loss (Priority: P1)

A maintainer reads the pull request. The maintainer learns that 88 lines carried an inert `# noqa: BLE001` directive. The maintainer therefore knows that the true `BLE001` count is 500, not 412.

**Why this priority**: This story shares the P1 rank with User Story 1, because the order of the two efforts decides whether 88 results survive. A wrong order loses them in silence.

**Independent Test**: A reviewer runs `ruff check . --select BLE001 --statistics` on the branch after the repair. The count reads 500.

**Acceptance Scenarios**:

1. **Given** the branch holds the repair, **When** a reviewer runs `ruff check . --select BLE001 --statistics`, **Then** the count reads 500.
2. **Given** the branch holds the repair, **When** a reviewer runs the same command with `--ignore-noqa`, **Then** the count reads 500 and matches the value above.
3. **Given** the pull request text, **When** a maintainer of issue #1794 reads it, **Then** the text states the 88-line difference and states the correct order of the two efforts.

---

### Edge Cases

- Ruff removes the whole comment when the directive is the only text in it. Ruff keeps the rest of the comment when other text follows the directive. A reviewer must confirm that no useful comment text disappears.
- A directive names two codes. One code matches a real result and the other does not. Ruff removes the unused code and keeps the rest of the directive. The line stays.
- The ruff `extend-exclude` list drops `mist-ops-platform`, `web_portal`, `scripts`, and `src/maps`. A directive inside one of those paths stays in place. The count of 286 does not cover them.
- The repair touches `tests/unit/refactors/test_fast_mode_small_seams.py`. A test file change needs the same review care as a source file change.
- A concurrent pull request adds a new directive while this work is open. The count then changes. The implementer must measure the count again before the final push.
- `src/device/ap_profile_migration_manager.py` holds 67 of the 286 directives. That single file needs its own read, because it holds 23 percent of the work.

---

## Requirements *(mandatory)*

### Repair requirements

- **FR-001**: The repository MUST hold zero `RUF100` results after this work. The measurement command MUST use `--extend-select`.
- **FR-002**: The implementer MUST use the ruff repair command `ruff check . --extend-select RUF100 --fix`. A hand edit is forbidden, because a hand edit invites a typing mistake across 94 files. The `--select RUF100 --fix` form is forbidden, because it deletes 34 live suppressions.
- **FR-003**: The difference MUST remove comment text only. It MUST change zero lines of code.
- **FR-004**: The implementer MUST read the whole difference and MUST record the count of changed lines that are not comments. The expected count is zero.
- **FR-005**: The implementer MUST NOT run any other ruff repair in the same commit. A mixed repair hides the comment change inside a code change.

### Gate requirements

- **FR-006**: The ruff `select` list in `pyproject.toml` MUST hold `RUF100` after the repair lands.
- **FR-007**: The `select` list change MUST land in the same pull request as the repair. A later change would allow the count to grow in between.
- **FR-008**: The implementer MUST NOT add any other rule to the `select` list in this work.

### Coordination requirements

- **FR-009**: The pull request text MUST state that 88 lines carry an inert `# noqa: BLE001` directive.
- **FR-010**: The pull request text MUST state that the true `BLE001` count is 500 and that the default ruff run reports 412.
- **FR-011**: The pull request text MUST state that issue #1794 depends on this work and MUST NOT start before this work lands.

### Quality requirements

- **FR-012**: Every quality gate MUST stay green. The unit test suite MUST keep its pass count.
- **FR-013**: All prose, all code comments, and all commit text MUST follow the Simplified Technical English guide at `documentation/ASD-STE100_writing-guide.md`.
- **FR-014**: The commit text MUST name the count of removed directives and MUST name the count of touched files.

### Key Entities

- **Noqa directive**: A source comment that tells ruff to hide a result on that line. It names zero or more rule codes.
- **Unused directive**: A directive that names a code which produces no result on that line. Ruff reports it under `RUF100`.
- **Inert directive**: A directive that names a code which the `select` list does not hold. Ruff reports it under `RUF100` today. It starts to hide results on the day the team selects that code.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `ruff check . --extend-select RUF100` reports zero results and exits with code 0.
- **SC-002**: The count of changed lines that are not comments is zero.
- **SC-003**: The ruff `select` list in `pyproject.toml` holds `RUF100`.
- **SC-004**: A pull request that adds one directive with no matching result fails the CI lint gate.
- **SC-005**: `ruff check . --select BLE001 --statistics` and the same command with `--ignore-noqa` both report 500.
- **SC-006**: Every quality gate stays green. The unit test suite keeps its pass count and adds no new failure.
- **SC-007**: The pull request text states the 88-line latent suppression and names issue #1794.
- **SC-008**: The work touches zero files under `mist-ops-platform`, `web_portal`, `scripts`, and `src/maps`.

---

## Non-Goals

- **NG-001**: This work does not add `BLE001` to the `select` list. Issue #1794 owns that decision.
- **NG-002**: This work does not add `T201`, `PLC0415`, or `SLF001` to the `select` list. Issue #886 owns the `T201` decision.
- **NG-003**: This work does not repair any result that a removed directive used to name. Removal of the directive is the whole scope.
- **NG-004**: This work does not review the directives that remain. A directive that suppresses a real result stays in place with no audit.
- **NG-005**: This work does not change the ruff `extend-exclude` list. The four excluded paths keep their directives.
- **NG-006**: This work does not touch a `# nosec` comment. Bandit reads those comments and ruff does not.
- **NG-007**: This work does not touch a `# type: ignore` comment. Mypy reads those comments and ruff does not.
- **NG-008**: This work does not add any lint suppression. It removes suppressions only. A contributor who meets a new result must repair the result.
- **NG-009**: This work does not repair the 34 directives that the isolated run reports. Those directives suppress a real result and must stay in place.

---

## Assumptions

- The ruff version stays at 0.16.0 during this work. A version change can add a rule and can change the count.
- The 286 count reflects the branch tip at commit `08a75d2`. The implementer must measure the count again before the first commit. The count moved from 231 to 286 in one day, so the value is not stable.
- Ruff repairs each result without help. The `[*]` marker in the statistics output states this.
- No directive in the set carries useful comment text that a reader needs after the removal.
- The team accepts a stricter lint gate. A new directive with no matching result becomes a build failure.

---

## Dependencies

- Issue [#1794](https://github.com/jmorrison-juniper/MistHelper/issues/1794) depends on this work. It must not start before this work lands.
- Issue [#1795](https://github.com/jmorrison-juniper/MistHelper/issues/1795) depends on this work for one `DTZ005` site that a directive hides.
- Issue [#886](https://github.com/jmorrison-juniper/MistHelper/issues/886) covers the `T201` rule. 49 directives name that code. The two efforts must not edit the same lines at the same time.
- The Simplified Technical English guide at `documentation/ASD-STE100_writing-guide.md` governs all prose in this work.
