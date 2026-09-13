# Contract: Operation Registry Classification

**Feature**: `1020-safe-test-clean-run`
**Consumers**: `MistHelper.py` systematic-test dispatch (`--test`,
`--testinteractive`), `tests/guardrails/*`, any future menu-option addition.

## Category enum (authoritative)

`OperationRegistry` category values are exactly:

```
safe | interactive_safe | destructive | wip | resource_intensive |
websocket | continuous_loop | interactive | unregistered
```

`unregistered` is **not** a value ever written into `_REGISTRY` by hand — it
is the value `OperationRegistry.get(option_id)` returns for any `option_id`
absent from `_REGISTRY`. It is a member of `SKIP_CATEGORIES`.

## Guarantees

1. **Fail-closed default**: `OperationRegistry.get(option_id)` for any
   `option_id` not present in `_REGISTRY` returns
   `{"category": "unregistered", "skip_reason": "Unregistered menu option — fail-closed pending classification"}`
   (exact message may vary; the category MUST be `unregistered`). It never
   returns `{"category": "safe", ...}` for an unknown key.
2. **Uniform mode behavior**: `is_safe(option_id)` and
   `is_interactive_safe(option_id)` both route through `get()`. An
   `unregistered` option is `False` for both — never eligible for `--test`
   nor `--testinteractive`.
3. **Exhaustive coverage**: `OperationRegistry.registered_options()` (new
   classmethod, returns `set(cls._REGISTRY.keys())`) is a **superset** of
   every key in `MistHelper.menu_actions` at all times. Enforced by
   `tests/guardrails/test_operation_registry_menu_coverage.py`. Any menu
   addition without a matching registry entry fails CI immediately (not
   silently defaulted to safe, not silently forgotten).
4. **Destructive labeling**: any `_REGISTRY` entry with
   `category == "destructive"` carries a `skip_reason` containing the
   substring `"DESTRUCTIVE"` (case-sensitive), so operators scanning skip
   output can visually identify high-risk skips without reading source.
5. **No accidental skip of genuinely safe operations**: this contract does
   NOT permit blanket-reclassifying ambiguous options as skip-categories to
   "solve" the coverage gate cheaply. Each of the 60 currently-unregistered
   options MUST receive an explicit category decided from its handler's real
   behavior (see `research.md` R1 for the preliminary, evidence-backed
   lean per option) — a read-only export handler must be classified `safe`,
   not defensively downgraded to `resource_intensive`/`wip` merely to avoid
   analysis. Guardrail tests MAY assert specific known-safe options (e.g.
   the site/device export handlers verified in `research.md`) remain `safe`
   as a regression check against over-cautious reclassification.

## Non-goals

- This contract does not define a schema for *how* categories are stored
  (dict literal vs. dataclass) — `_REGISTRY`'s existing dict-of-dicts shape
  is preserved; this is a behavioral/API contract on `get()`,
  `is_safe()`, `is_interactive_safe()`, `skip_reason()`, `skip_category()`,
  and the new `registered_options()`, not a storage-format contract.
