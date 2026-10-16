# Implementation Plan: Inventory model filter

**Branch**: `jmorrison-juniper-inventory-model-filter` | **Date**: 2026-10-16 | **Spec**: [spec.md](spec.md)

## Summary

Keep the shared supported catalog as the validation authority.
Add an inventory-filtered display operation used by the CLI and graphical catalog route.
Use the union of inventory models and the intersection of supported versions.

## Technical Context

Python 3.13, mistapi 0.64, Flask, and existing browser JavaScript.
Use pytest and Playwright with the existing settings-only SDK double.
No new dependency, storage format, environment variable, or production request is required.
Read inventory once per selected organization with checked pagination and existing request admission.

## Constitution Check

The change uses the existing SDK, logging, pagination, and response validation.
It preserves the settings write boundary, complete backups, and typed confirmation.
Existing API and menu classes exceed the five-member limit.
The catalog retains its five methods. The new package-level inventory class has two methods.
Keep edits in existing modules rather than adding children to an already overfull product package.
Separate future remediation: divide catalog parsing and presentation after this feature, with all callers migrated.
The process folders have existing debt. Add only the issue-specific managed record and release fragment.
Separate future remediation: migrate grandfathered process records through the existing managed-root program.
All generated evidence stays under ignored `test-artifacts/`.
Pre-design and post-design checks pass with the documented existing structural debt.

## Project Structure

- `src/operations/execution/firmware_policy/cli.py`: compatible catalogs and CLI scope choice.
- `src/operations/execution/firmware_policy/__init__.py`: inventory display class without another package child.
- `src/operations/execution/firmware_policy/sdk.py`: all-device inventory query.
- `web_portal/routes/firmware_policy/__init__.py`: strict display-scope input.
- `web_portal/routes/firmware_policy/templates/firmware_policy.html`: explicit all-model checkbox.
- `web_portal/static/js/firmware-policy.js`: scope invalidation, empty state, and refresh persistence.
- Existing firmware-policy unit, integration, and browser tests.
- `documentation/org-auto-upgrade-policy.md` and an issue-specific changelog fragment.
- Generated `documentation/menu-api/README.md`, `documentation/menu-api/destructive.md`, and their matching wiki pages.

## Validation

Run catalog, CLI, job, SDK, and browser regression tests with mock transport.
Run targeted lint, formatting, types, complexity, security lint, and documentation checks.
After committing tests, run the documented test-quality preflight and changed-test gate.
