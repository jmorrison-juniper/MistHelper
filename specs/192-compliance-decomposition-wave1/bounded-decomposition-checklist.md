# Wave 1 Bounded Decomposition Checklist

## Hard Boundaries

- [x] No packet-capture architecture decomposition in Wave 1.
- [x] No menu renumbering or option identity changes.
- [x] No global full-file comment/logging sweep.
- [x] No broad refactor outside touched compliance paths.

## Explicit Exclusions

- Packet-capture redesign (menus 9/10 internals)
- Whole-script logging retrofit
- Widespread class/module split outside selected touched functions

## Scope-Audit Conditions (US4)

Wave 1 fails scope audit if any of these are true:
1. New packet-capture class/module decomposition introduced.
2. Menu action key set changed unexpectedly.
3. Large unrelated edits outside targeted compliance tranche areas.
