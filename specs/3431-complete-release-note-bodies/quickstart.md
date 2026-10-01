# Validate Complete Release Note Bodies

Use this isolated worktree and its Python 3.13+ environment.
Keep the repository's existing test guard, configurations, baseline, and thresholds unchanged.
The helper uses only the standard library.
The tests use existing pytest, pytest-cov, and PyYAML.

## Targeted Tests

```bash
rtk proxy .venv/bin/python -m pytest tests/unit/test_release_body.py tests/contract/test_release_body_workflow.py tests/guardrails/test_ci_gate_triggers.py --cov=scripts.release_body --cov-branch --cov-report=term-missing --cov-fail-under=90 -q
```

Measure the complete emitted body at 124998, 124999, 125000, and 125001 units.
Check the final complete comparison, pinned CHANGELOG line, and terminal LF.
Check the 216840-character source and astral Unicode.
Require failure for invalid, empty, or unreadable input and file failures.
Use actual workflow mutations to prove body ownership and fatal preparation.

## File and Repository Gates

```bash
rtk proxy .venv/bin/python -m py_compile MistHelper.py scripts/release_body.py tests/unit/test_release_body.py tests/contract/test_release_body_workflow.py
rtk proxy .venv/bin/python -m ruff check .
rtk proxy .venv/bin/python -m ruff check scripts/release_body.py tests/unit/test_release_body.py tests/contract/test_release_body_workflow.py
rtk proxy .venv/bin/python -m black --check .
rtk proxy .venv/bin/python -m mypy --config-file pyproject.toml scripts/release_body.py tests/unit/test_release_body.py tests/contract/test_release_body_workflow.py
rtk proxy .venv/bin/python -m bandit scripts/release_body.py
rtk proxy .venv/bin/python -m bandit -c pyproject.toml -r .
rtk proxy .venv/bin/pip-audit -r requirements.txt
rtk proxy .venv/bin/test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json
rtk proxy .venv/bin/markdown-link-check --root . documentation/release-notes.md changelog.d/issue-3431-complete-release-note-bodies.md specs/3431-complete-release-note-bodies
rtk proxy .venv/bin/ste-linter --config .ste-linter.toml --min-score 80 scripts/release_body.py tests/unit/test_release_body.py tests/contract/test_release_body_workflow.py documentation/release-notes.md changelog.d/issue-3431-complete-release-note-bodies.md
```

Also run the exact `MYPY_PATHS` value from `.github/workflows/ci.yml`.
Explicit file checks include the helper despite broad exclusions of `scripts/`.
The security scan must report its checked scope.
Do not modify a baseline, exclusion, threshold, or suppression to obtain success.
Record each exact command and its result.

### Mac Dependency Audit

The uv-managed Mac interpreter can abort inside the audit tool's copied temporary environment.
If that occurs, resolve the complete runtime closure without changing tracked requirements.

```bash
rtk proxy mkdir -p data/issue-3431
rtk proxy env UV_SYSTEM_CERTS=1 UV_LINK_MODE=copy uv pip compile requirements.txt --python .venv/bin/python --native-tls --generate-hashes --quiet --output-file data/issue-3431/runtime-audit-lock.txt
rtk proxy .venv/bin/python -m pip_audit --no-deps --disable-pip --require-hashes -r data/issue-3431/runtime-audit-lock.txt --strict --format json --output data/issue-3431/runtime-audit.json
```

The generated file contains the complete pinned runtime closure and package hashes.
Audit every package in that file and report the actual package count.
Do not treat an incomplete installed-environment audit as equivalent evidence.
Git-only development tooling stays outside this runtime audit.

## Local CLI Proof

Use an isolated controlled directory for input and output.
Supply the exact tag event through the existing runner environment variables.
Read the complete output as bytes.
Measure both code points and UTF-16 units.
Verify both links and the final LF.
A missing source must return two and report zero checked source files.
A readable invalid source must return two and report one checked source file.

Caution: do not publish a release, draft, tag, upload, or workflow dispatch to validate this repair.
The tests and local CLI proof do not publish anything.

## Delivery

Wait for the parent's verified base before the first push or pull request.
Repeat all applicable validation after a rebase.
Wait for every required check, the title check, CodeQL, and a strict current base.
Merge only the verified exact head with a protected squash.
Do not use an admin bypass or delete the branch.
Verify the exact merged main tree locally without using the main checkout.
