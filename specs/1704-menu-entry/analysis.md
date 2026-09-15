# Analysis: Menu Entry Rows and Menu Dependency Factories

## Acceptance Evidence

### Issue #1704

1. `SiteExportUtils(` appears one time after the refactor.
   - Evidence: `rtk git show origin/main:MistHelper.py` and current `MistHelper.py` count.
   - Result: before 12, after 1.
2. `RoutingDeps(` appears one time after the refactor.
   - Evidence: `rtk git show origin/main:MistHelper.py` and current `MistHelper.py` count.
   - Result: before 3, after 1.
3. `GatewayTemplateConfigManager(` appears one time after the refactor.
   - Evidence: `rtk git show origin/main:MistHelper.py` and current `MistHelper.py` count.
   - Result: before 3, after 1.
4. The listed menus keep the same behavior surface.
   - Evidence: `documentation/menu_reference.md`.
   - Result: 18 rows changed only in the code expression column.

### Issue #1705

1. `menu_actions` holds `MenuEntry` values.
   - Evidence: `tests/unit/test_menu_entry_metadata.py`.
   - Result: 268 rows are instances of `MenuEntry`.
2. The destructive flag is explicit.
   - Evidence: `tests/unit/test_menu_entry_metadata.py`.
   - Result: 41 rows match the exact destructive set.
3. No destructive marker text was lost.
   - Evidence: `MistHelper.py` text count.
   - Result: `DESTRUCTIVE:` before 28, after 28.
4. No two entries share a number.
   - Evidence: `tests/unit/test_menu_entry_metadata.py`.
   - Result: the key set and the row `menu_id` set match.
5. Invalid input fails closed, and empty input remains safe.
   - Evidence: `tests/unit/test_menu_entry_metadata.py`.
   - Result: unknown and non-numeric selections exit with code 1. Empty input prints a retry prompt.
6. The systematic test runner reads fast-mode support from the row.
   - Evidence: `MistHelper.py`.
   - Result: `_resolve_systematic_test_invoke_kwargs` reads `entry.supports_fast`.
7. Tuple row call sites are migrated.
   - Evidence: `MistHelper.py`, `src/troubleshooting/interactive_test_runner.py`, `web_portal/services/operation.py`, and `web_portal/menu_registry.py`.
   - Result: those call sites read `handler` and `title` by name.

## Menu Reference Evidence

The menu reference identity check returned:

```text
rows_equal_without_code True
row_count 268
changed_table_rows 18
base_rows 268
```

No menu number changed. No menu name changed. No menu category changed.

## Gate Evidence

- `rtk python -m py_compile MistHelper.py`: pass.
- `rtk python -m ruff check .`: pass.
- `rtk python -m black --check .`: pass.
- `rtk python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml`: pass.
- `rtk python -m bandit -r MistHelper.py`: pass.
- `rtk python -m tools.symbol_diff --base origin/main MistHelper.py`: pass. It reported `no module-level name changed`.
- `rtk python -c "import MistHelper"`: pass.
- `rtk python MistHelper.py --help`: pass.
- `rtk python -c "import wsgi"` with a dummy token and host: pass.
- `rtk rg -n "type: ignore|noqa|nosec|pylint: disable" MistHelper.py`: no matches.
- `rtk pylint src/ --fail-under=9.5 --score=y` with `PYTHONIOENCODING=utf-8`: pass. It reported 9.51/10.
- `rtk radon cc MistHelper.py src -a -nb`: pass. It reported no block above B, so no block is above complexity 10.
- `rtk python -m pytest tests/unit/test_menu_entry_metadata.py tests/guardrails/test_menu_number_uniqueness.py tests/unit/export/test_msp_license_exporter.py tests/integration/test_menu_org_license_async_claim_status.py tests/integration/test_menu_site_beacon_detail.py tests/unit/refactors/test_main_entrypoint.py::TestMistHelperMenuAndModeCaches tests/unit/web_portal/test_operation_destructive_gate.py tests/unit/troubleshooting/test_interactive_test_runner.py -q`: pass. It reported 98 passed.
- `rtk python -m pytest tests/test_ticket_manager.py::TestMenuRegistration tests/unit/test_systematic_test_offline_mode.py tests/unit/test_systematic_test_unregistered_semantics.py -q`: pass. It reported 12 passed.

## Local Full-Suite Note

The local Windows full-suite command `rtk python -m pytest tests/ -x -q` did not finish in a practical time. It reached 1 percent after more than 30 minutes, so I stopped it. The pull request must use the required GitHub checks as the full-suite gate before merge.
