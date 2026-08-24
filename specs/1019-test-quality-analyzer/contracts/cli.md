# CLI Contract

**Feature**: 1019-test-quality-analyzer
**Consumer**: MistHelper maintainers (and later, CI once wired)
**Producer**: `tools.test_quality_analyzer.__main__:TestQualityCLI`

## Invocation

```bash
# Module form (preferred for internal use):
python -m tools.test_quality_analyzer [FLAGS]

# Script form (available once [project.scripts] entry is added; see plan.md deferred item 5):
test-quality-analyzer [FLAGS]
```

Runs from the repository root. All relative paths in flags are resolved
against the repository root.

## Flags

| Flag | Type | Default | Meaning |
|---|---|---|---|
| `--roots PATH [PATH ...]` | list of paths | `tests/` | Test roots to analyze. Multiple allowed. Must exist. |
| `--config PATH` | path | `tools/test_quality_analyzer/config.toml` | Alternate config file. |
| `--baseline PATH` | path | `tools/test_quality_analyzer/baseline.json` | Alternate baseline file. `""` disables baseline comparison. |
| `--report PATH` | path | `tools/test_quality_analyzer/output/report.json` | Where to write the JSON report. |
| `--summary PATH` | path | `tools/test_quality_analyzer/output/summary.md` | Where to write the Markdown summary. |
| `--gate` | flag | off | Enable gate mode: exit code 1 if new findings vs baseline. |
| `--write-baseline` | flag | off | Overwrite the baseline with the current run's findings and exit 0. |
| `--prune-baseline` | flag | off | Delete every baseline entry whose path the discoverer can never rediscover, then exit 0. |
| `--disable-rule RULE_ID` | repeatable | none | Runtime rule disable (config file remains untouched). |
| `--include-mist-api` | flag | off | Override the Mist-API exclusion for this run only. |
| `--fixed-timestamp ISO8601` | str | `now(UTC)` | Freeze the report timestamp; used by determinism tests only. |
| `--log-level LEVEL` | str | `INFO` | Standard `logging` level names. |
| `--help`, `-h` | flag | off | Print usage. |

All flags parsed by `argparse` with `choices=` where enumerable so invalid
input surfaces at parse time, not mid-run.

## Exit Codes

| Code | Meaning | When |
|---|---|---|
| `0` | Success | No new findings vs baseline in gate mode, or non-gate run completed. |
| `1` | New findings detected | Gate mode only; at least one new finding vs baseline. |
| `2` | Engine error | Parse error, malformed config, IO error, or invalid CLI usage. |

Exit codes match FR-012 exactly. FR-018 requires exit 2 on any parse error in
gate mode; the CLI honors this by treating `ParseError` records as fatal in
`--gate` mode.

## stdout / stderr

- **stdout**: A one-line summary at the end of every run:
  `test_quality_analyzer: <findings_total> findings (<critical>/<high>/<medium>/<low>), <skipped> skipped, <parse_errors> parse errors`
  In gate mode, an additional line: `gate: <N> new findings vs baseline`.
- **stderr**: Log output (respects `--log-level`). No mixing of stdout data
  with stderr logs.

## Standard Invocations

**First-time audit (P1 user story)**:
```bash
python -m tools.test_quality_analyzer
# Writes report.json and summary.md, exits 0.
```

**Seed the baseline** (after review of the first-run report):
```bash
python -m tools.test_quality_analyzer --write-baseline
```

**Gate a CI-style run (P2 user story)**:
```bash
python -m tools.test_quality_analyzer --gate
# Exits 0 if no new findings vs baseline, 1 if new findings, 2 if engine errored.
```

**Prune the stale baseline entries (issue #1769)**:
```bash
python -m tools.test_quality_analyzer --prune-baseline
# Deletes every entry whose path the discoverer can never rediscover, then exits 0.
```

The discoverer accepts `test_*.py` and `*_test.py` only. A baseline entry for any
other path can never clear, because no run rediscovers it. `--prune-baseline`
removes those entries. The flag is idempotent. A second run deletes nothing and
writes the same bytes.

Caution: `--prune-baseline` cannot combine with `--gate` or with
`--write-baseline`. Each pair exits 2, because the two modes disagree on what
the baseline should hold.

**Scoped run (Edge Case 7)**:
```bash
python -m tools.test_quality_analyzer --roots tests/unit/ssh/
```

**Fixture-only meta-test run**:
```bash
python -m tools.test_quality_analyzer \
  --roots tools/test_quality_analyzer/fixtures/bad/ \
  --baseline ""
```

## Determinism Guarantees

Given a byte-identical repository state, byte-identical config, and a fixed
`--fixed-timestamp` value, two runs MUST produce byte-identical
`report.json`, byte-identical `summary.md`, and byte-identical exit code
(SC-005). The tests in `tests/tools/test_quality_analyzer/test_reporting.py`
enforce this by hashing both artifacts across two consecutive runs.

## Non-Goals for this CLI

- No `--fix` mode. This iteration reports only; automated remediation is a
  separate future feature.
- No CI-workflow file emitted by the CLI. Wiring is deferred per
  Clarification Q3.
- No incremental / watch mode. Full-repo run is fast enough (SC-001).
