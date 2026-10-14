# Validation Guide

## Prerequisites

Run `python3 scripts/bootstrap_worktree.py`, then activate `.venv`.
All feature tests mock Mist. No production credential is required.

## Feature tests

```sh
python -m pytest tests/unit/firmware_policy tests/contract/firmware_policy tests/integration/firmware_policy
```

Verify model selection, supported schedules, full preview, exact typed confirmation, site inheritance, and partial results.
Verify the tests reject non-settings write methods and that dry run makes no write.

## Menu guards

```sh
python -m pytest tests/guardrails/test_operation_registry_menu_coverage.py tests/guardrails/test_destructive_menu_docs.py tests/guardrails/test_portal_operation_coverage.py tests/guardrails/test_nested_package_structure.py
```

Menu 305 must be destructive and excluded from safe sweeps.

## Generated references

```sh
python scripts/generate_menu_wiki.py
python -m scripts.menu_api_map
```

The generated pages must match the menu and its settings-only endpoint map.

## Product use

Warning: an enabled policy can cause later cloud-managed upgrades.
Do not run a live configuration change as a development test.
Use the mocked integration flow to prove the menu without touching Mist.
