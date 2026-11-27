# Data Model: Locked Worktree Bootstrap

**Scope**: The bootstrap run that calls the locked sync. No database and no persistent store.

## Entities

### Registry Source

| Field | Value |
|---|---|
| Origin | A line in `uv.lock` that names a registry, such as `source = { registry = "https://pypi.org/simple" }`. The reader is `LOCK_REGISTRY_PATTERN` (`scripts/bootstrap_worktree.py` line 117). |
| Fields | Package name (from the preceding `name` line), version, index URL, and line number. |
| Natural key | Package name, version, and index URL. |
| Values on `main` | 195 lines. Each names `https://pypi.org/simple`. The first line is line 8 (RC-14). |
| Other source kinds | The root project and the `misthelper-devtools` package use other source kinds (RC-15, RC-46). They are not registry sources. |

### Index Variable

| Field | Value |
|---|---|
| Origin | The child environment. `_install_environment` copies the caller environment (line 636), and `InstallationPolicy.apply` changes it (line 404). |
| Names | `UV_INDEX_URL`, `UV_DEFAULT_INDEX`, `UV_INDEX`, and `UV_EXTRA_INDEX_URL`. |
| Natural key | Variable name. |
| Bootstrap-set values | `UV_INDEX_URL` and `UV_EXTRA_INDEX_URL` are set from the pip index settings (lines 432 to 446, RC-04). The public override sets `UV_INDEX_URL` (line 354). |
| Removed by the bootstrap | `UV_DEFAULT_INDEX`, `UV_INDEX`, and `UV_INDEX_URL` are removed before the mapping (lines 407 to 411, RC-48). |
| Primary index rule | `configured_index` reads `UV_INDEX_URL` first (line 344, RC-10) and `UV_DEFAULT_INDEX` second (line 345, RC-47). The second read never sees a value (DEF-06). |
| Active names for the message | The names of the variables that hold a value in the child environment after the mapping. This change lists them (FR-004). |

### Cause Verdict

| Value | Condition |
|---|---|
| index-mismatch | The lock check output holds the stale phrase, and the primary index differs from the first registry source after normalization. |
| lock-drift | The lock check output holds the stale phrase, and no primary index exists, or the primary index equals the registry source. |
| unknown | The lock check passes, cannot start, or prints no stale phrase. |
| none | The locked sync passes. No verdict is needed. |

Normalization: remove the trailing slash and fold the case (`normalize_index`, line 337).

## State Transitions for One Bootstrap Run

1. `prepared`: the child environment exists, and the pip mapping is applied.
2. `synced`: the locked sync exits with code 0. The verdict is `none`.
3. `failed`: the locked sync exits with a non-zero code. The bootstrap then runs the lock check.
4. `checked`: the lock check finishes. The verdict follows the rules in the cause verdict table.
5. `reported`: `main` prints the final message and returns exit code 1 for a failed run (line 900).

With `--public-lock-index`, step 1 also sets `UV_INDEX_URL` to the public index and clears the other index variables (lines 349 to 355).

## Validation Rules

- The lock file is read as UTF-8 text. A read failure gives no registry, and the verdict then follows the drift path (lines 325 to 335).
- The first registry source is the only registry value that the verdict uses (DEF-05).
- The lock check runs with the same child environment as the locked sync (line 495 onward). The verdict therefore reflects the same index settings.
