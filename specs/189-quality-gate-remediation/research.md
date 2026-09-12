# Research: Quality Gate Exception Remediation

**Date**: 2026-05-07
**Branch**: `chore/189-quality-gate-remediation`
**Purpose**: Verify codebase state for all NEEDS CLARIFICATION items from plan.md

---

## 1. os.system() Call Inventory

**Decision**: Replace both confirmed calls; note spec/audit discrepancy.

**Rationale**: The audit report (2026-05-06) cited 3 B605 instances under "Container
cleanup / service management". Current codebase contains 2. The screen-clear use case
does not match the "container cleanup" description -- likely one call was removed between
the audit date and spec writing. Proceeding with 2 replacements.

**Alternatives considered**: `shell=True` was rejected because it re-introduces the
injection surface being removed. Python ANSI escape codes (`print("\033[2J...")`) were
considered but change observable terminal behavior in older Windows terminals.

| Line | Current | Replacement | Notes |
| - | - | - | - |
| 35543 | `os.system("cls")  # nosec B605 B607` | `subprocess.run(["cmd.exe", "/c", "cls"], check=False)` | Windows shell built-in |
| 35545 | `os.system("clear")  # nosec B605 B607` | `subprocess.run(["clear"], check=False)` | Linux/Mac standalone executable |

---

## 2. B101 Production Assert Inventory

**Decision**: Replace all 25 confirmed production asserts with explicit raises.

**Rationale**: FR-006 is unambiguous. Python strips asserts with `-O`. Runtime invariant
guards must use explicit raises to function correctly in optimized deployments.

| Line | Current assertion | Replacement type |
| - | - | - |
| 3166 | `assert apisession_cls is not None, "apisession_cls should be set for retry logic"` | `ValueError` |
| 5677 | `assert self.site_id is not None, "Site ID must be resolved before device ID"` | `ValueError` |
| 5730 | `assert self.mist_host is not None, "mist_host must be set"` | `ValueError` |
| 10947 | `assert self.cursor is not None, "Database cursor not initialized"` | `RuntimeError` |
| 10963 | `assert self.cursor is not None, "Database cursor not initialized"` | `RuntimeError` |
| 11000 | `assert self.cursor is not None, "Database cursor not initialized"` | `RuntimeError` |
| 11029 | `assert self.connection is not None, "Database connection not initialized"` | `RuntimeError` |
| 11030 | `assert self.cursor is not None, "Database cursor not initialized"` | `RuntimeError` |
| 25221 | `assert self.selected_template is not None  # Type narrowing for Pylance` | Special: keep as `assert` for Pylance narrowing; add `# type: ignore[assert-type]` comment instead of nosec |
| 25236 | `assert self.selected_template is not None, "Template must be selected before finding sites"` | `ValueError` |
| 25352 | `assert self.selected_template is not None, "Template must be selected"` | `ValueError` |
| 25406 | `assert self.selected_template is not None, "Template must be selected"` | `ValueError` |
| 25492 | `assert self.selected_template is not None, "Template must be selected"` | `ValueError` |
| 39243 | `assert self.selected_wlan is not None, "No WLAN selected"` | `ValueError` |
| 45588 | `assert self.client is not None` | `RuntimeError` (SSH client) |
| 45698 | `assert self.client is not None, "No active SSH connection"` | `RuntimeError` |
| 45752 | `assert self.client is not None, "No active SSH connection"` | `RuntimeError` |
| 46429 | `assert runner.client is not None, "No active SSH connection"` | `RuntimeError` |
| 47488 | `assert final_username is not None, "Username should be validated"` | `ValueError` |
| 47489 | `assert final_password is not None, "Password should be validated"` | `ValueError` |

> **NOTE on line 25221**: `assert self.selected_template is not None` is tagged
> "Type narrowing for Pylance". This pattern is intentionally used by Pylance for
> control-flow type narrowing. Replace with an explicit `if` check that also satisfies
> Pylance narrowing: `if self.selected_template is None: raise ValueError("Template not selected")`.
> Pylance accepts this pattern for narrowing `T | None` to `T`.

> **NOTE on lines 25219, 25234, 25350, 25404, 25490, 39241, 45696**: These line numbers
> appear in the grep output but are `def` signatures or non-assert comment lines with
> `# nosec B101` appended. Skip these -- they are not assert statements.

---

## 3. PyQt6 Import Verification

**Decision**: Remove `QColor`, `QIcon`, `QPalette` from line 261 import; remove
`QProgressBar` import at line 273; keep `QFont` (14 confirmed usages).

**Rationale**: Text search confirms zero references to `QColor`, `QIcon`, `QPalette`,
`QProgressBar` outside their import lines. `QFont` has 14 references and must be kept.
The `# noqa: F401` suppression on line 261 can be removed once unused symbols are
deleted (ruff will no longer flag the line).

| Symbol | References outside import | Action |
| - | - | - |
| `QColor` | 0 | Remove from import |
| `QFont` | 14 (lines 308, 318, 327, 418, 426, 451, 566, 578 + more) | Keep |
| `QIcon` | 0 | Remove from import |
| `QPalette` | 0 | Remove from import |
| `QProgressBar` | 0 | Delete entire import line (line 273) |

---

## 4. Dead Variable Verification

**Decision**: Delete line 1007 `title_color = "#9AA0A6"  # noqa: F841`.

**Rationale**: ruff F841 is authoritative. The surrounding code structure places lines
980/989/998 in if/elif branches that all feed into the `title_label.setStyleSheet` call
at line 1031. Line 1007 is in an elif/else branch where the assigned value is never
read before the branch ends. The noqa annotation itself confirms ruff's verdict.

**Alternatives considered**: Changing the value was rejected (spec requires removal, not
modification). Keeping the annotation was rejected (FR-002 requires removal).

---

## 5. pyproject.toml mypy Setting

**Decision**: Change `warn_unused_ignores = false` (line 126) to `true`.

**Rationale**: This is a one-line change with zero risk. It activates automatic detection
of stale `# type: ignore` annotations as the codebase gains type coverage over time.
The setting was previously disabled to avoid noise from the ~1,226 untyped-def
suppressions. Enabling it now allows Phase 3 cleanup to proceed systematically.

---

## 6. Magic HTTP Constant

**Decision**: Replace `response.status_code != 200` with `response.status_code != requests.codes.ok`.

**Rationale**: `requests` is already imported in `routing_utils.py`. `requests.codes.ok`
evaluates to `200` at runtime, so behavior is identical. The `# noqa: PLR2004` suppression
(magic number comparison) is removed after the replacement.

**Alternatives considered**: `http.HTTPStatus.OK` from stdlib was evaluated but requires
an additional import. `requests.codes.ok` reuses the existing import and is idiomatic for
a requests-heavy module.

---

## 7. PLR0913 Function Signature Survey

### csv_comparator.py

| Function | Current params (excluding self) | Proposed dataclass |
| - | - | - |
| `_build_mismatch_item` (line 1085) | device, device_serial, mist_address, comparison_address, comparison_result, week_key, mismatch_type, validation_result (8 params) | `ComparisonItemConfig` |
| `_build_diff_item` (line 1128) | Identical 8-param signature | `ComparisonItemConfig` (shared) |

### routing_utils.py

| Function | Current params (excluding self) | Proposed dataclass |
| - | - | - |
| `_process_routing_table_results` (line 1451) | websocket_manager, session_id, device_id, device_info, payload, debug_mode (6 params) | `RoutingTableContext` |
| `_display_routing_table_output` (line 1480) | result, device_id, device_info, payload, debug_mode (5 params) | `RoutingTableContext` (result passed separately or included) |
| `_build_ssr_payload` (line 1656) | protocol_input, prefix_input, vrf_input, neighbor_input, route_direction, node_input, interval_input, duration_input (8 params) | `SsrRouteQuery` |
| `_process_ssr_route_results` (line 1779) | Inspect at task time | `SsrRouteContext` |
| `_display_ssr_route_output` (line 1811) | Inspect at task time | `SsrRouteContext` |

> **NOTE on `_display_routing_table_output`**: The first parameter is `result` (the
> response dict), which is produced by `_process_routing_table_results`. Including it
> in `RoutingTableContext` avoids a 6th parameter. If the call site pattern is
> `context = RoutingTableContext(...); result = self._process(...context...); self._display(...context..., result=result)`,
> then `result` stays as a separate explicit argument (not in the dataclass) and
> the function stays at 2 params (self + context). Implementer decides at task time.

### MistHelper.py

| Function | Line | Current params (excluding self) | Proposed dataclass |
| - | - | - | - |
| `SiteDataFetcher.__init__` | 5626 | fetch_function, filename, description, device_type, site_id, device_id (6 params) | `SiteDataFetcherConfig` |
| `_report_rf_template_results` | 26054 | Inspect at task time | Define at task time |
| `_enrich_device_context` | 38816 | Inspect at task time | Define at task time |
| Function at line 44107 | 44107 | Inspect at task time | Define at task time |
