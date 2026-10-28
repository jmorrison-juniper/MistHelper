# Validation

Use the worktree virtual environment created by `python3 scripts/bootstrap_worktree.py`.

Run the focused exporter, SQLite, Arango, and primary-key guard tests.
Use fake SDK responses and temporary stores. Do not call the Mist cloud.

Confirm these outcomes:

1. Both complete identities reach persistence.
2. Repeated windows update one keyed record.
3. Distinct windows and request identifiers remain separate.
4. Legacy rows and UUID documents remain unchanged.
5. Missing identities and empty registry scans fail.

Run Ruff, Black, mypy, Bandit, complexity, documentation, and symbol gates for changed files.
After the local commit, run the documented test-quality preflight and changed-from gate.
Create a ready-for-review PR with the existing-data assumption and exact command results.
Keep human review required. Do not enable auto-merge or merge.
