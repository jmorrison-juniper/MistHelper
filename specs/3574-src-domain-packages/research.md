# Research: Source Domain Packages

## Current State

`origin/main` contains 39 direct package directories under `src`.
It also contains four direct Python modules, including `__init__.py`.
The issue acceptance criterion excludes only `__init__.py`.

The largest packages are `websocket_streams`, `upgrade_portal`, `reports`, and `export`.
The move must preserve their package data and their relative asset paths.

## Decision 1: Use Four Domain Packages

Use these direct children under `src`:

1. `foundation`
2. `mist`
3. `operations`
4. `interfaces`

Keep `src/__init__.py` as the package initializer.

This design leaves one available direct-child slot.

## Decision 2: Use Canonical Imports Only

Move every repository import to the new canonical path.
Do not keep an old forwarding package.
Do not add an alias in `sys.modules`.
Do not change `src.__path__`.

This decision follows the no-wrapper and no-compatibility-shim rules.

## Decision 3: Preserve Symbols, Not Old Internal Paths

Keep each public class, function, and constant in the moved module.
Keep each package initializer export that exists on `origin/main`.
Use symbol comparison and representative import tests as proof.

The old internal module paths are not an external package contract.
All repository call sites move in the same change.

## Decision 4: Use a Mechanical Import Migration

Use one deterministic path map for directory moves and import changes.
Apply the longest old path first.
Scan Python, configuration, and documentation files for old canonical paths.

Remove any temporary migration script before the commit.

## Rejected Alternatives

### Keep forwarding packages

This option preserves old paths, but it adds compatibility wrappers.
The project rules prohibit these wrappers.

### Modify the Python module search path

This option hides the old layout behind runtime path changes.
It is a compatibility shim and makes imports harder to inspect.

### Move one domain in separate pull requests

This option leaves the root violation in place until the final pull request.
It also creates repeated import conflicts across active branches.
Use one atomic migration for the current repository state.
