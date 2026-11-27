# Data Model: Locked Bootstrap With a Configured Pip Index

No database or persistent store is involved. The entities below exist in memory for one bootstrap run.

## ConfiguredIndex

- **Origin**: the caller `PIP_INDEX_URL` (highest precedence), then the install file setting, then the global file setting (research.md, R35).
- **Attributes**: origin, role (pip primary or pip extra), and a credential-bearing flag.
- **Natural key**: the URL text, compared after removing a trailing slash and folding case.
- **Rule**: the URL is never printed. The Caution text names no URL (FR-004, FR-017).

## LockRegistry

- **Source**: the first `source = { registry = "https://pypi.org/simple" }` line of `uv.lock` (research.md, R31 and R43).
- **Current value**: `https://pypi.org/simple`.
- **Natural key**: the registry URL text.
- **Rule**: a missing value stops the run before the locked sync (TST-04).

## SourceDecision (one per run)

- **Fields**: `sync_primary` (LockRegistry), `sync_extras` (always empty), `public_lock_index` (boolean), `pip_override` (public URL or none), and `caution_needed` (boolean).
- **Derivation**: `sync_primary` equals LockRegistry. `caution_needed` is true when a ConfiguredIndex exists and differs from LockRegistry after normalization.

## LockVerdict

- **Values**: `current`, `stale`, or `unknown`.
- **Source**: the exit code of the lock check.
- **Rule**: `stale` requires the stale phrase in the output (research.md, R37). Any other failure gives `unknown`.

## State transitions (one run)

| From | Event | To | Action |
| - | - | - | - |
| Start | LockRegistry read fails | Stopped | Raise one RuntimeError that names `uv.lock` (TST-04). |
| Start | LockRegistry read succeeds | Mapped | Set `UV_INDEX_URL` to LockRegistry. Remove the extra and alias settings. Log the Caution line when `caution_needed` is true. |
| Mapped | Locked sync exits 0 | Synced | Continue to the browser and account steps. |
| Mapped | Locked sync exits non-zero | Diagnosing | Run the lock check. |
| Diagnosing | Verdict is stale | Failed (drift) | Raise the lock drift message. |
| Diagnosing | Verdict is current or unknown | Failed (original) | Re-raise the original error. |
