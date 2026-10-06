# Research: Split Database Package

## Decision 1: Use Three Canonical Subpackages

**Decision**: Use `backends`, `coordination`, and `support`.

**Rationale**: The layout matches the approved specification. The database root has four direct children. Each new subpackage has three direct children.

**Alternatives considered**: Keep the six modules at the root. This fails the five-child rule. Use more subpackages. This adds hierarchy without a requirement.

## Decision 2: Remove Old Paths

**Decision**: Move each module once and remove its old path.

**Rationale**: One canonical path prevents import drift. The specification prohibits shims, aliases, adapters, and fallback imports.

**Alternatives considered**: Keep re-export modules or package aliases. These alternatives violate the specification and hide incomplete consumer updates.

## Decision 3: Keep Initializers Free of Moved Exports

**Decision**: Give each new initializer module documentation only. Replace root access to `host_resolver` with a private direct symbol import.

**Rationale**: The database root currently imports `host_resolver` as a module. That import creates a second access path. A private `DEFAULT_RESOLVER` import preserves root behavior without a moved-module export.

**Alternatives considered**: Keep `from ...db import host_resolver`. This violates the canonical import contract.

## Decision 4: Preserve Symbols Through an Exact Move Map

**Decision**: Extend `test_src_public_symbol_preservation.py` with six full old-to-new file mappings.

**Rationale**: The current guard maps old top-level packages. It does not detect a move below `src/foundation/persistence/db`. Exact mappings compare every baseline module-level definition, assignment, and import.

**Alternatives considered**: Run `symbol-diff` only on the new path. The baseline does not contain that path. A path-only comparison cannot prove a rename.

## Decision 5: Extend the Source Structure Guard

**Decision**: Measure `src/foundation/persistence/db` and its three new subpackages.

**Rationale**: The current guard stops at the group below each domain. It does not measure this deeper package level.

**Alternatives considered**: Count files manually. A manual count does not prevent later drift.

## Decision 6: Use the Coordinator Baseline

**Decision**: Wait for PR #3980 to release the serial slot. Use the exact `main` SHA supplied by the #3959 coordinator.

**Rationale**: A moving or inferred baseline can produce false symbol and test-quality results.

**Alternatives considered**: Fetch `origin/main`, rebase, or use the local remote-tracking ref. The user prohibited those actions during this work.

## Decision 7: Keep Parent Issue Open

**Decision**: Reference #3824 without a closing keyword.

**Rationale**: Issue #3984 is one part of the parent work.

**Alternatives considered**: Use `Closes #3824`. This would close the parent too early.

## Decision 8: Add No Release Fragment

**Decision**: Add no changelog fragment.

**Rationale**: The repository fragment policy excludes internal-only changes. This refactor changes no user behavior.

**Alternatives considered**: Add `issue-3984-split-database-package.md`. This would report an internal move as a user change.
