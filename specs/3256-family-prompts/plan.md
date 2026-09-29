# Implementation Plan: Endpoint family per-choice prompts

**Branch**: `feat/3256-family-prompts` | **Date**: 2026-09-23 | **Spec**: `specs/3256-family-prompts/spec.md`

**Input**: Feature specification from `specs/3256-family-prompts/spec.md`

## Summary

Menus 263 through 268 use `EndpointFamilyExporter`. The first prompt chooses an operation. Later prompts depend on the selected operation's `required` tuple. Add registry metadata for those tuples and add portal JavaScript that renders the selected operation's required controls.

## Technical Context

**Language/Version**: Python 3.13 and browser JavaScript.

**Primary Dependencies**: Flask portal, pytest, MistHelper endpoint exporter modules.

**Storage**: Not applicable.

**Testing**: pytest and browser verification through the local charter launcher.

**Target Platform**: Windows worktree and local Operations portal.

**Project Type**: Web portal inside a Python application.

**Performance Goals**: Parameter rendering must complete during normal form rendering.

**Constraints**: Do not touch destructive operations. Do not restart the shared container. Use port 9606 for local verification.

**Scale/Scope**: Six endpoint family rows and their source exporter tables.

## Constitution Check

- The change keeps code in existing portal and exporter structures.
- The change adds a guard test for the repaired behavior.
- The change avoids live Mist changes and only runs read-oriented portal rows.
- The change uses `origin/main` and an issue-numbered branch.

## Project Structure

### Documentation

```text
specs/3256-family-prompts/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── tasks.md
```

### Source Code

```text
web_portal/
├── services/operation.py
└── static/js/operations.js

tests/
└── unit/web_portal/test_portal_required_answers.py
```

**Structure Decision**: Use the existing portal registry and Operations controller. Add tests in the issue-owned guard file.

## Phase 0 Research

Decision: Keep `EndpointFamilyExporter` as the source of truth.

Rationale: The exporter table already carries the operation name and required tuple. A copied list would drift.

Alternatives considered: Keep menus command-line only. This fails issue #3256 because the browser can model the small prompt sets.

## Phase 1 Design

Decision: Add dynamic parameter metadata to the chooser parameter.

Rationale: The endpoint choice decides the later prompts. The choice control is the correct parent.

Decision: Do not queue `org_id` answers when the runtime context supplies the organization.

Rationale: `ConfigUtils.get_cached_or_prompted_org_id()` usually returns the portal context without calling `input()`. A queued `org_id` would shift later answers.

## Risks

- A selected option with no later controls must still allow Run after the chooser is selected.
- A site control returns the site name, because the CLI site prompt accepts a site name and resolves the ID.
- A future exporter table can add a new required name. The guard must fail until the portal maps that name.
