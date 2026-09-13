# Quickstart: Verifying the Firmware Manager Compliance Refactor

**Feature**: `refactor/firmware-manager-compliance`
**Audience**: Reviewer performing acceptance checks on the branch.
**Time required**: ~6 minutes of automated checks + ~3 minutes of manual REPL smoke.

---

## Prerequisites

- Branch `refactor/firmware-manager-compliance` checked out.
- Python 3.13+ available (per Constitution Technology & Compatibility Constraints).
- Repository dependencies installed (`pip install -r requirements.txt` or equivalent UV workflow).

---

## Step 1: Syntax and Lint Gates (30 seconds)

Run these two commands. Both MUST exit 0 with no output on stderr:

```bash
python -m py_compile src/firmware/firmware_manager.py
python -m ruff check src/firmware/firmware_manager.py
```

If either fails, the refactor is not ready. Do not proceed.

Corresponds to acceptance criteria FR-002, FR-003, SC-006, SC-007.

---

## Step 2: Compliance Analyzer Gate (30 seconds)

Run the compliance analyzer and confirm the score, grade, and violation counts:

```bash
python -m tools.compliance_analyzer src/firmware/firmware_manager.py
```

Expected output:

- **Score**: `100.0 / 100`.
- **Grade**: `A+`.
- **HIGH-severity findings**: 0.
- **MEDIUM-severity findings**: 0.
- **LOW-severity findings**: 0.
- **CONV-COMMENTS coverage**: >= 90% (spec SC-009).
- **Total findings by rule**: CONV-COMMENTS 0, CONV-NAME 0, STRUCT-BLOCKS 0, STRUCT-COMPLEXITY 0, STRUCT-LENGTH 0, STRUCT-NESTING 0, STRUCT-PARAMS 0.

Corresponds to acceptance criteria FR-001, SC-001, SC-002, SC-003, SC-004, SC-011, SC-012.

**No intermediate grades accepted.** Per spec, only 100.0/A+/zero violations is a pass. If the analyzer reports even a single LOW finding, the refactor is incomplete.

---

## Step 3: Factory-Wrapper Insulation Smoke (10 seconds)

Confirm the six-callsite insulation is intact — MistHelper.py's `FirmwareManager.create` is the sole construction site, and all five downstream callsites are byte-identical:

```bash
grep -n "FirmwareManager\.create\|from src\.firmware\.firmware_manager" MistHelper.py
```

Expected output (exactly these lines, in this order):

```
18795:        from src.firmware.firmware_manager import (
18797:    def create(apisession: Any, org_id: str) -> Any:
19809:        firmware_manager = FirmwareManager.create(apisession, org_id)
22097:    firmware_manager = FirmwareManager.create(apisession, org_id)
22154:    firmware_manager = FirmwareManager.create(apisession, org_id)
22237:    firmware_manager = FirmwareManager.create(apisession, org_id)
22246:    firmware_manager = FirmwareManager.create(apisession, org_id)
```

Line numbers may shift by a few positions if the factory body grew by 3 lines (import expanded to two-name form). What matters is:

- Exactly one `from src.firmware.firmware_manager import` (the factory's local import).
- Exactly one `def create(...)`.
- Exactly five `FirmwareManager.create(apisession, org_id)` call-sites — identical text to pre-refactor.

Also confirm no other Python file imports the module:

```bash
grep -rn "from src\.firmware\.firmware_manager" --include="*.py" .
```

Expected: exactly one match — MistHelper.py's local import inside the factory body.

Corresponds to acceptance criteria FR-011, FR-017, C-6.

---

## Step 4: Inline-Comment Coverage Spot Check (~1 minute)

Randomly sample 25 executable lines from the refactored file and count how many carry an inline `# WHY:` comment. Any comment form is acceptable (analyzer checks any inline comment); the `# WHY:` convention is our recommended style.

```bash
# Rough sampling helper — reviewer picks 25 line numbers by inspection.
sed -n '80,110p' src/firmware/firmware_manager.py     # spot-check __init__ / _bind_module_globals
sed -n '700,730p' src/firmware/firmware_manager.py    # spot-check inside _upgrade_ap_firmware_by_gateway_template
sed -n '1360,1385p' src/firmware/firmware_manager.py  # spot-check _split_results_by_status (rename site)
```

At least **20 of the 25 sampled lines MUST have an inline comment**. Comments must explain *why* the line exists, not merely restate the code (Constitution VI).

Fast global sanity check:

```bash
# Count executable lines and lines with inline comments; ratio should be >= 0.90.
python - <<'EOF'
import re
with open("src/firmware/firmware_manager.py", encoding="utf-8") as fh:
    lines = fh.readlines()
executable = 0
commented = 0
for line in lines:
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or stripped.startswith('"""'):
        continue
    executable += 1
    if re.search(r"\s#\s*\S", line):
        commented += 1
coverage = commented / executable if executable else 0.0
print(f"executable={executable} commented={commented} coverage={coverage:.1%}")
EOF
```

Expected: `coverage=90.0%` or higher.

Corresponds to acceptance criteria FR-006, SC-009, Constitution VI.

---

## Step 5: Logging Pattern Spot Check (~1 minute)

Confirm the info-before / debug-after pattern is present at the four HIGH-severity refactor sites (FR-012 companion behavior) and at the `__init__`:

```bash
grep -n -B 1 -A 3 "def check_firmware_upgrade_status\|def _continuous_monitoring_mode\|def _upgrade_ap_firmware_by_gateway_template\|def _execute_msp_upgrade_plan\|def __init__" src/firmware/firmware_manager.py
```

For each hit, verify:

- The first executable line inside the method is a `logging.info(...)` call.
- Somewhere before the method's return (typically the last executable line), a `logging.debug(...)` call reports the result summary.

Also confirm ASCII-only log strings and no f-strings inside `logging.*` calls:

```bash
python - <<'EOF'
import re
with open("src/firmware/firmware_manager.py", encoding="utf-8") as fh:
    for lineno, line in enumerate(fh, 1):
        if "logging." in line:
            for match in re.finditer(r"[\"'].*?[\"']", line):
                if any(ord(ch) > 127 for ch in match.group()):
                    print(f"UNICODE at {lineno}: {line.rstrip()}")
        if re.search(r"logging\.\w+\(f['\"]", line):
            print(f"F-STRING at {lineno}: {line.rstrip()}")
EOF
```

Expected output: empty. Any reported line is a violation of FR-008 (ASCII-only + lazy `%s`/`%d` form).

Corresponds to acceptance criteria SC-010, FR-007, FR-008.

---

## Step 6: Constructor Contract Smoke Test (~2 minutes)

Start a Python REPL from the repo root and verify the new constructor contract:

```python
python
>>> from unittest.mock import MagicMock
>>> from src.firmware.firmware_manager import FirmwareManager, FirmwareManagerConfig
>>>
>>> # C-1: Positive case — construct via config, verify no TypeError.
>>> config = FirmwareManagerConfig(apisession=MagicMock(), org_id="test-org")
>>> firmware_manager = FirmwareManager(config)
>>> firmware_manager.org_id
'test-org'
>>>
>>> # C-2: Legacy positional call MUST raise TypeError.
>>> try:
...     FirmwareManager("test-org", MagicMock())
... except TypeError as exc:
...     print(f"Got expected TypeError: {exc}")
...
Got expected TypeError: __init__() takes 2 positional arguments but 3 were given
>>>
>>> # C-3: Legacy kwargs call MUST raise TypeError.
>>> try:
...     FirmwareManager(apisession=MagicMock(), org_id="test-org")
... except TypeError as exc:
...     print(f"Got expected TypeError: {exc}")
...
Got expected TypeError: __init__() got an unexpected keyword argument 'apisession'
>>>
>>> # C-4: Immutability — frozen dataclass rejects mutation.
>>> try:
...     config.org_id = "changed"
... except Exception as exc:
...     print(f"Got expected FrozenInstanceError: {type(exc).__name__}")
...
Got expected FrozenInstanceError: FrozenInstanceError
>>>
>>> # C-5: Validation — empty org_id rejected at construction.
>>> try:
...     FirmwareManagerConfig(apisession=MagicMock(), org_id="")
... except ValueError as exc:
...     print(f"Got expected ValueError: {exc}")
...
Got expected ValueError: org_id must be a non-empty string
```

All five cases MUST behave exactly as shown. If any diverges, the contract in `contracts/constructor.md` is not satisfied.

Corresponds to acceptance criteria FR-014, SC-005, and the six contract invariants C-1 through C-6.

---

## Step 7: Naming Rename Spot Check (~15 seconds)

Confirm the three CONV-NAME loop-variable renames landed:

```bash
grep -n "for r in " src/firmware/firmware_manager.py
```

Expected output: **empty**. No single-letter `r` loop variables remain.

Then confirm the intended replacements are present (line numbers approximate):

```bash
grep -n "for result in \|for record in \|for report_row in " src/firmware/firmware_manager.py
```

Expected: three matches inside the (refactored) `_split_results_by_status` region.

Corresponds to acceptance criteria FR-009, SC-012.

---

## Step 8: Production Path Manual Smoke (Optional, ~3 minutes)

The most confident-inducing check is running menu 196 in dry-run mode against a real Mist org, confirming the menu launches, prompts as before, and reaches the "no upgrades executed (dry-run)" summary without error. This is optional if steps 1-7 all pass, but recommended before merging.

```bash
python MistHelper.py --dry-run
# In the menu, select 196 (firmware manager).
# Walk through the sub-menu (status check, AP upgrade, SSR upgrade, MSP bulk).
# Cancel at each confirmation prompt.
```

Expected: identical prompt sequence, identical log lines, and identical CSV output paths compared to the pre-refactor branch. Any observable divergence (extra prompt, missing log line, changed banner text, different CSV filename) is an FR-017 violation.

---

## Acceptance Summary

The refactor is ready to merge when every step 1 through 7 passes. Step 8 is optional but strongly recommended.

| Step | Gate | Corresponds To |
|------|------|----------------|
| 1 | py_compile + ruff | FR-002, FR-003, SC-006, SC-007 |
| 2 | Compliance analyzer 100.0 / A+ / zero findings | FR-001, SC-001 through SC-004, SC-011, SC-012 |
| 3 | Six-callsite grep smoke — one factory diff, five byte-identical callsites | FR-011, FR-017, C-6 |
| 4 | Inline-comment >=90% coverage | FR-006, SC-009, Constitution VI |
| 5 | Info-before / debug-after + ASCII-only lazy-form logs | FR-007, FR-008, SC-010 |
| 6 | Constructor contract (C-1 through C-5, C-6 via Step 3) | FR-014, SC-005 |
| 7 | Loop-variable rename spot check | FR-009, SC-012 |
| 8 | Manual menu 196 dry-run smoke (optional) | FR-017 |

---

## Failure Triage

| Symptom | Most Likely Cause | Fix |
|---------|-------------------|-----|
| Step 1 `ruff` reports unused import | Type-alias not consumed after decomposition | Delete the alias or wire it into a helper signature. |
| Step 2 reports STRUCT-LENGTH remaining | A PCPP helper wasn't split far enough | Re-decompose the offender per R-3/R-4 in `research.md`. |
| Step 2 reports CONV-COMMENTS < 90% | Some helpers missed the `# WHY:` pass | Grep for `^ *return ` / `^ *for ` without trailing `# ...` and back-fill. |
| Step 3 shows 4 callsites instead of 5 | A downstream MistHelper.py callsite was accidentally modified | `git diff MistHelper.py` — verify only lines 18791-18807 changed. |
| Step 6 REPL positional case does NOT raise | `__init__` still accepts more than one positional arg | Refactor incomplete — collapse to `def __init__(self, config)`. |
| Step 6 REPL frozen mutation does NOT raise | `FirmwareManagerConfig` missing `frozen=True` | Add the dataclass decorator flag. |
| Step 8 menu 196 shows a prompt that didn't exist before | A new prompt slipped in during decomposition | Diff the prompt sequence vs. pre-refactor branch; remove the addition. |
