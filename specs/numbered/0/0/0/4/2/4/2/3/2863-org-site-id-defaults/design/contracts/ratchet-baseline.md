# Contract: Masking-default ratchet baseline

## Scope

The baseline file and the guard that reads it, for batch 2 of issue #2863. The batch cannot start until the placement decision D-14 is resolved.

## Location

After remediation, the baseline path is `tests/guardrails/org_site_identifier_default/baseline.json`. The guard test is `tests/guardrails/org_site_identifier_default/test_ratchet.py`.

## Schema

```json
{
  "schema_version": 1,
  "rule_id": "org_site_identifier_default",
  "scope": {
    "tracked_python_files": true,
    "excluded_path_components": ["tests"]
  },
  "files": {
    "src/example.py": 1
  }
}
```

- `schema_version` must be `1`.
- `rule_id` must be `org_site_identifier_default`.
- `scope` must match the values above. The scope is tracked Python files, with test folders excluded.
- `files` maps each normalized repository path to a positive integer count.

## Rejected Inputs

The guard fails for each of these inputs:

- A duplicate key in the JSON object.
- A path that is absolute, uses backslashes, or leaves the repository.
- A count that is zero, negative, or not an integer.
- A missing baseline file.
- Malformed JSON.
- A wrong `schema_version`.
- A wrong `rule_id`.
- A wrong `scope`.
- A zero-file scope from `git ls-files -z "*.py"`.
- A zero-parse scope, where no file reaches the parser.

## Ratchet Behavior

- The guard fails when a file count rises above its baseline count. It also fails on a new file with a count above zero.
- The guard fails on growth only. It never raises a baseline count on its own.
- The guard passes when counts fall. A reviewer then lowers the baseline in the same change.
- The guard prints one proof line. The line gives the scanned, parsed, finding, and baseline totals.

Caution: a count that rises without review hides a new masking default. The guard must fail on that change.

## Counting Rule

Each count uses the rule in research decision D-10. The rule counts three forms. The first form is a `.get` call with an identifier key and an empty default. The second form is a `str(` wrapper around that call. The third form is an expression followed by `or ""`.
