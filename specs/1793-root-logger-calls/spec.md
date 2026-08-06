# Feature Specification: Module Logger Migration

**Feature Branch**: `docs/1792-1796-lint-debt-specs` (specification only). The implementation branch is `refactor/1793-module-logger`.

**GitHub Issue**: [#1793](https://github.com/jmorrison-juniper/MistHelper/issues/1793) — "refactor: 4478 logging calls use the root logger instead of a module logger"

**Created**: 2026-08-06

**Status**: Specification only. No code change exists yet.

**Input**: Replace every root logger call with a named module logger. Add the `LOG015` rule to the ruff `select` list after the last slice lands.

---

## Background

A call such as `logging.info("...")` sends the record to the root logger. A call such as `logger.info("...")` sends the record to a logger that carries the module name.

The record from a root logger call carries no module name. The logging framework cannot route that record by module and cannot filter that record by module. An operator who wants debug output from the firmware path must raise the level on the root logger. The operator then receives debug output from every module at once.

The repository holds 4478 root logger calls. Ruff reports each one under rule `LOG015`, which is named `root-logger-call`.

### Why no gate reports this today

The ruff `select` list in `pyproject.toml` line 164 reads as follows.

```toml
select = ["E", "F", "W", "I", "UP", "B", "G"]
```

`LOG015` belongs to the `LOG` family. That family sits outside the `select` list. The CI lint gate therefore never reports these calls. The count grows without limit and without notice.

### Measured baseline

A maintainer measured the counts on 2026-08-06 at commit `08a75d2` with ruff 0.16.0.

```powershell
.venv\Scripts\python.exe -m ruff check . --select LOG015 --statistics
```

| Measurement | Value |
| - | - |
| `LOG015` results | 4478 |
| Files that hold at least one call | 223 |
| Results that ruff repairs without help | 0 |

The count matches the value in issue #1793 exactly.

### The counts for each area

| Area | Count |
| - | - |
| src/export | 678 |
| src/firmware | 501 |
| src/refactors | 423 |
| MistHelper.py | 303 |
| src/gateway | 261 |
| src/capture | 220 |
| src/org | 191 |
| src/device | 182 |
| src/site | 156 |
| src/troubleshooting | 150 |
| tests | 134 |
| src/auth | 131 |
| src/inventory | 131 |
| src/ui | 131 |

Every other area holds fewer than 131 calls.

### The counts for the largest files

| File | Count |
| - | - |
| MistHelper.py | 303 |
| src/firmware/firmware_manager.py | 228 |
| src/firmware/org_ap_upgrader.py | 143 |
| src/firmware/bulk_ap_upgrader.py | 105 |
| src/org/org_ticket_manager.py | 86 |
| src/troubleshooting/marvis_troubleshoot_utils.py | 76 |
| src/org/org_config_migration_manager.py | 60 |
| src/ssh/ssh_runner_manager.py | 57 |
| src/troubleshooting/interactive_test_runner.py | 57 |
| src/device/prompt_utils.py | 56 |

### The project rule that shapes this work

The file `.github/copilot-instructions.md` states a NON-NEGOTIABLE rule for action logging. Each meaningful action logs before the action and logs after the action. Each message uses the lazy `%s` argument form that issue #429 delivered.

This work must keep every one of those records. It changes the logger object and nothing else. A change to a level or to a message text would break the action logging rule and would break the operator playbooks that read the messages.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Filter the log output by module (Priority: P1)

An operator debugs the firmware upgrade path. The operator raises the level for `src.firmware` alone. Every other module keeps its current level. The operator reads the firmware records without the other 3977 call sites.

**Why this priority**: This story delivers the whole operator value. A named logger is the only way to route a record by module.

**Independent Test**: An operator sets the level of the `src.firmware` logger to `DEBUG` and leaves the root logger at `INFO`. The operator then runs a firmware operation and reads debug records from the firmware modules only.

**Acceptance Scenarios**:

1. **Given** a converted module, **When** an operator raises the level for that module logger alone, **Then** the operator reads the debug records from that module and reads no debug record from another module.
2. **Given** a converted module, **When** a record reaches a handler, **Then** the record carries the module name in the `name` field.
3. **Given** a converted module, **When** a reviewer compares the message text against the earlier text, **Then** the two texts match byte for byte.
4. **Given** a converted module, **When** a reviewer compares the log level of each call against the earlier level, **Then** the two levels match.

---

### User Story 2 - Land the change in slices that a reviewer can read (Priority: P1)

A reviewer opens one pull request. The pull request holds one area. The reviewer reads the whole difference and confirms that only the logger object changed.

**Why this priority**: This story shares the P1 rank, because 4478 call sites in one pull request cannot receive a real review. A review that nobody can perform delivers no safety.

**Independent Test**: A reviewer counts the changed lines in any slice pull request. The count stays inside the stated limit.

**Acceptance Scenarios**:

1. **Given** any slice pull request, **When** a reviewer counts the changed lines, **Then** the count stays at or below 500.
2. **Given** any slice pull request, **When** a reviewer reads the file list, **Then** every file belongs to one area.
3. **Given** any slice pull request, **When** CI runs the gate set, **Then** every gate stays green and the unit test suite keeps its pass count.
4. **Given** the slice order, **When** a reviewer reads the plan, **Then** the smallest area lands first and the largest area lands last.

---

### User Story 3 - Stop the count from growing again (Priority: P2)

A contributor adds a root logger call. The CI lint gate reports the call and stops the pull request.

**Why this priority**: This story protects the result of the first two stories. The story cannot land first, because the gate fails while any call remains.

**Independent Test**: A reviewer adds one `logging.info(...)` call to a tracked file. The lint gate fails and names `LOG015`.

**Acceptance Scenarios**:

1. **Given** the updated `select` list, **When** a reviewer searches the list, **Then** the list holds `LOG015`.
2. **Given** the updated `select` list, **When** CI runs the lint gate on the clean branch, **Then** the gate succeeds.
3. **Given** a pull request that adds one root logger call, **When** CI runs the lint gate, **Then** the gate fails and the log names `LOG015` and the file.

---

### Edge Cases

- A module already binds the name `logger` to another object. The new module logger then collides with that name. The implementer must search each module for the name before the edit.
- A test reads records with the `caplog` fixture. That fixture attaches to the root logger by default and still captures a record that a child logger sends. A test that asserts on `logging.getLogger()` directly can fail. The implementer must run the whole unit suite for each slice.
- A module calls `logging.basicConfig` or `logging.getLogger()` with no argument. Those calls configure the root logger on purpose. Rule `LOG015` does not report them, and this work does not change them.
- `src/utils/logger_utils.py` configures the logging system. A module logger inside the configuration path can recurse. The implementer must read that module before any edit.
- `MistHelper.py` holds 303 calls in one file. The mypy gate now covers that file, so a wrong edit fails the type gate as well as the lint gate.
- The `tests` area holds 134 calls. A test that logs through the root logger carries no operator value, so the same conversion applies with a lower risk.
- Issue #886 converts `print()` calls into logging calls. Each new call must use a module logger from the start. The two efforts must not edit the same lines at the same time.

---

## Requirements *(mandatory)*

### Conversion requirements

- **FR-001**: Each converted module MUST define one module logger with `logger = logging.getLogger(__name__)`.
- **FR-002**: The module logger definition MUST sit at module level, after the import block and before the first class or function.
- **FR-003**: Each root logger call MUST become a call on the module logger. The rewrite covers `debug`, `info`, `warning`, `error`, `exception`, and `critical`.
- **FR-004**: The rewrite MUST NOT change the log level of any call.
- **FR-005**: The rewrite MUST NOT change the message text of any call.
- **FR-006**: The rewrite MUST NOT change the argument list of any call. It MUST keep the lazy `%s` form that issue #429 delivered.
- **FR-007**: The rewrite MUST NOT add a call and MUST NOT remove a call. The count of logging calls in each module stays the same.
- **FR-008**: The implementer MUST search each module for an existing name `logger` before the edit. A collision MUST receive a rename of the other object, not a different logger name.
- **FR-009**: The implementer MUST NOT change a `logging.basicConfig` call and MUST NOT change a `logging.getLogger()` call that takes no argument.

### Slice requirements

- **FR-010**: Each pull request MUST hold one area from the area table.
- **FR-011**: Each pull request MUST hold at most 500 changed lines.
- **FR-012**: An area above 500 calls MUST split into two or more pull requests by file. `src/export` and `src/firmware` need this split.
- **FR-013**: The slices MUST land from the smallest area to the largest area. A small area proves the pattern at a low cost.
- **FR-014**: Each slice MUST run the whole unit test suite, not the tests for that area alone.

### Gate requirements

- **FR-015**: The ruff `select` list in `pyproject.toml` MUST hold `LOG015` after the last slice lands.
- **FR-016**: The `select` list change MUST land in its own pull request, after the last slice reports zero results.
- **FR-017**: The implementer MUST NOT add any other rule to the `select` list in this work.

### Quality requirements

- **FR-018**: Every quality gate MUST stay green for each slice. The unit test suite MUST keep its pass count.
- **FR-019**: All prose, all code comments, and all commit text MUST follow the Simplified Technical English rules in `documentation/ASD-STE100_writing-guide.md`.
- **FR-020**: Each pull request body MUST name the area, the count of converted calls, and the count of touched files.

### Key Entities

- **Root logger call**: A call on the `logging` module itself, such as `logging.info(...)`. The record carries no module name.
- **Module logger**: A logger that `logging.getLogger(__name__)` returns. The record carries the module name.
- **Slice**: One pull request that converts one area or one part of an area.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `ruff check . --select LOG015` reports zero results and exits with code 0.
- **SC-002**: Every converted module defines `logger = logging.getLogger(__name__)` exactly once.
- **SC-003**: The count of changed log levels is zero across every slice.
- **SC-004**: The count of changed message texts is zero across every slice.
- **SC-005**: The count of added logging calls is zero and the count of removed logging calls is zero.
- **SC-006**: No slice pull request holds more than 500 changed lines.
- **SC-007**: The ruff `select` list in `pyproject.toml` holds `LOG015`.
- **SC-008**: A pull request that adds one root logger call fails the CI lint gate.
- **SC-009**: Every quality gate stays green for every slice. The unit test suite keeps its pass count and adds no new failure.
- **SC-010**: An operator raises the level for one module logger and reads records from that module alone.

---

## Non-Goals

- **NG-001**: This work does not add any lint suppression. It adds no `# noqa` directive and no rule to the ruff `ignore` list. The whole point is a repair, not a hidden result.
- **NG-002**: This work does not change the log level of any call. A level change would alter the operator output.
- **NG-003**: This work does not change the message text of any call. The action logging rule in `.github/copilot-instructions.md` depends on the current text.
- **NG-004**: This work does not add a logging call and does not remove one. A missing action log is a separate defect with a separate issue.
- **NG-005**: This work does not convert a `print()` call into a logging call. Issue #886 owns that scope.
- **NG-006**: This work does not change the logging configuration in `src/utils/logger_utils.py` beyond the conversion of the calls in that module.
- **NG-007**: This work does not add a handler, a filter, or a formatter.
- **NG-008**: This work does not change the `extend-exclude` list. The four excluded paths keep their root logger calls.
- **NG-009**: This work does not add `LOG` rules other than `LOG015` to the `select` list.

---

## Assumptions

- The ruff version stays at 0.16.0 during this work. A version change can add a rule and can move the count.
- The 4478 count reflects the branch tip at commit `08a75d2`. The implementer must measure the count again before each slice.
- The `caplog` fixture keeps working after the conversion, because it attaches to the root logger and a child logger propagates to it by default.
- No module in scope sets `propagate = False` on a logger. The implementer must confirm this before the first slice.
- The team accepts a stricter lint gate. A new root logger call becomes a build failure.
- A reviewer can read a 500-line mechanical difference. A larger difference receives no real review.

---

## Dependencies

- Issue [#886](https://github.com/jmorrison-juniper/MistHelper/issues/886) converts `print()` calls into logging calls. Each new call must use a module logger. The two efforts must not edit the same lines at the same time.
- Issue [#429](https://github.com/jmorrison-juniper/MistHelper/issues/429) delivered the lazy `%s` argument form. This work must keep that form.
- Issue [#1721](https://github.com/jmorrison-juniper/MistHelper/issues/1721) records a related defect. The Starlink dashboard configures logging after the bootstrap, so the startup records disappear.
- The Simplified Technical English rules in `documentation/ASD-STE100_writing-guide.md` govern all prose in this work.
