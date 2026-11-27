# Implementation Plan: Windows Path and Symlink Guardrails

**Branch**: `fix/4878-windows-path-symlink-guardrails` | **Date**: 2026-11-26 | **Spec**: `spec.md`

**Input**: Issue #4878. The record route `specs\numbered\0\0\1\2\4\0\0\3` holds the base-5 digits of 4878 (R-22, R-23, R-31).

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, and checklists under `design\`. This record omits `design\contracts\`, because no interface contract applies (D-11).

## Summary

Three guard tests fail on Windows. One builds a symlink without the required privilege. Two compare separator styles. The change edits three test modules and adds one changelog fragment. No product code changes (D-1).

## Technical Context

- **Language/Version**: Python 3.15.2 (`.venv\pyvenv.cfg`). The constitution requires Python 3.15 or newer (R-33).
- **Primary Dependencies**: pytest 9.2.0 (`.venv\Lib\site-packages\pytest-9.2.0.dist-info`). This change adds no dependency.
- **Storage**: Not applicable. Tests write only into pytest temporary folders.
- **Testing**: pytest, Ruff (R-46, R-66, R-67), Black (R-47), symbol-diff (R-51), and the test-quality analyzer (R-49).
- **Target Platform**: Windows 11 on the reporter host, and Linux on CI.
- **Project Type**: Python command-line tool with a guardrail test suite.
- **Performance Goals**: Not applicable.
- **Constraints**: No product change. No network call. No new module-level name in a changed test module (D-6).
- **Scale/Scope**: Three test modules, one changelog fragment, and one record.

## Constitution Check

| Rule | Result | Reason |
| - | - | - |
| I. Five-Item Rule (R-24) | Pass | The change adds no module-level name, file, or directory. The new method joins `SpecCommandFixture`, which then holds four members (R-07, R-08). Test modules already exceed five top-level names (R-10), so D-7 adds no test function. |
| II. Class-Based Architecture (R-25) | Pass | The symlink logic is a method of an existing class. It is not a wrapper, and no standalone function is added. |
| III. Safety-First (R-26) | Pass | The change adds no keyboard read, no destructive operation, and no external input. Each path value comes from pytest or Git. |
| IV. Full Deployment Pipeline (R-27) | Pass | The tasks run the local gates, commit, push, wait for CI, and merge only after authorization (tasks T-LOCAL-GATES to T-MERGE). Steps 10 to 12 do not start, because the container build runs on pushes that change product files, or on manual dispatch (R-43). |
| V. Observability and Logging (R-28) | Pass | Each new log line uses `%s` formatting and ASCII text. The logs carry no secret. |
| VI. Inline Comments (R-29) | Pass | Each changed line carries an inline comment, and each touched block gets comments on its adjacent lines (FR-009). |
| VII. Action Logging (R-30) | Pass | The symlink action logs before and after. The Git read logs before and after. The inspector logs before and after its directory check. |
| File Paths (R-35) | Pass | The code builds paths with `Path`, and the change compares path values with `Path` equality. |
| Container Runtime (R-36) | Not applicable | The change starts no container. The gates run on the host `.venv`. |
| Local development on Windows 11 (R-37) | Pass | The reproduction and the verification run on the reporter Windows host. |
| Security Findings (R-38) | Pass | The change adds no suppression comment, such as `# noqa`, `# type: ignore`, or `# nosec`. |
| Release notes (R-32) | Pass | The change adds one fragment, `changelog.d/issue-4878-windows-path-symlink-guardrails.md`, and D-8 explains the stricter rule. |
| Complexity Escalation (R-39) | Pass | The change touches three files, so this spec record exists before the code change. |
| Multi-Agent Git Workflow (R-40) | Pass | The branch uses the issue number, the commit names only explicit paths, and no push targets `main`. |

## Architecture

Three paths carry the change. Each path starts at a guard test and ends at a value check.

- Symlink path: the symlink case calls `SpecCommandFixture.symlink`, which creates the link or skips (R-03, R-05). The case then runs `check-prerequisites.ps1` through `SpecCommandFixture.run`, which starts `pwsh` (R-09, R-75). The script is unchanged.
- Git root path: `FixtureRepository.git` returns Git's stripped output (R-13). Git prints forward slashes on Windows (L-4). The guard compares that value with the resolved root as path values (D-4).
- Missing-root path: `AnalyticsStructureInspector._package_directories` builds the message (R-18, R-19). The test matches the message with an escaped pattern (R-20). Both sides use the forward-slash form (D-5).

## Project Structure

### Documentation (this feature)

```text
specs\numbered\0\0\1\2\4\0\0\3\4878-windows-path-symlink-guardrails\
  spec.md
  plan.md
  tasks.md
  analysis.md
  design\
    research.md
    data-model.md
    quickstart.md
    checklists\
      requirements.md
      test-quality.md
```

The route folder `specs\numbered\0\0\1\2\4\0\0\3` does not exist on `main` (R-70). The record adds the route. Its parent folders hold three children at most (`specs\numbered\0\0\1\2\4` holds `0`, `1`, and `2`).

### Source Code (repository root)

| Path | Action | Change |
| - | - | - |
| `tests\guardrails\test_spec_route_contract.py` | Modify | Add method `SpecCommandFixture.symlink` after line 184. Replace lines 294 to 296 with one call to the method. Add logging before and after `fixture.run`. |
| `tests\guardrails\local_test_quality_loop\test_scope.py` | Modify | Replace the assertion at lines 643 to 645 with a path-value comparison. Add logging before and after each Git call in `test_git_ignores_poisoned_locations`. |
| `tests\guardrails\test_analytics_package_structure.py` | Modify | Change line 74 to use `as_posix()`. Add logging around the directory check in lines 69 to 76. Change line 177 to escape `missing_root.as_posix()`. Add logging before the inspection in the test at line 171. |
| `changelog.d\issue-4878-windows-path-symlink-guardrails.md` | Add | One `###` heading and one `Fixed` bullet that names issue #4878 (D-8). |
| `specs\numbered\0\0\1\2\4\0\0\3\4878-windows-path-symlink-guardrails\` | Add | The record folder copied from the draft (task T006). |

No file under `src\` changes (FR-008).

## Target Shape of the Changes

### Symlink fixture (`tests\guardrails\test_spec_route_contract.py`)

The method sits in `SpecCommandFixture`, after `feature` (R-08). The test function keeps its parameter list.

```python
    def symlink(self, link: Path, target: Path) -> Path:
        """Create a directory symlink, or skip the case when the host lacks the privilege."""
        import logging  # Import here, so the module gains no top-level name that symbol-diff reports
        logging.info("Creating a directory symlink at %s", link)  # Announce the filesystem action before it runs
        try:
            link.symlink_to(target, target_is_directory=True)  # Create the link that the guard must reject
        except OSError as error:  # Creation failed on this host
            if getattr(error, "winerror", None) != 1314:  # Only WinError 1314 means the host lacks the privilege
                raise  # Every other failure stays visible to the operator
            logging.error("Cannot create the symlink at %s: %s", link, error)  # Record the cause before skipping
            pytest.skip(f"Host cannot create symlinks: {error}")  # Name the OS error in the skip reason
        logging.debug("Created the symlink at %s", link)  # Confirm the link exists after creation
        return link  # Return the link path for the selection
```

The test function then calls the method in place of lines 294 to 296:

```python
    if case == "symlink":  # Build the link case, or skip it on a host without the privilege
        selected = fixture.symlink(tmp_path / "specs" / "linked", parent)  # Link the parent directory
```

- Add `logging.info` before the `fixture.run` call and `logging.debug` after it, with inline comments.

### Git root comparison (`tests\guardrails\local_test_quality_loop\test_scope.py`)

`logging` is already imported (R-16). `Path` is already imported.

```python
        logging.info("Reading the Git top-level path of the fixture repository")  # Announce the external Git read
        top_level = repository.git("rev-parse", "--show-toplevel")  # Ask Git for the repository root
        logging.debug("Git reported the top-level path %s", top_level)  # Record the reported path
        assert Path(top_level) == repository.root.resolve()  # Compare path values, so the separator style does not matter
```

### Missing-root message (`tests\guardrails\test_analytics_package_structure.py`)

`LOGGER` is already defined at module level (R-21). The method change adds no module-level name.

```python
    def _package_directories(self) -> list[Path]:
        """Return each required readable package directory."""
        directories = [self.analytics_root / relative_path for relative_path in self.required_packages]
        LOGGER.info("Checking %s required analytics directories", len(directories))  # Announce the directory check
        missing = [directory for directory in directories if not directory.is_dir()]  # Validate all inputs first.
        LOGGER.debug("Found %s missing analytics directories", len(missing))  # Record the measured absent count
        if missing:  # A partial result cannot prove the package hierarchy.
            missing_paths = [path.as_posix() for path in missing]  # Use one separator style on every operating system
            raise AssertionError(f"Cannot inspect required analytics directories: {missing_paths}")
        return directories  # Return only the explicitly approved package levels.
```

The test at line 171 changes its expected pattern at line 177:

```python
            match=rf"Cannot inspect.*{re.escape(missing_root.as_posix())}",
```

### Changelog fragment

```markdown
### Windows guardrail tests

- **Fixed**: The symlink guard skips with a named reason when Windows denies the symlink privilege. The path guards compare paths, not separator style. Issue #4878.
```

## Dependencies

No new package and no dependency file change. The existing tests still need `pwsh` (R-12) and Git on `PATH`.

## Risks and Mitigations

| Risk | Mitigation |
| - | - |
| The skip hides the symlink proof on a host without the privilege. A skip can count as a pass in summaries (R-76). | The skip reason names the cause and prints under `-rs`. The outside and nested cases still run. Linux CI runs the proof (SC-003). |
| Another Windows error on the symlink call hides a real fault. | Only error 1314 skips. Every other error re-raises (D-2). |
| Linux CI never runs the skip branch. | The Windows run covers the branch (SC-001). U-1 records the follow-up. |
| Git returns a short 8.3 path. | The comparison resolves the expected root, as the earlier assertion did. The Windows run checks the value (UV-4). |
| The changed message breaks another reader. | A local search of the committed tree found no reader outside the test (S-14). |
| The test-quality ratchet reports a new finding. | The change adds no module-scope public function (R-10). The analyzer runs after the commit (T-PR). |
| `symbol-diff` reports an added module-level name. | The logging import sits inside the method (D-6). The comparator reads only top-level statements (S-7). |
| Ruff or Black reformats an added line. | Every line stays within 120 characters (R-66). The Format gate runs (T-LOCAL-GATES). |
| The changelog fragment names a removed analytics path. | The active-path scanner reads each tracked `.md` file outside `specs` (R-72). The fragment text names no module path, and that test must pass. |
| Unrelated modified files enter the commit. | Each file is staged by its explicit path. The status check runs before staging (Caution in tasks.md). |

## Rollback Steps

1. If the pull request is open, close it and delete the branch `fix/4878-windows-path-symlink-guardrails`.
2. If the pull request merged, reopen issue #4878 first. Then create a revert branch from `main` and revert the squash commit.
3. The revert removes the three test edits, the fragment, and the record folder in one commit.
4. No data, schema, or container change needs a rollback.

Caution: a revert restores the three Windows failures. Keep issue #4878 open until the revert merges.

## Contracts

Omitted. No menu, CLI, output column, or API shape changes (D-11).
