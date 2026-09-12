# Quickstart: Quality Gate Exception Remediation

**Purpose**: Pre/post validation commands for each implementation phase.

---

## Environment Setup

```powershell
cd "c:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper"
.venv\Scripts\Activate.ps1
```

---

## Phase 1 Validation

### Before starting (baseline counts)

```powershell
# Count current suppressions (baseline for SC-005)
(Select-String -Path MistHelper.py,starlink_dashboard.py,src\**\*.py -Pattern "# type: ignore|# noqa|# nosec" | Measure-Object).Count

# Confirm os.system locations
Select-String -Path MistHelper.py -Pattern "os\.system" | Select-Object LineNumber, Line

# Confirm B101 locations
Select-String -Path MistHelper.py -Pattern "nosec B101" | Measure-Object

# Confirm warn_unused_ignores current value
Select-String -Path pyproject.toml -Pattern "warn_unused_ignores"
```

### After task 1.1 (pyproject.toml)

```powershell
# Verify setting changed
Select-String -Path pyproject.toml -Pattern "warn_unused_ignores"
# Expected: warn_unused_ignores = true

# Run mypy to confirm unused-ignore detection is active
mypy --config-file pyproject.toml MistHelper.py 2>&1 | Select-String "unused-ignore" | Select-Object -First 5
```

### After task 1.2 and 1.3 (starlink_dashboard.py)

```powershell
python -m ruff check starlink_dashboard.py
# Expected: no F841 or F401 violations

python -m py_compile starlink_dashboard.py
# Expected: no output (syntax clean)
```

### After task 1.4 (os.system replacement)

```powershell
# Confirm no os.system calls remain
Select-String -Path MistHelper.py -Pattern "os\.system"
# Expected: no results

# Run bandit for B605
bandit -r MistHelper.py --tests B605 2>&1 | Select-String "Issue\|No issues"
# Expected: "No issues identified."

python -m py_compile MistHelper.py
# Expected: no output
```

### After task 1.5 (B101 assert replacement)

```powershell
# Confirm no B101 nosec annotations remain in production code
Select-String -Path MistHelper.py -Pattern "nosec B101"
# Expected: no results

# Run bandit for B101
bandit -r MistHelper.py --tests B101 2>&1 | Select-String "Issue\|No issues"
# Expected: "No issues identified."

python -m py_compile MistHelper.py
# Expected: no output
```

### Phase 1 gate check (task 1.6)

```powershell
# Full gate sweep
python -m py_compile MistHelper.py
python -m ruff check MistHelper.py
python -m ruff check starlink_dashboard.py
bandit -r MistHelper.py
mypy --config-file pyproject.toml MistHelper.py 2>&1 | Select-String "error:|unused-ignore" | Select-Object -First 20
```

---

## Phase 2 Validation

### Before each PLR0913 refactor

```powershell
# Find all call sites for the function being refactored (example: SiteDataFetcher)
Select-String -Path MistHelper.py -Pattern "SiteDataFetcher\(" | Select-Object LineNumber, Line

# Run tests as baseline before touching the function
python MistHelper.py --test 2>&1 | Select-String "PASS|FAIL|ERROR" | Select-Object -Last 20
```

### After each PLR0913 refactor

```powershell
# Confirm PLR0913 suppression removed from the refactored function
# (function name varies per task)
Select-String -Path MistHelper.py -Pattern "PLR0913" | Select-Object LineNumber, Line

# Lint and test
python -m ruff check MistHelper.py
python MistHelper.py --test
```

### After task 2.1 (magic constant)

```powershell
python -m ruff check src\network\routing_utils.py
# Expected: no PLR2004 on line 1062

Select-String -Path src\network\routing_utils.py -Pattern "!= 200|requests.codes.ok" | Select-Object LineNumber, Line
# Expected: requests.codes.ok present, raw 200 gone
```

### Phase 2 gate check (task 2.8)

```powershell
python -m py_compile MistHelper.py
python -m ruff check MistHelper.py
python -m ruff check src\inventory\csv_comparator.py
python -m ruff check src\network\routing_utils.py
bandit -r MistHelper.py
python MistHelper.py --test
```

---

## Phase 3 Validation

### Stale annotation audit

```powershell
# Collect all unused-ignore warnings
mypy --config-file pyproject.toml MistHelper.py 2>&1 | Select-String "unused-ignore"

# Count remaining suppressions (must be lower than pre-Phase-1 baseline)
(Select-String -Path MistHelper.py,starlink_dashboard.py,src\**\*.py -Pattern "# type: ignore|# noqa|# nosec" | Measure-Object).Count
```

### Final gate sweep

```powershell
python -m py_compile MistHelper.py
python -m ruff check MistHelper.py
bandit -r MistHelper.py
python MistHelper.py --test
```
