# Cache error validation

If the environment is absent, run `python3 scripts/bootstrap_worktree.py`.
Activate it with `source .venv/bin/activate`.

Run `python -m pytest tests/unit/cache/test_cache_utils.py -q`.
Every cache test must pass.

The mocked failure tests inspect the [failure record contract](data-model.md).
The interrupt tests must preserve both keyboard interrupts and process exits.
No live Mist operation is necessary.
