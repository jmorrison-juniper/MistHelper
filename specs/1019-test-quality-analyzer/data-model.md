# Phase 1 Data Model: Test Quality Analysis Engine

**Feature**: 1019-test-quality-analyzer
**Date**: 2026-07-14

All types are Python `dataclass`es defined in the analyzer package. Read-only
types are `frozen=True`. Attribute names use full words per constitution
Principle II.

## Enumerations

### `Severity`

```python
class Severity(str, Enum):
    CRITICAL = "critical"  # Ranked 4
    HIGH = "high"          # Ranked 3
    MEDIUM = "medium"      # Ranked 2
    LOW = "low"            # Ranked 1
```

Ordering: `CRITICAL > HIGH > MEDIUM > LOW` when sorting descending in the
Markdown summary and the deterministic report sort.

Source of truth: FR-009 taxonomy.

### `Category`

```python
class Category(str, Enum):
    UNTESTED = "untested"
    WEAK_ASSERTION = "weak_assertion"
    MISSING_FAILURE_MODE = "missing_failure_mode"
    MISSING_EDGE_CASE = "missing_edge_case"
    TAUTOLOGICAL = "tautological"
    PARSE_ERROR = "parse_error"        # From FR-018
    STALE_BASELINE = "stale_baseline"  # From FR-019
```

The last two are engine-level advisories, not detection findings.

### `RuleId`

Free-form string, one per detection rule (`untested_public_function`,
`weak_bare_truthy`, `weak_assert_not_none`, `weak_mock_called`,
`weak_broad_raises`, `weak_no_assertions`, `weak_self_mock`,
`missing_timeout`, `missing_connection_error`, `missing_http_4xx`,
`missing_http_5xx`, `missing_malformed_json`, `missing_empty_body`,
`edge_empty_value`, `edge_none_value`, `edge_oversized_value`,
`edge_unicode_value`, `tautological_return_echo`, `parse_error`,
`stale_baseline`). Documented in `contracts/config.schema.md`.

## Core Data Types

### `Finding` (atomic detection record)

```python
@dataclass(frozen=True)
class Finding:
    category: Category           # One of the taxonomy values above.
    rule_id: str                 # Stable identifier for the specific detector rule.
    severity: Severity           # Post-override severity.
    file_path: str               # Repo-relative POSIX path (forward slashes always).
    line_number: int             # 1-based line number of the offending code.
    explanation: str             # One-to-two sentence human explanation (FR-008).
    remediation: str             # One sentence suggested fix (FR-008).
    heuristic: bool = False      # True for FR-006 edge-case findings.
    related_source: str | None = None  # Optional repo-relative path to related SUT.
```

Invariants:
- `file_path` normalized to POSIX slashes regardless of host OS.
- `line_number >= 1`.
- `explanation` and `remediation` are pure ASCII (constitution Principle V).

### `Report` (envelope emitted per run)

```python
@dataclass(frozen=True)
class Report:
    engine_version: str                       # From tools.test_quality_analyzer.__version__.
    generated_at: str                         # ISO-8601 UTC, seconds precision.
    scanned_roots: tuple[str, ...]            # CLI-supplied test roots.
    config_snapshot: ConfigSnapshot           # Effective config after merge.
    findings: tuple[Finding, ...]             # Deterministically sorted.
    skipped_files: tuple[SkippedFile, ...]    # Excluded per FR-002.
    parse_errors: tuple[ParseError, ...]      # Per FR-018.
    stale_baseline_entries: tuple[str, ...]   # Per FR-019.
```

### `ConfigSnapshot`

Frozen view of the effective configuration for auditability.

```python
@dataclass(frozen=True)
class ConfigSnapshot:
    rules_enabled: Mapping[str, bool]       # rule_id -> enabled.
    severity_overrides: Mapping[str, Severity]  # rule_id -> Severity.
    exclusion_globs: tuple[str, ...]        # Path globs from [exclusions].
    mist_api_predicate: MistApiPredicate    # Parameters of the two-part rule.
```

### `MistApiPredicate`

```python
@dataclass(frozen=True)
class MistApiPredicate:
    banned_imports: tuple[str, ...]  # Default ("mistapi",).
    excluded_src_prefixes: tuple[str, ...]  # Default ("src/api/",).
```

### `SkippedFile`

```python
@dataclass(frozen=True)
class SkippedFile:
    file_path: str          # Repo-relative POSIX path.
    reason: str             # "mist_api_excluded" or user-configured exclusion id.
    matched_rule: str       # Predicate rule that matched.
```

### `ParseError`

```python
@dataclass(frozen=True)
class ParseError:
    file_path: str          # Repo-relative POSIX path.
    line_number: int | None  # None if the parser cannot locate a line.
    message: str            # SyntaxError.msg text (ASCII-normalized).
```

### `Baseline`

Baseline payload is a tuple of `Finding` records with the run envelope stripped.

```python
@dataclass(frozen=True)
class Baseline:
    findings: tuple[Finding, ...]  # Same shape as Report.findings.
```

On disk: JSON array of finding objects, canonicalized per research Decision 3.

### `BaselineDiff`

```python
@dataclass(frozen=True)
class BaselineDiff:
    new_findings: tuple[Finding, ...]      # In current run, not in baseline.
    removed_findings: tuple[Finding, ...]  # In baseline, not in current run.
    unchanged_count: int                   # Findings in both.
```

`new_findings` is the trigger for exit code 1 in gate mode. `removed_findings`
is advisory only — it never fails a gate but is printed so the maintainer can
prune the baseline.

## Relationships

- `Report.findings` is the atomic content stream; `Report.skipped_files`,
  `Report.parse_errors`, and `Report.stale_baseline_entries` are auxiliary
  streams that describe what the engine *did not* analyze and why.
- `Baseline.findings` is a strict subset of the report shape: identical
  `Finding` type, no envelope.
- `BaselineDiff.new_findings` and `.removed_findings` are computed by set
  difference on a canonical finding key: `(category, rule_id, file_path,
  line_number, explanation)`. Severity and remediation are NOT part of the
  key so severity re-tuning does not spuriously invalidate the baseline.

## Serialization Rules

- All `Finding` fields serialize as JSON scalars or arrays. `Severity` and
  `Category` serialize as their `.value` strings.
- `Report` serializes to JSON object with the six top-level keys in the order
  declared above.
- Baseline serialization uses only the `findings` array — the report envelope
  is dropped entirely.
- `json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True,
  separators=(",", ": "))` with a trailing newline.

## Sort Keys

**Findings sort key** (descending severity, then ascending everything else):
```python
def _sort_key(finding: Finding) -> tuple[int, str, str, int, str]:
    severity_rank = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    return (
        -severity_rank[finding.severity.value],  # descending severity
        finding.category.value,
        finding.file_path,
        finding.line_number,
        finding.rule_id,
    )
```

**Skipped-files, parse-errors, stale-baseline-entries** sort by `file_path`
ascending.

## Validation Rules

All validation happens in the constructors / factory methods on the owning
classes (no dataclass `__post_init__` gymnastics beyond simple asserts):

| Type | Validation |
|---|---|
| `Finding` | `line_number >= 1`; ASCII explanation/remediation; POSIX path. |
| `Report` | `generated_at` matches `YYYY-MM-DDTHH:MM:SS+00:00` regex; findings pre-sorted. |
| `Baseline` | Findings pre-sorted; no duplicates by canonical key. |
| `ConfigSnapshot` | Severity overrides restricted to the taxonomy enum. |

## State Transitions

The engine is stateless within a run — no state machine to model. Between
runs, the only durable state is:

1. `config.toml` — hand-edited.
2. `baseline.json` — updated deliberately by the maintainer (never
   auto-regenerated per spec.md Assumption 5).
3. `output/report.json` and `output/summary.md` — overwritten every run.

Baseline regeneration is a manual CLI action (`--write-baseline`) that
serializes the current run's `findings` array to `baseline.json` after the
maintainer has verified the report.
