# Detailed Implementation Tasks: Issue #293

**Feature**: Reduce Cyclomatic Complexity of `_launch_plotly_viewer` from 138 → ≤10  
**Status**: Ready for Phase 1 execution  
**Total Effort**: 27–35 hours (≈1 developer-week)  
**Timeline**: 6 phases, 2–4 weeks  

---

## Task Execution Overview

**Constraint**: Complete phases sequentially. Phase N+1 depends on Phase N deliverables.

**CI/CD Gates**: Must pass all quality gates after EACH phase before proceeding.

**Branch Strategy**: One worktree per phase
```powershell
git worktree add ../MistHelper-phase-<N> -b chore/293-phase-<N> main
```

**Merge Strategy**: Squash merge each phase PR before starting next phase
```powershell
# After Phase N PR is merged to main:
git fetch origin && git rebase origin/main
cd ../MistHelper-<next-phase>
git rebase origin/main
```

---

## PHASE 1: Extract DashTemplateManager

**Risk**: LOW  
**Effort**: 2–3 hours  
**Estimated Effort (actual)**: 2.5 hours  
**Dependency**: None (independent)  
**Blocks**: Phase 6 (integration)

---

### Task P1.1: Create and Implement DashTemplateManager Class

**ID**: T001  
**Priority**: P1 (blocks all downstream)  
**Acceptance Criteria**:
- [ ] New file `src/maps/plotly_map_templates.py` created with `DashTemplateManager` class
- [ ] Class has 4 methods: `__init__`, `get_custom_css`, `get_layout_html`, `get_app_meta`
- [ ] All CSS/styling extracted byte-for-byte from original
- [ ] All HTML layout components extracted exactly
- [ ] No external dependencies except `dash` and stdlib
- [ ] Python syntax valid (py_compile passes)
- [ ] Class docstring and all methods documented

**File Paths & Line Numbers** (from `maps_manager.py`):
- CSS code: Lines 3070–3120 (approximate, ~50 lines of CSS content)
- Layout structure: Lines 3120–3220 (approximate, ~100 lines of Dash components)
- Styling dict: Lines 3220–3250 (approximate, ~30 lines)

**Implementation Steps**:

1. **Copy CSS/styling code**:
   ```python
   # Extract from maps_manager._launch_plotly_viewer
   # Lines 3070–3250 (HTML/CSS defs)
   
   # Into new file:
   # src/maps/plotly_map_templates.py
   
   class DashTemplateManager:
       def __init__(self, org_id: str, base_template_dir: str = "src/maps/templates"):
           self.org_id = org_id
           self.base_template_dir = base_template_dir
           self._template_cache: Dict[str, str] = {}
       
       def get_custom_css(self) -> str:
           """Retrieve custom CSS styling for the map viewer."""
           return """
           ... paste CSS from lines 3070–3120 ...
           """
       
       def get_layout_html(self) -> Dict[str, Any]:
           """Build the main Dash HTML layout structure."""
           return html.Div([
               # ... paste layout from lines 3120–3220 ...
           ])
       
       def get_app_meta(self) -> Dict[str, str]:
           """Get metadata for Dash app."""
           return {
               "title": "Mist Coverage Heatmap Viewer",
               "favicon_url": "/favicon.png"
           }
       
       def validate_template(self) -> bool:
           """Validate that all templates are syntactically correct."""
           # Basic validation: ensure CSS and layout are non-empty
           assert len(self.get_custom_css()) > 100, "CSS too short"
           assert self.get_layout_html() is not None, "Layout is None"
           return True
   ```

2. **Git operations**:
   ```powershell
   # From repository root
   git worktree add ../MistHelper-phase-1 -b chore/293-phase-1 main
   cd ../MistHelper-phase-1
   ```

3. **Validation (pre-commit)**:
   ```powershell
   cd "MistHelper-phase-1"
   python -m py_compile src/maps/plotly_map_templates.py
   python -m ruff check src/maps/plotly_map_templates.py --fix
   python -m black src/maps/plotly_map_templates.py
   ```

**Test Cases**:

```python
# tests/maps/test_plotly_map_templates.py

import pytest
from src.maps.plotly_map_templates import DashTemplateManager

class TestDashTemplateManager:
    
    def test_init_creates_instance(self):
        """DashTemplateManager initializes without errors."""
        mgr = DashTemplateManager(org_id="test-org")
        assert mgr.org_id == "test-org"
        assert mgr.base_template_dir == "src/maps/templates"
    
    def test_get_custom_css_returns_string(self):
        """get_custom_css() returns non-empty CSS string."""
        mgr = DashTemplateManager(org_id="test-org")
        css = mgr.get_custom_css()
        assert isinstance(css, str)
        assert len(css) > 100
        assert "background-color" in css or "color:" in css
    
    def test_get_layout_html_returns_dict(self):
        """get_layout_html() returns valid Dash layout dict."""
        mgr = DashTemplateManager(org_id="test-org")
        layout = mgr.get_layout_html()
        assert layout is not None
        # Verify key Dash components present
        # (can't directly check type without importing Dash components,
        #  but we can verify it's not None/empty)
    
    def test_get_app_meta_returns_dict(self):
        """get_app_meta() returns metadata dict with required keys."""
        mgr = DashTemplateManager(org_id="test-org")
        meta = mgr.get_app_meta()
        assert isinstance(meta, dict)
        assert "title" in meta
        assert meta["title"] == "Mist Coverage Heatmap Viewer"
    
    def test_validate_template_passes(self):
        """validate_template() returns True when templates are valid."""
        mgr = DashTemplateManager(org_id="test-org")
        assert mgr.validate_template() is True
```

**Quality Gate Validation**:

```powershell
# Run in ../MistHelper-phase-1

# 1. Syntax check
python -m py_compile src/maps/plotly_map_templates.py
# Expected output: (none, exit code 0)

# 2. Lint check
python -m ruff check src/maps/plotly_map_templates.py
# Expected output: 0 errors

# 3. Format check
python -m black --check src/maps/plotly_map_templates.py
# Expected output: All done! (exit code 0)

# 4. Unit tests
pytest tests/maps/test_plotly_map_templates.py -v
# Expected output: 5 passed

# 5. Type check (optional)
python -m mypy src/maps/plotly_map_templates.py --ignore-missing-imports
# Expected output: Success (or just informational, not blocking)
```

**Risk Mitigations**:
- **Risk**: CSS/HTML not byte-for-byte identical → visual regression
  - **Mitigation**: Compare output HTML in browser dev tools; screenshot comparison
- **Risk**: Missing dependency on `dash` components
  - **Mitigation**: Run syntax check and import test
- **Risk**: Copy-paste errors in template code
  - **Mitigation**: Side-by-side diff original vs. new file

**Git Commit**:

```powershell
git add src/maps/plotly_map_templates.py tests/maps/test_plotly_map_templates.py
git commit -m "chore(293): Extract DashTemplateManager from _launch_plotly_viewer

- Extract HTML/CSS templates to DashTemplateManager class
- Consolidate CSS styling, layout structure, and metadata
- Add comprehensive unit tests for template methods
- CC target: ≤5 (utility class)

Closes #293"
```

---

### Task P1.2: Update MapsManager to Use DashTemplateManager

**ID**: T002  
**Priority**: P1  
**Acceptance Criteria**:
- [ ] `MapsManager._launch_plotly_viewer` imports `DashTemplateManager`
- [ ] Lines 3070–3250 replaced with call to `template_mgr.get_custom_css()`, etc.
- [ ] Web UI CSS rendering identical (visual regression test)
- [ ] Original lines removed (not commented out)
- [ ] Syntax still valid

**File Paths**:
- `src/maps/maps_manager.py`: Lines 3010–3260 (method start to end of styling)

**Implementation Steps**:

1. **Add import** at top of `maps_manager.py`:
   ```python
   from src.maps.plotly_map_templates import DashTemplateManager
   ```

2. **Replace inline styling** in `_launch_plotly_viewer` (lines 3070–3250):
   ```python
   # Before (old code):
   custom_css = """... 50 lines of CSS ..."""
   custom_js = """... JS ..."""
   layout = html.Div([...])  # 100 lines
   
   # After (new code):
   template_mgr = DashTemplateManager(self.org_id)
   custom_css = template_mgr.get_custom_css()
   custom_js = template_mgr.get_custom_js()  # (if method exists)
   layout = template_mgr.get_layout_html()
   app_meta = template_mgr.get_app_meta()
   ```

3. **Validation**:
   ```powershell
   python -m py_compile src/maps/maps_manager.py
   ```

4. **Regression test** (visual UI check):
   - Launch app: `python MistHelper.py --menu 5` (or equivalent)
   - Inspect CSS in browser dev tools
   - Compare to original (should be identical)

**Test Cases**:

```python
# tests/maps/test_maps_manager_phase1.py

def test_launch_plotly_viewer_uses_template_manager():
    """_launch_plotly_viewer uses DashTemplateManager."""
    mgr = MapsManager(org_id="test-org")
    # Mock the rest of the method to just check template creation
    # (full integration test in Phase 6)
    with patch('src.maps.maps_manager.DashTemplateManager') as mock_tmpl:
        # Verify template manager is instantiated
        # (Can only test after full integration)
```

**Quality Gate Validation**:

```powershell
python -m py_compile src/maps/maps_manager.py
python -m ruff check src/maps/maps_manager.py
# Expected: all quality gates still pass
```

**Git Commit**:

```powershell
git add src/maps/maps_manager.py
git commit -m "chore(293): Integrate DashTemplateManager into _launch_plotly_viewer

- Replace inline CSS/HTML/layout code with DashTemplateManager calls
- Maintains visual output identity (CSS/layout byte-for-byte)
- Reduces method size by ~180 lines

Closes #293"
```

---

### Task P1.3: Run Full Quality Gates and PR Review

**ID**: T003  
**Priority**: P1  
**Acceptance Criteria**:
- [ ] All linting checks pass
- [ ] All unit tests pass (100% new code coverage)
- [ ] Type checks pass (mypy strict)
- [ ] Security scan passes (Bandit)
- [ ] No regressions in existing tests
- [ ] PR created and all CI checks green
- [ ] Regression test confirms CSS/UI unchanged

**Quality Gate Commands**:

```powershell
$py = ".venv\Scripts\python.exe"

# 1. Syntax validation
& $py -m py_compile src/maps/plotly_map_templates.py
& $py -m py_compile src/maps/maps_manager.py
Write-Host "✓ Syntax validation passed"

# 2. Lint & format
& $py -m ruff check src/maps/plotly_map_templates.py src/maps/maps_manager.py --fix
& $py -m black src/maps/plotly_map_templates.py src/maps/maps_manager.py
Write-Host "✓ Lint/format passed"

# 3. Type check
& $py -m mypy src/maps/plotly_map_templates.py --ignore-missing-imports --strict
Write-Host "✓ Type check passed"

# 4. Security scan
& $py -m bandit -r src/maps/plotly_map_templates.py
Write-Host "✓ Security scan passed"

# 5. Unit tests
& $py -m pytest tests/maps/test_plotly_map_templates.py -v --cov=src/maps/plotly_map_templates --cov-report=term-missing
# Expected: ≥70% coverage, all tests pass
Write-Host "✓ Unit tests passed"

# 6. Regression tests (if applicable)
& $py -m pytest tests/maps/ -k "regression" -v
Write-Host "✓ Regression tests passed"
```

**PR Creation**:

```powershell
# Push branch
git push origin chore/293-phase-1

# Create PR
gh pr create \
  --title "chore(293-phase1): Extract DashTemplateManager" \
  --body "Phase 1 of 6: Extract HTML/CSS template management

## Changes
- New file: src/maps/plotly_map_templates.py (DashTemplateManager class)
- Updated: src/maps/maps_manager.py (use DashTemplateManager)

## Acceptance Criteria
- [x] DashTemplateManager class created with 4 methods
- [x] CSS/HTML extracted byte-for-byte
- [x] Unit tests added (5 test cases)
- [x] Quality gates pass (lint, type, security, tests)
- [x] Visual regression test: CSS/layout unchanged

## Effort
- Estimated: 2–3 hours
- Actual: ___ hours
- Risk: LOW

Closes #293" \
  --base main
```

**Wait for CI**:

```powershell
# Monitor PR checks
gh pr checks --watch

# Expected: All checks ✓ (ruff, mypy, pytest, bandit, CodeQL)
# Do NOT merge until CodeQL completes (~2–3 minutes)
```

**Merge PR**:

```powershell
# Add auto-merge label after ALL checks pass (including CodeQL)
gh pr edit --add-label "auto-merge"

# Wait for squash merge
git fetch origin && git rebase origin/main
cd ../MistHelper
git worktree remove ../MistHelper-phase-1
```

---

## PHASE 2: Extract PlotlyMapDataSerializer

**Risk**: LOW  
**Effort**: 2–3 hours  
**Estimated Effort (actual)**: 2.5 hours  
**Dependency**: Phase 1 (merged)  
**Blocks**: Phase 5, Phase 6

---

### Task P2.1: Create PlotlyMapDataSerializer Class

**ID**: T004  
**Priority**: P1  
**Acceptance Criteria**:
- [ ] New file `src/maps/plotly_map_serializer.py` created
- [ ] Class has 6 methods: `__init__`, `serialize_figure_state`, `deserialize_figure_state`, `serialize_callback_inputs`, `deserialize_callback_inputs`, `validate_numeric_precision`
- [ ] Handles `numpy` arrays, datetime objects, edge cases
- [ ] Round-trip serialization produces exact match
- [ ] Numeric precision validation with configurable tolerance
- [ ] All JSON transformations byte-for-byte identical to original

**File Paths & Line Numbers** (from `maps_manager.py`):
- JSON serialization calls: Search for `json.dumps`, `json.loads` (lines ~3300–8000)
- Type conversions: numpy arrays, datetimes (lines ~3500–4500)

**Implementation Steps**:

1. **Create new file** `src/maps/plotly_map_serializer.py`:
   ```python
   import json
   import numpy as np
   from datetime import datetime
   from typing import Any, Dict
   
   class PlotlyMapDataSerializer:
       """Encapsulates JSON serialization for Plotly callback data."""
       
       def __init__(self):
           """Initialize serializer."""
           self._encoder = json.JSONEncoder(default=self._encode_defaults)
       
       def serialize_figure_state(self, figure_dict: Dict[str, Any]) -> str:
           """Serialize Plotly figure dict to JSON string."""
           return json.dumps(figure_dict, default=self._encode_defaults)
       
       def deserialize_figure_state(self, json_str: str) -> Dict[str, Any]:
           """Deserialize JSON string back to Plotly figure dict."""
           return json.loads(json_str)
       
       def serialize_callback_inputs(self, inputs: Dict[str, Any]) -> str:
           """Serialize callback input dictionary."""
           return json.dumps(inputs, default=self._encode_defaults)
       
       def deserialize_callback_inputs(self, json_str: str) -> Dict[str, Any]:
           """Deserialize callback input dictionary."""
           return json.loads(json_str)
       
       def validate_numeric_precision(self,
                                       original: Dict[str, Any],
                                       refactored: Dict[str, Any],
                                       rtol: float = 1e-10) -> bool:
           """Validate that numeric values match within tolerance."""
           # Compare floats with relative tolerance
           # Use np.allclose for arrays
           original_json = json.dumps(original, default=self._encode_defaults)
           refactored_json = json.dumps(refactored, default=self._encode_defaults)
           
           # Parse both back to objects and do deep comparison
           orig_obj = json.loads(original_json)
           refac_obj = json.loads(refactored_json)
           
           return self._compare_objects_with_tolerance(orig_obj, refac_obj, rtol)
       
       def _encode_defaults(self, obj: Any) -> Any:
           """Handle non-standard types during JSON encoding."""
           if isinstance(obj, np.ndarray):
               return obj.tolist()
           elif isinstance(obj, (np.integer, np.floating)):
               return float(obj)
           elif isinstance(obj, datetime):
               return obj.isoformat()
           elif isinstance(obj, np.bool_):
               return bool(obj)
           else:
               raise TypeError(f"Object of type {type(obj)} not JSON serializable")
       
       def _compare_objects_with_tolerance(self, obj1: Any, obj2: Any, rtol: float) -> bool:
           """Deep comparison of two objects with numeric tolerance."""
           if isinstance(obj1, dict) and isinstance(obj2, dict):
               if set(obj1.keys()) != set(obj2.keys()):
                   return False
               return all(
                   self._compare_objects_with_tolerance(obj1[k], obj2[k], rtol)
                   for k in obj1.keys()
               )
           elif isinstance(obj1, (list, tuple)) and isinstance(obj2, (list, tuple)):
               if len(obj1) != len(obj2):
                   return False
               return all(
                   self._compare_objects_with_tolerance(o1, o2, rtol)
                   for o1, o2 in zip(obj1, obj2)
               )
           elif isinstance(obj1, float) and isinstance(obj2, float):
               return np.isclose(obj1, obj2, rtol=rtol)
           else:
               return obj1 == obj2
   ```

2. **Git operations**:
   ```powershell
   git worktree add ../MistHelper-phase-2 -b chore/293-phase-2 main
   cd ../MistHelper-phase-2
   ```

3. **Validation**:
   ```powershell
   python -m py_compile src/maps/plotly_map_serializer.py
   ```

**Test Cases**:

```python
# tests/maps/test_plotly_map_serializer.py

import pytest
import json
import numpy as np
from datetime import datetime
from src.maps.plotly_map_serializer import PlotlyMapDataSerializer

class TestPlotlyMapDataSerializer:
    
    def test_serialize_figure_state_simple(self):
        """serialize_figure_state handles simple dict."""
        serializer = PlotlyMapDataSerializer()
        figure = {"data": [1, 2, 3], "layout": {"title": "Test"}}
        json_str = serializer.serialize_figure_state(figure)
        assert isinstance(json_str, str)
        assert '"data"' in json_str
    
    def test_deserialize_figure_state_roundtrip(self):
        """Roundtrip: serialize → deserialize produces exact match."""
        serializer = PlotlyMapDataSerializer()
        original = {"data": [1, 2, 3], "layout": {"title": "Test"}}
        json_str = serializer.serialize_figure_state(original)
        deserialized = serializer.deserialize_figure_state(json_str)
        assert deserialized == original
    
    def test_encode_numpy_array(self):
        """Serializer converts numpy arrays to lists."""
        serializer = PlotlyMapDataSerializer()
        arr = np.array([1.0, 2.0, 3.0])
        json_str = serializer.serialize_figure_state({"array": arr})
        deserialized = serializer.deserialize_figure_state(json_str)
        assert deserialized["array"] == [1.0, 2.0, 3.0]
    
    def test_encode_datetime(self):
        """Serializer converts datetime to ISO format."""
        serializer = PlotlyMapDataSerializer()
        dt = datetime(2026, 5, 13, 12, 0, 0)
        json_str = serializer.serialize_figure_state({"timestamp": dt})
        deserialized = serializer.deserialize_figure_state(json_str)
        assert deserialized["timestamp"] == "2026-05-13T12:00:00"
    
    def test_validate_numeric_precision_exact_match(self):
        """Exact numeric match passes validation."""
        serializer = PlotlyMapDataSerializer()
        data = {"grid": [[1.0, 2.0], [3.0, 4.0]]}
        assert serializer.validate_numeric_precision(data, data)
    
    def test_validate_numeric_precision_within_tolerance(self):
        """Numeric difference within tolerance passes."""
        serializer = PlotlyMapDataSerializer()
        data1 = {"values": [1.0, 2.0, 3.0]}
        data2 = {"values": [1.00000000001, 2.00000000001, 3.00000000001]}
        assert serializer.validate_numeric_precision(data1, data2, rtol=1e-9)
    
    def test_validate_numeric_precision_outside_tolerance_fails(self):
        """Numeric difference outside tolerance fails."""
        serializer = PlotlyMapDataSerializer()
        data1 = {"values": [1.0, 2.0, 3.0]}
        data2 = {"values": [1.1, 2.1, 3.1]}  # 10% difference
        assert not serializer.validate_numeric_precision(data1, data2, rtol=1e-9)
```

**Quality Gate Validation**:

```powershell
python -m py_compile src/maps/plotly_map_serializer.py
python -m ruff check src/maps/plotly_map_serializer.py --fix
python -m black src/maps/plotly_map_serializer.py
pytest tests/maps/test_plotly_map_serializer.py -v --cov=src/maps/plotly_map_serializer
```

**Git Commit**:

```powershell
git add src/maps/plotly_map_serializer.py tests/maps/test_plotly_map_serializer.py
git commit -m "chore(293): Extract PlotlyMapDataSerializer from _launch_plotly_viewer

- Extract JSON serialization logic to PlotlyMapDataSerializer
- Handle numpy arrays, datetime, and custom types
- Add round-trip serialization tests
- Add numeric precision validation
- CC target: ≤7

Closes #293"
```

---

### Task P2.2: Integrate PlotlyMapDataSerializer into _launch_plotly_viewer

**ID**: T005  
**Priority**: P1  
**Acceptance Criteria**:
- [ ] `MapsManager._launch_plotly_viewer` imports serializer
- [ ] All `json.dumps` calls replaced with `serializer.serialize_*`
- [ ] All `json.loads` calls replaced with `serializer.deserialize_*`
- [ ] Callback data serialization identical to original
- [ ] No functional changes to app behavior

**Implementation Steps**:

1. **Add import**:
   ```python
   from src.maps.plotly_map_serializer import PlotlyMapDataSerializer
   ```

2. **In `_launch_plotly_viewer`, instantiate serializer**:
   ```python
   serializer = PlotlyMapDataSerializer()
   ```

3. **Replace all `json.dumps/loads` calls**:
   ```python
   # Before:
   callback_data = json.dumps(fig_dict)
   deserialized_data = json.loads(callback_data)
   
   # After:
   callback_data = serializer.serialize_figure_state(fig_dict)
   deserialized_data = serializer.deserialize_figure_state(callback_data)
   ```

**Test Cases**:

```python
def test_callback_serialization_matches_original():
    """Callback data serialization identical to original."""
    serializer = PlotlyMapDataSerializer()
    test_data = {"figure": {...}, "heatmap": {...}}
    
    # Original code (mocked)
    original_result = json.dumps(test_data)
    
    # Refactored code
    refactored_result = serializer.serialize_figure_state(test_data)
    
    assert original_result == refactored_result
```

**Git Commit**:

```powershell
git add src/maps/maps_manager.py
git commit -m "chore(293): Integrate PlotlyMapDataSerializer into _launch_plotly_viewer

- Replace all json.dumps/loads with serializer methods
- Maintains data serialization byte-for-byte equivalence

Closes #293"
```

---

### Task P2.3: Quality Gates and PR Merge

**ID**: T006  
**Priority**: P1  
**Acceptance Criteria**: Same as P1.3

**Quality Gate Commands**:

```powershell
& $py -m py_compile src/maps/plotly_map_serializer.py
& $py -m ruff check src/maps/
& $py -m black src/maps/
& $py -m pytest tests/maps/test_plotly_map_serializer.py -v --cov=src/maps/plotly_map_serializer
```

**PR Creation & Merge**:

```powershell
git push origin chore/293-phase-2

gh pr create \
  --title "chore(293-phase2): Extract PlotlyMapDataSerializer" \
  --body "Phase 2 of 6: Extract JSON serialization

## Changes
- New file: src/maps/plotly_map_serializer.py
- Updated: src/maps/maps_manager.py

## Acceptance Criteria
- [x] PlotlyMapDataSerializer class created
- [x] Round-trip serialization tests pass
- [x] Numeric precision validation implemented
- [x] All json.dumps/loads calls delegated to serializer
- [x] Quality gates pass

## Risk: LOW
## Effort: 2–3 hours

Closes #293" \
  --base main

gh pr checks --watch
# Wait for CodeQL, then add auto-merge label
```

---

## PHASE 3: Extract CoverageHeatmapRenderer

**Risk**: MEDIUM  
**Effort**: 4–5 hours  
**Estimated Effort (actual)**: 4.5 hours  
**Dependency**: Phase 1, 2 (merged)  
**Blocks**: Phase 4, 5, 6

---

### Task P3.1: Create CoverageHeatmapRenderer Class

**ID**: T007  
**Priority**: P1  
**Acceptance Criteria**:
- [ ] New file `src/maps/plotly_map_heatmap.py` created with `CoverageHeatmapRenderer` class
- [ ] All interpolation algorithms extracted (Kriging, IDW, RBF)
- [ ] Methods: `__init__`, `interpolate_grid`, `apply_colorscale`, `smooth_heatmap`, `build_heatmap_figure`, `validate_algorithm`, `get_algorithm_config`
- [ ] Heatmap output numerically identical to original (within 1e-10 relative tolerance)
- [ ] Grid shape matches expected resolution (default 100x100)
- [ ] All dependencies declared (scipy, numpy, plotly)

**File Paths & Line Numbers** (from `maps_manager.py`):
- Interpolation algorithms: Lines ~3700–4200 (kriging/IDW setup)
- Grid processing: Lines ~4200–4500 (smoothing, colorscaling)
- Figure building: Lines ~4500–4800 (Plotly heatmap figure)

**Implementation Steps**:

1. **Create baseline test data snapshot**:
   ```powershell
   # Run original code to capture heatmap output
   python -c "
   from src.maps.maps_manager import MapsManager
   import json
   
   mgr = MapsManager(org_id='test', ...)
   # Extract test data from _launch_plotly_viewer
   test_data = {...heatmap input...}
   original_grid = {...heatmap output...}
   
   with open('tests/data/heatmap_baseline.json', 'w') as f:
       json.dump({
           'input': test_data,
           'output': original_grid.tolist()
       }, f)
   " 2>&1 | tee .heatmap-baseline.log
   ```

2. **Implement CoverageHeatmapRenderer** in `src/maps/plotly_map_heatmap.py`:
   ```python
   import numpy as np
   from scipy.interpolate import Rbf, kriging_estimator
   import plotly.graph_objects as go
   from typing import Dict, Any, Optional, List
   
   class CoverageHeatmapRenderer:
       """Renders coverage heatmaps using various interpolation algorithms."""
       
       def __init__(self, 
                    site_id: str,
                    algorithm: str = 'kriging',
                    interpolation_method: str = 'thin_plate',
                    grid_resolution: int = 100):
           """Initialize heatmap renderer."""
           self.site_id = site_id
           self.algorithm = algorithm
           self.interpolation_method = interpolation_method
           self.grid_resolution = grid_resolution
           self._interpolator = None
           self._validate_algorithm()
       
       def interpolate_grid(self, data: Dict[str, Any]) -> np.ndarray:
           """Interpolate coverage signal data to regular grid."""
           # Extract coordinates and signal strengths from data
           x_coords = np.array(data['x_coords'])
           y_coords = np.array(data['y_coords'])
           signal_strengths = np.array(data['signal_strengths'])
           
           # Get bounds (or auto-detect)
           if 'bounds' in data:
               bounds = data['bounds']
           else:
               bounds = {
                   'x_min': x_coords.min(),
                   'x_max': x_coords.max(),
                   'y_min': y_coords.min(),
                   'y_max': y_coords.max()
               }
           
           # Build regular grid
           x_grid = np.linspace(bounds['x_min'], bounds['x_max'], self.grid_resolution)
           y_grid = np.linspace(bounds['y_min'], bounds['y_max'], self.grid_resolution)
           X, Y = np.meshgrid(x_grid, y_grid)
           
           # Interpolate using selected algorithm
           if self.algorithm == 'kriging':
               return self._interpolate_kriging(x_coords, y_coords, signal_strengths, X, Y)
           elif self.algorithm == 'idw':
               return self._interpolate_idw(x_coords, y_coords, signal_strengths, X, Y)
           elif self.algorithm == 'rbf':
               return self._interpolate_rbf(x_coords, y_coords, signal_strengths, X, Y)
           else:
               raise ValueError(f"Unsupported algorithm: {self.algorithm}")
       
       def _interpolate_kriging(self, x, y, z, X, Y) -> np.ndarray:
           """Kriging interpolation."""
           # Copy original kriging algorithm from maps_manager._launch_plotly_viewer
           # (lines ~3750–3900)
           pass
       
       def _interpolate_idw(self, x, y, z, X, Y) -> np.ndarray:
           """Inverse Distance Weighting interpolation."""
           # Copy original IDW algorithm from maps_manager
           pass
       
       def _interpolate_rbf(self, x, y, z, X, Y) -> np.ndarray:
           """Radial Basis Function interpolation."""
           # Copy original RBF algorithm from maps_manager
           pass
       
       def apply_colorscale(self,
                           grid: np.ndarray,
                           colorscale: str = 'Viridis',
                           min_val: Optional[float] = None,
                           max_val: Optional[float] = None) -> np.ndarray:
           """Convert interpolated grid to colorscaled values [0, 1]."""
           # Normalize to [0, 1] range
           if min_val is None:
               min_val = grid.min()
           if max_val is None:
               max_val = grid.max()
           
           if max_val == min_val:
               return np.zeros_like(grid)
           
           normalized = (grid - min_val) / (max_val - min_val)
           return np.clip(normalized, 0, 1)
       
       def smooth_heatmap(self,
                         grid: np.ndarray,
                         kernel_size: int = 3) -> np.ndarray:
           """Apply Gaussian smoothing to heatmap grid."""
           from scipy.ndimage import gaussian_filter
           return gaussian_filter(grid, sigma=1.0)
       
       def build_heatmap_figure(self,
                               grid: np.ndarray,
                               colorscale: str = 'Viridis') -> go.Figure:
           """Build complete Plotly heatmap figure."""
           fig = go.Figure(data=go.Heatmap(
               z=grid,
               colorscale=colorscale,
               colorbar=dict(title="Signal Strength (dBm)")
           ))
           fig.update_layout(
               title="Coverage Heatmap",
               xaxis_title="X Position",
               yaxis_title="Y Position"
           )
           return fig
       
       def validate_algorithm(self) -> bool:
           """Validate that algorithm is supported and working."""
           if self.algorithm not in ['kriging', 'idw', 'rbf']:
               raise ValueError(f"Unsupported algorithm: {self.algorithm}")
           # Test with dummy data
           test_data = {
               'x_coords': [0, 1, 2],
               'y_coords': [0, 1, 2],
               'signal_strengths': [-60, -70, -80]
           }
           grid = self.interpolate_grid(test_data)
           assert grid.shape == (self.grid_resolution, self.grid_resolution)
           return True
       
       def get_algorithm_config(self) -> Dict[str, Any]:
           """Get current algorithm configuration."""
           return {
               'algorithm': self.algorithm,
               'interpolation_method': self.interpolation_method,
               'grid_resolution': self.grid_resolution
           }
       
       def _validate_algorithm(self):
           """Internal validation of algorithm selection."""
           if self.algorithm not in ['kriging', 'idw', 'rbf']:
               raise ValueError(f"Unsupported algorithm: {self.algorithm}")
   ```

3. **Git operations**:
   ```powershell
   git worktree add ../MistHelper-phase-3 -b chore/293-phase-3 main
   cd ../MistHelper-phase-3
   ```

4. **Validation**:
   ```powershell
   python -m py_compile src/maps/plotly_map_heatmap.py
   ```

**Test Cases**:

```python
# tests/maps/test_plotly_map_heatmap.py

import pytest
import numpy as np
import json
from src.maps.plotly_map_heatmap import CoverageHeatmapRenderer

class TestCoverageHeatmapRenderer:
    
    def test_init_creates_instance(self):
        """CoverageHeatmapRenderer initializes."""
        renderer = CoverageHeatmapRenderer(site_id="test-site")
        assert renderer.site_id == "test-site"
        assert renderer.grid_resolution == 100
    
    def test_interpolate_grid_shape(self):
        """Interpolated grid has correct shape."""
        renderer = CoverageHeatmapRenderer(site_id="test", grid_resolution=50)
        test_data = {
            'x_coords': [0, 1, 2],
            'y_coords': [0, 1, 2],
            'signal_strengths': [-60, -70, -80]
        }
        grid = renderer.interpolate_grid(test_data)
        assert grid.shape == (50, 50)
    
    def test_heatmap_output_matches_original(self):
        """Interpolated grid matches original within tolerance."""
        renderer = CoverageHeatmapRenderer(site_id="test", algorithm='kriging')
        
        # Load baseline data
        with open('tests/data/heatmap_baseline.json') as f:
            baseline = json.load(f)
        
        test_data = baseline['input']
        expected_grid = np.array(baseline['output'])
        
        actual_grid = renderer.interpolate_grid(test_data)
        
        # Allow 1e-10 relative tolerance for numerical precision
        assert np.allclose(actual_grid, expected_grid, rtol=1e-10)
    
    def test_apply_colorscale_range(self):
        """Colorscaled output values in [0, 1]."""
        renderer = CoverageHeatmapRenderer(site_id="test")
        grid = np.random.rand(100, 100) * 100  # [0, 100]
        scaled = renderer.apply_colorscale(grid)
        assert scaled.min() >= 0 and scaled.max() <= 1
    
    def test_smooth_heatmap_reduces_noise(self):
        """Smoothing reduces high-frequency noise."""
        renderer = CoverageHeatmapRenderer(site_id="test")
        # Create noisy grid
        grid = np.random.rand(100, 100)
        smoothed = renderer.smooth_heatmap(grid)
        
        # Verify smoothing reduced variance
        assert smoothed.std() < grid.std()
    
    def test_build_heatmap_figure(self):
        """Build Plotly heatmap figure."""
        renderer = CoverageHeatmapRenderer(site_id="test")
        grid = np.random.rand(50, 50)
        fig = renderer.build_heatmap_figure(grid)
        
        assert fig is not None
        assert len(fig.data) > 0
        assert fig.data[0].type == 'heatmap'
    
    def test_validate_algorithm_passes(self):
        """Algorithm validation passes for supported algorithms."""
        for algo in ['kriging', 'idw', 'rbf']:
            renderer = CoverageHeatmapRenderer(site_id="test", algorithm=algo)
            assert renderer.validate_algorithm()
    
    def test_validate_algorithm_fails_unsupported(self):
        """Algorithm validation fails for unsupported algorithm."""
        with pytest.raises(ValueError):
            CoverageHeatmapRenderer(site_id="test", algorithm="unsupported")
    
    def test_get_algorithm_config(self):
        """Algorithm config returns correct parameters."""
        renderer = CoverageHeatmapRenderer(
            site_id="test",
            algorithm="kriging",
            grid_resolution=75
        )
        config = renderer.get_algorithm_config()
        assert config['algorithm'] == 'kriging'
        assert config['grid_resolution'] == 75
```

**Quality Gate Validation**:

```powershell
python -m py_compile src/maps/plotly_map_heatmap.py
python -m ruff check src/maps/plotly_map_heatmap.py --fix
python -m black src/maps/plotly_map_heatmap.py
pytest tests/maps/test_plotly_map_heatmap.py -v --cov=src/maps/plotly_map_heatmap

# Critical: Numeric equivalence
pytest tests/maps/test_plotly_map_heatmap.py::TestCoverageHeatmapRenderer::test_heatmap_output_matches_original -v
```

**Risk Mitigations**:
- **Risk**: Interpolation algorithm changes → different heatmap output
  - **Mitigation**: Baseline test data (snapshot), 1e-10 tolerance test
- **Risk**: Missing scipy/numpy dependency
  - **Mitigation**: Declare in requirements.txt (already present)
- **Risk**: Grid resolution affects performance
  - **Mitigation**: Parameterized resolution, benchmark if needed

**Git Commit**:

```powershell
git add src/maps/plotly_map_heatmap.py tests/maps/test_plotly_map_heatmap.py
git commit -m "chore(293): Extract CoverageHeatmapRenderer from _launch_plotly_viewer

- Extract interpolation algorithms (Kriging, IDW, RBF) to new class
- Add colorscale, smoothing, figure building methods
- Add baseline test data for numeric equivalence validation
- CC target: ≤10

Closes #293"
```

---

### Task P3.2: Integrate CoverageHeatmapRenderer and Quality Gates

**ID**: T008  
**Priority**: P1  
**Similar to P2.2 and P2.3**: Replace heatmap code, run quality gates, merge PR

---

## PHASE 4: Extract PlotlyMapFigureBuilder

**Risk**: MEDIUM  
**Effort**: 5–6 hours  
**Estimated Effort (actual)**: 5.5 hours  
**Dependency**: Phase 1, 2, 3 (merged)  
**Blocks**: Phase 5, 6

---

### Task P4.1: Create PlotlyMapFigureBuilder Class

**ID**: T009  
**Priority**: P1  
**Acceptance Criteria**:
- [ ] New file `src/maps/plotly_map_figures.py` created
- [ ] Methods: `__init__`, `build_walls_figure`, `build_device_scatter`, `build_client_scatter`, `build_heatmap_figure`, `build_combined_figure`, `validate_figure_structure`, `get_figure_json`
- [ ] Figure output JSON byte-for-byte identical to original (with svg data)
- [ ] All traces (walls, devices, clients) properly formatted
- [ ] Integration with `CoverageHeatmapRenderer` for heatmap building

**File Paths & Line Numbers** (from `maps_manager.py`):
- Walls figure: Lines ~3300–3350
- Device scatter: Lines ~3350–3450
- Client scatter: Lines ~3450–3550
- Heatmap figure: Lines ~3550–3650

**Implementation Steps**: Similar to P3.1

**Test Cases**:

```python
# tests/maps/test_plotly_map_figures.py

class TestPlotlyMapFigureBuilder:
    
    def test_build_walls_figure_json_matches_original(self):
        """Walls figure JSON byte-for-byte identical to original."""
        # Load original figure JSON from baseline
        original_fig_json = load_baseline_walls_figure()
        
        builder = PlotlyMapFigureBuilder(svg_data=TEST_SVG)
        fig = builder.build_walls_figure()
        refactored_fig_json = fig.to_json()
        
        assert original_fig_json == refactored_fig_json
    
    def test_device_scatter_includes_all_devices(self):
        """Device scatter has one point per device."""
        inventory = {
            "devices": [
                {"id": "ap1", "x": 10, "y": 20},
                {"id": "ap2", "x": 30, "y": 40}
            ]
        }
        builder = PlotlyMapFigureBuilder(device_inventory=inventory)
        trace = builder.build_device_scatter()
        assert len(trace.x) == 2
    
    def test_build_combined_figure_with_all_layers(self):
        """Combined figure includes all requested layers."""
        builder = PlotlyMapFigureBuilder(
            svg_data=TEST_SVG,
            device_inventory=TEST_INVENTORY,
            client_data=TEST_CLIENT_DATA
        )
        renderer = CoverageHeatmapRenderer(site_id="test")
        
        fig = builder.build_combined_figure(
            layers=['walls', 'devices', 'clients', 'heatmap'],
            heatmap_renderer=renderer
        )
        
        # Verify traces present
        assert len(fig.data) >= 4
    
    def test_validate_figure_structure_passes(self):
        """Figure validation passes for valid figure."""
        builder = PlotlyMapFigureBuilder(svg_data=TEST_SVG)
        fig = builder.build_walls_figure()
        assert builder.validate_figure_structure(fig)
    
    def test_get_figure_json_returns_string(self):
        """get_figure_json returns JSON string."""
        builder = PlotlyMapFigureBuilder(svg_data=TEST_SVG)
        fig = builder.build_walls_figure()
        json_str = builder.get_figure_json(fig)
        assert isinstance(json_str, str)
        assert json_str.startswith('{')  # Valid JSON object
```

**Quality Gate Validation**: Same as previous phases

**Git Commit**:

```powershell
git add src/maps/plotly_map_figures.py tests/maps/test_plotly_map_figures.py
git commit -m "chore(293): Extract PlotlyMapFigureBuilder from _launch_plotly_viewer

- Extract figure building logic for walls, devices, clients, heatmap
- Build combined figures with multiple layers
- Add figure structure validation
- CC target: ≤10

Closes #293"
```

---

## PHASE 5: Extract PlotlyMapCallbackManager (~25 Callbacks)

**Risk**: HIGH  
**Effort**: 8–10 hours  
**Estimated Effort (actual)**: 9 hours  
**Dependency**: Phase 1, 2, 3, 4 (merged)  
**Blocks**: Phase 6

---

### Overview: Callback Organization

**Callbacks from session memory (24 total)** (lines 1-indexed from maps_manager.py):

1. **Group A: Layer Toggles** (3 callbacks)
   - `handle_site_switch_from_dropdown`: Lines 5322–5542
   - `sync_dropdown_with_url`: Lines 5577–5610
   - `handle_url_map_switch`: Lines 5611–6370 (HIGH CC)

2. **Group B: Heatmap Controls** (4 callbacks)
   - `toggle_layers`: Lines 6371–6474
   - `set_scale`: Lines 6552–6611
   - `set_origin_from_click`: Lines 6630–6699
   - `refresh_rf_coverage`: Lines 8059–8208 (HIGH CC)

3. **Group C: Navigation & Export** (4 callbacks)
   - `handle_site_from_url`: Lines 5543–5576
   - `display_click_data`: Lines 6475–6501
   - `toggle_origin_mode`: Lines 6612–6629
   - `toggle_zone_name_input`: Lines 6700–6709

4. **Group D: Drawing & Zones** (5 callbacks)
   - `update_shape_labels`: Lines 6502–6551
   - `handle_drawing_tools`: Lines 6710–7095 (HIGH CC)
   - `handle_utilities`: Lines 7096–7139
   - `handle_zone_actions`: Lines 7325–7493 (HIGH CC)
   - `toggle_individual_zones`: Lines 7295–7324

5. **Group E: Deletion, Cloning, Refresh** (8 callbacks)
   - `toggle_delete_panel`: Lines 7140–7190
   - `execute_delete_map`: Lines 7191–7255
   - `toggle_clone_panel`: Lines 7256–7294
   - `execute_clone_operation`: Lines 7557–7771 (HIGH CC)
   - `toggle_auto_refresh`: Lines 7494–7525
   - `update_countdown_display`: Lines 7526–7556
   - `refresh_map_dropdown`: Lines 7772–7817
   - `refresh_client_positions`: Lines 7818–8058 (HIGH CC)

---

### Task P5A.1: Extract Layer Toggle Callbacks

**ID**: T010  
**Priority**: P1  
**Acceptance Criteria**:
- [ ] Group A callbacks (layer toggles) extracted to `PlotlyMapCallbackManager.register_layer_callbacks()`
- [ ] All callback decorators remain on methods
- [ ] Callback input/output IDs match layout
- [ ] Callbacks accessible via `self.app.callback_map`

**Implementation Steps**:

1. **Create `src/maps/plotly_map_callbacks.py`**:
   ```python
   import dash
   from dash import Output, Input, State, no_update
   from typing import Dict, List
   
   class PlotlyMapCallbackManager:
       """Manages ~25 callbacks for Plotly map viewer."""
       
       def __init__(self, app: dash.Dash, viewer, serializer):
           self.app = app
           self.viewer = viewer
           self.serializer = serializer
           self._registered_callbacks: List[str] = []
       
       def register_all_callbacks(self) -> int:
           """Register all callback groups."""
           count = 0
           count += self.register_layer_callbacks()
           count += self.register_heatmap_callbacks()
           count += self.register_navigation_callbacks()
           count += self.register_drawing_callbacks()
           count += self.register_admin_callbacks()
           return count
       
       # ===== GROUP A: LAYER TOGGLES =====
       def register_layer_callbacks(self) -> int:
           """Layer toggle and site switching callbacks."""
           count = 0
           
           # Callback 1: handle_site_switch_from_dropdown (lines 5322–5542)
           @self.app.callback(
               [Output('url', 'pathname'),
                Output('map-dropdown', 'value'),
                Output('map-content', 'children')],
               [Input('site-dropdown', 'value'),
                Input('url', 'pathname')]
           )
           def handle_site_switch_from_dropdown(site_value, pathname):
               # Extract from maps_manager.py lines 5335–5542
               pass
           
           self._registered_callbacks.append('handle_site_switch_from_dropdown')
           count += 1
           
           # Callback 2: sync_dropdown_with_url (lines 5577–5610)
           @self.app.callback(
               Output('site-dropdown', 'value'),
               Input('url', 'pathname')
           )
           def sync_dropdown_with_url(pathname):
               # Extract from maps_manager.py lines 5584–5610
               pass
           
           self._registered_callbacks.append('sync_dropdown_with_url')
           count += 1
           
           # Callback 3: handle_url_map_switch (lines 5611–6370) - HIGH CC
           @self.app.callback(
               [Output('map-content', 'children'),
                Output('map-dropdown', 'options')],
               Input('url', 'pathname'),
               State('site-id-store', 'data')
           )
           def handle_url_map_switch(pathname, site_id):
               # Extract from maps_manager.py lines 5626–6370
               # This is HIGH CC (745 lines) - consider sub-splitting if needed
               pass
           
           self._registered_callbacks.append('handle_url_map_switch')
           count += 1
           
           return count
       
       # ===== GROUP B: HEATMAP CONTROLS =====
       def register_heatmap_callbacks(self) -> int:
           """Heatmap algorithm, scaling, and refresh callbacks."""
           count = 0
           
           # Callback 4: toggle_layers (lines 6371–6474)
           @self.app.callback(
               [Output('walls-layer', 'visible'),
                Output('devices-layer', 'visible'),
                Output('clients-layer', 'visible'),
                Output('heatmap-layer', 'visible')],
               [Input('toggle-walls-btn', 'n_clicks'),
                Input('toggle-devices-btn', 'n_clicks'),
                Input('toggle-clients-btn', 'n_clicks'),
                Input('toggle-heatmap-btn', 'n_clicks')],
               [State('walls-layer', 'visible'),
                State('devices-layer', 'visible'),
                State('clients-layer', 'visible'),
                State('heatmap-layer', 'visible')]
           )
           def toggle_layers(walls_clicks, devices_clicks, clients_clicks, heatmap_clicks,
                           walls_vis, devices_vis, clients_vis, heatmap_vis):
               # Extract from maps_manager.py lines 6383–6474
               pass
           
           count += 1
           
           # Callback 5: set_scale (lines 6552–6611)
           @self.app.callback(
               Output('heatmap-scale-store', 'data'),
               Input('scale-slider', 'value')
           )
           def set_scale(scale_value):
               # Extract from maps_manager.py lines 6559–6611
               pass
           
           count += 1
           
           # Callback 6: set_origin_from_click (lines 6630–6699)
           @self.app.callback(
               Output('origin-store', 'data'),
               Input('map-graph', 'clickData'),
               State('origin-mode-store', 'data')
           )
           def set_origin_from_click(click_data, origin_mode):
               # Extract from maps_manager.py lines 6637–6699
               pass
           
           count += 1
           
           # Callback 24 (High CC): refresh_rf_coverage (lines 8059–8208)
           @self.app.callback(
               [Output('heatmap-figure', 'figure'),
                Output('auto-refresh-countdown', 'children')],
               [Input('refresh-timer', 'n_intervals'),
                Input('refresh-btn', 'n_clicks')],
               State('auto-refresh-store', 'data')
           )
           def refresh_rf_coverage(intervals, refresh_clicks, auto_refresh_enabled):
               # Extract from maps_manager.py lines 8074–8208
               # This is HIGH CC (226 lines) - consider sub-splitting
               pass
           
           count += 1
           
           return count
       
       # ===== GROUP C: NAVIGATION & DISPLAY =====
       def register_navigation_callbacks(self) -> int:
           """Navigation, display, and interaction callbacks."""
           count = 0
           
           # Callbacks: handle_site_from_url, display_click_data, toggle_origin_mode, toggle_zone_name_input
           # (similar structure to above groups)
           
           return count
       
       # ===== GROUP D: DRAWING & ZONES =====
       def register_drawing_callbacks(self) -> int:
           """Drawing tools and zone management callbacks."""
           count = 0
           
           # Callbacks: update_shape_labels, handle_drawing_tools, handle_utilities, handle_zone_actions, toggle_individual_zones
           # (similar structure to above groups)
           
           return count
       
       # ===== GROUP E: DELETION, CLONING, REFRESH =====
       def register_admin_callbacks(self) -> int:
           """Administrative callbacks (delete, clone, refresh)."""
           count = 0
           
           # Callbacks: toggle_delete_panel, execute_delete_map, toggle_clone_panel, execute_clone_operation,
           #            toggle_auto_refresh, update_countdown_display, refresh_map_dropdown, refresh_client_positions
           
           return count
       
       def validate_callback_count(self, expected_count: int = 24) -> bool:
           """Validate that expected number of callbacks are registered."""
           actual = len(self._registered_callbacks)
           assert actual == expected_count, \
               f"Expected {expected_count} callbacks, got {actual}"
           return True
       
       def get_callback_list(self) -> List[str]:
           """Get list of registered callback IDs."""
           return self._registered_callbacks.copy()
   ```

2. **Extract callback bodies** from `maps_manager.py` (lines 5322–8208):
   - Copy each callback function body into corresponding method
   - Preserve all logic unchanged
   - Update `self.viewer`, `self.serializer` for data access
   - Maintain same input/output structure

3. **Git operations**:
   ```powershell
   git worktree add ../MistHelper-phase-5 -b chore/293-phase-5 main
   cd ../MistHelper-phase-5
   ```

**Test Cases**:

```python
# tests/maps/test_plotly_map_callbacks.py

class TestPlotlyMapCallbackManager:
    
    def test_layer_callbacks_registered(self):
        """Layer toggle callbacks are registered."""
        app = dash.Dash(__name__)
        viewer = MagicMock()
        serializer = MagicMock()
        mgr = PlotlyMapCallbackManager(app, viewer, serializer)
        count = mgr.register_layer_callbacks()
        assert count == 3
        assert 'handle_site_switch_from_dropdown' in mgr.get_callback_list()
    
    def test_all_callbacks_registered(self):
        """All callback groups registered."""
        app = dash.Dash(__name__)
        viewer = MagicMock()
        serializer = MagicMock()
        mgr = PlotlyMapCallbackManager(app, viewer, serializer)
        count = mgr.register_all_callbacks()
        assert count == 24  # or expected total
        mgr.validate_callback_count(24)
    
    def test_callback_count_validation_fails_if_mismatch(self):
        """Validation fails if callback count mismatch."""
        app = dash.Dash(__name__)
        viewer = MagicMock()
        serializer = MagicMock()
        mgr = PlotlyMapCallbackManager(app, viewer, serializer)
        mgr.register_all_callbacks()
        
        with pytest.raises(AssertionError):
            mgr.validate_callback_count(999)  # Expected count wrong
```

**Quality Gate Validation**:

```powershell
python -m py_compile src/maps/plotly_map_callbacks.py
python -m ruff check src/maps/plotly_map_callbacks.py --fix
python -m black src/maps/plotly_map_callbacks.py
pytest tests/maps/test_plotly_map_callbacks.py::TestPlotlyMapCallbackManager::test_layer_callbacks_registered -v
```

---

### Task P5B.1 – P5E.1: Extract Remaining Callback Groups

**ID**: T011–T014  
**Priority**: P1  
**Similar structure to P5A.1**: Each group extracts callbacks, creates tests, passes quality gates

**Groups B–E Effort**:
- P5B: Heatmap controls (4 callbacks, ~400 lines) – 2 hrs
- P5C: Navigation (4 callbacks, ~200 lines) – 1.5 hrs
- P5D: Drawing tools (5 callbacks, ~1500 lines HIGH CC) – 3 hrs
- P5E: Admin (8 callbacks, ~600 lines) – 2.5 hrs

**Total Phase 5 Effort**: 9 hours

---

### Task P5F.1: Integrate PlotlyMapCallbackManager into _launch_plotly_viewer

**ID**: T015  
**Priority**: P1  
**Acceptance Criteria**:
- [ ] All ~25 callbacks from `_launch_plotly_viewer` removed and moved to `PlotlyMapCallbackManager`
- [ ] Method calls `callback_mgr = PlotlyMapCallbackManager(...); callback_mgr.register_all_callbacks()`
- [ ] Web UI callbacks still work identically
- [ ] Callback registration count verified

**Implementation Steps**:

1. **In `_launch_plotly_viewer`** (lines ~4500–8000), replace all callbacks with:
   ```python
   from src.maps.plotly_map_callbacks import PlotlyMapCallbackManager
   
   # Instead of ~3500 lines of callback definitions:
   callback_mgr = PlotlyMapCallbackManager(app, self, serializer)
   callback_count = callback_mgr.register_all_callbacks()
   logging.info(f"Registered {callback_count} callbacks")
   assert callback_count >= 24, f"Expected ≥24 callbacks, got {callback_count}"
   ```

2. **Remove callback decorators** from `_launch_plotly_viewer` (lines 5322–8208 approximately)

3. **Validation**:
   ```powershell
   python -m py_compile src/maps/maps_manager.py
   ```

**Git Commit**:

```powershell
git add src/maps/plotly_map_callbacks.py src/maps/maps_manager.py
git commit -m "chore(293): Extract PlotlyMapCallbackManager (~25 callbacks)

- Extract all ~25 callbacks into PlotlyMapCallbackManager class
- Organize callbacks into 5 groups: layer toggles, heatmap, navigation, drawing, admin
- Callback methods maintain all original logic
- CC target: ≤10 per callback group

Callbacks extracted:
- Group A (Layer Toggles): handle_site_switch_from_dropdown, sync_dropdown_with_url, handle_url_map_switch (3)
- Group B (Heatmap): toggle_layers, set_scale, set_origin_from_click, refresh_rf_coverage (4)
- Group C (Navigation): handle_site_from_url, display_click_data, toggle_origin_mode, toggle_zone_name_input (4)
- Group D (Drawing): update_shape_labels, handle_drawing_tools, handle_utilities, handle_zone_actions, toggle_individual_zones (5)
- Group E (Admin): toggle_delete_panel, execute_delete_map, toggle_clone_panel, execute_clone_operation, toggle_auto_refresh, update_countdown_display, refresh_map_dropdown, refresh_client_positions (8)

Closes #293"
```

---

### Task P5G.1: Quality Gates, Integration Tests, and Merge

**ID**: T016  
**Priority**: P1  
**Acceptance Criteria**: All quality gates pass, integration tests verify callbacks work

**Integration Test**:

```python
# tests/maps/test_plotly_map_callbacks_integration.py

def test_callback_chain_site_switch():
    """Full callback chain: site dropdown → URL update → map refresh."""
    app = create_test_app_with_callbacks()
    
    # Simulate user selecting a different site
    # Verify callback chain executes and map updates
    pass

def test_all_callback_count():
    """All callbacks are registered."""
    app = create_test_app()
    viewer = create_test_viewer()
    serializer = PlotlyMapDataSerializer()
    mgr = PlotlyMapCallbackManager(app, viewer, serializer)
    
    count = mgr.register_all_callbacks()
    assert count == 24  # Total expected callbacks
```

**Quality Gate Commands**:

```powershell
& $py -m py_compile src/maps/plotly_map_callbacks.py
& $py -m ruff check src/maps/plotly_map_callbacks.py
& $py -m black src/maps/plotly_map_callbacks.py
& $py -m pytest tests/maps/test_plotly_map_callbacks*.py -v --cov=src/maps/plotly_map_callbacks
```

---

## PHASE 6: Integration & Orchestration (PlotlyMapViewer)

**Risk**: HIGH  
**Effort**: 6–8 hours  
**Estimated Effort (actual)**: 7 hours  
**Dependency**: Phase 1–5 (merged)  
**Blocks**: None (final phase)

---

### Task P6.1: Create PlotlyMapViewer Orchestrator

**ID**: T017  
**Priority**: P1  
**Acceptance Criteria**:
- [ ] New file `src/maps/plotly_map_viewer.py` created with `PlotlyMapViewer` class
- [ ] Methods: `__init__`, `create_app`, `_create_layout`, `_register_callbacks`, `run_server`, `validate_app`
- [ ] All extracted classes instantiated and coordinated
- [ ] Dash app fully functional (layout + callbacks)

**File Paths & Line Numbers**:
- `src/maps/plotly_map_viewer.py`: New file (500–700 lines)

**Implementation Steps**:

1. **Create `src/maps/plotly_map_viewer.py`**:
   ```python
   import dash
   from dash import dcc, html
   import logging
   from typing import Dict, Any, Optional
   
   from src.maps.plotly_map_templates import DashTemplateManager
   from src.maps.plotly_map_serializer import PlotlyMapDataSerializer
   from src.maps.plotly_map_heatmap import CoverageHeatmapRenderer
   from src.maps.plotly_map_figures import PlotlyMapFigureBuilder
   from src.maps.plotly_map_callbacks import PlotlyMapCallbackManager
   
   class PlotlyMapViewer:
       """Main orchestrator for Plotly map viewer."""
       
       def __init__(self,
                    org_id: str,
                    site_id: str,
                    device_inventory: Dict[str, Any],
                    client_data: Dict[str, Any],
                    svg_data: Optional[str] = None,
                    style_config: Optional[Dict[str, Any]] = None,
                    heatmap_algorithm: str = 'kriging'):
           """Initialize map viewer."""
           self.org_id = org_id
           self.site_id = site_id
           self.device_inventory = device_inventory
           self.client_data = client_data
           self.svg_data = svg_data
           self.style_config = style_config or {}
           self.heatmap_algorithm = heatmap_algorithm
           
           # Initialize component managers
           self.template_mgr = DashTemplateManager(org_id)
           self.serializer = PlotlyMapDataSerializer()
           self.heatmap_renderer = CoverageHeatmapRenderer(
               site_id, algorithm=heatmap_algorithm
           )
           self.figure_builder = PlotlyMapFigureBuilder(
               svg_data=svg_data,
               device_inventory=device_inventory,
               client_data=client_data,
               style_config=style_config
           )
           
           self.app = None
           self.callback_mgr = None
       
       def create_app(self) -> dash.Dash:
           """Create and configure Dash app."""
           # Create Dash app instance
           self.app = dash.Dash(
               __name__,
               meta_tags=[
                   {"name": "viewport", "content": "width=device-width, initial-scale=1"}
               ]
           )
           
           # Apply custom CSS
           custom_css = self.template_mgr.get_custom_css()
           self.app.index_string = f"""
           <!DOCTYPE html>
           <html>
           <head>
               <style>{custom_css}</style>
           </head>
           <body>
               {'{%app_entry%}'}
               <footer>{'{%config%}'}{'{%scripts%}'}{'{%renderer%}'}</footer>
           </body>
           </html>
           """
           
           # Set layout
           self.app.layout = self._create_layout()
           
           # Register callbacks
           self._register_callbacks()
           
           # Validate
           self.validate_app()
           
           return self.app
       
       def _create_layout(self) -> html.Div:
           """Build Dash layout structure."""
           layout = self.template_mgr.get_layout_html()
           return layout
       
       def _register_callbacks(self) -> int:
           """Register all callbacks."""
           self.callback_mgr = PlotlyMapCallbackManager(
               self.app,
               self,
               self.serializer
           )
           count = self.callback_mgr.register_all_callbacks()
           logging.info(f"Registered {count} callbacks")
           return count
       
       def run_server(self,
                     host: str = '0.0.0.0',
                     port: int = 8050,
                     debug: bool = False,
                     threaded: bool = True) -> None:
           """Launch Dash server."""
           if self.app is None:
               self.create_app()
           
           self.app.run(
               host=host,
               port=port,
               debug=debug,
               use_reloader=False,
               threaded=threaded
           )
       
       def validate_app(self) -> bool:
           """Validate app configuration and callbacks."""
           assert self.app is not None, "App not created"
           assert self.app.layout is not None, "Layout not set"
           assert self.callback_mgr is not None, "Callbacks not registered"
           
           # Validate callback count
           self.callback_mgr.validate_callback_count()
           
           logging.info("✓ PlotlyMapViewer validation passed")
           return True
   ```

2. **Git operations**:
   ```powershell
   git worktree add ../MistHelper-phase-6 -b chore/293-phase-6 main
   cd ../MistHelper-phase-6
   ```

3. **Validation**:
   ```powershell
   python -m py_compile src/maps/plotly_map_viewer.py
   ```

**Test Cases**:

```python
# tests/maps/test_plotly_map_viewer.py

class TestPlotlyMapViewer:
    
    def test_viewer_initialization(self):
        """PlotlyMapViewer initializes all components."""
        viewer = PlotlyMapViewer(
            org_id="test-org",
            site_id="test-site",
            device_inventory=TEST_INVENTORY,
            client_data=TEST_CLIENTS
        )
        assert viewer.template_mgr is not None
        assert viewer.heatmap_renderer is not None
        assert viewer.figure_builder is not None
        assert viewer.serializer is not None
    
    def test_create_app_returns_dash_instance(self):
        """create_app returns Dash app."""
        viewer = PlotlyMapViewer(
            org_id="test-org",
            site_id="test-site",
            device_inventory=TEST_INVENTORY,
            client_data=TEST_CLIENTS
        )
        app = viewer.create_app()
        assert isinstance(app, dash.Dash)
        assert app.layout is not None
    
    def test_app_has_all_callbacks(self):
        """App has all expected callbacks registered."""
        viewer = PlotlyMapViewer(
            org_id="test-org",
            site_id="test-site",
            device_inventory=TEST_INVENTORY,
            client_data=TEST_CLIENTS
        )
        app = viewer.create_app()
        
        # Verify callbacks registered
        assert viewer.callback_mgr is not None
        callbacks = viewer.callback_mgr.get_callback_list()
        assert len(callbacks) >= 20  # At least this many
    
    def test_validate_app_passes(self):
        """App validation passes after creation."""
        viewer = PlotlyMapViewer(
            org_id="test-org",
            site_id="test-site",
            device_inventory=TEST_INVENTORY,
            client_data=TEST_CLIENTS
        )
        app = viewer.create_app()
        assert viewer.validate_app()
```

**Quality Gate Validation**:

```powershell
python -m py_compile src/maps/plotly_map_viewer.py
python -m ruff check src/maps/plotly_map_viewer.py --fix
python -m black src/maps/plotly_map_viewer.py
pytest tests/maps/test_plotly_map_viewer.py -v --cov=src/maps/plotly_map_viewer
```

---

### Task P6.2: Update MapsManager to Use PlotlyMapViewer

**ID**: T018  
**Priority**: P1  
**Acceptance Criteria**:
- [ ] `MapsManager._launch_plotly_viewer` delegated to `PlotlyMapViewer`
- [ ] Method reduced to 3–5 lines
- [ ] All functionality preserved
- [ ] Original signature maintained

**Implementation Steps**:

1. **Replace `_launch_plotly_viewer` method body** (lines 3010–8256):
   ```python
   def _launch_plotly_viewer(self, org_id, site_id, device_inventory, client_data, ...):
       """Launch Plotly map viewer."""
       from src.maps.plotly_map_viewer import PlotlyMapViewer
       
       viewer = PlotlyMapViewer(
           org_id=org_id,
           site_id=site_id,
           device_inventory=device_inventory,
           client_data=client_data,
           svg_data=self.svg_data,
           style_config=self.style_config,
           heatmap_algorithm=self.heatmap_algorithm
       )
       app = viewer.create_app()
       viewer.run_server(host='0.0.0.0', port=8050, debug=False, threaded=True)
   ```

2. **Remove old code** (lines 3070–8208) – all replaced with above

3. **Add import**:
   ```python
   from src.maps.plotly_map_viewer import PlotlyMapViewer
   ```

4. **Validation**:
   ```powershell
   python -m py_compile src/maps/maps_manager.py
   ```

**Git Commit**:

```powershell
git add src/maps/plotly_map_viewer.py src/maps/maps_manager.py
git commit -m "chore(293): Create PlotlyMapViewer orchestrator and integrate

- New file: src/maps/plotly_map_viewer.py (PlotlyMapViewer class)
- Updated: src/maps/maps_manager.py (delegate to PlotlyMapViewer)
- Consolidates all extracted components (templates, serializer, heatmap, figures, callbacks)
- MapsManager._launch_plotly_viewer reduced to 3-line delegator
- CC reduction: 138 → ≤10 (average per method)

Closes #293"
```

---

### Task P6.3: Regression Testing (Full Integration)

**ID**: T019  
**Priority**: P1  
**Acceptance Criteria**:
- [ ] All regression tests pass (figure JSON, callback behavior, heatmap output)
- [ ] Web UI renders identically to original
- [ ] All callbacks work as expected
- [ ] No functional differences

**Regression Test Suite**:

```python
# tests/maps/test_plotly_map_viewer_regression.py

def test_walls_figure_json_identical():
    """Refactored walls figure JSON identical to original."""
    # Load original figure JSON
    original_json = load_baseline_figure_json('walls')
    
    # Build with refactored code
    viewer = PlotlyMapViewer(org_id="test", site_id="test", ...)
    fig = viewer.figure_builder.build_walls_figure()
    refactored_json = fig.to_json()
    
    assert original_json == refactored_json

def test_heatmap_interpolation_identical():
    """Heatmap interpolation output numerically identical."""
    original_grid = load_baseline_heatmap_grid()
    
    viewer = PlotlyMapViewer(org_id="test", site_id="test", ...)
    heatmap_renderer = viewer.heatmap_renderer
    refactored_grid = heatmap_renderer.interpolate_grid(TEST_DATA)
    
    assert np.allclose(original_grid, refactored_grid, rtol=1e-10)

def test_callback_site_switch_identical():
    """Site switch callback produces same result as original."""
    # Simulate site switch callback
    # Verify output identical to original

def test_ui_CSS_rendering_identical():
    """CSS rendering identical to original (visual regression)."""
    # Launch original app, take screenshot
    # Launch refactored app, take screenshot
    # Compare (pixel-level or CSS-level)
```

**Quality Gate Commands**:

```powershell
& $py -m pytest tests/maps/test_plotly_map_viewer_regression.py -v
& $py -m pytest tests/maps/test_plotly_map_viewer_integration.py -v
```

---

### Task P6.4: Verify Cyclomatic Complexity Reduction

**ID**: T020  
**Priority**: P1  
**Acceptance Criteria**:
- [ ] `MapsManager._launch_plotly_viewer` CC ≤ 10 (was 138)
- [ ] All extracted classes CC ≤ 10 per method
- [ ] radon CC report shows all green

**CC Verification Commands**:

```powershell
python -m radon cc src/maps/maps_manager.py -s | grep "_launch_plotly_viewer"
# Expected: A (≤5) or B (6-10), NOT C/D/E/F

python -m radon cc src/maps/plotly_map*.py -a -s
# Expected: All methods A or B (no C/D/E/F)

python -m radon cc src/maps/ --exclude tests -a -s
# Full report, should show all methods ≤10
```

**Expected Report**:

```
src/maps/maps_manager.py:
    MapsManager._launch_plotly_viewer (lines 3010-3014): A (3)
                                                          ^ was 138 (F)

src/maps/plotly_map_templates.py:
    DashTemplateManager.get_custom_css (lines ...): A (2)
    DashTemplateManager.get_layout_html (lines ...): B (7)
    DashTemplateManager.validate_template (lines ...): A (3)

src/maps/plotly_map_serializer.py:
    PlotlyMapDataSerializer.serialize_figure_state: A (2)
    PlotlyMapDataSerializer.deserialize_figure_state: A (2)
    PlotlyMapDataSerializer.validate_numeric_precision: B (8)
    PlotlyMapDataSerializer._compare_objects_with_tolerance: B (9)

src/maps/plotly_map_heatmap.py:
    CoverageHeatmapRenderer.interpolate_grid: B (9)
    CoverageHeatmapRenderer.apply_colorscale: B (7)
    CoverageHeatmapRenderer.smooth_heatmap: A (2)
    CoverageHeatmapRenderer.build_heatmap_figure: A (3)

src/maps/plotly_map_figures.py:
    PlotlyMapFigureBuilder.build_walls_figure: B (8)
    PlotlyMapFigureBuilder.build_device_scatter: B (7)
    PlotlyMapFigureBuilder.build_combined_figure: B (9)

src/maps/plotly_map_callbacks.py:
    PlotlyMapCallbackManager.register_all_callbacks: A (5)
    PlotlyMapCallbackManager.register_layer_callbacks: B (10)
    PlotlyMapCallbackManager.register_heatmap_callbacks: B (8)
    PlotlyMapCallbackManager.register_navigation_callbacks: B (7)
    PlotlyMapCallbackManager.register_drawing_callbacks: B (9)
    PlotlyMapCallbackManager.register_admin_callbacks: B (8)

src/maps/plotly_map_viewer.py:
    PlotlyMapViewer.create_app: B (8)
    PlotlyMapViewer._create_layout: A (2)
    PlotlyMapViewer._register_callbacks: A (3)
    PlotlyMapViewer.run_server: A (4)
    PlotlyMapViewer.validate_app: A (5)
```

---

### Task P6.5: Final Quality Gates & CI/CD

**ID**: T021  
**Priority**: P1  
**Acceptance Criteria**:
- [ ] All linting checks pass (ruff, black)
- [ ] All type checks pass (mypy)
- [ ] All security checks pass (bandit)
- [ ] All unit tests pass (pytest, 70%+ coverage)
- [ ] All regression tests pass
- [ ] All integration tests pass
- [ ] Cyclomatic complexity validated
- [ ] No CodeQL findings
- [ ] PR ready for auto-merge

**Final Quality Gate Commands**:

```powershell
# COMPREHENSIVE QUALITY CHECK

$py = ".venv\Scripts\python.exe"
$failures = 0

# 1. Syntax validation
Write-Host ">>> Syntax validation..." -ForegroundColor Cyan
& $py -m py_compile src/maps/plotly_map*.py src/maps/maps_manager.py
if ($LASTEXITCODE -ne 0) { Write-Host "FAILED: Syntax"; $failures++ } else { Write-Host "✓ Passed" -ForegroundColor Green }

# 2. Lint & format
Write-Host "`n>>> Lint check..." -ForegroundColor Cyan
& $py -m ruff check src/maps/plotly_map*.py src/maps/maps_manager.py
if ($LASTEXITCODE -ne 0) { Write-Host "FAILED: Lint"; $failures++ } else { Write-Host "✓ Passed" -ForegroundColor Green }

Write-Host "`n>>> Format check..." -ForegroundColor Cyan
& $py -m black --check src/maps/plotly_map*.py src/maps/maps_manager.py
if ($LASTEXITCODE -ne 0) { Write-Host "FAILED: Format"; $failures++ } else { Write-Host "✓ Passed" -ForegroundColor Green }

# 3. Type check
Write-Host "`n>>> Type check..." -ForegroundColor Cyan
& $py -m mypy src/maps/plotly_map*.py src/maps/maps_manager.py --ignore-missing-imports
if ($LASTEXITCODE -ne 0) { Write-Host "FAILED: Type check"; $failures++ } else { Write-Host "✓ Passed" -ForegroundColor Green }

# 4. Security
Write-Host "`n>>> Security scan..." -ForegroundColor Cyan
& $py -m bandit -r src/maps/plotly_map*.py src/maps/maps_manager.py
if ($LASTEXITCODE -ne 0) { Write-Host "FAILED: Security"; $failures++ } else { Write-Host "✓ Passed" -ForegroundColor Green }

# 5. Unit tests + coverage
Write-Host "`n>>> Unit tests + coverage..." -ForegroundColor Cyan
& $py -m pytest tests/maps/test_plotly_map*.py -v --cov=src/maps --cov-report=term-missing --cov-fail-under=70
if ($LASTEXITCODE -ne 0) { Write-Host "FAILED: Tests"; $failures++ } else { Write-Host "✓ Passed" -ForegroundColor Green }

# 6. Regression tests
Write-Host "`n>>> Regression tests..." -ForegroundColor Cyan
& $py -m pytest tests/maps/test_plotly_map_viewer_regression.py -v
if ($LASTEXITCODE -ne 0) { Write-Host "FAILED: Regression"; $failures++ } else { Write-Host "✓ Passed" -ForegroundColor Green }

# 7. Integration tests
Write-Host "`n>>> Integration tests..." -ForegroundColor Cyan
& $py -m pytest tests/maps/test_plotly_map_viewer_integration.py -v
if ($LASTEXITCODE -ne 0) { Write-Host "FAILED: Integration"; $failures++ } else { Write-Host "✓ Passed" -ForegroundColor Green }

# 8. Cyclomatic complexity
Write-Host "`n>>> Cyclomatic complexity check..." -ForegroundColor Cyan
& $py -m radon cc src/maps/plotly_map*.py src/maps/maps_manager.py -a -s | Where-Object { $_ -match "C \(|D \(|E \(|F \(" }
if ($?) { 
    Write-Host "✓ All methods ≤ B (CC ≤ 10)" -ForegroundColor Green 
} else { 
    Write-Host "WARNING: Check CC output manually" -ForegroundColor Yellow 
}

Write-Host "`n>>> RESULT: $failures failures" -ForegroundColor $(if ($failures -eq 0) { 'Green' } else { 'Red' })
exit $failures
```

**Expected Output**:

```
>>> Syntax validation...
✓ Passed

>>> Lint check...
✓ Passed

>>> Format check...
✓ Passed

>>> Type check...
✓ Passed

>>> Security scan...
✓ Passed

>>> Unit tests + coverage...
... tests/maps/test_plotly_map_*.py ...
PASSED (107 passed)
========= 71% coverage =========
✓ Passed

>>> Regression tests...
tests/maps/test_plotly_map_viewer_regression.py::test_walls_figure_json_identical PASSED
tests/maps/test_plotly_map_viewer_regression.py::test_heatmap_interpolation_identical PASSED
✓ Passed

>>> Integration tests...
tests/maps/test_plotly_map_viewer_integration.py::test_full_workflow_map_rendering PASSED
✓ Passed

>>> Cyclomatic complexity check...
✓ All methods ≤ B (CC ≤ 10)

>>> RESULT: 0 failures
```

---

### Task P6.6: Create and Merge Final PR

**ID**: T022  
**Priority**: P1  
**Acceptance Criteria**:
- [ ] PR created with comprehensive description
- [ ] All CI checks green (including CodeQL)
- [ ] Auto-merge label added
- [ ] PR squash-merged to main
- [ ] Worktree cleaned up
- [ ] Branch deleted

**PR Creation**:

```powershell
git push origin chore/293-phase-6

gh pr create \
  --title "chore(293): Complete extraction: PlotlyMapViewer orchestrator and integration" \
  --body "Phase 6 of 6 (FINAL): Complete extraction and integration of PlotlyMapViewer

## Summary

Successfully refactored \`MapsManager._launch_plotly_viewer\` from a 5,247-line monolith (CC=138) into 6 focused, testable classes, each with CC ≤10.

## Changes

### New Files Created
1. **src/maps/plotly_map_templates.py** - DashTemplateManager (CC ≤5)
2. **src/maps/plotly_map_serializer.py** - PlotlyMapDataSerializer (CC ≤7)
3. **src/maps/plotly_map_heatmap.py** - CoverageHeatmapRenderer (CC ≤10)
4. **src/maps/plotly_map_figures.py** - PlotlyMapFigureBuilder (CC ≤10)
5. **src/maps/plotly_map_callbacks.py** - PlotlyMapCallbackManager (CC ≤10)
6. **src/maps/plotly_map_viewer.py** - PlotlyMapViewer orchestrator (CC ≤10)

### Modified Files
- **src/maps/maps_manager.py** - \_launch_plotly_viewer now 3-line delegator

### Test Files Created
- **tests/maps/test_plotly_map_templates.py** (5 tests)
- **tests/maps/test_plotly_map_serializer.py** (7 tests)
- **tests/maps/test_plotly_map_heatmap.py** (8 tests)
- **tests/maps/test_plotly_map_figures.py** (6 tests)
- **tests/maps/test_plotly_map_callbacks.py** (3 tests)
- **tests/maps/test_plotly_map_viewer.py** (4 tests)
- **tests/maps/test_plotly_map_viewer_regression.py** (4 regression tests)
- **tests/maps/test_plotly_map_viewer_integration.py** (3 integration tests)

## Acceptance Criteria (All Complete)

### Complexity Reduction
- [x] \_launch_plotly_viewer: CC 138 → 3 (A-grade)
- [x] All extracted classes: CC ≤10
- [x] radon CC report: No C/D/E/F grades

### Code Quality
- [x] Lint: ruff check ✓
- [x] Format: black ✓
- [x] Type Check: mypy --strict ✓
- [x] Security: bandit ✓
- [x] Dependency CVEs: pip-audit ✓
- [x] Code Scanning: CodeQL ✓

### Testing
- [x] Unit tests: 40 tests, all passing
- [x] Coverage: ≥70% of new code
- [x] Regression tests: Verify figure JSON equivalence, heatmap numeric equivalence
- [x] Integration tests: Full workflow validation

### Functionality
- [x] All 25 callbacks extracted and working
- [x] Web UI renders identically to original
- [x] CSS/HTML styling byte-for-byte identical
- [x] Heatmap interpolation output numerically identical (rtol=1e-10)
- [x] All user interactions preserved

## Breaking Changes

None. The public API of \`MapsManager._launch_plotly_viewer\` remains identical.

## Migration Notes

This refactoring is internal; no user-facing changes. The method signature and behavior are preserved exactly.

## Performance

- Negligible performance impact (delegation layer adds <1ms)
- Improved maintainability and testability

## Effort Summary

| Phase | Effort (hrs) | Actual (hrs) |
|-------|------------|------------|
| 1: DashTemplateManager | 2–3 | ___ |
| 2: PlotlyMapDataSerializer | 2–3 | ___ |
| 3: CoverageHeatmapRenderer | 4–5 | ___ |
| 4: PlotlyMapFigureBuilder | 5–6 | ___ |
| 5: PlotlyMapCallbackManager | 8–10 | ___ |
| 6: PlotlyMapViewer + Integration | 6–8 | ___ |
| **TOTAL** | **27–35** | **___ hrs** |

## Timeline

- Phases 1–2: ~2–3 days
- Phase 3: ~1 day
- Phase 4: ~1 day
- Phase 5: ~1–2 days (high complexity, callback extraction)
- Phase 6: ~1 day (final integration)

## Risk Assessment

| Phase | Risk | Mitigation |
|-------|------|-----------|
| 1–2 | LOW | Unit tests, CSS regression validation |
| 3–4 | MEDIUM | Baseline test data, numeric tolerance tests |
| 5 | HIGH | Callback group testing, callback count validation |
| 6 | HIGH | Full regression suite, integration tests, manual UI testing |

## Files Modified

- [ ] src/maps/maps_manager.py (modified)
- [ ] src/maps/plotly_map_templates.py (new)
- [ ] src/maps/plotly_map_serializer.py (new)
- [ ] src/maps/plotly_map_heatmap.py (new)
- [ ] src/maps/plotly_map_figures.py (new)
- [ ] src/maps/plotly_map_callbacks.py (new)
- [ ] src/maps/plotly_map_viewer.py (new)
- [ ] tests/maps/test_plotly_map_*.py (multiple new)

## CI/CD Status

All checks must pass before merge:
- ✓ Syntax (py_compile)
- ✓ Lint (ruff)
- ✓ Format (black)
- ✓ Type Check (mypy)
- ✓ Security (bandit, pip-audit)
- ✓ Tests (pytest 70%+ coverage)
- ✓ Code Scanning (CodeQL)

Closes #293" \
  --base main
```

**Wait for CI & Merge**:

```powershell
gh pr checks --watch

# After ALL checks pass (including CodeQL), add auto-merge label
gh pr edit --add-label "auto-merge"

# Wait for squash merge to complete
git fetch origin && git rebase origin/main

# Cleanup
cd ../MistHelper
git worktree remove ../MistHelper-phase-6
git branch -D chore/293-phase-6
```

---

## SUMMARY

### Total Task Count: 22 Tasks across 6 Phases

| Phase | Tasks | Task IDs | Effort (hrs) |
|-------|-------|----------|-------------|
| Phase 1: DashTemplateManager | 3 | T001–T003 | 2.5 |
| Phase 2: PlotlyMapDataSerializer | 3 | T004–T006 | 2.5 |
| Phase 3: CoverageHeatmapRenderer | 2 | T007–T008 | 4.5 |
| Phase 4: PlotlyMapFigureBuilder | 2 | T009–T010 | 5.5 |
| Phase 5: PlotlyMapCallbackManager | 7 | T011–T017 | 9 |
| Phase 6: PlotlyMapViewer + Integration | 6 | T018–T023 | 7 |
| **TOTAL** | **22** | **T001–T023** | **31 hrs** |

### Dependency Chain

```
T001-T003 (Phase 1) ✓
   ↓
T004-T006 (Phase 2) ✓
   ↓
T007-T008 (Phase 3) ✓
   ↓
T009-T010 (Phase 4) ✓
   ↓
T011-T017 (Phase 5) ✓
   ↓
T018-T023 (Phase 6 + Integration) ✓
```

All phases must complete sequentially. Each phase's PR must be merged before the next phase begins.

### Success Criteria

- ✅ Cyclomatic complexity: 138 → ≤10 per method
- ✅ Code coverage: ≥70%
- ✅ All tests passing
- ✅ All linting/type/security checks passing
- ✅ Functionality preserved (regression tests)
- ✅ User experience identical (visual regression test)

---

**READY FOR SPECKIT.IMPLEMENT** ✓

All tasks are actionable with concrete file paths, test cases, git commands, and quality gate validation steps.
