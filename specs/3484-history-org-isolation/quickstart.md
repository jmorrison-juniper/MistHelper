# Quickstart Validation: History Organization Isolation

**Feature**: [spec.md](spec.md)

## Execution Boundary

This guide defines validation after implementation authorization.
None of these acceptance tests ran during planning.
The planning step wrote only the five approved documents.

The parent checked and claimed the six migration files in [plan.md](plan.md#exact-additional-test-migration-list).
The user authorized local implementation, validation, and commit.
This guide grants no permission to push or open a pull request before the coordinator releases the verified base.

## Prerequisites

- Use this issue's current exclusive worktree and app-managed branch.
- Use the existing `.venv` with Python 3.13.13 and installed requirements.
- Use a credential-free shell.
- Do not load `.env`, production configuration, cloud sessions, or production data.
- Use synthetic database readers, in-memory records, and temporary audit trails only.

Do not install dependencies or run bootstrap scripts.
Do not start a server, browser, production container, or store.
Do not inspect another worktree or the main checkout.

The existing pytest fixtures isolate working directories, configuration caches, and audit trails.
The new fixtures must also replace database connections with synthetic readers.
Adding a selected organization must not activate an unused real operation reader.
Keep those readers in memory in the three migrated fixtures.

## 1. Prepare Local Validation

Run these commands from the current worktree root after implementation authorization:

```bash
export PATH="$PWD/.venv/bin:$PATH"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$PWD"
export MISTHELPER_STANDALONE=true
export VALIDATION_DIR="$(.venv/bin/python -c 'import tempfile; print(tempfile.mkdtemp(prefix="issue-3484-validation-"))')"
export COVERAGE_FILE="$VALIDATION_DIR/.coverage"
rtk proxy .venv/bin/python --version
rtk git status --short
```

Expected result: the interpreter reports Python 3.13.13.
The worktree remains on its existing branch.
Validation reports stay outside the repository.
No dependency installation occurs.

## 2. Record the Existing Baseline

Before production edits, run the coupled baseline:

```bash
rtk proxy .venv/bin/python -m pytest --timeout=120 \
  tests/contract/upgrade_portal/test_history_routes.py \
  tests/contract/upgrade_portal/test_history_device_type.py \
  tests/contract/upgrade_portal/test_history_operations.py \
  tests/contract/upgrade_portal/test_lock_audit_log.py \
  tests/contract/upgrade_portal/test_lock_free_reads.py \
  tests/contract/upgrade_portal/test_upgrade_routes/test_stale_views.py \
  tests/unit/upgrade_portal/test_review_store_seams.py \
  tests/unit/upgrade_portal/test_store.py \
  tests/unit/upgrade_portal/test_store_history.py \
  tests/unit/upgrade_portal/test_org_history.py
```

Record the exit status, collected count, passed count, failed count, and skip reasons.
Do not treat an unexpected skip as evidence.
If an unexpected network or store access occurs, stop and repair the isolated fixture.
Do not retry against production services.

## 3. Prove the Defect, Then the Repair

After the new regression files exist, run them against the unrepaired production source:

```bash
rtk proxy .venv/bin/python -m pytest --timeout=120 \
  tests/contract/upgrade_portal/test_issue_3484_history_org_isolation.py \
  tests/unit/upgrade_portal/test_issue_3484_audit_org_isolation.py
```

Expected red evidence: foreign content, incorrect scoped totals, incorrect source calls, or incorrect expiry attribution.
An unsupported proposed signature alone does not prove the original leak.
The real route and real adapter cases must demonstrate the defect.

After the repair and claimed fixture migrations, rerun the same command.
Expected result: every new case passes with zero foreign output.

## 4. Validate the Acceptance Matrix

Use the synthetic relationships in [data-model.md](data-model.md#synthetic-validation-relationships).
Use the exact obligations in [contracts/history-scope.md](contracts/history-scope.md).

| Scenario | Required evidence |
| --- | --- |
| Organization A selected, A and B both permitted | All four HTML cards exclude B content. Both JSON histories exclude B records. |
| No site restriction | A1 and A2 records appear. B1 contributes no records or totals. |
| Empty A, populated B | Existing empty states, zero capture and run totals, and no foreign operation or audit content. |
| A1 requested | Organization-and-site intersection on the page and both site APIs. |
| B1 or unknown site requested under A | Successful empty intersection without foreign stored content. |
| Later page and beyond-end offset | Exact scoped total, correct matching rows, and preserved site links. |
| Foreign data added, removed, or reordered | Matching rows, totals, and page boundaries do not change. |
| Missing or invalid selection | `400 org_not_chosen` and zero calls to all four sources. |
| Excluded, unknown, removed, or stale selection | `403 org_not_permitted` and zero calls to all four sources. |
| Known empty privileges | Refusal before every history source. |
| Unavailable environment-token privileges | Existing policy permits explicit A selection. Every result still matches A. |
| Caller supplies another organization | The signed A selection remains authoritative. |
| No active sign-in | Existing JSON refusal or HTML redirect before every history source. |
| Missing record attribution | No unattributed capture, run, operation, or audit record reaches output. |
| Another operator holds the site lock | Authorized history succeeds without a lock lookup or typed word. |
| Operation started by another browser session | Matching operation stays visible without its owner-only progress link. |

Inspect full response text and decoded JSON.
Check foreign identifiers, site labels, moments, operator labels, account labels, digests, links, and embedded values.
Assert exact totals rather than only the absence of a foreign row.

For an empty foreign-site request, distinguish the requested site value from returned stored history.
Keep existing request-scope attributes and bulk-control context.
Do not change the interface to remove a site value that the caller supplied.

### Real adapter proof

Do not inject `CAPTURE_LISTER` or `RUN_LISTER` for the isolation proof.
Use the actual route fallback adapters and actual `CaptureQuery` and `RunQuery`.
Replace `store.connect_database` with the synthetic database reader.
Exercise the actual count and page query functions.

The synthetic reader must apply only filters present in the query text.
Inspect both calls' `org_id` binds and optional site binds.
Confirm filter clauses precede counting and pagination.
Include newer foreign records that would otherwise consume the first page.

### Audit proof

Use temporary trails with interleaved A and B records.
Include A1 and A2 records and reused site text across organizations.

Verify these cases:

- A take after an unreleased take inserts one correctly attributed expiry.
- A take after an unreleased takeover inserts one correctly attributed expiry.
- A release prevents the corresponding expiry.
- A takeover inserts no expiry by itself.
- Foreign actions and other sites change no matching inference state.
- Earlier matching holds outside the result limit still support inference.
- Foreign events do not consume bounded result positions.
- Missing organization attribution produces no matching output.
- Bounded output equals the newest events from the full scoped output.
- Zero, negative, and `None` limits retain their existing slice behavior.
- Missing files, damaged lines, and legacy actions retain existing behavior.
- Actual and inferred rows retain digests without stored audit addresses.

Use independent expected events.
Do not build the complete expected answer with `audit_row` or `mark_expiries`.

## 5. Run Local Quality Gates

Compile the changed production files, new tests, and each claimed migration file.
The command below shows the minimum source and new-test set:

```bash
rtk proxy .venv/bin/python -m py_compile MistHelper.py \
  src/upgrade_portal/app/routes/review.py \
  src/upgrade_portal/compare/lock_audit.py \
  tests/contract/upgrade_portal/test_issue_3484_history_org_isolation.py \
  tests/unit/upgrade_portal/test_issue_3484_audit_org_isolation.py
rtk proxy .venv/bin/python -m ruff check MistHelper.py \
  src/upgrade_portal/app/routes/review.py src/upgrade_portal/compare/lock_audit.py \
  tests/contract/upgrade_portal/test_issue_3484_history_org_isolation.py \
  tests/unit/upgrade_portal/test_issue_3484_audit_org_isolation.py \
  tests/contract/upgrade_portal/test_history_routes.py \
  tests/contract/upgrade_portal/test_history_device_type.py \
  tests/contract/upgrade_portal/test_history_operations.py \
  tests/contract/upgrade_portal/test_lock_audit_log.py \
  tests/contract/upgrade_portal/test_upgrade_routes/test_stale_views.py \
  tests/unit/upgrade_portal/test_review_store_seams.py
rtk proxy .venv/bin/python -m black --check --diff MistHelper.py \
  src/upgrade_portal/app/routes/review.py src/upgrade_portal/compare/lock_audit.py \
  tests/contract/upgrade_portal/test_issue_3484_history_org_isolation.py \
  tests/unit/upgrade_portal/test_issue_3484_audit_org_isolation.py \
  tests/contract/upgrade_portal/test_history_routes.py \
  tests/contract/upgrade_portal/test_history_device_type.py \
  tests/contract/upgrade_portal/test_history_operations.py \
  tests/contract/upgrade_portal/test_lock_audit_log.py \
  tests/contract/upgrade_portal/test_upgrade_routes/test_stale_views.py \
  tests/unit/upgrade_portal/test_review_store_seams.py
```

Read the full CI mypy scope from the workflow.
Local strict typing and security checks cover the two changed source files:

```bash
rtk proxy .venv/bin/python -m mypy src/upgrade_portal/app/routes/review.py \
  src/upgrade_portal/compare/lock_audit.py --config-file pyproject.toml
rtk proxy .venv/bin/bandit-exclude-check
rtk proxy .venv/bin/python -m bandit -c pyproject.toml \
  src/upgrade_portal/app/routes/review.py src/upgrade_portal/compare/lock_audit.py
```

Expected result: every applicable check passes.
Keep the existing configuration and exclusions unchanged.
Do not add a suppression for a real finding.
Inspect new methods for the five-item, parameter, block, and 25-line limits.
Check inline comments and action logging in each touched block.

### Scoped coverage

Run the new regressions and their coupled contracts with coverage on the two changed production modules:

```bash
rtk proxy .venv/bin/python -m pytest --timeout=120 \
  tests/contract/upgrade_portal/test_issue_3484_history_org_isolation.py \
  tests/unit/upgrade_portal/test_issue_3484_audit_org_isolation.py \
  tests/contract/upgrade_portal/test_history_routes.py \
  tests/contract/upgrade_portal/test_history_device_type.py \
  tests/contract/upgrade_portal/test_history_operations.py \
  tests/contract/upgrade_portal/test_lock_audit_log.py \
  tests/contract/upgrade_portal/test_lock_free_reads.py \
  tests/contract/upgrade_portal/test_upgrade_routes/test_stale_views.py \
  tests/unit/upgrade_portal/test_review_store_seams.py \
  tests/unit/upgrade_portal/test_store.py \
  tests/unit/upgrade_portal/test_store_history.py \
  tests/unit/upgrade_portal/test_org_history.py \
  tests/contract/upgrade_portal/test_comparison.py \
  tests/contract/upgrade_portal/test_comparison_errors.py \
  tests/contract/upgrade_portal/test_comparison_export.py \
  tests/contract/upgrade_portal/test_compare_picker_moment.py \
  --cov=src.upgrade_portal.app.routes.review \
  --cov=src.upgrade_portal.compare.lock_audit \
  --cov-report=term-missing --cov-fail-under=80
```

Require at least 80% coverage for each changed module, not only the combined percentage.
Check both module percentages:

```bash
rtk proxy .venv/bin/python -m coverage json -o "$VALIDATION_DIR/coverage.json"
rtk proxy .venv/bin/python -c 'import json, os; from pathlib import Path; report=json.loads((Path(os.environ["VALIDATION_DIR"])/"coverage.json").read_text()); paths=("src/upgrade_portal/app/routes/review.py", "src/upgrade_portal/compare/lock_audit.py"); scores={path: report["files"][path]["summary"]["percent_covered"] for path in paths}; print("Checked", len(scores), "modules:", scores); assert all(score >= 80 for score in scores.values()), "Each changed module must reach 80%"'
```

If either module falls below the floor, add relevant isolated tests.
Do not lower the floor or add an exclusion.

### Repository test-quality ratchet

```bash
rtk proxy .venv/bin/test-quality-analyzer --gate \
  --config .github/test-quality-config.toml \
  --baseline .github/test-quality-baseline.json \
  --roots tests/contract/upgrade_portal/test_issue_3484_history_org_isolation.py \
  tests/unit/upgrade_portal/test_issue_3484_audit_org_isolation.py \
  tests/contract/upgrade_portal/test_history_routes.py \
  tests/contract/upgrade_portal/test_history_device_type.py \
  tests/contract/upgrade_portal/test_upgrade_routes/test_stale_views.py \
  tests/contract/upgrade_portal/test_history_operations.py \
  tests/unit/upgrade_portal/test_review_store_seams.py \
  tests/contract/upgrade_portal/test_lock_audit_log.py \
  --report "$VALIDATION_DIR/test-quality-report.json" \
  --summary "$VALIDATION_DIR/test-quality-summary.md"
```

Expected result: no new finding compared with the unchanged baseline.
Do not use `--write-baseline`, `--prune-baseline`, rule overrides, or replacement configuration.
Include feature-owned untracked tests in the scan.
Do not use a committed-diff filter that omits them.

## 6. Run Preserved-Behavior Regressions

Rerun the coupled baseline after the repair.
Also run these unchanged presentation, firmware, and bulk-control contracts:

```bash
rtk proxy .venv/bin/python -m pytest --timeout=120 \
  tests/unit/upgrade_portal/test_issue_3482_history_scope.py \
  tests/unit/upgrade_portal/test_issue_3486_history_site_column.py \
  tests/contract/upgrade_portal/test_upgrade_options.py \
  tests/contract/upgrade_portal/test_org_advanced_options.py \
  tests/contract/upgrade_portal/test_upgrade_start.py \
  tests/contract/upgrade_portal/test_upgrade_routes/test_bulk_preview.py \
  tests/contract/upgrade_portal/test_upgrade_routes/test_bulk_actions.py
```

Expected result: existing history text, site columns, device types, firmware choices, and typed confirmations remain correct.
Do not edit unrelated text or styles to make these tests pass.

Record complete counts, failures, skip reasons, and the final runner summary for the focused commands.
Compare the coupled regressions with the recorded pre-repair baseline.
The broader repository baseline commands did not run and are not local acceptance prerequisites.
The coordinator explicitly requires focused validation.
Required PR checks remain unchanged.

Do not add a browser journey for this server-only repair.
The direct response and control contracts cover this server-only repair.

## 7. Verify Ownership and Enter the Delivery Hold

Verify that the implementation changes contain only the five claimed files and six parent-approved migration files.
Verify that shared context, instructions, quality configuration, and quality baseline remain unchanged.

Prepare local evidence for the parent:

1. List the exact changed files.
2. Report the failing contract and repaired result.
3. Report every gate, per-module coverage, and regression count.
4. Complete the authorized local commit.
5. Wait for the coordinator's release and stable main SHA.

Do not push or open a pull request before that release.
Do not change branches or inspect another checkout.
The latest queue places #3305 after #3398 and before #3484.
