# Feature Specification: Small Correctness Rule Cleanup

**Feature Branch**: `docs/1792-1796-lint-debt-specs` (specification only). The implementation branch is `lint/1795-small-correctness`.

**GitHub Issue**: [#1795](https://github.com/jmorrison-juniper/MistHelper/issues/1795) — "lint: five small correctness rule families report 137 findings that no gate sees"

**Created**: 2026-08-06

**Status**: Specification only. No code change exists yet.

**Input**: Clear six small rule families. Add the ruff rules to the `select` list. One family names a real cross-platform defect.

---

## Background

Six small rule families report findings across the repository. No quality gate reports any of them today. Five families come from ruff. One family comes from pylint.

Each family is small enough to clear in one effort. One family names a real defect that changes the content of a file between Windows and Linux.

### Why no gate reports this today

The ruff `select` list in `pyproject.toml` line 164 reads as follows.

```toml
select = ["E", "F", "W", "I", "UP", "B", "G"]
```

`RUF012`, `DTZ005`, `ISC004`, `C408`, and `SIM103` all sit outside that list. The CI lint gate therefore never reports them.

The pylint gate does read `W1514`. The CI pylint job passes today, so the 5 sites did not fail a build. The implementer must confirm the current pylint job scope before the work starts, because pull request #1788 changed that scope.

### Measured baseline

A maintainer measured the counts on 2026-08-06 at commit `08a75d2` with ruff 0.16.0 and pylint 4.0.6.

```powershell
.venv\Scripts\python.exe -m ruff check . --select DTZ005,ISC004,C408,RUF012,SIM103 --statistics
.venv\Scripts\python.exe -m pylint MistHelper.py src --disable=all --enable=W1514 --score=n
```

| Rule | Tool | Count | Files | Name |
| - | - | - | - | - |
| RUF012 | ruff | 60 | 32 | mutable-class-default |
| DTZ005 | ruff | 56 | 26 | call-datetime-now-without-tzinfo |
| ISC004 | ruff | 13 | 3 | implicit-string-concatenation-in-collection-literal |
| SIM103 | ruff | 9 | 9 | needless-bool |
| W1514 | pylint | 5 | 4 | unspecified-encoding |
| C408 | ruff | 3 | 2 | unnecessary-collection-call |
| **Total** | | **146** | | |

### Correction: the issue names five families and the total is 137

Issue #1795 names five families. Those five are `RUF012`, `DTZ005`, `ISC004`, `W1514`, and `C408`. Their total reads 60 + 56 + 13 + 5 + 3, which equals 137. That value is correct.

A later verification command replaced `W1514` with `SIM103`. That command reports 60 + 56 + 13 + 9 + 3, which equals 141. Both totals describe a different family set.

This specification covers all six families and states 146 as the total. The extra family is `SIM103`, which reports 9 sites. That family is small, mechanical, and shares the same gate change, so it belongs in the same effort.

### W1514 names the real defect

The `open()` function with no `encoding` argument uses the platform default encoding. Windows returns `cp1252`. Linux returns `utf-8`.

MistHelper runs on a Windows workstation and inside a Linux container. A file that MistHelper writes on Windows under `cp1252` does not read back the same on Linux under `utf-8`. Any character above code point 127 changes or raises a decode error.

The 5 sites are as follows.

| File | Line |
| - | - |
| MistHelper.py | 777 |
| MistHelper.py | 1154 |
| src/config/config_utils.py | 84 |
| src/utils/rate_limiting.py | 134 |
| src/utils/rate_limiting.py | 163 |

Two of these files hold state that moves between a workstation and a container. `src/utils/rate_limiting.py` reads and writes the adaptive delay metrics. `src/config/config_utils.py` reads the project configuration.

### DTZ005 changes behavior, so it needs the most care

The `datetime.now()` call returns a naive value with no time zone. Rule `DTZ005` asks for an aware value.

A conversion from naive to aware can change the result of a comparison. Two naive values compare without error. A naive value and an aware value raise `TypeError` when they compare.

Pull request #1791 converted 4 of these sites. The author proved that the printed output stayed byte identical after the change. This work applies the same proof to every remaining site.

One further site hides behind a `# noqa` directive. Ruff reports 56 sites by default and 57 sites with `--ignore-noqa`. Issue #1792 removes that directive.

The six files with the most sites are as follows.

| File | Count |
| - | - |
| src/firmware/bulk_switch_upgrader.py | 5 |
| src/firmware/firmware_manager.py | 5 |
| src/site/bulk_radius_wlan_config_manager.py | 4 |
| src/ssh/batch/interactive_batch_executor.py | 4 |
| src/firmware/org_ap_upgrader.py | 3 |
| src/reports/e911_bssid.py | 3 |

### RUF012 is a typing rule, not a runtime defect

Rule `RUF012` asks for a `ClassVar` annotation on a class attribute that holds a mutable default. A shared mutable default is a common Python trap. The 60 sites here are class constants, not instance state.

The repair adds `typing.ClassVar` to each annotation. The change is mechanical. Run mypy after each file, because a wrong annotation changes the inferred type.

The six files with the most sites are as follows.

| File | Count |
| - | - |
| src/analytics/site_analytics_configurator.py | 6 |
| src/utils/address_utils.py | 4 |
| starlink_dashboard.py | 4 |
| src/export/const_definitions_exporter.py | 3 |
| src/firmware/firmware_manager.py | 3 |
| src/reports/e911_bssid.py | 3 |

### ISC004, SIM103, and C408 are small and mechanical

Rule `ISC004` reports 13 sites in 3 files. The rule finds two string parts joined by an implicit concatenation inside a list or a tuple. A missing comma produces the same shape, so each site needs a read before the edit.

| File | Count |
| - | - |
| tools/refactor_analyzer/reporting.py | 8 |
| MistHelper.py | 4 |
| src/websocket/diagnostics/arp_executor.py | 1 |

Rule `SIM103` reports 9 sites in 9 files. Each site holds an `if` block that returns `True` and an `else` block that returns `False`. The repair returns the condition directly.

| File | Line |
| - | - |
| src/api/api_data_fetcher.py | 163 |
| src/audit/filter.py | 50 |
| src/cache/cache_utils.py | 198 |
| src/websocket/service_ping_manager.py | 416 |
| tests/unit/org/test_org_synthetic_probes_manager.py | 2491 |
| tools/codemod_logging_lazy.py | 276 |
| tools/compliance_analyzer/analyzers.py | 935 |
| tools/ste_linter/parsing/markdown.py | 89 |
| tools/test_quality_analyzer/discovery.py | 64 |

Rule `C408` reports 3 sites in 2 files. Each site calls `dict()` where a `{}` literal works.

| File | Count |
| - | - |
| MistHelper.py | 2 |
| tests/unit/troubleshooting/test_marvis_troubleshoot_utils_extended.py | 1 |

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read a file the same way on both platforms (Priority: P1)

An operator writes a metrics file on a Windows workstation. The operator then copies that file into a Linux container. The container reads every character without a change and without an error.

**Why this priority**: This story removes the only real defect in the whole feature. The other five families report a style question or a typing question.

**Independent Test**: A reviewer writes a file that holds a character above code point 127 on Windows. The reviewer reads that file inside a Linux container. The two contents match byte for byte.

**Acceptance Scenarios**:

1. **Given** a repaired `open()` call, **When** a reviewer reads the source line, **Then** the call names `encoding="utf-8"`.
2. **Given** a repaired module, **When** a reviewer runs `pylint --enable=W1514` on it, **Then** the command reports zero results.
3. **Given** a metrics file that a Windows run writes, **When** a Linux container reads that file, **Then** every character matches.
4. **Given** the whole tree, **When** a reviewer searches for an `open()` call with no encoding, **Then** the search returns zero matches.

---

### User Story 2 - Keep the printed output identical after a time zone change (Priority: P1)

A reviewer converts a naive `datetime.now()` call to an aware call. The reviewer then runs the affected operation and compares the printed output against the earlier output. The two outputs match byte for byte.

**Why this priority**: This story shares the P1 rank, because `DTZ005` is the only family that can change behavior. A wrong conversion raises `TypeError` on a comparison or shifts a printed timestamp.

**Independent Test**: A reviewer captures the printed output of one affected operation before the change and after the change. The two captures match.

**Acceptance Scenarios**:

1. **Given** a converted site, **When** a reviewer compares the printed output before and after, **Then** the two outputs match byte for byte.
2. **Given** a converted site, **When** the code compares that value against another datetime value, **Then** the comparison raises no `TypeError`.
3. **Given** a converted site, **When** a reviewer reads the pull request body, **Then** the body records the proof for that site.
4. **Given** the whole tree, **When** a reviewer runs `ruff check . --select DTZ005 --ignore-noqa`, **Then** the command reports zero results.

---

### User Story 3 - Stop the six families from growing again (Priority: P2)

A contributor adds a naive `datetime.now()` call. The CI lint gate reports the call and stops the pull request.

**Why this priority**: This story protects the result of the first two stories. The story cannot land first, because the gate fails while any result remains.

**Independent Test**: A reviewer adds one naive `datetime.now()` call to a tracked file. The lint gate fails and names `DTZ005`.

**Acceptance Scenarios**:

1. **Given** the updated `select` list, **When** a reviewer searches the list, **Then** the list holds `RUF012`, `DTZ005`, `ISC004`, `C408`, and `SIM103`.
2. **Given** the updated `select` list, **When** CI runs the lint gate on the clean branch, **Then** the gate succeeds.
3. **Given** a pull request that adds one site in any of the six families, **When** CI runs the gate set, **Then** a gate fails and the log names the rule and the file.

---

### Edge Cases

- An `ISC004` site holds a missing comma instead of a deliberate concatenation. The repair then changes the list length and changes behavior. Each site needs a read before the edit.
- A `RUF012` annotation names the wrong type. Mypy then infers a wrong type for every reader of that attribute. Run mypy after each file.
- A `DTZ005` site feeds a value into a filename. An aware value prints a time zone offset, which changes the filename. The proof must cover the filename, not the log text alone.
- A `DTZ005` site compares its value against a naive value from another module. The comparison then raises `TypeError`. The repair must convert both sides or neither.
- A `SIM103` site returns the condition where the condition is not a boolean. The repair then changes the return type. Read each site and confirm that the condition is a boolean.
- One `DTZ005` site hides behind a `# noqa` directive. Ruff reports 56 by default and 57 with `--ignore-noqa`. Issue #1792 removes the directive.
- A `W1514` site opens a binary file. A binary mode takes no encoding argument, and the rule does not report it. Confirm the mode before the edit.
- The `RUF012` and `DTZ005` families both touch `src/firmware/firmware_manager.py` and `src/reports/e911_bssid.py`. The two repairs must not run at the same time in the same file.

---

## Requirements *(mandatory)*

### Repair requirements

- **FR-001**: Every `open()` call in the tree MUST name an explicit encoding, or MUST use a binary mode.
- **FR-002**: The `W1514` repair MUST use `encoding="utf-8"`. It MUST NOT use the platform default and MUST NOT use another encoding.
- **FR-003**: Every `C408` site MUST use a literal instead of a `dict()` call.
- **FR-004**: Every `ISC004` site MUST receive a read before the edit. The implementer MUST confirm that the author did not drop a comma.
- **FR-005**: Every `SIM103` site MUST return a boolean after the repair. The implementer MUST confirm that the condition is a boolean.
- **FR-006**: Every `RUF012` site MUST receive a `typing.ClassVar` annotation. The implementer MUST run mypy after each file.
- **FR-007**: Every `DTZ005` site MUST receive a proof that the printed output stayed byte identical. Pull request #1791 records the model.
- **FR-008**: A `DTZ005` repair MUST NOT leave a comparison between a naive value and an aware value.
- **FR-009**: The `DTZ005` scope MUST use the count with `--ignore-noqa`, which reads 57.

### Order requirements

- **FR-010**: The families MUST land in order of risk. The order is `W1514`, then `C408`, then `SIM103`, then `ISC004`, then `RUF012`, then `DTZ005`.
- **FR-011**: Each family MUST land in its own pull request.
- **FR-012**: The `DTZ005` family MUST NOT start before issue #1792 lands, because one site hides behind a directive.
- **FR-013**: The `RUF012` family and the `DTZ005` family MUST NOT edit the same file at the same time.

### Gate requirements

- **FR-014**: The ruff `select` list in `pyproject.toml` MUST hold `RUF012`, `DTZ005`, `ISC004`, `C408`, and `SIM103` after the last repair lands.
- **FR-015**: The gate change MUST land in its own pull request, after every family reports zero results.
- **FR-016**: The implementer MUST confirm the current pylint job scope in `.github/workflows/ci.yml` and MUST confirm that the job reads every file that holds a `W1514` site.
- **FR-017**: The implementer MUST NOT add any other rule to the `select` list in this work.

### Quality requirements

- **FR-018**: Every quality gate MUST stay green for each family. The unit test suite MUST keep its pass count.
- **FR-019**: All prose, all code comments, and all commit text MUST follow the Simplified Technical English rules in `documentation/ASD-STE100_writing-guide.md`.
- **FR-020**: Every changed Python line MUST carry an inline comment that explains why the line exists.

### Key Entities

- **Rule family**: One lint rule and the set of sites that it reports.
- **Byte-identical proof**: A record that shows the printed output before a change and after a change, and states that the two match.
- **Hidden site**: A site that a `# noqa` directive suppresses. Ruff reports it only with `--ignore-noqa`.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `ruff check . --select RUF012,DTZ005,ISC004,C408,SIM103 --ignore-noqa` reports zero results and exits with code 0.
- **SC-002**: `pylint MistHelper.py src --disable=all --enable=W1514` reports zero results.
- **SC-003**: A text search of the tree finds zero `open()` calls in text mode without an encoding argument.
- **SC-004**: Every `DTZ005` change carries a written record that the printed output stayed the same.
- **SC-005**: The count of `ISC004` sites that held a missing comma is recorded. The expected value is zero, and a value above zero names a real defect that the work repaired.
- **SC-006**: The ruff `select` list holds all five ruff rules.
- **SC-007**: A pull request that adds one site in any of the six families fails a CI gate.
- **SC-008**: Every quality gate stays green. The unit test suite keeps its pass count and adds no new failure.
- **SC-009**: A file that a Windows run writes reads back with identical content inside a Linux container.

---

## Non-Goals

- **NG-001**: This work does not add any lint suppression. It adds no `# noqa` directive and adds no rule to the ruff `ignore` list or the pylint `disable` list. The whole point is a repair, not a hidden result.
- **NG-002**: This work does not change the time zone that the code uses. It adds the time zone information to a naive value and keeps the same instant.
- **NG-003**: This work does not convert a naive value that a third-party library returns. The scope covers the call sites in this repository.
- **NG-004**: This work does not add the whole `DTZ` family, the whole `RUF` family, the whole `ISC` family, the whole `C4` family, or the whole `SIM` family to the `select` list. It adds the five named rules only.
- **NG-005**: This work does not remove the `# noqa` directive that hides one `DTZ005` site. Issue #1792 owns that scope.
- **NG-006**: This work does not change the ruff `extend-exclude` list. The four excluded paths keep their sites.
- **NG-007**: This work does not change the encoding of any file that the repository already holds. It changes the code that reads and writes a file.
- **NG-008**: This work does not change the pylint job scope in `.github/workflows/ci.yml`. It confirms the scope and records the result.

---

## Assumptions

- The ruff version stays at 0.16.0 and the pylint version stays at 4.0.6 during this work. A version change can move any count.
- The counts reflect the branch tip at commit `08a75d2`. The implementer must measure each count again before the family starts.
- Every `W1514` site opens a text file. A binary site takes no encoding argument, and the rule does not report it.
- Every `RUF012` site holds a class constant, not instance state. The implementer must confirm this before each annotation.
- Every `SIM103` condition returns a boolean. The implementer must confirm this before each repair.
- The `utf-8` encoding is correct for every file that MistHelper reads and writes. No file uses another encoding on purpose.
- Pull request #1791 proved the byte-identical result for 4 `DTZ005` sites. The same method works for the other 53.

---

## Dependencies

- Issue [#1792](https://github.com/jmorrison-juniper/MistHelper/issues/1792) removes the `# noqa` directive that hides one `DTZ005` site. The `DTZ005` family must not start before that work lands.
- Pull request #1791 converted 4 `DTZ005` sites and recorded the byte-identical proof. This work follows that model.
- Pull request #1788 changed the pylint job scope. Requirement FR-016 demands a check of the current scope.
- The Simplified Technical English rules in `documentation/ASD-STE100_writing-guide.md` govern all prose in this work.
