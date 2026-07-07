# Contract: DI Slot Rename (12 Occurrences Across 5 Naming Layers)

**Feature**: `specs/1012-misthelper-refactor-hot-functions/`
**Contract kind**: Symbol-level rename contract — enumerates exactly which occurrences change and how.

---

## Contract Statement

**Two DI slot names are renamed atomically across all five naming layers**, in the same PR as the extractions they follow (Actions 2 and 3). Zero occurrences of the old names survive the merge.

## Rename Table

### Rename A: `is_debug_mode_fn` -> `check_fn` (Action 2 — 6 occurrences)

| # | File | Line | Naming Layer | Change Detail |
|---|------|------|--------------|---------------|
| 1 | `src/export/site_export_utils.py` | 32 | Module-level slot declaration | `is_debug_mode_fn = None` (or similar init) -> `check_fn = None` |
| 2 | `src/export/site_export_utils.py` | 52 | Dataclass field or `global` list | Rename in place |
| 3 | `src/export/site_export_utils.py` | 64 | Assignment LHS or RHS | Rename both sides where applicable |
| 4 | `src/export/site_export_utils.py` | 76 | Assignment LHS or RHS | Rename both sides where applicable |
| 5 | `src/export/site_export_utils.py` | 337 | Function-body reference | Rename in place |
| 6 | `MistHelper.py` | 13372 | Kwarg key in wiring call | `is_debug_mode_fn=<callable>` -> `check_fn=IsDebugMode.check` |

### Rename B: `connection_pool_fn` -> `execute_fn` (Action 3 — 6 occurrences)

| # | File | Line | Naming Layer | Change Detail |
|---|------|------|--------------|---------------|
| 1 | `src/gateway/overrides/_deps.py` | 18 | Module-level slot declaration | Rename in place |
| 2 | `src/gateway/overrides/_deps.py` | 33 | Dataclass field or global list | Rename in place |
| 3 | `src/gateway/overrides/_deps.py` | 41 | Assignment LHS/RHS | Rename in place |
| 4 | `src/gateway/overrides/_deps.py` | 49 | Assignment LHS/RHS | Rename in place |
| 5 | `src/gateway/overrides/device_data_fetcher.py` | 40 | Function-body reference or dataclass field | Rename in place |
| 6 | `MistHelper.py` | 15564 | Kwarg key in wiring call | `connection_pool_fn=<callable>` -> `execute_fn=ConnectionPoolExecutor.execute` |

## The Five Naming Layers (Reference)

Every DI slot rename may touch any subset of these layers. The 12 occurrences above collectively cover all five:

1. **Module-level slot declaration** — `foo_fn: Callable | None = None` at module scope.
2. **Dataclass field name** — a `dataclass` field whose name matches the slot.
3. **`global` list** — `global foo_fn` inside a function body that mutates the slot.
4. **Assignment LHS/RHS** — `foo_fn = injected_callable` (LHS) or `use = foo_fn` (RHS).
5. **Kwarg key** — `wire(foo_fn=<callable>)` at the wiring call site.

## Verification Grep Commands

Post-PR, the following commands MUST all return zero hits (confirming the rename is total):

```bash
grep -R "is_debug_mode_fn" src/ MistHelper.py       # Expected: 0 hits
grep -R "connection_pool_fn" src/ MistHelper.py     # Expected: 0 hits
```

Post-PR, the following commands MUST return exactly 1 hit each (confirming the pinned NOTE breadcrumb landed at the canonical module-level slot declaration for each DI cluster — 1 NOTE per cluster, not per occurrence):

```bash
grep -R "renamed from is_debug_mode" src/                       # Expected: 1 hit (site_export_utils.py:32 module-level slot)
grep -R "renamed from execute_with_connection_pool_management" src/  # Expected: 1 hit (_deps.py:18 module-level slot)
```

## Wiring-Source Invariant

Every new `check_fn` occurrence must be wired (or documented to be wired at the kwarg site MistHelper.py:13372) to `IsDebugMode.check` — never to any other callable.

Every new `execute_fn` occurrence must be wired (or documented to be wired at the kwarg site MistHelper.py:15564) to `ConnectionPoolExecutor.execute` — never to any other callable.

The pinned NOTE template at each rename site names the wiring-source callable and the MistHelper.py line where the wiring actually happens:

```python
# NOTE: renamed from is_debug_mode; wiring source IsDebugMode.check at MistHelper.py:13372.
# NOTE: renamed from execute_with_connection_pool_management; wiring source ConnectionPoolExecutor.execute at MistHelper.py:15564.
```

Only ONE such NOTE lands per DI cluster — at the module-level slot declaration (Rename A: `src/export/site_export_utils.py:32`; Rename B: `src/gateway/overrides/_deps.py:18`). The other rename occurrences (dataclass fields, global lists, LHS/RHS assignments, kwarg keys, cross-module references) are renamed in place WITHOUT additional NOTE breadcrumbs. The canonical NOTE at the module-level slot is the sole grep-discoverable audit trail for the cluster.

## Non-Contracts

- The contract does NOT require any change to the type annotation on the renamed slot (e.g., `Callable | None` remains `Callable | None`). Only the identifier changes.
- The contract does NOT require deprecation warnings for the old name — FR-003 prohibits shims, including deprecation-warning shims.
- The contract does NOT require a NOTE breadcrumb at every rename occurrence — only at the canonical module-level slot declaration for each cluster (1 NOTE per cluster). The other 10 rename occurrences (5 in Rename A minus 1 canonical, 5 in Rename B minus 1 canonical) are silent renames.
- Line numbers may shift within tolerance during rewrite; the contract is content-based (grep-audited), not line-number-based.
