# Feature Specification: Quality Gate Exception Remediation

**Feature Branch**: `189-quality-gate-remediation`  
**Created**: 2026-05-07  
**Status**: Draft  
**Audit Report**: `data/quality-gate-exceptions-report.md`

## User Scenarios & Testing *(mandatory)*

### User Story 1 -- Enable stale-suppression detection (Priority: P1)

A developer adds `warn_unused_ignores = true` to the mypy configuration so that mypy
automatically flags `# type: ignore` annotations that are no longer needed as the
codebase gains type coverage over time.

**Why this priority**: This is a one-line config change with zero behavioral risk and
provides ongoing, automatic cleanup leverage for all future type annotation work. It
is a prerequisite for Phase 3 stale-ignore removal.

**Independent Test**: Can be fully tested by running `mypy --config-file pyproject.toml`
after the change and confirming mypy reports stale ignores rather than silently
skipping them. Delivers immediate value: any annotation that has become unnecessary
is surfaced immediately.

**Acceptance Scenarios**:

1. **Given** `pyproject.toml` mypy section does not have `warn_unused_ignores`,
   **When** `warn_unused_ignores = true` is added and mypy is run,
   **Then** mypy outputs warnings for any `# type: ignore` annotations that are
   no longer necessary.
2. **Given** a `# type: ignore[assignment]` annotation that is genuinely still
   needed, **When** mypy runs with the new setting,
   **Then** mypy does NOT flag it as unused.

---

### User Story 2 -- Remove dead code and resolve phantom import suppressions (Priority: P1)

A developer removes the dead variable `title_color = "#9AA0A6"` from
`starlink_dashboard.py` and resolves the unused PyQt6 import suppressions at lines
261 and 273 by either deleting the imports (if truly unused) or removing the
`# noqa: F401` suppression (if the imports are genuinely needed).

**Why this priority**: Dead code and redundant suppressions are the highest
signal-to-noise quality issues -- they mislead readers and are trivially removable
with zero risk.

**Independent Test**: Can be tested in isolation by running `ruff check starlink_dashboard.py`
after the change and confirming zero F841 and F401 violations remain for those lines.
The Starlink dashboard renders and operates correctly.

**Acceptance Scenarios**:

1. **Given** `starlink_dashboard.py:1007` contains `title_color = "#9AA0A6"  # noqa: F841`,
   **When** the line is deleted,
   **Then** `ruff check starlink_dashboard.py` reports no F841 and the dashboard
   launches without error.
2. **Given** `QColor, QFont, QIcon, QPalette` are imported at line 261 with `# noqa: F401`,
   **When** the file is checked for references to each symbol and the import or
   suppression is resolved accordingly,
   **Then** `ruff check` reports no F401 on line 261 and the UI functions correctly.
3. **Given** `QProgressBar` is imported at line 273 with `# noqa: F401`,
   **When** the reference check is complete and the import or suppression is resolved,
   **Then** `ruff check` reports no F401 on line 273.

---

### User Story 3 -- Replace `os.system` calls with secure subprocess invocation (Priority: P1)

A developer replaces all 3 `os.system()` calls in `MistHelper.py` (flagged B605)
with `subprocess.run()` using the list-form invocation, preserving equivalent
behavior, then removes the `# nosec B605` annotations.

**Why this priority**: `os.system()` passes the command through the shell, creating
injection risk. `subprocess.run()` with a list argument is the secure, modern
replacement and eliminates the security finding entirely -- a P1 security improvement.

**Independent Test**: Can be tested independently by running `bandit -r MistHelper.py`
after changes and confirming zero B605 findings, plus running the full test suite to
confirm no behavioral regression in container cleanup and service management operations.

**Acceptance Scenarios**:

1. **Given** an `os.system()` call used for container cleanup or service management,
   **When** it is replaced with `subprocess.run([...], check=False)`,
   **Then** the operation produces the same system-level result as before.
2. **Given** all three `os.system()` calls are replaced,
   **When** `bandit -r MistHelper.py` runs,
   **Then** zero B605 findings are reported.
3. **Given** the replaced calls, **When** the full test suite runs,
   **Then** all tests pass with no behavioral change.

---

### User Story 4 -- Replace production-critical `assert` with explicit exception raises (Priority: P2)

A developer replaces `assert` statements at production-critical paths in `MistHelper.py`
(lines ~3166, 5677, 5730 and similar B101-suppressed sites outside test code) with
explicit `ValueError` or `RuntimeError` raises containing descriptive messages.
Developer-only assertions in test code remain as `assert`.

**Why this priority**: Python silently strips `assert` statements when run with the
`-O` optimization flag. Production code that relies on asserts for runtime validation
may silently skip those checks in optimized deployments -- a correctness risk.

**Independent Test**: Can be tested by verifying the replaced guards still trigger
when conditions are false (unit test with invalid input), and by running the full
test suite to confirm no regression.

**Acceptance Scenarios**:

1. **Given** a production `assert condition, "message"  # nosec B101` at line ~3166,
   **When** it is replaced with `if not condition: raise ValueError("message")`,
   **Then** `bandit -r MistHelper.py` reports no B101 for that line and the
   validation still triggers on invalid input.
2. **Given** test-only `assert` statements in files under `tests/`,
   **When** the production asserts are replaced,
   **Then** the test assertions remain unchanged and test execution is unaffected.
3. **Given** all production B101-suppressed asserts are replaced,
   **When** the test suite runs,
   **Then** all tests pass.

---

### User Story 5 -- Replace magic HTTP status code with named constant (Priority: P2)

A developer replaces `status_code != 200` in `src/network/routing_utils.py:1062`
with `status_code != requests.codes.ok` (or `http.HTTPStatus.OK`) to eliminate the
magic number.

**Why this priority**: Named constants are self-documenting and prevent future bugs
from mistyping the expected status code. Low-effort, zero-risk change.

**Independent Test**: Can be tested by running `ruff check src/network/routing_utils.py`
after the change and confirming no magic-number violation remains on that line, plus
running routing-related tests.

**Acceptance Scenarios**:

1. **Given** `status_code != 200` at line 1062 in `routing_utils.py`,
   **When** it is replaced with `status_code != requests.codes.ok`,
   **Then** `ruff check` reports no magic-number violation on that line and routing
   behavior is unchanged.

---

### User Story 6 -- Refactor over-parameterized functions to config dataclasses (Priority: P3)

A developer refactors the functions identified as PLR0913 targets to accept a stdlib
`@dataclass` config object instead of 6+ positional parameters. Call sites are
updated in the same commit.

**Why this priority**: P3 because it is safe to defer -- it improves maintainability
and removes suppression noise but carries more refactoring risk than the above items.
Coded to the project's 5-parameter limit standard.

**Independent Test**: Each function can be refactored and tested independently. The
test suite is run after each individual function refactor to catch regressions
before moving to the next.

**Acceptance Scenarios**:

1. **Given** `SiteDataFetcher.__init__()` takes 6+ positional parameters,
   **When** it is refactored to accept a `SiteDataFetcherConfig` dataclass and all
   callers are updated,
   **Then** the test suite passes and `ruff check MistHelper.py` reports no PLR0913
   for that function.
2. **Given** `_build_mismatch_item()` and `_build_diff_item()` in `csv_comparator.py`
   have 6+ parameters, **When** they are refactored to config dataclasses,
   **Then** inventory compare operations produce identical output and tests pass.
3. **Given** `_process_routing_table_results()`, `_display_routing_table_output()`,
   and `_build_ssr_payload()` in `routing_utils.py` have 6+ parameters,
   **When** they are refactored to config dataclasses,
   **Then** routing table display and SSR payload construction work identically.

---

### Edge Cases

- A `# type: ignore` annotation may be load-bearing for a third-party library with
  incomplete stubs. After enabling `warn_unused_ignores`, mypy must NOT emit a
  false "unused ignore" for a genuinely-needed suppression -- verify each warning
  before removing.
- An `os.system()` call may pass a dynamically-constructed string. The
  `subprocess.run()` replacement must use a list form (never `shell=True`) and
  handle dynamic parts as separate list elements. If a truly dynamic shell command
  is needed, document it explicitly with a security review note.
- A PyQt6 import may be referenced only in a deferred type annotation string. Verify
  at runtime (or by import tracing), not just by text search, before removing.
- Removing `# noqa: F841` from a dead variable is only safe if the right-hand side
  is a pure literal with no side effects. Verify before deleting.
- Dataclass refactors: callers that pass arguments positionally (not as keyword args)
  must all be located and updated. A missed call site causes a runtime error.
  Use `grep` or IDE "find references" to confirm completeness.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `pyproject.toml` MUST include `warn_unused_ignores = true` in the
  `[tool.mypy]` section.
- **FR-002**: The dead variable `title_color = "#9AA0A6"  # noqa: F841` at
  `starlink_dashboard.py:1007` MUST be removed.
- **FR-003**: The PyQt6 import suppressions at `starlink_dashboard.py:261` and `:273`
  MUST be resolved: either unused imports are deleted, or if imports are confirmed
  used, the `# noqa: F401` annotations are removed.
- **FR-004**: All 3 `os.system()` calls in `MistHelper.py` MUST be replaced with
  `subprocess.run([...], check=False)` using the list-form (non-shell) invocation.
- **FR-005**: The `# nosec B605` annotations on those 3 calls MUST be removed after
  replacement.
- **FR-006**: Production-critical `assert` statements in `MistHelper.py` at lines
  ~3166, 5677, 5730 (and any other B101-suppressed asserts outside `tests/`) MUST
  be replaced with `if not condition: raise ValueError("message")` or
  `raise RuntimeError("message")` with a descriptive message.
- **FR-007**: `status_code != 200` in `src/network/routing_utils.py:1062` MUST be
  replaced with `requests.codes.ok` or `http.HTTPStatus.OK`.
- **FR-008**: Functions identified as PLR0913 targets MUST be refactored to accept
  a stdlib `@dataclass` config object, with all call sites updated in the same commit.
- **FR-009**: `# nosec B608` annotations in `web_portal/services/data_browser.py`
  MUST NOT be modified.
- **FR-010**: No behavior changes are permitted -- all changes are internal quality
  improvements only.
- **FR-011**: `subprocess.run` replacements MUST preserve the exit-code handling
  semantics of the `os.system` calls they replace (`check=False`, capture return
  code as needed).

### Key Entities

- **Suppression Annotation**: A `# type: ignore`, `# noqa`, or `# nosec` comment
  that silences a quality gate finding. Each removal reduces technical debt and
  improves signal-to-noise for genuine suppressions that remain.
- **Config Dataclass**: A stdlib `@dataclass` that groups related parameters for a
  function, replacing a long positional parameter list and satisfying the project's
  5-parameter limit.
- **Production-Critical Assert**: An `assert` in non-test code that guards a runtime
  invariant. Python strips these in optimized mode (`-O`), making them unsafe for
  production validation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `bandit -r MistHelper.py` reports zero B605 findings (all `os.system`
  calls replaced).
- **SC-002**: `bandit -r MistHelper.py` reports zero B101 findings in production
  source files (all production-critical asserts replaced with explicit raises).
- **SC-003**: `ruff check starlink_dashboard.py` reports no F841 or F401 violations
  on the lines identified in FR-002 and FR-003.
- **SC-004**: `ruff check src/network/routing_utils.py` reports no magic-number
  violation on line 1062.
- **SC-005**: The total count of suppression annotations (`# type: ignore`, `# noqa`,
  `# nosec`) across the codebase is strictly lower after this feature than before.
- **SC-006**: `mypy --config-file pyproject.toml MistHelper.py` emits
  "note: ... unused ignore" for any stale `# type: ignore` annotations, confirming
  `warn_unused_ignores` is active.
- **SC-007**: The full test suite (`python MistHelper.py --test`, skipping 14, 18,
  63-65, 90-100) passes with zero regressions after all phases are complete.
- **SC-008**: `ruff check src/inventory/csv_comparator.py` and
  `ruff check src/network/routing_utils.py` report no PLR0913 for the refactored
  functions.
- **SC-009**: `python -m py_compile MistHelper.py` passes without error.

## Assumptions

- The audit report at `data/quality-gate-exceptions-report.md` is current and
  accurately identifies the 3 `os.system` call sites and B101 assertion locations.
- The PyQt6 imports at lines 261 and 273 are verifiable as used or unused by text
  search within `starlink_dashboard.py`.
- `requests` is already a project dependency (it is), making `requests.codes.ok`
  available without adding a new import.
- Test code (files under `tests/`) may retain `assert` statements -- the B101
  replacements target only production source files.
- The PLR0913-suppressed function signatures are stable enough to refactor without
  breaking undocumented external callers.
- No `os.system()` call constructs its argument from untrusted user input; the
  `subprocess.run()` list-form replacement is straightforward (no shell=True needed).

## Non-Goals

- The ~980 `no-untyped-def` / `no-untyped-call` `# type: ignore` annotations are
  out of scope -- they require the full type annotation campaign (separate spec).
- Complexity refactoring (C901 / PLR0912 / PLR0915) is out of scope -- that requires
  architectural decomposition (separate spec).
- No new user-facing features are introduced.
- `# nosec B608` annotations in `web_portal/services/data_browser.py` are not
  modified.

## Implementation Notes

### Phase 1 -- Immediate (Low Effort, High Impact)

1. **`pyproject.toml`**: Add `warn_unused_ignores = true` under `[tool.mypy]`.
2. **`starlink_dashboard.py:1007`**: Delete the `title_color = "#9AA0A6"  # noqa: F841` line.
3. **`starlink_dashboard.py:261,273`**: Text-search for `QColor`, `QFont`, `QIcon`,
   `QPalette`, `QProgressBar` outside the import lines. If none found, delete the
   import lines. If found, remove the `# noqa: F401` annotations.
4. **`MistHelper.py` os.system → subprocess.run**:
   ```python
   # Before:
   os.system("podman stop misthelper")  # nosec B605
   # After:
   subprocess.run(["podman", "stop", "misthelper"], check=False)
   ```
5. **`MistHelper.py` assert → raise**:
   ```python
   # Before:
   assert condition, "message"  # nosec B101
   # After:
   if not condition:
       raise ValueError("message")
   ```

### Phase 2 -- Medium Term

1. **`routing_utils.py:1062`**: Replace `200` with `requests.codes.ok`. Confirm
   `import requests` is already present.
2. **PLR0913 refactoring** (one function at a time, run tests after each):
   - Define a `@dataclass` config object near the class or in a `_types.py` sibling.
   - Update the function signature to accept the dataclass.
   - Update all call sites in the same commit.
   - Run `python MistHelper.py --test` (skipping 14, 18, 63-65, 90-100) after each.

### Phase 3 -- After Phase 1 (Stale Ignore Cleanup)

1. Run `mypy --config-file pyproject.toml` and review each "unused ignore" warning.
   Remove only annotations mypy confirms are no longer needed.
2. In the highest-traffic utility functions, replace bare `dict`, `list`, `tuple`
   type annotations with parameterized equivalents (`dict[str, Any]`, `list[str]`).

### Files Affected

| File | Change |
| - | - |
| `pyproject.toml` | Add `warn_unused_ignores = true` under `[tool.mypy]` |
| `starlink_dashboard.py` | Remove dead var at :1007; resolve import suppressions at :261, :273 |
| `MistHelper.py` | Replace 3x `os.system` with `subprocess.run`; replace B101 production asserts |
| `src/network/routing_utils.py` | Replace magic `200` with named constant; PLR0913 refactor |
| `src/inventory/csv_comparator.py` | PLR0913 refactor (`_build_mismatch_item`, `_build_diff_item`) |
