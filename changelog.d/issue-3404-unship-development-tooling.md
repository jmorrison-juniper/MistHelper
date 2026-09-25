### Changed

- The in-house development tooling now lives in the separate repository
  `jmorrison-juniper/misthelper-devtools`. MistHelper keeps a local copy for
  now, and phase 2 deletes that copy. See issue #3404.
- The Zscaler city metadata moved from `scripts/build_zen_city_metadata.py`
  into `src/utils/zen_city_metadata.py`. The synthetic probe scheduler reads
  that map at run time, so it is product code. The maintenance command stays
  in `scripts/` and it imports the new module. See issue #3404.

### Removed

- The Python wheel no longer ships the `tools/` package. A customer never runs
  the repository linters, the analyzers, or the compliance checkers. See issue
  #3404.
- The Python wheel no longer exposes the `test-quality-analyzer` and the
  `ste-linter` console scripts. Both commands serve MistHelper development
  only. Install `misthelper-devtools` to get them. See issue #3404.
- The container image no longer ships the `scripts/` directory. The image kept
  about 55 development scripts that no container path runs. See issue #3404.

### Added

- `tests/guardrails/test_shipped_artifacts.py` keeps the development tooling
  out of the wheel and out of the container image. The guard reads the wheel
  package list, the console script list, every Dockerfile `COPY` source, and
  the container exclude list. Each check reports the count it measured. See
  issue #3404.
