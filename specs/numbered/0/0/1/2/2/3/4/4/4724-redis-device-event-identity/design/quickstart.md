# Quickstart: Redis device event identity

This guide gives the exact reproduction steps and the exact verification commands for issue #4724. Run each command from the root of the implementation worktree. The tests use mocks, so no live service is required.

## Prerequisites

1. Create the Python 3.15 environment as the repository instructions describe (RC-31).
2. Use the branch `fix/4724-redis-device-event-identity` in a git worktree. Branch from `main` only (plan, Dependencies).

## Reproduction before the fix

1. Run the Redis regression test. It fails before the fix. The fake pipeline keeps one document for two events with equal timestamps.

   `python -m pytest tests/unit/config/standalone/foundation/persistence/redis/test_redis_json_writer.py -k equal_timestamp`

2. Run the router tests. The stamp tests fail before the fix, because no `record_id` exists yet.

   `python -m pytest tests/unit/config/standalone/foundation/persistence/database/test_router.py -k record_id`

Warning: Do not point any command at a production Redis or ArangoDB host. A write against production data cannot be undone.

## Expected result after the fix

- Step 1 prints one failed test before the fix and one passed test after the fix.
- Step 2 prints three passed tests after the fix.

## Local gates

Run each command that applies to the changed files. Run the test quality command after the local commit, because it reads committed tests (copilot-instructions, Test quality ratchet). Stop at the first failed command.

1. Compile: `python -m py_compile MistHelper.py`
2. Lint: `python -m ruff check .`
3. Format: `python -m black --check .`
4. Types: `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml`
5. Tests for each changed test file:
   `python -m pytest tests/unit/config/standalone/foundation/persistence/redis/test_redis_json_writer.py`
   `python -m pytest tests/unit/config/standalone/foundation/persistence/database/test_router.py`
   `python -m pytest tests/unit/config/standalone/foundation/persistence/arango_writer/test_arango_writer.py`
   `python -m pytest tests/unit/config/foundation/persistence/storage/arango_indexes/test_preservation.py`
   `python -m pytest tests/unit/config/foundation/persistence/storage/arango_indexes/test_declared_indexes.py`
   `python -m pytest tests/contract/test_arango_declared_indexes.py`
   `python -m pytest tests/guardrails/test_persistence_package_structure.py`
6. Full tests, Windows shards from the repository instructions:
   `pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal`
   `pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\contract tests\guardrails tests\integration --split tests\contract\upgrade_portal --split tests\integration\upgrade_portal`
7. Safe sweep: `python MistHelper.py --test`
8. Coverage: `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=`
9. Test quality, after the local commit: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/main" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt`
10. Complexity: `radon cc src/foundation/persistence/db -j | complexity-gate --max 10`
11. Security lint: `bandit -c pyproject.toml -r src/foundation/persistence -q`
12. Code quality: `pylint src/ --fail-under=9.5`
13. Dead code: `vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70`
14. Docstrings: `pydocstyle src/ wsgi.py web_portal` and `interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90`
15. Menu reference: `python scripts/generate_menu_wiki.py` and `python -m scripts.menu_api_map`. No changed file may appear after the run.
16. Symbols, for each changed source file:
   `symbol-diff --base origin/main src/foundation/persistence/db/router.py`
   `symbol-diff --base origin/main src/foundation/persistence/db/writers/redis_writer.py`
   `symbol-diff --base origin/main src/foundation/persistence/db/writers/arango_writer.py`
   `symbol-diff --base origin/main src/foundation/support/refactors/endpoint_primary_key_strategies.py`
17. STE, for the changed Markdown files:
   `.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 .github/copilot-instructions.md`
   `.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 documentation/diagrams/core/database-strategy.md`

Not applicable: Dependency audit, because no dependency manifest changes. Ops portal and Ops platform, because no file under those folders changes.

## Scope check before the push

- Run `python -m pytest tests/guardrails/test_persistence_package_structure.py`. It must pass without a change to the test.
- Confirm that the diff holds no call to a Redis delete, a purge, or an ArangoDB remove operation.
- Confirm that the open pull request list still shows no overlap with the changed files (decision D-12).
