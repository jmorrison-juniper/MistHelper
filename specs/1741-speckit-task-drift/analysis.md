# Analysis: Speckit task record drift

Run date: 2026-09-13.

## Before counts

The first measurement walked every `specs/*/tasks.md` file and counted task
boxes outside no context filter. The repository held 2,661 unchecked task boxes
and 2,837 checked task boxes.

The four target specs held the drift from issue #1741.

| Spec | Before unchecked | Before checked |
| - | -: | -: |
| `specs/1026-ste-linter/` | 35 | 0 |
| `specs/1027-ste-dict-extractor/` | 17 | 0 |
| `specs/1028-ste-compliance-cleanup/` | 19 | 0 |
| `specs/1030-ste-src-cleanup/` | 38 | 0 |
| **Total** | **109** | **0** |

The template at `.specify/templates/tasks-template.md` held 34 checkbox
markers. Those examples remain, because the template teaches the task format.

## After counts

The same measurement after reconciliation found 2,552 unchecked task boxes and
2,946 checked task boxes.

| Spec | After unchecked | After checked |
| - | -: | -: |
| `specs/1026-ste-linter/` | 0 | 35 |
| `specs/1027-ste-dict-extractor/` | 0 | 17 |
| `specs/1028-ste-compliance-cleanup/` | 0 | 19 |
| `specs/1030-ste-src-cleanup/` | 0 | 38 |
| **Total** | **0** | **109** |

## Evidence basis

Each tick in the four task files has an evidence note. Each note cites one
proof path. The paths name shipped tools, tests, workflows, specs, or source
folders.

These paths give the strongest evidence:

```text
tools/ste_linter/ - STE linter package
tests/unit/ste_linter/ - STE linter tests
tools/ste_linter/dictionary/extract.py - dictionary extractor
tools/ste_linter/dictionary/quality.py - extractor quality harness
tests/unit/ste_linter/test_dictionary_extract.py - extractor tests
MistHelper.py - root-file STE cleanup
src/ - source-tree STE cleanup
.github/workflows/ste-lint.yml - STE writing gate
.pre-commit-config.yaml - STE pre-commit hook
pyproject.toml - STE linter configuration and allow list
```

## Unproved tasks

No task in the four target specs stayed unproved. Each one now has a delivery
path. The large set of unchecked boxes outside the four target specs remains
outside this reconciliation.

## Reserved task files that this change skipped

This change did not edit these five task files, because other agents owned them:

- `specs/006-web-interactivity/tasks.md`
- `specs/001-wired-client-global-report/tasks.md`
- `specs/003-menu1-compliance-refactor/tasks.md`
- `specs/001-mist-ops-platform/tasks.md`
- `specs/1016-misthelper-suppression-cleanup/tasks.md`

These files need follow-up reconciliation after the active edits finish.

## Guard evidence

The guard tool is `tools/speckit_task_audit.py`. It walks the spec directories.
It counts checked and unchecked task boxes. It ignores fenced code blocks.
It accepts an allow-list file. It exits nonzero for unchecked tasks in complete specs.

The tests in `tests/unit/tools/test_speckit_task_audit.py` cover:

- A complete spec with all tasks checked.
- A complete spec with unchecked tasks.
- A complete spec covered by the allow list.
- A missing `tasks.md` file.
- An empty task file.
- A task file with no checkbox.
- A malformed checkbox.
- A nested checkbox.
- A checkbox inside a fenced code block.

The workflow job `SpecKit task audit (advisory)` runs the tool in
`.github/workflows/ci.yml` with `continue-on-error: true`. It cannot block an
unrelated pull request on day one.

## Local validation

The targeted validation passed:

```text
python -m ruff check tools/speckit_task_audit.py tests/unit/tools/test_speckit_task_audit.py
All checks passed.

python -m black --check tools/speckit_task_audit.py tests/unit/tools/test_speckit_task_audit.py
2 files would be left unchanged.

python -m pytest tests/unit/tools/test_speckit_task_audit.py -q
8 passed in 1.98s.
```

The requested local gate results were:

```text
python -m ruff check .
All checks passed.

python -m black --check .
1492 files would be left unchanged.

python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml
Success: no issues found in 463 source files.

python -m pytest tests/unit/tools/test_speckit_task_audit.py -q
8 passed in 1.99s.

python -m pytest tests/ -x -q
Collected 16641 tests. The run reached the upgrade portal contract suite with no failure. The local run was stopped after extended runtime.
```
