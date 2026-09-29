# Contract: Organization Security Posture Checklist Output

## Command behavior

Menu 276 generates the organization security posture checklist.

Required behavior:

1. In normal mode, the operation reads organization context and required Mist resources.
2. In `--test` mode, the operation uses fixture data and does not prompt.
3. The operation evaluates all registered checks.
4. The operation writes `data/OrgSecurityPosture.csv`.
5. The operation prints pass, fail, and review counts.

## CSV file

File path:

```text
data/OrgSecurityPosture.csv
```

Required columns, in order:

```text
check id,area,setting path,current value,recommended value,verdict,reason
```

Column rules:

| Column | Rule |
|--------|------|
| `check id` | Stable check ID. Must not be blank. |
| `area` | Human-readable area. Must not be blank. |
| `setting path` | Reviewer-facing setting path. Must not be blank. |
| `current value` | Safe display value. Must redact secrets. |
| `recommended value` | Secure target value. Must not be blank. |
| `verdict` | Must be `pass`, `fail`, or `review`. |
| `reason` | Must be one sentence. Must not be blank. |

## Verdict contract

| Verdict | Meaning |
|---------|---------|
| `pass` | The source data clearly meets the recommended value. |
| `fail` | The source data clearly violates the recommended value. |
| `review` | The source data is absent, unreadable, ambiguous, or needs exception evidence. |

Absent API settings must return `review`, and the reason must contain `absent`.

Any webhook URL that does not start with `https://` must return `fail`.

## Console summary

The console summary must include these counts:

- `pass`
- `fail`
- `review`

The counts must match the CSV verdict counts.

## Minimum checklist size

The registry must contain at least twelve checks. The planned registry contains sixteen checks.
