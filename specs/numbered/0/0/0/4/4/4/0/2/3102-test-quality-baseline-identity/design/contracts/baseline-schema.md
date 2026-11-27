# Contract: Baseline file schema

**Path**: `.github/test-quality-baseline.json` in MistHelper. The writer is `BaselineDiffer.write` in misthelper-devtools `baseline.py` (blob a5b505cd, R-31). This contract takes effect in release 0.7.0.

## Format

- The file holds one JSON array of baseline entry objects. The array has no envelope.
- The text is UTF-8 with ASCII-only escapes. It uses two-space indentation and sorted keys.
- Separators are a comma and a colon followed by one space. Line endings are LF. The file ends with one newline.
- The writer is the same canonical writer as release 0.6.4. The only new key is `content_anchor`.

## Fields of a baseline entry

| Field | Type | Role |
| - | - | - |
| `category` | string | Category value. Part of the identity key. |
| `content_anchor` | string | 64 lowercase hexadecimal characters, or the sentinel `file-level`. Part of the identity key. |
| `explanation` | string | Rule text for the finding. Part of the identity key. |
| `file_path` | string | POSIX path relative to the repository root. Part of the identity key. |
| `heuristic` | boolean | Marks an edge-case finding. Not part of the identity key. |
| `line_number` | integer | Line number at the last write. Information only. Not part of the identity key. |
| `related_source` | string or null | Source module path for the finding. Not part of the identity key. |
| `remediation` | string | Suggested fix text. Not part of the identity key. |
| `rule_id` | string | Rule identifier. Part of the identity key. |
| `severity` | string | Severity value. Not part of the identity key. |

## Identity key

The identity key is the tuple `(category, rule_id, file_path, explanation, content_anchor)`. It replaces `line_number` with `content_anchor` in the pinned key at `baseline.py` line 55.

Two entries with the same identity key are two occurrences of one key. The comparison counts occurrences. It does not collapse them into one key.

## Content anchor

1. Read the source file as UTF-8 text with universal newlines.
2. Take the line at `line_number`, counted from 1.
3. Normalize the line. Join its whitespace-separated tokens with one ASCII space.
4. Compute SHA-256 over the UTF-8 bytes of the normalized text. Write the digest in lowercase hexadecimal.
5. For a file-level finding, write `file-level`, and skip steps 1 to 4.

A file-level finding is a finding that the `_finding` helper creates at line 1 (`missing_failure_mode.py` line 760, R-45).

## Validation

The loader fails closed with exit code 2 in these cases:

- The `content_anchor` field is missing or is not a string.
- The value is neither 64 lowercase hexadecimal characters nor `file-level`.
- The `line_number` value lies outside the source file.

## Example entry

This entry is real. It is on main at `mist-ops-platform/tests/integration/test_e2e_smoke.py` line 26 (R-22). The anchor is the digest of the normalized line `assert app is not None`.

```json
{
  "category": "weak_assertion",
  "content_anchor": "5201feb70a5f94ce6321d47d0e892442c87998aa1545b37e5f4950734bfcdcfb",
  "explanation": "assert x is not None only verifies non-None state.",
  "file_path": "mist-ops-platform/tests/integration/test_e2e_smoke.py",
  "heuristic": false,
  "line_number": 26,
  "related_source": "mist-ops-platform/tests/integration/test_e2e_smoke.py",
  "remediation": "Assert on the actual value / type / structure you expect.",
  "rule_id": "weak_is_not_none",
  "severity": "medium"
}
```

## Migration rules

- The migration regenerates the file from current findings with the release 0.7.0 writer.
- A retained entry keeps its `line_number` value.
- An entry that no current finding matches is not written. The pull request lists each such entry.
- The migration writes no anchor for an entry whose file is missing. Such an entry is not written.
