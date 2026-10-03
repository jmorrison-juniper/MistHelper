# Contract: History record presentation

## Supported pages

- `/history?limit=200`
- `/history?site_id=22222222-2222-2222-2222-222222222222&limit=200`

Both pages support 1024, 1280, and 1440 pixels in `magenta` and `default`.

## Tables

Runs retains 11 columns.
Multi-site upgrades retains eight columns.
Audit log retains five columns.
The Captures table retains its current nine-column or ten-column presentation.

Every record value stays on one text line.
An operation identifier and its ownership explanation may occupy two separate lines.
An inferred audit explanation retains its own complete title.
Each populated row stays at or below 48 pixels.

Text that exceeds a value box uses an ellipsis.
Its title retains the complete value.
The DOM retains the original escaped text.
Existing stored-moment titles do not change.

## Color and actions

Each row header uses `--portal-surface`.
During hover, each cell uses `--portal-table-row-hover`.
No fixed color or font reduction replaces a theme rule.
Existing link targets, selection controls, bulk controls, and sort controls remain usable.

## Overflow

The table may exceed its container width.
The container must stay inside the viewport.
The page must not scroll horizontally.
The evidence identifies columns outside the current visible container.
No out-of-view column counts as visible.

## Protected semantics

Notes, captions, accessible names, empty statements, escaping, source scope, and privacy remain unchanged.
The repair changes no shared stylesheet, script, fixture, route, model, dependency, policy, or exclusion.
