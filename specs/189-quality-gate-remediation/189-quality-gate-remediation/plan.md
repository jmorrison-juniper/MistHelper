# Implementation Plan: Quality Gate Exception Remediation

**Branch**: `chore/189-quality-gate-remediation` | **Date**: 2026-05-07 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/189-quality-gate-remediation/spec.md`

## Summary

Eliminate or resolve all actionable quality gate suppressions identified in
`data/quality-gate-exceptions-report.md`. Three categories of improvement:

1. **Security (P1)**: Replace 2 `os.system("cls/clear")` calls (B605) with
   `subprocess.run` list-form; replace ~25 production-critical `assert` statements
   (B101) with explicit `ValueError`/`RuntimeError` raises.
2. **Code quality (P1-P2)**: Enable `warn_unused_ignores` in mypy; remove dead
   variable and phantom PyQt6 imports in `starlink_dashboard.py`; replace magic
   HTTP constant in `routing_utils.py`.
3. **Architecture (P3)**: Refactor 10+ PLR0913-suppressed over-parameterized
   functions to accept stdlib `@dataclass` config objects.

Zero behavior changes. All improvements are internal quality remediations.

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: `requests` (present), `subprocess` (stdlib),
`dataclasses` (stdlib), `http` (stdlib)
**Storage**: N/A -- no data model or schema changes
**Testing**: `python MistHelper.py --test` (skip 14, 18, 63-65, 90-100);
`bandit -r`, `ruff check`, `mypy --config-file pyproject.toml`
**Target Platform**: Windows 11 (local dev) + Linux container (production)
**Project Type**: CLI menu-driven NOC tool (~28K-line monolith + `src/` modules)
**Performance Goals**: No performance impact -- purely structural changes
**Constraints**: Zero behavior change; full test suite must pass; suppression
count must be strictly lower after this feature than before (SC-005)
**Scale/Scope**: 5 source files; ~25 assert replacements; 10+ dataclass refactors

## Constitution Check

| Gate | Status | Notes |
| - | - | - |
| Five-Item Rule | **ENFORCED** | PLR0913 refactors introduce `@dataclass` config objects, reducing param count to <=5 per Principle I. |
| Class-Based Architecture | **ENFORCED** | New dataclasses are stdlib value objects co-located with their class, not wrapper functions. |
| Safety-First | **ENFORCED** | `os.system -> subprocess.run` is a security improvement. No new `input()` calls. |
| Security: Fix Over Suppress | **ENFORCED** | This spec eliminates suppressions at their root cause -- fully aligned with Constitution. |
| Full Deployment Pipeline | **REQUIRED** | Execute Principle IV pipeline after all phases complete. |
| Logging (ASCII-only) | **N/A** | No new logging statements added. |

**Constitution violations**: None. Every change reduces the suppression count and improves correctness.

## Project Structure

### Documentation (this feature)

```text
specs/189-quality-gate-remediation/
+-- spec.md          # Feature specification
+-- plan.md          # This file (speckit.plan output)
+-- research.md      # Phase 0 -- codebase state verification
+-- data-model.md    # Phase 1 -- config dataclass designs
+-- quickstart.md    # Phase 1 -- pre/post validation commands
+-- tasks.md         # Phase 2 output (speckit.tasks -- NOT created by speckit.plan)
```

### Source Code (files affected)

```text
pyproject.toml                        # Add warn_unused_ignores = true
starlink_dashboard.py                 # Remove dead var; remove unused PyQt6 imports
MistHelper.py                         # Replace os.system; replace B101 asserts; PLR0913 refactors
src/
+-- inventory/
|   +-- csv_comparator.py             # PLR0913 dataclass refactor
+-- network/
    +-- routing_utils.py              # Magic constant; PLR0913 refactor
```

**Structure Decision**: No new directories or modules for Phases 1-2.
Config dataclasses co-located with their class in the same file. If file length
warrants extraction, a `_types.py` sibling is appropriate (future phase).

---

## Phase 0: Research

*Full findings in [research.md](research.md). Key decisions:*

| Question | Finding | Decision |
| - | - | - |
| How many `os.system()` calls exist? | 2 (lines 35543, 35545 -- `cls` and `clear`). Spec cites 3 based on audit snapshot; current code has 2. | Replace both; note discrepancy. |
| Can `cls`/`clear` use `subprocess.run` without `shell=True`? | `clear` is an executable at `/usr/bin/clear`. `cls` is a `cmd.exe` built-in requiring `cmd.exe /c cls`. | Windows: `subprocess.run(["cmd.exe", "/c", "cls"], check=False)`; Linux: `subprocess.run(["clear"], check=False)`. |
| Which PyQt6 symbols at line 261 are used elsewhere? | Only `QFont` (14 references). `QColor`, `QIcon`, `QPalette` have zero references outside the import line. | Remove `QColor`, `QIcon`, `QPalette`; keep `QFont`; remove `# noqa: F401`. |
| Is `QProgressBar` (line 273) used anywhere? | Zero references outside the import line. | Delete the import line entirely. |
| Is `title_color` at line 1007 a true dead assignment? | ruff F841 confirmed. Line 1007 is in the final else branch; no reference follows before the block ends (subsequent usage at line 1031 reads from earlier branches). | Delete line 1007 and its `# noqa: F841`. |
| How many B101 production asserts need replacement? | 25 `# nosec B101` annotations in `MistHelper.py` (all outside `tests/`). | Replace all 25 per FR-006. |
| Is `requests` already imported in `routing_utils.py`? | Yes -- `import requests` confirmed present. | Use `requests.codes.ok` at line 1062; remove `# noqa: PLR2004`. |
| Do `_build_mismatch_item` and `_build_diff_item` share identical signatures? | Yes -- both take identical 8-parameter signatures. | Shared `ComparisonItemConfig` dataclass. |
| Do `_process_routing_table_results` and `_display_routing_table_output` share params? | Yes -- both take (websocket_manager, session_id, device_id, device_info, payload, debug_mode). | Shared `RoutingTableContext` dataclass. |
| `pyproject.toml` current `warn_unused_ignores` value? | `= false` at line 126. | Change to `true`. |

---

## Phase 1: Design & Contracts

### Config Dataclass Designs

*Full field-level specs in [data-model.md](data-model.md).*

#### `SiteDataFetcherConfig` -- MistHelper.py

Replaces 6-parameter `SiteDataFetcher.__init__` (line 5626):

```python
@dataclass
class SiteDataFetcherConfig:
    fetch_function: Callable  # type: ignore[type-arg]
    filename: str
    description: str
    device_type: str = "all"
    site_id: str | None = None
    device_id: str | None = None
```

#### `ComparisonItemConfig` -- csv_comparator.py

Shared by `_build_mismatch_item` (line 1085) and `_build_diff_item` (line 1128):

```python
@dataclass
class ComparisonItemConfig:
    device: dict[str, Any]
    device_serial: str
    mist_address: dict[str, str]
    comparison_address: dict[str, str]
    comparison_result: dict[str, Any]
    week_key: str
    mismatch_type: str
    validation_result: dict[str, Any] | None
```

#### `RoutingTableContext` -- routing_utils.py

Shared by `_process_routing_table_results` (line 1451) and
`_display_routing_table_output` (line 1480):

```python
@dataclass
class RoutingTableContext:
    websocket_manager: Any
    session_id: str
    device_id: str
    device_info: dict[str, Any] | None
    payload: dict[str, Any]
    debug_mode: bool
```

#### `SsrRouteQuery` -- routing_utils.py

For `_build_ssr_payload` (line 1656, 8 string parameters):

```python
@dataclass
class SsrRouteQuery:
    protocol_input: str
    prefix_input: str
    vrf_input: str
    neighbor_input: str
    route_direction: str
    node_input: str
    interval_input: str
    duration_input: str
```

#### `SsrRouteContext` -- routing_utils.py

For `_process_ssr_route_results` (line 1779) and `_display_ssr_route_output`
(line 1811):

> **IMPLEMENTER NOTE**: Read signatures at lines 1779 and 1811 before coding.
> Define fields to match the shared subset. If signatures diverge, create two
> separate dataclasses rather than one with unused fields.

### No New External Interfaces

Pure internal refactoring. No public APIs, CLI flags, environment variables, or
webhook contracts are added or modified. No `contracts/` directory required.

---

## Implementation Sequence

### Phase 1: Immediate -- Low Effort, High Impact

Each task is independently testable. Execute in order.

| # | Task | File | FR | SC | Risk |
| - | - | - | - | - | - |
| 1.1 | `pyproject.toml`: change `warn_unused_ignores = false` to `true` at line 126 | `pyproject.toml` | FR-001 | SC-006 | None |
| 1.2 | Delete dead `title_color = "#9AA0A6"  # noqa: F841` at line 1007 | `starlink_dashboard.py` | FR-002 | SC-003 | None |
| 1.3 | Remove unused imports `QColor`, `QIcon`, `QPalette` from line 261 and delete `# noqa: F401`; delete `QProgressBar` import at line 273 | `starlink_dashboard.py` | FR-003 | SC-003 | None |
| 1.4 | Replace `os.system("cls")` and `os.system("clear")` at lines 35543/35545 with `subprocess.run` list-form; remove `# nosec B605 B607` | `MistHelper.py` | FR-004, FR-005 | SC-001 | Low |
| 1.5 | Replace all 25 B101-suppressed production `assert` with `if not ...: raise ValueError/RuntimeError` | `MistHelper.py` | FR-006 | SC-002 | Medium |
| 1.6 | **Gate**: `bandit -r MistHelper.py` (zero B605, zero B101); `ruff check starlink_dashboard.py` (no F841/F401); `mypy` (SC-006 notes appear); `py_compile` | All | SC-001..006, SC-009 | -- | Gate |

### Phase 2: Medium Term -- Refactoring

Run `python MistHelper.py --test` after each function refactor (tasks 2.2-2.7).

| # | Task | File | FR | SC | Risk |
| - | - | - | - | - | - |
| 2.1 | Replace `status_code != 200` with `requests.codes.ok` at line 1062; remove `# noqa: PLR2004` | `routing_utils.py` | FR-007 | SC-004 | None |
| 2.2 | Define `SiteDataFetcherConfig`; refactor `SiteDataFetcher.__init__` (line 5626); update all call sites | `MistHelper.py` | FR-008 | SC-008 | Medium |
| 2.3 | Define `ComparisonItemConfig`; refactor `_build_mismatch_item` + `_build_diff_item`; update call sites | `csv_comparator.py` | FR-008 | SC-008 | Medium |
| 2.4 | Define `RoutingTableContext`; refactor `_process_routing_table_results` + `_display_routing_table_output`; update call sites | `routing_utils.py` | FR-008 | SC-008 | Medium |
| 2.5 | Define `SsrRouteQuery`; refactor `_build_ssr_payload`; update call sites | `routing_utils.py` | FR-008 | SC-008 | Medium |
| 2.6 | Inspect lines 1779/1811; define `SsrRouteContext`; refactor `_process_ssr_route_results` + `_display_ssr_route_output`; update call sites | `routing_utils.py` | FR-008 | SC-008 | Medium |
| 2.7 | Refactor remaining MistHelper.py PLR0913 targets: `_report_rf_template_results` (line 26054), `_enrich_device_context` (line 38816), and the function at line 44107; define one config dataclass per function; update call sites | `MistHelper.py` | FR-008 | SC-008 | High |
| 2.8 | **Gate**: `ruff check src/` (no PLR0913); `bandit -r`; full test suite | All | SC-007, SC-008 | SC-009 | Gate |

### Phase 3: Stale Type Annotation Cleanup

*Run after Phase 1 is merged so `warn_unused_ignores = true` is live in CI.*

| # | Task | File(s) | FR | SC |
| - | - | - | - | - |
| 3.1 | Run `mypy --config-file pyproject.toml` and collect all `unused-ignore` warnings | All | FR-001 | SC-006 |
| 3.2 | For each warning: verify annotation is truly stale (not a load-bearing stub suppression), then remove it | Varies | FR-001 | SC-005 |
| 3.3 | Run full test suite and final suppression count audit | All | FR-010 | SC-007 |

---

## Quality Gate Commands

Run these before each commit:

```powershell
# Syntax (Principle IV -- mandatory before every commit)
python -m py_compile MistHelper.py

# Lint
python -m ruff check MistHelper.py
python -m ruff check starlink_dashboard.py
python -m ruff check src/inventory/csv_comparator.py
python -m ruff check src/network/routing_utils.py

# Security (target: zero B605, zero B101 in production files after Phase 1)
bandit -r MistHelper.py

# Type check
mypy --config-file pyproject.toml MistHelper.py

# Tests (skip 14, 18, 63-65, 90-100)
python MistHelper.py --test
```

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
| - | - | - | - |
| `cls` is a `cmd.exe` built-in requiring `cmd.exe /c cls` | High | Low | Use `subprocess.run(["cmd.exe", "/c", "cls"], check=False)` on Windows |
| B101 assert replacement misses a site | Medium | Medium | Run `bandit -r MistHelper.py` after replacement; SC-002 is the gate |
| PLR0913 refactor misses a positional call site | Medium | High | Use grep + IDE find-references before each refactor; run tests after each function |
| `warn_unused_ignores = true` triggers unexpected failures for load-bearing stub suppressions | Low | Medium | Review every mypy warning before removing; keep annotations guarding third-party stub gaps |
| `title_color` line 1007 removal is incorrect (ruff false positive) | Low | Low | Read surrounding if/elif/else structure to confirm before deleting |
| `_process_ssr_route_results` / `_display_ssr_route_output` have divergent signatures | Low | Low | Read both signatures at task time; create two dataclasses if they diverge rather than one with unused fields |
