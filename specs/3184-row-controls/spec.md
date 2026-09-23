# Specification: missing row controls

## Problem

Seven Operations portal rows reach site or device prompts that the browser did not show. The run then read a closed input stream and stopped.

## Acceptance criteria

1. Menus 64, 67, 82, 83, 197, and 203 show a site control.
2. Menu 78 shows a site control followed by a device control.
3. A guard test fails if one repaired row loses its required control order.

## Out of scope

- Do not change handler behavior in `MistHelper.py`.
- Do not change rows 235 through 268.
- Do not change destructive operations.
