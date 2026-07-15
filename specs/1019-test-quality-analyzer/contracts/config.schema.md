# Config Contract: `tools/test_quality_analyzer/config.toml`

**Feature**: 1019-test-quality-analyzer

Committed to git. Single source of truth for rule enablement, severity
overrides, and exclusion predicate parameters. Parsed with stdlib `tomllib`
at engine start.

Malformed config → exit code 2 (per FR-021). Unknown rule id in any table
→ exit code 2. Unknown severity value in `[severity]` → exit code 2.

## Tables

### `[rules]` — per-rule enable/disable

Keys are rule ids from the enumeration in `data-model.md` under `RuleId`.
Values are booleans. Missing keys default to `true` (enabled).

```toml
[rules]
untested_public_function = true
weak_bare_truthy = true
weak_assert_not_none = true
weak_mock_called = true
weak_broad_raises = true
weak_no_assertions = true
weak_self_mock = true
missing_timeout = true
missing_connection_error = true
missing_http_4xx = true
missing_http_5xx = true
missing_malformed_json = true
missing_empty_body = true
edge_empty_value = true
edge_none_value = true
edge_oversized_value = true
edge_unicode_value = true
tautological_return_echo = true
```

Purpose: FR-021 enable/disable toggles. Disabling a rule silences all
findings from that detector without deleting code.

### `[severity]` — rule-id → severity overrides

Keys are rule ids. Values must be one of `critical`, `high`, `medium`, `low`.
Missing keys use the built-in default for the rule (documented as a comment
above each entry).

```toml
[severity]
# Defaults (from FR-009 mapping):
untested_public_function = "high"   # default: high
weak_bare_truthy = "medium"         # default: medium
weak_assert_not_none = "medium"     # default: medium
weak_mock_called = "high"           # default: high
weak_broad_raises = "medium"        # default: medium
weak_no_assertions = "high"         # default: high
weak_self_mock = "high"             # default: high
missing_timeout = "high"            # default: high  (HTTP path)
missing_connection_error = "high"   # default: high
missing_http_4xx = "medium"         # default: medium
missing_http_5xx = "high"           # default: high
missing_malformed_json = "medium"   # default: medium
missing_empty_body = "low"          # default: low
edge_empty_value = "low"            # default: low  (heuristic)
edge_none_value = "low"             # default: low  (heuristic)
edge_oversized_value = "low"        # default: low  (heuristic)
edge_unicode_value = "low"          # default: low  (heuristic)
tautological_return_echo = "high"   # default: high
```

Purpose: FR-009 configurable severity mapping. Maintainer can raise or lower
severity to match local risk tolerance without touching engine code.

### `[exclusions]` — Mist-API predicate + additional path globs

```toml
[exclusions]
# Path globs (POSIX-style) evaluated against repo-relative test paths. A file
# matching any glob here is skipped with reason "user_excluded".
path_globs = []

# Parameters of the Mist-API two-part predicate (FR-002 / research Decision 6).
# Both keys default to the values shown; override only if the repo layout
# changes.
banned_imports = ["mistapi"]              # Module-scope imports that mark a test as Mist-API.
excluded_src_prefixes = ["src/api/"]      # Any src/* module under these prefixes marks its callers as Mist-API.
```

Purpose: FR-002 configurable Mist-API predicate + FR-021 general exclusions.
The Mist-API predicate keys are ALWAYS present with defaults; the
`path_globs` list is a user-extensible allowlist for tests that must be
excluded for reasons other than the Mist-API surface.

## Validation

| Input | Behavior |
|---|---|
| File missing | Use built-in defaults, log an `info` message, continue. |
| File present, empty | Same as missing. |
| Unknown rule id in `[rules]` or `[severity]` | Exit 2, message names the offending key. |
| Non-boolean value in `[rules]` | Exit 2. |
| Non-taxonomy string in `[severity]` | Exit 2. |
| Non-list value in `[exclusions].path_globs` | Exit 2. |
| Invalid TOML syntax | Exit 2, forward the `tomllib.TOMLDecodeError` message. |

## Non-Goals

- No per-file overrides in `config.toml`. Per-file suppressions live in the
  baseline, not in config.
- No environment-variable overrides. CLI flags are the runtime override
  surface.
