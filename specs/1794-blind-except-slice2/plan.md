# Implementation Plan: Blind Exception Handler Cleanup Slice 2

**Branch**: `refactor/1794-blind-except-slice2` | **Date**: 2026-09-16 | **Spec**: `specs\1794-blind-except-slice2\spec.md`

**Input**: Feature specification from `specs\1794-blind-except-slice2\spec.md`

## Summary

Narrow 17 broad handlers in firmware upgrade, device reboot, service-ping, and Mist SDK export paths. Runtime failures keep the existing operational result. Programming errors now raise.

## Technical Context

**Language/Version**: Python 3.13.

**Primary Dependencies**: `mistapi` 0.64.0, pytest, ruff, black, mypy, Bandit.

**Storage**: No schema change.

**Testing**: Targeted pytest and requested repository gates.

**Target Platform**: Windows worktree and GitHub Actions.

**Project Type**: Python CLI and web service repository.

**Performance Goals**: No new network calls.

**Constraints**: Do not alter issue #1766 log levels or issue #1793 logger ownership.

**Scale/Scope**: Baseline is 812 handlers after #2837. This slice repairs 17 and leaves 795.

## Constitution Check

- Five-Item Rule: No new source class or module.
- Class-Based Architecture: All source changes stay inside existing classes and functions.
- Safety-First: Programming defects raise on production device paths.
- Observability: Existing error messages and result shapes stay intact for runtime failures.
- Quality Gates: Targeted tests and repository checks run before pull request completion.

## Changed Files

- `src\firmware\bulk_switch_upgrader.py`
- `src\firmware\site_auto_upgrade.py`
- `src\device\device_reboot_manager.py`
- `src\websocket\service_ping_manager.py`
- `src\export\site_config_exporter.py`
- `src\export\site_client_exporter.py`
- `tests\unit\test_bulk_switch_upgrader.py`
- `tests\unit\test_site_auto_upgrade.py`
- `tests\unit\device\test_device_reboot_manager.py`
- `tests\unit\websocket\test_service_ping_manager.py`
- `tests\unit\export\test_site_config_exporter.py`
- `tests\unit\export\test_site_client_exporter.py`
- `changelog.d\issue-1794-blind-except-slice2.md`

## Deferred Work

Issue #1794 stays open. Follow-up issues #2833 through #2836 track the remaining areas.
