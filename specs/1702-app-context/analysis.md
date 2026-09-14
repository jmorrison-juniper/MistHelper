# Analysis: Application context

## Acceptance Evidence

- **AC-001 (#1702)**: `test_misthelper_declares_no_live_session_global` proves `MistHelper.__dict__` stores none of the live session names.
- **AC-002 (#1702)**: `test_two_app_context_instances_do_not_share_state` proves separate `AppContext` instances do not share a session or grant list.
- **AC-003 (#1702)**: `rg` found no `ConfigUtils.set_apisession` or `ConfigUtils.set_cached_org_id` call in `MistHelper.py`.
- **AC-004 (#1702)**: `MistSessionInteractiveInitializer.initialize()` now uses `context.as_selector_state()` and `context.apply_msp_selection()`.
- **AC-005 (#1702)**: `rtk python -m tools.symbol_diff --base main MistHelper.py` passed with no module-level name change.
- **AC-006 (#1712)**: `test_session_configurator_runs_once_and_never_adds_mist_get` proves `MistSessionConfigurator` mounts only during the first call.
- **AC-007 (#1712)**: The same test proves the configurator does not add `mist_get` to a session that exposes `get`.
- **AC-008 (#1712)**: `MistSessionConfigurator._configure_timeout()` is the only active seam that reads the private transport.
- **AC-009 (#1712)**: `test_credential_problem_edges_do_not_build_a_session` covers a missing token, a placeholder token, and an absent `.env` file.
- **AC-010 (#1702, #1712)**: The entry point smoke checks passed for `import MistHelper`, `MistHelper.py --help`, and `import wsgi`.
- **AC-011 (#1702, #1712)**: The local quality gate section records the final command results.

## Counts

- `global` statement count before: 14.
- `global` statement count after: 0.
- Run-time patch count before in `MistHelper.py`: 3.
- Run-time patch count after in `MistHelper.py`: 0.

## Issue #1703 Compatibility Note

These modules still reach into `MistHelper` through an import and must move next under issue #1703:

- `src/export/org_admin_exporter.py`
- `src/maps/maps_manager.py`
- `src/maps/_maps_coverage.py`
- `src/maps/launcher/_viewer_refresh.py`
- `src/maps/launcher/_viewer_url_switch.py`
- `src/inventory/org_device_inventory_summary.py`
- `src/ui/execution/function_executor.py`

`MistHelper.py` keeps legacy attribute reads and writes routed to `MainEntrypoint.context` so those call sites do not break.

## Local Quality Gates

- `rtk python -m py_compile MistHelper.py`: pass.
- `rtk python -m ruff check .`: pass.
- `rtk python -m black --check .`: pass.
- `rtk python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml`: pass.
- `rtk python -m pytest tests/unit/refactors tests/unit/test_config_utils.py tests/unit/test_config_utils_org_id_preflight.py -x -q`: pass, 510 passed.
- `rtk python -m pytest tests/ -x -q`: local Windows run was stopped after prolonged progress below 2 percent. The pull request coverage gate must finish this check before merge.
- `rtk python -m bandit -r MistHelper.py`: pass with zero findings and zero skipped lines.
- `rtk python -m tools.symbol_diff --base main MistHelper.py`: pass with no module-level name change.
- `rtk python -c "import MistHelper"`: pass.
- `rtk python MistHelper.py --help`: pass.
- `rtk python -c "import wsgi"`: pass.
- `rtk pylint src/ --fail-under=9.5 --score=y`: pass, 9.51/10.
- `rtk radon cc src/ MistHelper.py wsgi.py starlink_dashboard.py scripts/analyze_marvis_pcap.py scripts/probe_zscaler_endpoints.py tests/unit/utils/test_zscaler_catalogue.py -a -nb`: pass with no block above B.
- `rg "type: ignore|noqa|nosec|pylint: disable" MistHelper.py`: pass, no matches.
