# Quickstart: Verifying the Bulk AP Upgrader Compliance Refactor

**Feature**: `refactor/bulk-ap-upgrader-compliance`
**Audience**: Reviewer performing acceptance checks on the branch.
**Time required**: ~5 minutes of automated checks + ~3 minutes of manual REPL smoke.

---

## Prerequisites

- Branch `refactor/bulk-ap-upgrader-compliance` checked out.
- Python 3.13+ available (per Constitution Technology & Compatibility Constraints).
- Repository dependencies installed (`pip install -r requirements.txt` or equivalent UV workflow).

---

## Step 1: Syntax and Lint Gates (30 seconds)

Run these two commands. Both MUST exit 0 with no output on stderr:

```bash
python -m py_compile src/firmware/bulk_ap_upgrader.py
python -m ruff check src/firmware/bulk_ap_upgrader.py
```

If either fails, the refactor is not ready. Do not proceed.

Corresponds to acceptance criteria FR-002, FR-003, SC-006, SC-007.

---

## Step 2: Compliance Analyzer Gate (30 seconds)

Run the compliance analyzer and confirm the score and grade:

```bash
python -m tools.compliance_analyzer src/firmware/bulk_ap_upgrader.py
```

Expected output includes:

- **Score**: >=80.0/100.
- **Grade**: `B` or better (`A-`, `A`, `A+`).
- **HIGH-severity findings**: 0.
- **MEDIUM-severity findings**: at most 2, and NONE of them may be one of the ten enumerated in FR-012.

Corresponds to acceptance criteria FR-001, SC-001 through SC-004.

If the score is below 80, capture the analyzer's remaining findings and iterate on the highest-impact ones (usually still MEDIUM function-complexity offenders that were partially split but not enough).

---

## Step 3: Regression Test Gate (~1 minute)

Run the existing unit test suite:

```bash
python -m pytest tests/unit/test_bulk_ap_upgrader.py -v
```

Expected: all tests pass. Zero failures, zero errors.

If a test fails, the most likely cause is that a test constructs `BulkAPFirmwareUpgrader` directly (bypassing the `_make_upgrader` factory) with the pre-refactor keyword signature. Sweep for such tests with:

```bash
grep -n "BulkAPFirmwareUpgrader(" tests/
```

Every match should be either `_make_upgrader`'s call site or a test-body assertion that references the class name in a comment.

Corresponds to acceptance criterion SC-008.

---

## Step 4: Inline-Comment Coverage Spot Check (~1 minute)

Randomly sample 25 executable lines from the refactored file and count how many carry an inline `# ...` comment:

```bash
# Rough sampling helper — reviewer picks 25 line numbers by inspection
sed -n '100,150p' src/firmware/bulk_ap_upgrader.py    # spot-check a helper body
sed -n '700,720p' src/firmware/bulk_ap_upgrader.py    # spot-check inside _select_strategy
```

At least 20 of the 25 sampled lines MUST have an inline comment. The comments must explain *why* the line exists, not merely restate the code (per Constitution VI).

Corresponds to acceptance criterion SC-009.

---

## Step 5: Logging Pattern Spot Check (~1 minute)

Confirm the info-before / debug-after pattern is present at the ten targeted refactor sites (FR-012):

```bash
grep -n -B 2 -A 2 "def _select_strategy\|def _estimate_api_calls\|def _offer_additional_model_versions\|def _fetch_ap_model_families\|def _configure_auto_upgrade_schedule\|def _step11_write_results\|def _apply_version_selection\|def _upgrade_version_group\|def _log_upgrade_results\|def execute" src/firmware/bulk_ap_upgrader.py
```

Each method's first executable line should be a `logging.info(...)` call. Somewhere before the method's return, a `logging.debug(...)` call MUST report the result summary.

Also confirm ASCII-only log strings:

```bash
python -c "
import re
with open('src/firmware/bulk_ap_upgrader.py', encoding='utf-8') as fh:
    for lineno, line in enumerate(fh, 1):
        if 'logging.' in line:
            for match in re.finditer(r'[\"\'].*?[\"\']', line):
                if any(ord(ch) > 127 for ch in match.group()):
                    print(f'{lineno}: {line.rstrip()}')
"
```

Expected output: empty. Any line reported is a Unicode-in-log-string violation of FR-008.

Corresponds to acceptance criteria SC-010, FR-007, FR-008.

---

## Step 6: Constructor Contract Smoke Test (~2 minutes)

Start a Python REPL from the repo root and verify the new constructor contract:

```python
python
>>> from unittest.mock import MagicMock
>>> from src.firmware.bulk_ap_upgrader import BulkAPFirmwareUpgrader, BulkAPUpgraderConfig
>>>
>>> # Positive case: construct via config, verify no TypeError
>>> config = BulkAPUpgraderConfig(org_id="test-org", apisession=MagicMock(), dry_run=True)
>>> upgrader = BulkAPFirmwareUpgrader(config)
>>> upgrader.org_id
'test-org'
>>> upgrader.dry_run
True
>>>
>>> # Negative case: legacy positional call MUST raise TypeError
>>> try:
...     BulkAPFirmwareUpgrader("org", MagicMock(), dry_run=True)
... except TypeError as exc:
...     print(f"Got expected TypeError: {exc}")
...
Got expected TypeError: __init__() takes 2 positional arguments but 3 were given
>>>
>>> # Immutability: frozen dataclass rejects mutation
>>> try:
...     config.dry_run = False
... except Exception as exc:
...     print(f"Got expected FrozenInstanceError: {type(exc).__name__}")
...
Got expected FrozenInstanceError: FrozenInstanceError
```

All three cases MUST behave as shown. If any diverges, the contract in `contracts/constructor.md` is not satisfied.

Corresponds to acceptance criteria FR-014, SC-005, and the spec Edge Case ("fail fast with a clear TypeError").

---

## Step 7: Production Path Manual Smoke (Optional, ~2 minutes)

The most confident-inducing check is running menu 195 in dry-run mode against a real Mist org, confirming the menu launches, prompts as before, and reaches the "no upgrades executed (dry-run)" summary without error. This is optional if steps 1-6 all pass, but recommended before merging.

```bash
python MistHelper.py --dry-run
# In the menu, select 195 (bulk AP firmware upgrade by site)
# Walk through site selection, cancel at the confirmation prompt
```

Expected: identical prompt sequence and identical log lines compared to the pre-refactor branch. Any observable divergence (extra prompt, missing log line, changed banner text) is an FR-017 violation.

---

## Acceptance Summary

The refactor is ready to merge when every step 1 through 6 passes. Step 7 is optional but recommended.

| Step | Gate | Corresponds To |
|------|------|----------------|
| 1 | py_compile + ruff | FR-002, FR-003, SC-006, SC-007 |
| 2 | Compliance analyzer >=80 grade B | FR-001, SC-001 through SC-004 |
| 3 | pytest all-green | SC-008 |
| 4 | Inline-comment >=80% on 25-line sample | FR-006, SC-009 |
| 5 | Info-before / debug-after + ASCII-only logs | FR-007, FR-008, SC-010 |
| 6 | Constructor contract (positive + TypeError + FrozenInstanceError) | FR-014, SC-005 |
| 7 | Manual menu 195 smoke (optional) | FR-017 |
