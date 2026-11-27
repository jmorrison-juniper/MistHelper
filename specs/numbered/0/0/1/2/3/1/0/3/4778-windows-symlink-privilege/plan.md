# Implementation Plan: Windows Symlink Privilege in the Spec-Route Contract Guard

**Branch**: `fix/4778-windows-symlink-privilege` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric record `specs/numbered/0/0/1/2/3/1/0/3/4778-windows-symlink-privilege/spec.md`.

`spec.md`, `plan.md`, `tasks.md`, and `analysis.md` stay at the record root. Research, data model, quickstart, contracts, and checklists stay under `design/`.

## Summary

The spec-route contract guard fails on a Windows host without the symlink privilege. The failing call is `selected.symlink_to(parent, target_is_directory=True)` at line 296 of `tests/guardrails/test_spec_route_contract.py`. That call runs before the guard runs the route script. The production check already rejects reparse points. This change alters the test fixture only. The fixture creates a symlink when the host allows it. Otherwise, it creates a junction. It skips the case with a printed cause only when the junction also fails.

## Technical Context

**Language/Version**: Python 3.15 (`pyproject.toml` requires `>=3.15`, as the section Language and environment of `.github/copilot-instructions.md` states).

**Primary Dependencies**: pytest and PowerShell 7 (`pwsh`). The guard runs `check-prerequisites.ps1` through `pwsh` (test lines 170-182). No package changes. The pinned `mistapi` 0.64.1 is installed locally (research F-12), and this change calls no mistapi function.

**Storage**: Not applicable. The guard writes only to `tmp_path`.

**Testing**: pytest, with the gates in `.github/copilot-instructions.md` (section Local gates, lines 50-74).

**Target Platform**: Windows 11 (local checkout and the affected host) and `ubuntu-latest` (CI).

**Project Type**: Test fixture and documentation change in an existing repository.

**Performance Goals**: Not applicable. The change adds three short tests and one fixture method.

**Constraints**: No production code change. No privilege or host policy change. Log output is ASCII only (constitution Principle V, line 182). Each new executable line has an inline comment (Principle VI, line 204). Each link attempt writes info and debug log lines (Principle VII, line 235).

**Scale/Scope**: One test module of 525 lines, one fixture method, one test class with three methods, and one documentation file.

## Constitution Check

*Gate: passes before research. Re-checked after design: passes.*

| Principle or rule | Gate | Evidence in this plan |
|-------------------|------|-----------------------|
| I. Five-item rule (constitution line 38) | No new directory. Each class holds five members or fewer. | No new folder. `SpecCommandFixture` gains one class attribute and one method. Its members become `__init__`, `run`, `feature`, `link_selection`, and `PRIVILEGE_NOT_HELD`. That is five. |
| I. Touched existing violation | Record each touched violation and a remediation action. | `tests/guardrails/test_spec_route_contract.py` already has more than five top-level names. This change adds one class name. Remediation R-1 splits the module by topic in a separate issue. |
| II. Class-based, no wrappers (constitution line 91) | Behavior lives in named classes. | The link logic is a method of `SpecCommandFixture`. The tests are methods of `TestLinkSelectionFallback`. No standalone wrapper function is added. |
| III. Safety first (constitution line 113) | Validate input and keep secrets out of output. | The fixture uses paths from `tmp_path` only. The `mklink` arguments are paths that the test creates. No secret and no external input reach the code. |
| IV. Full deployment pipeline (constitution line 143) | Local gates, explicit paths, CI, and merge. | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE. Files are added by explicit path. |
| V. Observability (constitution line 182) | ASCII logs and no secret. | Log messages are ASCII. They print link and target paths only. |
| VI. Inline comments (constitution line 204) | Every executable line carries a same-line comment. | Tasks T003 and T004 require the comment on each new executable line. |
| VII. Action logging (constitution line 235) | Info before, debug after, and error on exception. | `link_selection` writes an info line before each `symlink_to` and `mklink` call. It writes a debug line after each success. It writes an error line before it raises. |
| Mist transport (constitution line 274) | Every REST call uses mistapi. | Not applicable. The change calls no Mist REST endpoint. |
| Output backends and database keys | Export and key rules. | Not applicable. The change writes no collected data and adds no operation. |
| Data directory | Product output stays under `data/`. | Not applicable. Test output stays in `tmp_path`. |
| Containers | Test containers join the compose group. | Not applicable. The change starts no container. |
| File paths (constitution line 274 section) | Use `pathlib` or `os.path`. | The fixture uses `Path` objects. Command arguments use `str(path)`. |
| Documentation (AGENTS.md lines 336-339) | The same change updates documentation. | Task T006 updates `documentation/development-setup.md`. |
| Release notes (`changelog.d/README.md` line 58) | An internal-only change adds no fragment. | No fragment. The pull request states the reason (FR-010). |
| Security findings (constitution, Development Workflow section) | Fix over suppress. | No finding is suppressed. The skip path does not hide a finding. |

For repository structure and generated files:

- The commit subject and the pull request title use `fix(tests): use a junction when the symlink privilege is missing`.
- The record adds only its own folder under `specs/numbered/0/0/1/2/3/1/0/3/`.
- The record root holds five children. `design/` holds five children. `design/contracts/` holds two files. `design/checklists/` holds two files.
- Product output stays under `data/`. Test output stays in `tmp_path`.

For a feature that uses Juniper Mist Cloud:

- Not applicable. The change touches no Mist REST call, no mistapi method, and no WebSocket transport.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/3/1/0/3/4778-windows-symlink-privilege/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      link-fallback.md
      selection-rejection.md
    checklists/
      requirements.md
      security.md
```

### Source Code (repository root)

```text
tests/guardrails/test_spec_route_contract.py    modify
documentation/development-setup.md              modify
```

Read only in this change: `.specify/scripts/powershell/common.ps1`, `.specify/scripts/powershell/spec-route.ps1`, `.specify/scripts/powershell/check-prerequisites.ps1`, `tests/guardrails/process_folder_baseline.json`, and `changelog.d/README.md`.

**Structure Decision**: Edit the existing guard module and the existing setup document. Add no module, no directory, and no production file.

## File-by-File Change Map

| Path | Action | Change |
|------|--------|--------|
| `tests/guardrails/test_spec_route_contract.py` | modify | Add `import logging` after line 5. Add the class attribute `PRIVILEGE_NOT_HELD = 1314` after the class docstring (line 160). Add the method `link_selection` after the `feature` method (after line 193). Replace line 296 with `fixture.link_selection(selected, parent)`. Add the class `TestLinkSelectionFallback` with three methods after line 301. |
| `documentation/development-setup.md` | modify | Add a PowerShell 7 row after the Container runtime row (after line 15). Add a note about the link fallback under Step 4 (lines 168-174). |
| `specs/numbered/0/0/1/2/3/1/0/3/4778-windows-symlink-privilege/` | add | This record. Eleven files. |

## Gate Map

| Gate (`.github/copilot-instructions.md`, Local gates, lines 50-74) | Applies | Command | Reason |
|-----------------------------------------------------------------|---------|---------|--------|
| Compile | No | `python -m py_compile MistHelper.py` | `MistHelper.py` is unchanged. |
| Lint | Yes | `python -m ruff check .` | The test module changes. |
| Format | Yes | `python -m black --check .` | The test module changes. |
| Types | No | `python -m mypy $MYPY_PATHS --config-file pyproject.toml` | `MYPY_PATHS` in `ci.yml` line 93 excludes `tests/`. |
| Tests | Yes | `python -m pytest tests/guardrails/test_spec_route_contract.py` | The changed module runs here. |
| Full tests | Yes | The second `pytest-chunks` command in the Local gates section | The shard includes `tests\guardrails` (`ci.yml` line 255). |
| Safe sweep | No | `python MistHelper.py --test` | No menu changes. |
| Coverage | No | `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=` | No `src/` change. |
| Test quality | Yes | The ratchet procedure (section Test quality ratchet) | A test module changes. Run it after the local commit and before the push. |
| Complexity | No | `radon cc <package> -j \| complexity-gate --max 10` | `RADON_PATHS` in `ci.yml` line 99 excludes the guard module. |
| Security lint | No | `bandit -c pyproject.toml -r <package> -q` | No package file changes. |
| Dependency audit | No | `pip-audit -r requirements.txt` | No manifest changes. |
| Code quality | No | `pylint src/ --fail-under=9.5` | No `src/` change. |
| Dead code | No | `vulture $VULTURE_PATHS --min-confidence 70` | `VULTURE_PATHS` in `ci.yml` excludes tests. |
| Docstrings | No | `pydocstyle $PYDOCSTYLE_PATHS` and `interrogate $INTERROGATE_PATHS --fail-under 90` | Both path variables in `ci.yml` exclude `tests/`. |
| Menu reference | No | `python scripts/generate_menu_wiki.py` and `python -m scripts.menu_api_map` | No menu change. |
| Symbols | Yes | `symbol-diff --base origin/main tests/guardrails/test_spec_route_contract.py` | The module keeps every module-level name. |
| STE | Yes | `ste-linter --config .ste-linter.toml --min-score 80 documentation/development-setup.md` | A Markdown file changes. |
| Ops portal and ops platform | No | The npm and pytest commands in the Local gates table | No `ops-portal/` or `mist-ops-platform/` change. |
| Changelog policy guard | Yes | `python -m pytest tests/guardrails/test_changelog_fragment_policy.py` | `ci.yml` line 298 runs this guard in CI. |

## Risks and Mitigations

| ID | Risk | Mitigation |
|----|------|------------|
| R-1 | `mklink /J` also needs the symlink privilege on the host. The FSCTL page does not limit its privilege rule to symlinks. | The skip path prints the cause. Task T-LOCAL-GATES records the link kind on the host. |
| R-2 | A skip hides the Windows check on that host. | The Caution in `spec.md` records the loss. The Ubuntu shard runs the real symlink case. |
| R-3 | A recursive delete follows a junction and removes files at its target. | The junction target stays inside `tmp_path`. The Warning in `spec.md` records the rule. |
| R-4 | A monkeypatch of `symlink_to` leaks into other tests. | Use the `monkeypatch` fixture. It restores each attribute after its test. |
| R-5 | `snapshot_tree` reads junction contents in a different way on Python 3.15.2. | TEST-01 compares the before and after snapshots. The traversal behavior stays unverified (research U-3). |
| R-6 | Log lines add noise to the pytest output. | Logs appear only with `--log-cli-level` or on a failure. |
| R-7 | The affected host lacks PowerShell 7 on PATH. | The existing `pytest.fail` message stays. FR-009 adds the requirement to the setup document. |

## Rollback Steps

1. Before the merge, close the pull request and delete the branch. No change reaches `main`.
2. After the merge, open a new issue. Branch from `main`. Revert `tests/guardrails/test_spec_route_contract.py` and `documentation/development-setup.md`.

Warning: a commit pushed after a squash merge becomes an orphan. Open a new branch from `main` for every follow-up change.

## Complexity Tracking

| Violation | Why needed | Simpler alternative rejected because |
|-----------|------------|--------------------------------------|
| Existing: the top-level names of `tests/guardrails/test_spec_route_contract.py` exceed five (grandfathered). This change adds one class name. | The module already holds the fixture and the route tests. | A new module adds a child to `tests/guardrails`, a busy directory, and splits the shared fixture. |

Remediation R-1: open a separate issue that splits the module by topic. This record does not perform that split.

## Implementation Outline

1. Add the three test methods first and see them fail (T003).
2. Add the class attribute and the fixture method (T004).
3. Replace the call site at line 296 (T005).
4. Update the setup document (T006).
5. Confirm the changelog reason (T007).
6. Run the red proof on the task branch and revert it (T008).
7. Run the applicable gates and record the link kind (T-LOCAL-GATES).
8. Open the pull request, watch CI, and merge after authorization (T-PR, T-REMOTE-CI, T-MERGE).
