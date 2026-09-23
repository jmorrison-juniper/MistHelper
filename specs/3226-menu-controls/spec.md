# Specification: menu controls 6 through 10

## Problem

Menus 6 through 10 show controls for WebSocket operations that now use menu numbers 103 through 107. The real handlers for menus 6 through 10 do not read those answers.

## Acceptance criteria

1. Menus 6 through 10 show no stale site, device, command, route, or capture controls.
2. The portal still runs the real analysis and inventory handlers from the selected organization context.
3. A guard test fails if any stale control returns on menus 6 through 10.

## Out of scope

- Do not add WebSocket menus 103 through 107 to the portal.
- Do not change the handlers in `MistHelper.py`.
- Do not change rows 235 through 268.
