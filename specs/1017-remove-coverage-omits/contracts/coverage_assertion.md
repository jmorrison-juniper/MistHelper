# Contract: Coverage Assertion

**Feature**: 1017-remove-coverage-omits
**Refs**: #878
**Applies to**: every PR from PR-1 through T-Final

**Validation rule**: Each PR MUST demonstrate BOTH (a) per-file coverage ≥ 90% for every module de-omitted in that PR, AND (b) full-suite `pytest --cov --cov-fail-under=90` exits with status 0. A PR that lowers global coverage below the branch-cut baseline (measured pre-PR) fails SC-003 and MUST be rejected.

## §1 Per-file assertion

Invoked once per de-omitted module in the PR under review.

```bash
pytest --cov=<dotted.module.path> \
       --cov-report=term-missing \
       --cov-fail-under=90 \
       tests/unit/<matching-path>/
```

**Example — PR-1 utility check**:
```bash
pytest --cov=src.utils.filter_operator_engine \
       --cov-report=term-missing \
       --cov-fail-under=90 \
       tests/unit/utils/test_filter_operator_engine.py
```

**Exit criterion**: status 0. Any uncovered line surfaced under "Missing" MUST be either (i) reachable and tested in the same PR, or (ii) covered by an explicit `# pragma: no cover` that was pre-existing at branch-cut (new pragmas violate SC-006).

## §2 Full-suite assertion

Invoked once at the end of each PR before pushing.

```bash
pytest --cov --cov-fail-under=90 --cov-report=term
```

**Exit criterion**: status 0. `pyproject.toml [tool.coverage.report] fail_under = 90` is authoritative — this command reads it. Do NOT pass `--cov-fail-under=<N>` with `N != 90` in CI or local pre-push checks (FR-009).

## §3 Omit-list assertion (SC-001)

Invoked in T-Final. Verifies the retained omit set matches the frozen 6-entry inventory from data-model.md §1.

```bash
python -c "
import tomllib, pathlib
data = tomllib.loads(pathlib.Path('pyproject.toml').read_text())
omit = data['tool']['coverage']['run']['omit']
expected = ['tests/*', 'venv/*', '.venv/*', 'setup.py', '*/site-packages/*', 'src/maps/*']
assert sorted(omit) == sorted(expected), f'SC-001 violated: {sorted(omit)} != {sorted(expected)}'
print('SC-001 OK: retained omit list matches frozen inventory')
"
```

**Exit criterion**: status 0 and stdout contains `SC-001 OK`.

## §4 Escape-hatch cap assertion (FR-015)

At most 2 modules may retain their omit entry with a `# TODO(1017): refactor pending` annotation. Verify:

```bash
python -c "
import tomllib, pathlib
data = tomllib.loads(pathlib.Path('pyproject.toml').read_text())
omit = data['tool']['coverage']['run']['omit']
retained = {'tests/*', 'venv/*', '.venv/*', 'setup.py', '*/site-packages/*', 'src/maps/*'}
escape_hatches = [e for e in omit if e not in retained]
assert len(escape_hatches) <= 2, f'FR-015 violated: {len(escape_hatches)} escape hatches > 2'
print(f'FR-015 OK: {len(escape_hatches)} escape hatches')
"
```

**Exit criterion**: status 0. If `len(escape_hatches) > 0`, a matching `# TODO(1017)` comment MUST appear on the same line in pyproject.toml (grep the file separately).

## §5 New-suppression assertion (SC-006)

No PR from PR-1 through T-Final may introduce new `# pragma: no cover`, `# type: ignore`, or `# noqa` annotations inside newly-added test files.

```bash
git diff main...HEAD -- tests/ | \
  grep -E '^\+.*(# pragma: no cover|# type: ignore|# noqa)' && \
  { echo 'SC-006 violated: new suppression added'; exit 1; } || \
  echo 'SC-006 OK: no new suppressions in tests/'
```

**Exit criterion**: status 0.

## §6 Baseline-drift assertion

Before each PR, capture the pre-PR coverage number; after the PR, verify the number strictly rose (or stayed equal only if the PR is docs-only like PR-0).

```bash
# pre-PR
git checkout main
pytest --cov --cov-report=json:/tmp/baseline.json --cov-fail-under=90
python -c "import json; print(json.load(open('/tmp/baseline.json'))['totals']['percent_covered'])" > /tmp/baseline.txt

# post-PR
git checkout <branch>
pytest --cov --cov-report=json:/tmp/postpr.json --cov-fail-under=90
python -c "
import json
baseline = float(open('/tmp/baseline.txt').read())
postpr = json.load(open('/tmp/postpr.json'))['totals']['percent_covered']
assert postpr >= baseline, f'Coverage regressed: {postpr} < {baseline}'
print(f'Coverage: {baseline:.2f} -> {postpr:.2f}')
"
```

**Exit criterion**: status 0.
