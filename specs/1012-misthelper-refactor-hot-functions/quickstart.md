# Quickstart: Landing the 1012 Hot-Functions Bundle

**Feature**: `specs/1012-misthelper-refactor-hot-functions/`
**Audience**: The operator (human or agent) opening and merging the single bounded PR.
**Estimated wall-clock**: 30-45 minutes for the mechanical edits + full CI cycle.

---

## Prerequisites

1. `main` is at the post-1011 head (all 20 low-use PRs merged, baseline `>=99.6/A+`).
2. Fresh analyzer output confirms the three targets are still valid:
   ```bash
   python -m tools.refactor_analyzer > refactor_candidates.md
   grep -E "is_debug_mode|execute_with_connection_pool_management|tqdm" refactor_candidates.md
   ```
3. `gh` CLI authenticated; branch protection status readable via `gh pr view --json mergeStateStatus`.
4. Local pre-commit hooks installed:
   ```bash
   pre-commit install
   ```

## Branch Setup

```bash
git fetch origin main
git checkout -b 1012-misthelper-refactor-hot-functions origin/main
```

## Step 1 — Action 1: tqdm Skip-Pin (Zero Extraction)

Open `MistHelper.py` and locate line ~635 (the tqdm fallback shim block).

Add the mandatory NOTE breadcrumb immediately above the shim:

```python
# NOTE: tqdm extracted to SKIP_ALWAYS (bootstrap-critical). See specs/1012-misthelper-refactor-hot-functions/spec.md.
```

If the refactor analyzer exposes a `--skip` CLI flag (`python -m tools.refactor_analyzer --skip tqdm --help`), invoke it once to persist the skip-pin in the analyzer's config file. If the flag is absent, the NOTE alone satisfies SC-001.

**Do NOT modify the tqdm shim source code.** SC-001 is metadata-only.

**Verification**:
```bash
grep -n "tqdm extracted to SKIP_ALWAYS" MistHelper.py    # Expect: 1 hit
```

## Step 2 — Action 2: Extract `is_debug_mode`

### 2a. Create the new module

Create `src/refactors/is_debug_mode.py`:

```python
"""is_debug_mode extracted from MistHelper (SC-002).

Owns the module-level ``is_debug_mode()`` predicate originally defined at
MistHelper.py:318-320, and re-lands it as a ``@staticmethod`` on
``IsDebugMode`` per FR-005 carry-forward. All 12 MistHelper.py callsites
are rewritten in the same PR to reference the extracted class method;
no wrapper shim remains in MistHelper.py after this extraction. The
legacy ``EnvironmentUtils.is_debug_mode`` wrapper at MistHelper.py:5891-5900
is deleted outright in the same PR (0 callers per spec clarification Q1).
"""

from __future__ import annotations  # Enable postponed evaluation for forward-ref typing

import os  # Read the environment override value


class IsDebugMode:  # Class-body seam for the debug-mode predicate
    """Class-body seam owning the debug-mode predicate."""

    @staticmethod
    def check() -> bool:  # Return True when debug logging should be enabled
        """Return True if MISTHELPER_DEBUG env override enables verbose debug logs."""
        return os.getenv("MISTHELPER_DEBUG", "").strip().lower() in {"1", "true", "yes", "on"}
```

(Exact predicate body: copy the origin's implementation verbatim; the snippet above is illustrative.)

### 2b. Delete the origin function and wrapper

Remove `def is_debug_mode():` at `MistHelper.py:318-320`. Replace with the mandatory NOTE:

```python
# NOTE: is_debug_mode extracted to IsDebugMode.check. See specs/1012-misthelper-refactor-hot-functions/spec.md.
```

Remove `EnvironmentUtils.is_debug_mode` at `MistHelper.py:5891-5900` entirely (0 callers per Q1). No NOTE required at this site (SC-011 documents the deletion audit trail via the spec itself).

### 2c. Add the import to MistHelper.py

At the appropriate import block near the top of `MistHelper.py`:

```python
from src.refactors.is_debug_mode import IsDebugMode
```

### 2d. Rewrite the 12 callsites

Run this repeatedly with `git grep` until zero hits remain:

```bash
git grep -n "is_debug_mode()" MistHelper.py
```

For each hit, rewrite `is_debug_mode()` -> `IsDebugMode.check()`.

### 2e. Rename `is_debug_mode_fn` -> `check_fn` (6 occurrences; canonical NOTE at slot only)

- `src/export/site_export_utils.py` at L32, L52, L64, L76, L337 — rename identifier in place at all 5 sites. Add the canonical rename NOTE **ONLY at L32** (module-level slot declaration):
  ```python
  # NOTE: renamed from is_debug_mode; wiring source IsDebugMode.check at MistHelper.py:13372.
  ```
  The other 4 sites (L52/L64/L76/L337) get identifier rename WITHOUT breadcrumbs.
- `MistHelper.py:13372` — rewrite the kwarg key `is_debug_mode_fn=<callable>` -> `check_fn=IsDebugMode.check`. **No breadcrumb** at this site; the cluster's canonical NOTE lives on `_deps.py`-equivalent site (`site_export_utils.py:L32`).

### 2f. Verify

```bash
grep -Rn "is_debug_mode(" src/ MistHelper.py                       # Expect: 0 hits (function calls)
grep -Rn "is_debug_mode_fn" src/ MistHelper.py                     # Expect: 0 hits (old DI slot)
grep -Rn "IsDebugMode.check" src/ MistHelper.py                    # Expect: 12 callsite hits + 1 wiring
grep -Rn "renamed from is_debug_mode" src/ MistHelper.py           # Expect: 1 hit (canonical NOTE at site_export_utils.py:32)
```

## Step 3 — Action 3: Extract `execute_with_connection_pool_management`

### 3a. Create the new module

Create `src/refactors/connection_pool_executor.py` (skeleton):

```python
"""execute_with_connection_pool_management extracted from MistHelper (SC-003).

Owns the module-level ``execute_with_connection_pool_management()`` public
function plus its three private ``_pool_*`` helpers originally defined at
MistHelper.py:7503-7576, and re-lands them as class-body ``@staticmethod``
members on ``ConnectionPoolExecutor`` per FR-005 carry-forward. All 7
callsites (4 in MistHelper.py, 2 in gateway_export_utils.py, 1 in
gateway_stats_exporter.py) are rewritten in the same PR to reference
``ConnectionPoolExecutor.execute``; no wrapper shim remains in
MistHelper.py after this extraction.
"""

from __future__ import annotations  # Enable postponed evaluation for forward-ref typing


class ConnectionPoolExecutor:  # Class-body seam for pool-managed execution
    """Class-body seam owning the pool-managed execution lifecycle."""

    @staticmethod
    def execute(...):  # Copy origin signature verbatim
        """Run the caller-supplied callable inside a managed connection pool."""
        # Copy body verbatim; adjust internal calls to reference the private static helpers below
        ...

    @staticmethod
    def _pool_setup(...):  # Copy origin helper verbatim
        ...

    @staticmethod
    def _pool_teardown(...):  # Copy origin helper verbatim
        ...

    @staticmethod
    def _pool_error_handler(...):  # Copy origin helper verbatim
        ...
```

(The exact three private helper names must match the origin — copy them verbatim.)

### 3b. Delete the origin function and helpers

Remove all four functions at `MistHelper.py:7503-7576`. Replace with the mandatory NOTE:

```python
# NOTE: execute_with_connection_pool_management extracted to ConnectionPoolExecutor.execute. See specs/1012-misthelper-refactor-hot-functions/spec.md.
```

### 3c. Add the import

At the appropriate import block in `MistHelper.py` and in each of the 3 caller files:

```python
from src.refactors.connection_pool_executor import ConnectionPoolExecutor
```

### 3d. Rewrite the 7 callsites

- `MistHelper.py:6309, 10076, 15399, 15564` — 4 rewrites
- `src/gateway/gateway_export_utils.py:48, 550` — 2 rewrites
- `src/gateway/gateway_stats_exporter.py:32` — 1 rewrite

For each hit, rewrite `execute_with_connection_pool_management(...)` -> `ConnectionPoolExecutor.execute(...)` (arguments preserved verbatim).

### 3e. Rename `connection_pool_fn` -> `execute_fn` (6 occurrences; canonical NOTE at slot only)

- `src/gateway/overrides/_deps.py` at L18, L33, L41, L49 — rename identifier in place at all 4 sites. Add the canonical rename NOTE **ONLY at L18** (module-level slot declaration):
  ```python
  # NOTE: renamed from execute_with_connection_pool_management; wiring source ConnectionPoolExecutor.execute at MistHelper.py:15564.
  ```
  The other 3 sites (L33/L41/L49) get identifier rename WITHOUT breadcrumbs.
- `src/gateway/overrides/device_data_fetcher.py:40` — rename identifier in place. **No breadcrumb** at this site.
- `MistHelper.py:15564` — rewrite the kwarg key `connection_pool_fn=<callable>` -> `execute_fn=ConnectionPoolExecutor.execute`. **No breadcrumb** at this site; the cluster's canonical NOTE lives on `_deps.py:L18`.

### 3f. Verify

```bash
grep -Rn "execute_with_connection_pool_management(" src/ MistHelper.py   # Expect: 0 hits
grep -Rn "connection_pool_fn" src/ MistHelper.py                          # Expect: 0 hits
grep -Rn "ConnectionPoolExecutor.execute" src/ MistHelper.py              # Expect: 7 callsites + 1 wiring
grep -Rn "renamed from execute_with_connection_pool_management" src/ MistHelper.py  # Expect: 1 hit (canonical NOTE at _deps.py:18)
```

## Step 4 — Full Breadcrumb Audit (SC-014)

```bash
# Extraction template — expect exactly 3 hits (E1/E2/E3)
grep -R "specs/1012-misthelper-refactor-hot-functions/spec.md" src/ MistHelper.py

# Rename template — expect exactly 2 hits total (1 canonical NOTE per DI cluster)
grep -R "renamed from is_debug_mode" src/ MistHelper.py                          # Expect: 1
grep -R "renamed from execute_with_connection_pool_management" src/ MistHelper.py  # Expect: 1
```

If any count is off, correct before proceeding to Step 5.

## Step 5 — Local Pre-Push Gate (feedback_prepush_black_ruff.md)

```bash
black --check src/ MistHelper.py
ruff check src/ MistHelper.py
ruff format --check src/ MistHelper.py
```

All three must report zero diff / zero issues.

## Step 6 — Compliance Verification

```bash
python -m tools.compliance_analyzer src/refactors/is_debug_mode.py            # Expect: A+/100
python -m tools.compliance_analyzer src/refactors/connection_pool_executor.py # Expect: A+/100
python -m tools.compliance_analyzer --repo-wide                                # Expect: >=99.6/A+
pylint src/ MistHelper.py                                                       # Expect: >=8.74/10
```

## Step 7 — Commit and Push

Use a single squashed commit:

```bash
git add -A
git commit -m "refactor(1012): bundle hot-functions extractions (tqdm skip-pin + is_debug_mode + connection_pool_executor)"
git push -u origin 1012-misthelper-refactor-hot-functions
```

## Step 8 — Open the PR

```bash
gh pr create \
  --title "refactor(1012): hot-functions bounded bundle (SC-001/002/003)" \
  --body "$(cat <<'EOF'
## Summary
Single bounded PR landing the three hot-bucket actions from `specs/1012-misthelper-refactor-hot-functions/spec.md`:

- **Action 1 (SC-001)**: tqdm skip-pin at `MistHelper.py:635` (NOTE breadcrumb + optional analyzer `--skip` flag).
- **Action 2 (SC-002/005/011)**: Extract `is_debug_mode` -> `IsDebugMode.check` (12 callsites), delete `EnvironmentUtils.is_debug_mode` wrapper (0 callers per Q1), rename `is_debug_mode_fn` -> `check_fn` (6 occurrences).
- **Action 3 (SC-003/005)**: Extract `execute_with_connection_pool_management` + 3 private helpers -> `ConnectionPoolExecutor.execute` + 3 private static methods (7 callsites), rename `connection_pool_fn` -> `execute_fn` (6 occurrences).

## Edit Surface
- 2 new files under `src/refactors/`
- 19 callsite rewrites
- 12 DI-slot rename occurrences
- 5 mandatory NOTE breadcrumb sites (grep-audited per SC-014) — 3 extraction + 2 DI-rename canonical NOTEs
- Zero wrapper shims (FR-003)

## Compliance
- Both new files A+/100.
- Aggregate baseline `>=99.6/A+` preserved.
- Pylint `>=8.74/10` preserved.
- All 15 CI jobs green.

## Verification
See `specs/1012-misthelper-refactor-hot-functions/quickstart.md` for the full audit-command list.

## Constitution
All seven principles PASS + REINFORCED. See `plan.md` Constitution Check.
EOF
)"
```

## Step 9 — Monitor CI and Merge

```bash
gh pr checks --watch
```

Once all 15 jobs are green:

```bash
gh pr view --json mergeStateStatus     # Expect: CLEAN
```

If `CLEAN`, merge normally:

```bash
gh pr merge --squash --delete-branch
```

If `BLOCKED / DIRTY / BEHIND`, do NOT reach for `--admin` reflexively (per `feedback_no_admin_bypass.md`). Investigate root cause; SKIPPED conditional jobs are not blocking.

## Step 10 — Post-Merge Housekeeping

Regenerate the analyzer catalog against the new `main` head:

```bash
git checkout main
git pull
python -m tools.refactor_analyzer > refactor_candidates.md
git add refactor_candidates.md
git commit -m "chore: regenerate refactor_candidates.md post-1012 merge"
git push
```

The 1012 initiative is now closed. Subsequent hot-bucket work is scoped by a new `1013-*` initiative if warranted.
