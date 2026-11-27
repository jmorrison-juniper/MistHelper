# Contract: Credential default ratchet output and baseline

## Output

The guard prints two ASCII lines.

1. `credential-default-scan files=<n> parse_failures=<p> candidates=<c>`
2. `credential-default-baseline open=<o> accepted=<a>`

`files` counts tracked Python files that the scanner read. `parse_failures` counts files that the parser rejected. `candidates` counts defaults that match the rule.

## Baseline file

Path: `tests/guardrails/credential_default_ratchet/credential_default_baseline.json`

Shape:

```json
{"schema_version": 1, "candidates": [{"path": "src/example.py", "scope": "function name", "kind": "dataclass-default", "fingerprint": "hex digest", "group": "A", "line": 1}], "accepted": [{"path": "src/example.py", "scope": "function name", "kind": "env-default", "fingerprint": "hex digest", "group": "B", "line": 2, "reason": "Display label only."}]}
```

The fingerprint hashes the normalized statement, the enclosing scope, and the occurrence order. A literal value does not enter the fingerprint.

## Failure conditions

The guard fails when any condition holds.

- `files` equals 0.
- `parse_failures` is greater than 0.
- A scanned candidate has no entry in either section.
- A baseline entry has no scanned match.
- An accepted entry has an empty reason.
- The baseline file is missing or is not valid JSON.

## Proofs

- A zero-input fixture fails with `files=0`.
- A negative fixture holds one environment default and one dataclass credential default. The scanner reports both.
