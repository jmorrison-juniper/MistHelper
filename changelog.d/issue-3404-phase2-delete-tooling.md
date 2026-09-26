### Removed

- The repository no longer holds a local copy of the in-house development
  tooling. The `tools/` package, the `src/juniper_skills/` package, the
  `scripts/juniper_skills/` scripts, and the `tests/unit/juniper_skills/`
  tests moved to `jmorrison-juniper/misthelper-devtools`. See issue #3404.

### Changed

- `requirements-dev.txt` installs the development tooling from the
  `misthelper-devtools` repository at an immutable commit. A contributor gets
  the analyzers, the Simplified Technical English linter, and the citation
  checker from that package. See issue #3404.
- The continuous integration workflows, the pre-commit configuration, and
  `scripts/run_repository_analyzers.py` call the installed `ste-linter` and
  `test-quality-analyzer` commands. They no longer run a local copy. See
  issue #3404.

### Added

- `.ste-linter.toml` holds the Simplified Technical English linter settings.
  The settings left `pyproject.toml`, because the linter now reads them from
  an installed package instead of the project file. See issue #3404.
