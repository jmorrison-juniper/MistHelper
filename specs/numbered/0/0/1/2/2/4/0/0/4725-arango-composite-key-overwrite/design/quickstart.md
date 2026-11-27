# Quickstart: ArangoDB Identity Keys for Declared Multi-Field Primary Keys

This quickstart gives the reproduction steps for issue #4725 and the verification commands for the change. Run every command from the repository root in Windows PowerShell after you activate the environment.

Use one command per line. Do not chain commands in one line.

## Prerequisites

1. Create the environment with the bootstrap in `documentation/development-setup.md` (RC-35). Activate it with `.venv\Scripts\Activate.ps1`.
2. Confirm that the branch is `fix/4725-arango-composite-key-overwrite`, created from `main` (RC-114).
3. Complete T001 first. No edit to `src/foundation/persistence/db/writers/arango_writer.py` starts before T001 records the handoffs (RC-123).

No command in this quickstart starts a container or connects to a live ArangoDB or Mist service. Live checks are outside this change.

Caution: A live run writes to the ArangoDB collections. Use a test database only.

## Section 1: Reproduce the Defect (Before the Change)

The reproduction uses the in-memory fake collection. It needs no network and no database.

1. Run the new test for distinct neighbors:

```powershell
python -m pytest tests/unit/config/standalone/foundation/persistence/arango_writer/test_arango_composite_keys.py -k distinct_neighbor
```

2. Expect the test to fail on unchanged code. The fake collection then holds one document for two records. The writer still reports two created documents.
3. Run the control test for distinct routers:

```powershell
python -m pytest tests/unit/config/standalone/foundation/persistence/arango_writer/test_arango_composite_keys.py -k distinct_router
```

4. Expect the control to pass on unchanged code. The control proves that the fake collection keeps distinct keys.

## Section 2: Scenarios

Each scenario states its test, its expected result, and its source.

| Scenario | Test or check | Expected result | Source |
| - | - | - | - |
| S1 Distinct neighbor | Test 1 | Fails before T004. Passes after T004. The collection holds two documents. | FR-001, SC-001 |
| S2 Distinct timestamp | Test 2 | Fails before T004. Passes after T004. | FR-002 |
| S3 Distinct router control | Test 3 | Passes before and after T004. | FR-002 |
| S4 Identical record | Test 4 | Passes before and after T004. One document, one update. | FR-003, SC-002 |
| S5 Key format | Test 5 | Passes after T003. The key is ASCII and at most 254 bytes. | FR-005 |
| S6 Number normalization | Test 6 | Passes after T003. Integer and float timestamps share one key. | FR-004 |
| S7 Type distinction | Test 7 | Passes after T003. Text `"1"` and number `1` keep distinct keys. | FR-004 |
| S8 Missing or empty key | Test 8 | Passes after T005. The record uses a UUID key and the warning counts it. | FR-006 |
| S9 Non-scalar or non-finite key | Test 9 | Passes after T003. The record uses a UUID key. | FR-006 |
| S10 Single-field keys | Test 10 | Passes before and after T004. The key equals the legacy value. | FR-007, SC-003 |
| S11 SLE keys | Test 11 | Passes before and after T004. The key equals the SLE identity function value. | FR-008, SC-003 |
| S12 Exempt collection | Test 12 | Passes after T004. The legacy key is kept. | FR-009 |
| S13 No deletion or rewrite | Test 13 | Passes after T004. The handle receives only `import_bulk`. | FR-010, FR-012, SC-004 |
| S14 Replace semantics | Test 14 | Passes before and after T004. The kwargs equal `{"on_duplicate": "replace"}`. | FR-011 |
| S15 Audit covers every entry | Test 15 | Passes after T002. The guard prints 121 examined entries and zero unclassified entries. | FR-013, FR-015, SC-005 |
| S16 Audit fails on empty input | Test 16 | Passes after T002. The guard fails when the input is empty. | FR-015 |
| S17 Batch logs | Test 17 | Passes after T005. The log text is ASCII and reports counts. | FR-014 |
| S18 SLE regression | `tests/unit/db/sle_window_summary/test_export_identity.py` and `tests/unit/db/sle_window_summary/test_backend_preservation.py` | Pass with no edit. | FR-008 |
| S19 Preservation expectation | `tests/unit/config/foundation/persistence/storage/arango_indexes/test_preservation.py` | Passes after T010. | FR-011, D-10 |
| S20 Changelog guard | `tests/guardrails/test_changelog_fragment_policy.py` | Passes after T014. | FR-016 |

## Section 3: Verification Commands

These commands come from the local gates table in `.github/copilot-instructions.md` (RC-04). The CI path values come from `.github/workflows/ci.yml` (RC-23 to RC-26).

### Syntax and lint

```powershell
python -m py_compile MistHelper.py
python -m ruff check .
python -m black --check .
```

Expected results: no output for the compile check, `All checks passed` for ruff, and `No file needs a change` for black.

### Types

```powershell
python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml
```

Expected result: `Success`. The path list equals the `MYPY_PATHS` value in `ci.yml` (RC-23).

### Changed tests

```powershell
python -m pytest tests/unit/config/standalone/foundation/persistence/arango_writer/test_arango_composite_keys.py
python -m pytest tests/unit/config/standalone/foundation/persistence/arango_writer/test_arango_writer.py
python -m pytest tests/unit/config/foundation/persistence/storage/arango_indexes/test_preservation.py
python -m pytest tests/unit/db/sle_window_summary/test_export_identity.py
python -m pytest tests/unit/db/sle_window_summary/test_backend_preservation.py
python -m pytest tests/unit/export/test_site_search_exporter.py
python -m pytest tests/guardrails/test_endpoint_catalog.py
python -m pytest tests/guardrails/test_changelog_fragment_policy.py
```

Expected result: all tests pass.

### Full tests (two shards, Windows)

```powershell
pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal
pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\contract tests\guardrails tests\integration --split tests\contract\upgrade_portal --split tests\integration\upgrade_portal
```

Expected result: one summary line for each shard, with no failed chunk.

### Safe sweep

```powershell
python MistHelper.py --test
```

Expected result: each `safe` operation completes. Without `MIST_APITOKEN` or `MIST_API_TOKEN`, the Mist API checks skip with a credential reason (RC-04). Menu 217 belongs to `interactive_safe`, so the sweep does not run it (RC-91).

### Coverage

```powershell
python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=
```

Expected result: the combined coverage is 80 percent or above.

### Test quality

```powershell
python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/main" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
```

Expected result: `gate: 0 new findings vs baseline`.

### Complexity, security, code quality, dead code, docstrings

```powershell
radon cc src/foundation/persistence/db/writers -j | complexity-gate --max 10
bandit -c pyproject.toml -r src/foundation/persistence/db/writers -q
pylint src/ --fail-under=9.5
vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70
pydocstyle src/ wsgi.py web_portal
interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90
```

Expected results: no complexity block above 10, and no bandit finding. Pylint scores 9.5 or above. Vulture and pydocstyle report no finding. Interrogate reports 90 percent or above. The path lists equal the `PYDOCSTYLE_PATHS`, `VULTURE_PATHS`, and `INTERROGATE_PATHS` values in `ci.yml` (RC-24 to RC-26).

### Symbols

```powershell
symbol-diff --base origin/main src/foundation/persistence/db/writers/arango_writer.py
```

Expected result: `no module-level name changed` with exit code 0. The new module `composite_key_identity.py` has no base revision, so the gate does not apply to it.

### Gates that do not apply

| Gate | Reason |
| - | - |
| Dependency audit (`pip-audit -r requirements.txt`) | No dependency changes (RC-31, RC-32). |
| Menu reference | No menu or menu documentation changes (RC-90). |
| STE (`ste-linter`) | No changed file is in the STE list (README.md, AGENTS.md, copilot-instructions.md, CLAUDE.md, or the ASD guide). |
| Ops portal and ops platform | No change under `ops-portal/` or `mist-ops-platform/`. |

## Section 4: Not Performed

- No live ArangoDB check. The fake collection covers the write contract. A live check needs the compose service and a test database, under `documentation/container-deployment.md` Rules 1 and 2 (RC-34).
- No live Mist check. The SDK call stays unchanged (RC-89).
- No migration. D-7 requires approval first (T017).
