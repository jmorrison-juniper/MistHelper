# The ruff ratchet for mist-ops-platform

This page tells you how the CI job `Ruff (ops platform)` works. It also tells
you how to tighten the job. Issue #1974 created the job.

## Why the job exists

`mist-ops-platform/pyproject.toml` declares its own `[tool.ruff]` configuration.
That configuration is stricter than the root configuration. It sets
`line-length = 99`, it selects the extra rule families `N`, `A`, `C4`, `SIM`,
`TCH`, `RUF`, and `PLR`, and it sets `max-args = 5` and `max-statements = 15`.

No gate ever read it. The root `pyproject.toml` names `mist-ops-platform` in
`extend-exclude`, and every root lint job runs from the repository root. The
`pytest (ops platform)` job runs inside the sub-project, but it runs pytest
only.

The gap had a cost. `src/worker/sync/events.py` called `uuid4` without an
import. The documented fallback in `_extract_entity_id` raised `NameError` on
every execution, and the Celery worker crashed on any Mist audit event with no
usable identifier. Ruff reports that defect as `F821`. Issue #1975 repaired the
crash. This job stops the next one.

## The config discovery trap

Ruff picks the configuration file closest to the file that it checks. Two
commands therefore give two different answers for the same file.

```powershell
# Reads the SUB-PROJECT config. Reports findings.
python -m ruff check mist-ops-platform/src/api/routes/health.py

# Reads the ROOT config. Reports nothing, because extend-exclude skips the path.
python -m ruff check .
```

The cause is config discovery, not path exclusion. `--force-exclude` does not
change the result.

Warning: a verification command must match the gate command. If you name a file
inside `mist-ops-platform` from the repository root, you read a different rule
set than the root gate reads. To reproduce this job, change into the
sub-project directory first.

```powershell
cd mist-ops-platform
python -m ruff check . --select F,B,E9 --ignore F401,B008,B905 --output-format=concise
```

## What the job blocks on today

The blocking step selects the correctness families. Those families hold the
rules that find defects rather than style.

```
ruff check . --select F,B,E9 --ignore F401,B008,B905 --output-format=concise
```

The step measures zero findings, so it is green today and red on the first
regression. It blocks on `F821` (undefined name), `F841` (unused variable),
`F811` (redefinition), `F632` (identity comparison), `B006` (mutable default
argument), `B904` (lost exception context), and every other rule in `F`, `B`,
and `E9` except the three named below.

A second step runs the whole sub-project configuration with
`continue-on-error: true`. That step prints every remaining finding, so the
work stays visible. It does not block.

## The deferred rules

The full configuration reports 393 findings. Measured with ruff 0.16.3 against
commit `4e1b69e6`.

These three rules sit inside the blocking families, so the job names each one in
its `--ignore` list.

| Rule | Count | Why it waits |
| - | - | - |
| `B008` function-call-in-default-argument | 122 | Every hit is the FastAPI `Depends` and `Query` idiom. The repair is the `flake8-bugbear` `extend-immutable-calls` setting, not a source edit. |
| `F401` unused-import | 69 | Mechanical. `ruff check --select F401 --fix` clears it. |
| `B905` zip-without-explicit-strict | 1 | One call site. Add `strict=`. |

These rules sit outside the blocking families. The advisory step reports them.

| Rule | Count |
| - | - |
| `E501` line-too-long | 33 |
| `TC003` typing-only-standard-library-import | 32 |
| `PLR2004` magic-value-comparison | 27 |
| `TC002` typing-only-third-party-import | 23 |
| `N815` mixed-case-variable-in-class-scope | 17 |
| `I001` unsorted-imports | 14 |
| `TC001` typing-only-first-party-import | 14 |
| `RUF100` unused-noqa | 13 |
| `PLR0915` too-many-statements | 8 |
| `PLR0917` too-many-positional-arguments | 8 |
| `SIM117` multiple-with-statements | 4 |
| `PLR0402` manual-from-import | 3 |
| `RUF023` unsorted-dunder-slots | 2 |
| `RUF022` unsorted-dunder-all | 1 |
| `UP043` unnecessary-default-type-args | 1 |
| `UP046` non-pep695-generic-class | 1 |

## How to tighten the ratchet

Follow these steps for each family.

1. Clear one family in the source. Start with `F401`, because
   `ruff check . --select F401 --fix` clears it.
2. Confirm the family reports zero. Run
   `ruff check . --select <RULE> --statistics` from inside the sub-project.
3. Delete that rule from the `--ignore` list in the blocking step, or add its
   family to the `--select` list.
4. Run the blocking command and confirm exit code 0.
5. Update the table above with the new counts.

Never add a rule to the `--ignore` list to clear a new finding. The repository
rule is fix over suppress. If a rule reports a false positive, change the ruff
configuration for that rule, and record the reason.
