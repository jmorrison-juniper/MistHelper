# Local Verification: Bounded numeric inputs

## Prepare this worktree

If the interpreter is absent, run the existing bootstrap.

```bash
rtk proxy python3.13 scripts/bootstrap_worktree.py
```

If macOS cannot seed pip, restore only this worktree environment with uv.

```bash
rtk proxy env UV_LINK_MODE=copy UV_SYSTEM_CERTS=1 uv venv --allow-existing --seed --python python3.13 .venv
rtk proxy .venv/bin/python scripts/bootstrap_worktree.py
```

## Run the focused proof

```bash
rtk proxy .venv/bin/python -m pytest \
  tests/unit/upgrade_portal/test_bounded_numeric_inputs.py \
  tests/contract/upgrade_portal/test_bounded_numeric_routes.py \
  --no-cov -q
```

Run these cases before source edits to record the original failures.
After source edits, run the same cases with branch coverage.
Check exact first page offsets, refusal bodies, fallback values, and callback counts.

## Run the quality gates

Read the current commands from `.github/workflows/ci.yml`.
Use the unchanged `.github/test-quality-config.toml` and `.github/test-quality-baseline.json`.
Do not replace missing guard inputs with a successful result.
Record `dictionary_unavailable` if the authorized STE dictionary is absent.

## Hold publication

Commit only the reserved files.
Do not push or create a pull request before the parent grants the full verified main SHA.
After a grant, repeat the local proof on the authorized base before publication.
