# Implementation Plan: Network Routing Support Package

**Branch**: `4006-network-routing-support` | **Date**: 2026-10-06

**Spec**: [spec.md](spec.md)

## Summary

Move three routing helper modules into `network/support/`.
Update canonical imports, focused tests, documentation links, and generated menu pages.
Preserve behavior and module-level symbols without compatibility wrappers.

## Implementation Order

1. Move the three modules with `git mv`.
2. Add the support package initializer and focused structure guard.
3. Update active imports, patch targets, logger names, and documentation paths.
4. Add exact public symbol mappings, changelog, and routed specification files.
5. Regenerate the WebSocket menu API pages.
6. Run focused tests and the required repository quality gates.
7. Commit locally with the issue reference and Copilot co-author trailer.

## Scope Boundaries

Do not edit historical specifications 1780, 198, 1034, or 2448.
Do not edit performance inventory records.
Do not add wrappers, aliases, fallback imports, workflows, or pull requests.
