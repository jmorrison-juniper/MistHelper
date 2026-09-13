# Quickstart: Test Quality Analysis Engine

**Feature**: 1019-test-quality-analyzer

This is the maintainer's runnable validation guide for the engine. It is the
document a maintainer opens to prove the feature is delivered and working.
For architectural context, see [`plan.md`](./plan.md). For rule-by-rule
behavior, see [`spec.md`](./spec.md) and
[`contracts/config.schema.md`](./contracts/config.schema.md).

## Prerequisites

- Repository checked out; you are at the repo root.
- Python 3.13+ installed and on `PATH` (matches constitution binding).
- Dev dependencies installed (`uv sync` or `pip install -e ".[dev]"`).
- No network access required by the engine — it can run offline (SC-006).

## One-Time Setup

The engine ships as a repo-internal tool at `tools/test_quality_analyzer/`.
No install step is needed once the package is committed. On first invocation
the engine creates `tools/test_quality_analyzer/output/` (git-ignored).

## Scenario A — Baseline audit (User Story 1)

Run the analyzer against the current repo:

```bash
python -m tools.test_quality_analyzer
```

**Expected**:
- Exit code `0`.
- `tools/test_quality_analyzer/output/report.json` exists and validates
  against `tools/test_quality_analyzer/report.schema.json`.
- `tools/test_quality_analyzer/output/summary.md` exists, grouped by
  severity descending.
- Wall-clock time under 60 s (SC-001).
- stdout final line matches the pattern:
  `test_quality_analyzer: <N> findings (<C>/<H>/<M>/<L>), <S> skipped, <P> parse errors`.

**Validate SC-002 (golden findings)**:
```bash
python -c "
import json
from pathlib import Path
report = json.loads(Path('tools/test_quality_analyzer/output/report.json').read_text())
skipped = {s['file_path'] for s in report['skipped_files']}
findings = {(f['file_path'], f['line_number'], f['category']) for f in report['findings']}
assert 'src/api/api_data_fetcher.py' in skipped, 'FR-002: api_data_fetcher.py must be skipped'
assert ('tests/unit/ssh/test_shell_executor.py', 110, 'weak_assertion') in findings
assert ('tests/maps/test_viewer_callbacks_wave_b_c.py', 526, 'weak_assertion') in findings
print('golden findings present')
"
```

**Validate FR-014 (no network) and FR-011 (schema validates)** are covered by
the tests under `tests/tools/test_quality_analyzer/` — see Scenario D below.

## Scenario B — Seed the baseline

After reviewing the report from Scenario A, freeze it:

```bash
python -m tools.test_quality_analyzer --write-baseline
```

**Expected**:
- Exit code `0`.
- `tools/test_quality_analyzer/baseline.json` written with the findings
  array only (no run envelope), canonicalized per research Decision 3.
- Subsequent runs in gate mode see zero new findings.

Commit the baseline (`git add tools/test_quality_analyzer/baseline.json`)
so it becomes the shared reference.

## Scenario C — Gate mode (User Story 2)

Regression prevention:

```bash
python -m tools.test_quality_analyzer --gate
```

**Expected on a clean tree**: Exit `0`, message `gate: 0 new findings vs baseline`.

**Expected on a tree that adds a weak assertion**: Exit `1`, the new finding
listed distinctly from baseline entries.

**Expected on a tree with a syntax error in a test file**: Exit `2`, the
failing file called out in the `parse_errors` section of the report.

Validate SC-004 by hand:
```bash
# Introduce a synthetic weak-assertion test, run gate, expect exit 1.
echo 'def test_x():
    result = 5
    assert result is not None
' > tests/scratch_test.py
python -m tools.test_quality_analyzer --gate; echo "exit=$?"
rm tests/scratch_test.py
python -m tools.test_quality_analyzer --gate; echo "exit=$?"
```
Expect `exit=1` then `exit=0`.

## Scenario D — Meta-test suite (User Story 3)

Verify the engine's own fixtures pass:

```bash
pytest tests/tools/test_quality_analyzer/ -v
```

**Expected**:
- All tests pass.
- `test_meta_fixtures.py` proves SC-003: every bad fixture yields the exact
  claimed finding; every good fixture yields zero findings.
- `test_golden_repo.py` proves SC-002 against the real repo.
- `test_reporting.py` proves SC-005 by running the engine twice with a
  frozen timestamp and asserting byte-identical output.

## Scenario E — Determinism check (SC-005)

```bash
python -m tools.test_quality_analyzer --fixed-timestamp 2026-07-14T00:00:00+00:00
sha256sum tools/test_quality_analyzer/output/report.json > /tmp/hash1
python -m tools.test_quality_analyzer --fixed-timestamp 2026-07-14T00:00:00+00:00
sha256sum tools/test_quality_analyzer/output/report.json > /tmp/hash2
diff /tmp/hash1 /tmp/hash2 && echo "SC-005 pass"
```

**Expected**: `SC-005 pass` printed and hash files identical.

## Scenario F — Configuration override

Disable a rule at runtime without editing the config file:

```bash
python -m tools.test_quality_analyzer --disable-rule edge_oversized_value
```

**Expected**: All `edge_oversized_value` findings absent from the report.
Other findings unchanged. The `config_snapshot.rules_enabled` block in the
report shows `"edge_oversized_value": false` reflecting the runtime override.

## Success Criteria Mapping

| Success Criterion | Validated by |
|---|---|
| SC-001 (60 s budget) | Scenario A wall-clock. |
| SC-002 (golden findings) | Scenario A validation script + `test_golden_repo.py`. |
| SC-003 (fixture accuracy) | Scenario D (`test_meta_fixtures.py`). |
| SC-004 (gate exit codes) | Scenario C. |
| SC-005 (determinism) | Scenario E + `test_reporting.py`. |
| SC-006 (zero network) | `test_cli.py` socket monkey-patch. |
| SC-007 (schema validates) | `test_reporting.py`. |
| SC-008 (weak tests drop 80%) | Longitudinal — measured post-adoption. |
| SC-009 (findings locatable < 30 s) | Human review of `summary.md`. |

## Troubleshooting

- **`ImportError: No module named tools.test_quality_analyzer`** — run from
  the repo root, not from inside `tools/`.
- **`exit 2` with no obvious error** — check stderr for the `tomllib` error
  message; malformed config is the most common cause.
- **Golden-set drift** — if `test_golden_repo.py` fails because the real repo
  no longer has the anchor findings, that is a *win*, not a bug: update the
  golden fixture list to the next stable set of anchors.

## References

- [`spec.md`](./spec.md) — functional requirements FR-001..FR-021.
- [`plan.md`](./plan.md) — implementation plan and module structure.
- [`data-model.md`](./data-model.md) — dataclass and enum definitions.
- [`contracts/cli.md`](./contracts/cli.md) — full CLI surface.
- [`contracts/config.schema.md`](./contracts/config.schema.md) — TOML schema.
- [`contracts/report.schema.json`](./contracts/report.schema.json) — JSON Schema for the report.
