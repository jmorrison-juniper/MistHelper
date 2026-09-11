# Implementation Plan: Discoverable Upgrade Confirmation Navigation

**Branch**: `fix/2447-confirmation-navigation` | **Date**: 2026-09-10 | **Spec**: [spec.md](spec.md)

## Summary

Add a visible confirmation link to the live run page when a run is awaiting confirmation and has a verified pre-check. Keep the existing confirmation route and safety gates unchanged. Validate with contract tests and the existing Playwright journey.

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: Flask, Jinja templates, pytest, Playwright
**Storage**: Existing run store and site-lock state
**Testing**: pytest contract suite and Playwright E2E suite
**Target Platform**: Browser portal in local/container deployments
**Project Type**: Web application
**Performance Goals**: Link renders in the normal run-page response with no extra cloud call
**Constraints**: No production upgrade submission; preserve typed confirmation and lock checks
**Scale/Scope**: One template branch, one route contract regression, one browser regression

## Constitution Check

| Principle | Status | Evidence |
|---|---|---|
| I. Five-Item Rule | PASS | One conditional template control and focused tests |
| II. Class-Based Architecture | PASS | No new standalone service or wrapper |
| III. Safety-First | PASS | Navigation does not bypass confirmation route guards |
| IV. Full Deployment Pipeline | PASS | Run syntax/tests before commit and CI |
| V. Observability | PASS | Existing route logging is retained |
| VI. Inline Comments | PASS | Changed template block includes intent explanation |
| VII. Action Logging | PASS | No new meaningful backend action; existing page log remains |

## Project Structure

```text
specs/2447-confirmation-navigation/{spec.md,plan.md,research.md,data-model.md,quickstart.md,tasks.md}
src/upgrade_portal/app/assets/templates/upgrade/progress.html
tests/contract/upgrade_portal/test_upgrade_routes.py
tests/e2e/upgrade_portal/test_capture.py
```

## Design

The run template will render a `Review and confirm the upgrade` link only when `run_state == 'awaiting_confirmation'` and `pre_key` is present. The link uses the existing literal `/runs/<run_id>/confirm` path and `data-testid="upgrade-confirm-link"`. The route remains responsible for current lock, target, pre-check, and typed-word validation.

## Validation

1. Contract test asserts the link appears with the exact run-specific href for a prepared run.
2. Contract test asserts it is absent for an unprepared run.
3. Playwright test opens a prepared run from the normal portal flow and clicks the link to reach confirmation.
4. Run targeted pytest and Playwright tests on an isolated test port.
