# Contract: Breadcrumb Audit (SC-014)

**Feature**: `specs/1012-misthelper-refactor-hot-functions/`
**Contract kind**: Post-merge grep-verifiable contract — every breadcrumb must be discoverable with a single-line grep command.

---

## Contract Statement

**The PR lands exactly the enumerated set of mandatory NOTE breadcrumbs** at the enumerated sites, each using one of the two pinned template strings. The set is verifiable by grep in under one second, providing durable one-shot discoverability for future refactor sweeps.

## Pinned Template Strings (Verbatim)

### Template E — Extraction/Deletion

```
# NOTE: <symbol> extracted to <new-location>. See specs/1012-misthelper-refactor-hot-functions/spec.md.
```

Placeholder substitutions:

- `<symbol>` — the extracted or skip-pinned symbol name (e.g., `is_debug_mode`, `execute_with_connection_pool_management`, `tqdm`).
- `<new-location>` — the destination path or the string `SKIP_ALWAYS (bootstrap-critical)` for Action 1.

### Template R — DI Rename

```
# NOTE: renamed from <old-name>; wiring source <new-callable> at MistHelper.py:<line>.
```

Placeholder substitutions:

- `<old-name>` — `is_debug_mode_fn` or `connection_pool_fn`.
- `<new-callable>` — `IsDebugMode.check` or `ConnectionPoolExecutor.execute`.
- `<line>` — `13372` (Action 2 wiring) or `15564` (Action 3 wiring).

## Breadcrumb Manifest

The PR MUST land exactly the following breadcrumbs. Total: **5 mandatory sites** (3 extraction + 2 rename canonical NOTEs). Per spec FR-024, only ONE rename NOTE lands per DI cluster — at the module-level slot declaration. The other 10 rename occurrences are silent (renamed in place without breadcrumbs); the canonical NOTE at the module-level slot is the sole grep-discoverable audit trail for the cluster.

### Extraction Breadcrumbs (Template E — 3 sites)

| # | Site | Rendered NOTE |
|---|------|---------------|
| E1 | `MistHelper.py:635` | `# NOTE: tqdm extracted to SKIP_ALWAYS (bootstrap-critical). See specs/1012-misthelper-refactor-hot-functions/spec.md.` |
| E2 | `MistHelper.py` at former `is_debug_mode` delete site (line ~318) | `# NOTE: is_debug_mode extracted to IsDebugMode.check. See specs/1012-misthelper-refactor-hot-functions/spec.md.` |
| E3 | `MistHelper.py` at former `execute_with_connection_pool_management` delete site (line ~7503) | `# NOTE: execute_with_connection_pool_management extracted to ConnectionPoolExecutor.execute. See specs/1012-misthelper-refactor-hot-functions/spec.md.` |

### DI Rename Breadcrumbs (Template R — 2 rendered lines across 2 files)

Only the canonical module-level slot declaration in each DI cluster carries a Template R NOTE. The remaining 10 rename occurrences enumerated in `di-slot-rename-contract.md` are renamed in place WITHOUT breadcrumbs.

| Cluster | File | Site | Rendered NOTE |
|---------|------|------|---------------|
| R-A | `src/export/site_export_utils.py` | L32 (module-level slot) | `# NOTE: renamed from is_debug_mode; wiring source IsDebugMode.check at MistHelper.py:13372.` |
| R-B | `src/gateway/overrides/_deps.py` | L18 (module-level slot) | `# NOTE: renamed from execute_with_connection_pool_management; wiring source ConnectionPoolExecutor.execute at MistHelper.py:15564.` |

Total rendered R lines: **2**.

Sites explicitly WITHOUT breadcrumbs (renamed in place only): `site_export_utils.py:L52/L64/L76/L337`, `_deps.py:L33/L41/L49`, `src/gateway/overrides/device_data_fetcher.py:L40`, `MistHelper.py:L13372`, `MistHelper.py:L15564`.

## Verification Grep Commands

Post-PR, the following grep commands MUST produce the enumerated counts:

```bash
# Extraction template — expected exactly 3 hits from spec-URL search + 2 hits from rename-URL search referencing spec = 5
grep -R "specs/1012-misthelper-refactor-hot-functions/spec.md" src/ MistHelper.py
# Expected: 3 lines (all in MistHelper.py, at approximately lines 318, 635, 7503) — rename NOTEs
# do NOT reference the spec.md URL

# Extraction template detail — count by search pattern (C4 bare form: no path prefix, no double-colon)
grep -c "tqdm extracted to SKIP_ALWAYS" MistHelper.py                           # Expected: 1
grep -c "is_debug_mode extracted to IsDebugMode.check" MistHelper.py             # Expected: 1
grep -c "execute_with_connection_pool_management extracted to ConnectionPoolExecutor.execute" MistHelper.py  # Expected: 1

# Rename template — expected exactly 2 hits total (1 per DI cluster canonical NOTE)
grep -R "renamed from is_debug_mode" src/ MistHelper.py                          # Expected: 1
grep -R "renamed from execute_with_connection_pool_management" src/ MistHelper.py  # Expected: 1

# Per-file rename NOTE counts (only canonical module-level slot sites carry NOTEs)
grep -c "renamed from is_debug_mode" src/export/site_export_utils.py             # Expected: 1  (L32 slot)
grep -c "renamed from is_debug_mode" MistHelper.py                                # Expected: 0
grep -c "renamed from execute_with_connection_pool_management" src/gateway/overrides/_deps.py  # Expected: 1  (L18 slot)
grep -c "renamed from execute_with_connection_pool_management" src/gateway/overrides/device_data_fetcher.py  # Expected: 0
grep -c "renamed from execute_with_connection_pool_management" MistHelper.py     # Expected: 0

# Zero-survivor greps for the renamed identifiers (5-layer identifier rename is total)
grep -R "is_debug_mode_fn" src/ MistHelper.py                                    # Expected: 0
grep -R "connection_pool_fn" src/ MistHelper.py                                  # Expected: 0
```

## Formatting Invariants

- Every NOTE begins at column 0 or matches the surrounding code's indentation exactly (Black-safe).
- Every NOTE is a single-line comment (`# NOTE: ...`) — no multi-line NOTE blocks.
- Every NOTE uses ASCII only (no smart quotes, em-dashes, or Unicode punctuation).
- Every NOTE terminates with a period after the URL-like path (`spec.md.`) or line reference (`MistHelper.py:<line>.`).
- No trailing whitespace on any NOTE line (enforced by Ruff / pre-commit).

## Non-Contracts

- The contract does NOT require a specific inline position (before/after the code the NOTE describes). Contributors may place the NOTE immediately above the code, on the same line as a `pass`, or at the top of the enclosing block, whichever reads best in context.
- The contract does NOT require breadcrumbs at unaffected callsites — only at extraction/deletion sites and DI-rename sites.
- The contract does NOT require breadcrumbs inside the two new modules (`is_debug_mode.py`, `connection_pool_executor.py`) — those files have their own module docstrings referencing the spec.
