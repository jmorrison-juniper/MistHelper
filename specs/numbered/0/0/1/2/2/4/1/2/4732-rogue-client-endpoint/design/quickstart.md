# Quickstart: Rogue client exports use the client endpoint name

This file gives the reproduction steps and the verification commands for the implementer. The record does not run them. Run each command in a worktree that holds the `fix/4732-rogue-client-endpoint` branch.

## Prepare the worktree

1. Create the worktree from `origin/main`. Run `git worktree add ..\MistHelper-4732 -b fix/4732-rogue-client-endpoint origin/main`.
2. Enter the worktree. Run `cd ..\MistHelper-4732`.
3. Create the environment. Run `uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py`, then `.venv\Scripts\Activate.ps1`.

## Reproduce the defect before the fix

1. Add the test from T008 (`test_writes_client_endpoint_name`) and the tests from T010 (`PrimaryKeys`).
2. Run `python -m pytest tests/unit/export/test_org_client_security_exporter.py -q -k writes_client_endpoint_name`.
3. Expected before the fix: the test fails. The export writer call carries `listSiteRogueAPs`, not `listSiteRogueClients`.
4. Run `python -m pytest tests/unit/export/test_org_client_security_exporter.py -q -k PrimaryKeys`.
5. Expected before and after the fix: both tests pass. The strategy catalog already keys the client endpoint on `client_mac` and `bssid`.

## Verify the fix

Run these commands after T004 to T017. Each command must pass before `T-LOCAL-GATES`.

1. Run `python -m pytest tests/unit/export/test_org_client_security_exporter.py -q`. Expected: all tests pass.
2. Run `python -m pytest tests/unit/export/test_org_client_security_exporter.py -q -k cache_hit`. Expected: both cache-hit tests pass.
3. Run `python -m pytest tests/unit/export/test_org_client_security_exporter.py -q -k test_success`. Expected: the preserved list-type test passes.
4. Run `python -m pytest tests/guardrails/test_changelog_fragment_policy.py -q`. Expected: the changelog guard passes.

## Local gates for the changed files (T-LOCAL-GATES)

Each gate applies to the Phase 1 paths and to the Markdown files in the record. The commands follow `.github/copilot-instructions.md:57-75`.

| Gate | Command | Expected result |
| - | - | - |
| Compile | `python -m py_compile MistHelper.py` | No output |
| Compile, changed module | `python -m py_compile src/operations/exporting/export/org_client_security_exporter.py` | No output |
| Lint | `python -m ruff check .` | `All checks passed` |
| Format | `python -m black --check .` | No file needs a change |
| Types | `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` | `Success` |
| Tests, changed file | `python -m pytest tests/unit/export/test_org_client_security_exporter.py` | All tests pass |
| Full tests | The two `pytest-chunks` commands in `.github/copilot-instructions.md` | One summary line for each shard |
| Safe sweep | `python MistHelper.py --test` | Each safe operation completes. The Mist API checks skip without a token |
| Coverage | `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=` | The combined report holds 80 percent or above |
| Test quality | The ratchet commands in `.github/copilot-instructions.md`, section "Test quality ratchet" | `gate: 0 new findings vs baseline` |
| Complexity | `radon cc src/operations/exporting/export -j \| complexity-gate --max 10` | No block above complexity 10 |
| Security lint | `bandit -c pyproject.toml -r src/operations/exporting/export -q` | No finding |
| Dependency audit | Not applicable. `requirements.txt` does not change | Not applicable |
| Code quality | `pylint src/ --fail-under=9.5` | Score 9.5 or above |
| Dead code | `vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70` | No finding |
| Docstrings | `pydocstyle src/ wsgi.py web_portal` and `interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90` | No violation. Coverage 90 percent or above |
| Menu reference | `python scripts/generate_menu_wiki.py` and `python -m scripts.menu_api_map` | No changed file after the run |
| Symbols | `symbol-diff --base origin/main src/operations/exporting/export/org_client_security_exporter.py` and the same command for the test file | `no module-level name changed`, exit code 0 |
| STE | `ste-linter --config .ste-linter.toml --min-score 80` with each changed Markdown file | Each file scores 80 or above |
| Link check | `markdown-link-check` with each changed Markdown file | No broken link |
| Changelog guard | `python -m pytest tests/guardrails/test_changelog_fragment_policy.py -q` | Pass |
| Guardrails | `python -m pytest tests/guardrails -q` | Pass. The guard reads the process folder baseline |
| Ops portal and platform | Not applicable. No file in `ops-portal/` or `mist-ops-platform/` changes | Not applicable |

Record each result in the pull request body during `T-PR`. Do not claim a gate passed when it did not run.

## Phase 2 read-only checks (HOLD)

Run these checks only after decisions D-3 and D-4 are approved. They read the database and change no row.

Warning: Do not run a write statement against `data/mist_data.db` during these checks.

1. Read the stored table definition. Run this Python code from the repository root:

```python
import sqlite3  # Load the SQLite module
connection = sqlite3.connect("file:data/mist_data.db?mode=ro", uri=True)  # Open read-only so no change occurs
for row in connection.execute("SELECT sql FROM sqlite_master WHERE name = 'OrgRogueClients'"):  # Read the stored DDL
    print(row[0])  # Print the stored primary key definition
connection.close()  # Release the connection
```

2. Find candidate-key duplicates. Run this query against the same database:

```sql
SELECT client_mac, bssid, COUNT(*) AS row_count FROM OrgRogueClients GROUP BY client_mac, bssid HAVING COUNT(*) > 1
```

3. Find missing candidate keys. Run this query against the same database:

```sql
SELECT COUNT(*) AS missing_keys FROM OrgRogueClients WHERE client_mac IS NULL OR client_mac = '' OR bssid IS NULL OR bssid = ''
```

4. Create a backup copy of `data/mist_data.db` before any migration step. Store the copy outside the repository. Confirm the copy opens before any change.

Caution: A duplicate found by step 2 means that two rows share a candidate key. Each such pair needs a conflict policy before any change (D-3).
