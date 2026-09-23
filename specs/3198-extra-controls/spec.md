# Feature Specification: Remove stale portal controls

## Problem
Menu rows 5, 29, 30, 33, 34, 49, 50, 51, 52, 53, 87, 88, and 89 asked for values that their handlers did not read. Menus 66 and 68 use injected site prompts that the static audit cannot see.

## Acceptance Criteria
- Organization-wide rows show no target controls.
- Menu 87 shows only the site picker that its handler reads.
- Menu 88 shows one AP model number field for the one prompt that its handler reads.
- Menus 66 and 68 keep their site picker and leave the stale backlog.
- The required-controls guard fails when a stale control returns.

## Out of Scope
- Add new site scoping to organization-wide handlers.
- Change destructive operations.
- Replace menu 88 with a dynamic AP model picker.
