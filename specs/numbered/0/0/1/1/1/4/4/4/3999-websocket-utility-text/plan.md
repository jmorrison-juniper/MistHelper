# Implementation Plan: WebSocket Utility Text Catalog

**Branch**: `3999-websocket-utility-text` | **Date**: 2026-10-06 | **Spec**: [spec.md](spec.md)

## Summary

Move `utility_text.py` into the existing `catalog/utilities` package. Update the four active import consumers and add the exact move to the public symbol preservation map. Preserve source text, module-level symbols, and behavior.

## Design Decisions

### Decision: Use the existing utilities package

The utilities package already owns related utility catalog modules. Moving the text catalog there reduces the direct catalog children without adding another package.

### Decision: Use one canonical module path

The old module path is removed through `git mv`. No wrapper, alias, or fallback import remains.

### Decision: Keep the change bounded

Only the moved module, active imports, focused tests, the symbol map, one release note, and these three routed records are in scope. Historical specifications 3574, 3889, and 3890 remain unchanged.

## Implementation Steps

1. Move `src/mist/realtime/websocket_streams/catalog/utility_text.py` to `src/mist/realtime/websocket_streams/catalog/utilities/utility_text.py`.
2. Update active imports in `utility_fields.py`, `utility_discovery.py`, `test_ws_utility_text.py`, and `test_ws_utility_text_3890.py`.
3. Add the old-to-new path mapping to `test_src_public_symbol_preservation.py`.
4. Run focused utility tests, structure and symbol guards, and the requested quality gates.
5. Commit the verified changes locally with the required co-author trailer.

## Validation

Run the focused utility tests, package structure checks, public symbol preservation check, Python compile, Ruff, Black, Mypy, Bandit, complexity, applicable docstring checks, changelog and Markdown-link checks, and the required post-commit test-quality procedure.
