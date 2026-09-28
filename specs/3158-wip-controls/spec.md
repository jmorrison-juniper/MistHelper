# Feature Specification: Repair Work In Progress portal rows

## Problem
Menus 63, 64, and 65 appeared under `Work In Progress`. The rows are real site exports, so the category made them look unfinished. Menu 63 also asked for a site and then prompted for a switch, but the portal collected only the site.

## Acceptance Criteria
- Menus 63, 64, and 65 appear under `Site Data Exports`.
- The `Work In Progress` category contains no shipped rows.
- Menu 63 declares a site picker followed by a switch picker.
- Menus 64 and 65 keep their required site picker.
- Guard tests fail when the category or menu 63 controls regress.

## Out of Scope
- Change the menu handlers.
- Add destructive operations.
- Change the output walk.
