# Implementation Plan: Network Routing Support Package

**Branch**: `network-routing-support-4006` | **Date**: 2026-10-06 |
**Spec**: [spec.md](spec.md)

## Summary

Move the routing display, parsing, and payload modules into
`src/mist/networking/network/support/`. Update each active path and preserve
behavior without compatibility wrappers. Add exact symbol mappings and a
focused structure guard.

## Technical Context

**Language/Version**: Python 3.13 or newer

**Dependencies**: Existing routing modules, `pytest`, and repository guards

**Testing**: Focused routing tests, structure and symbol guards, generated
reference checks, and applicable repository quality gates

**Constraints**: Keep five network children and three support children. Do not
edit historical specifications or performance inventory records.

## Constitution Check

- **Five-Item Rule**: PASS. The move reduces the network package from seven
  structural children to five.
- **Class-Based Architecture**: PASS. The move preserves the three support
  classes and their parent binding.
- **Safety-First**: PASS. The change adds no command or destructive behavior.
- **Observability**: PASS. Module logger names follow the new canonical paths.
- **Process Folder**: PASS. The records use the fixed eight-level route.

## Implementation Plan

1. Create the `support` package and move the three modules with Git.
2. Update runtime imports, test imports, mock targets, logger names, and active
   documentation.
3. Add exact old-to-new entries to the public symbol guard.
4. Add a focused guard for exact package shapes and removed active paths.
5. Regenerate both WebSocket menu API pages.
6. Add the issue release-note fragment.
7. Run each requested gate and commit the verified change.

## Project Structure

```text
src/mist/networking/network/
├── _routing_utils_forwarding.py
├── _routing_utils_routing.py
├── _routing_utils_ssr.py
├── routing_utils.py
└── support/
    ├── __init__.py
    ├── _routing_utils_display.py
    ├── _routing_utils_parsing.py
    └── _routing_utils_payload.py
```

No constitution exception is required.
