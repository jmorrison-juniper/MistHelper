# Feature Specification: Reduce CC in _launch_plotly_viewer (Issue #293)

**Feature Branch**: `chore/293-reduce-cc-plotly-viewer`  
**Created**: 2026-05-13  
**Status**: Draft  
**Target Issue**: #293  
**File**: `src/maps/maps_manager.py`  
**Current Method**: `MapsManager._launch_plotly_viewer` (lines 3010-8256, 5,247 lines)  
**Current CC**: 138 (Target: ≤10 per method)

---

## Problem Statement

The method `_launch_plotly_viewer` in `src/maps/maps_manager.py` has a cyclomatic complexity (CC) of 138, exceeding the target of ≤10 by 13.8×. This monolithic method combines multiple concerns:

- **Dash application initialization** (imports, config)
- **HTML/CSS template setup** (custom styling)
- **Figure building** (walls, wayfinding devices, clients)
- **Coverage heatmap rendering** (complex multi-step calculations)
- **UI layout definition** (~25 callback functions)
- **Server startup** (configuration and threading)

**Root Cause**: All concerns are implemented as a single 5,247-line method with nested conditionals, loops, and callback decorators, making the code:
- Difficult to test (requires full Dash environment setup)
- Hard to maintain (changes to one concern risk breaking others)
- Impossible to reuse (entire method called monolithically)
- Violates single responsibility principle (SRP)

**Impact**:
- Code review friction and slow merge velocity
- Testing overhead (integration tests only, no unit tests)
- New developer onboarding friction
- Risk of regressions when modifying map behavior

---

## Goal

Decompose `_launch_plotly_viewer` into focused classes and helper methods, each with CC ≤10, while preserving all functionality. Enable unit testing of individual concerns and reduce cognitive complexity.

---

## User Scenarios & Testing

### User Story 1 – Refactor Without Breaking Changes (Priority: P1)

A developer receives the refactored code and runs all existing tests, expecting the web UI to work identically to the original.

**Why this priority**: Preserving existing functionality is the foundation. Any regression breaks trust in the refactoring.

**Independent Test**: Full integration test suite passes; web UI renders maps, callbacks execute, figures display identically.

**Acceptance Scenarios**:

1. **Given** the refactored `MapsManager` class, **When** a developer launches the maps viewer, **Then** the Dash app initializes without errors and displays the same figure as before.
2. **Given** a map with walls, wayfinding devices, and clients, **When** the UI renders, **Then** all three layers display with identical styling and positioning.
3. **Given** coverage heatmap data, **When** the heatmap callback fires, **Then** the heatmap renders with the same algorithm and color scale.
4. **Given** callback functions (show/hide devices, toggle heatmap, etc.), **When** UI interactions trigger callbacks, **Then** callbacks execute identically to the original.

---

### User Story 2 – Enable Unit Testing of Figure Building (Priority: P1)

A developer writes unit tests for the figure-building logic without needing a full Dash environment.

**Why this priority**: Unit testability is essential for maintainability. Extracted helper methods can be tested in isolation.

**Independent Test**: Helper methods (e.g., `build_walls_figure`, `build_heatmap`) can be called with test data and assert on returned Plotly figure structure.

**Acceptance Scenarios**:

1. **Given** a `PlotlyMapFigureBuilder` class with `build_walls_figure(svg_data, style_config)`, **When** called with test SVG, **Then** returns Plotly figure object with correct traces, layout, and styling.
2. **Given** heatmap test data (coordinates, signal strengths), **When** `build_heatmap(data, algorithm_type)` is called, **Then** returns correct interpolated grid and colorscale.
3. **Given** device inventory data, **When** `build_device_scatter(devices, device_type_filter)` is called, **Then** returns scatter trace with correct markers and hover text.

---

### User Story 3 – Reduce Cognitive Load for Map Feature Enhancements (Priority: P2)

A developer adds support for a new map layer (e.g., energy usage heatmap) without modifying the entire 5,247-line method.

**Why this priority**: New features should be additive, not disruptive. Modular design allows independent feature development.

**Independent Test**: New layer can be built and integrated with minimal changes to existing callback structure; all tests still pass.

**Acceptance Scenarios**:

1. **Given** a new `PlotlyMapLayerBuilder` for energy heatmaps, **When** integrated into the callback system, **Then** new layer renders without touching wall/device/client logic.
2. **Given** existing callbacks, **When** a developer adds a new toggle button in the UI, **Then** corresponding callback is added to `PlotlyMapCallbackManager` without modifying heatmap or device logic.

---

### User Story 4 – Enable Code Review & Compliance (Priority: P2)

Code review tools (ruff, mypy, CodeQL) run successfully with no violations; quality gates pass.

**Why this priority**: Quality gates are mandatory. Compliance ensures consistency with project standards.

**Independent Test**: All quality gates pass: ruff lint, mypy type checking, CodeQL security scanning, pytest coverage ≥70%.

**Acceptance Scenarios**:

1. **Given** refactored code, **When** `ruff check` runs, **Then** no violations found.
2. **Given** refactored code, **When** `mypy` runs in strict mode, **Then** all type hints are correct and no `Any` type overrides needed.
3. **Given** refactored code, **When** pytest runs with coverage analysis, **Then** coverage for new classes ≥70%.

---

## Requirements

### Functional Requirements

- **FR-001**: Method `_launch_plotly_viewer` MUST initialize Dash app with identical configuration to current implementation.
- **FR-002**: Dash callbacks MUST execute identically to the original (same data serialization, state transitions, figure updates).
- **FR-003**: HTML/CSS templates MUST render with identical styling (custom Dash templates preserved).
- **FR-004**: Figure building (walls, wayfinding, devices, clients, heatmap) MUST produce identical Plotly figures.
- **FR-005**: Coverage heatmap rendering MUST use identical algorithm and produce same interpolated grid.
- **FR-006**: All UI interactions (toggle buttons, dropdowns, callbacks) MUST work identically.
- **FR-007**: Server startup MUST configure threading, port binding, and debug mode identically.
- **FR-008**: Extracted classes MUST have CC ≤10 per method.
- **FR-009**: Cyclomatic complexity of `MapsManager` class MUST average ≤10 across all methods.
- **FR-010**: No breaking changes to public method signatures or API contracts.

### Technical Requirements

- **TR-001**: Refactored code MUST pass all existing unit + integration tests without modification.
- **TR-002**: Code MUST pass quality gates: ruff lint, black format, mypy type checking, pytest with ≥70% coverage.
- **TR-003**: Each extracted class MUST have docstrings explaining purpose, public API, and callback constraints.
- **TR-004**: Type hints MUST be complete (no `Any` unless explicitly documented).
- **TR-005**: Dash callback decorators MUST remain on class methods to preserve Dash's callback registry.
- **TR-006**: State and data serialization MUST be identical (JSON serialization, callback inputs/outputs).
- **TR-007**: No changes to dependencies or imports; only internal refactoring.

### Key Entities

#### Current Structure (Monolithic)
- **`MapsManager._launch_plotly_viewer()`**: Single 5,247-line method combining all concerns (CC: 138)

#### Proposed Architecture (Modular)

1. **`PlotlyMapViewer`** – Main Dash app wrapper (replaces core launch logic)
   - Purpose: Initialize Dash app, register callbacks, manage server lifecycle
   - Methods: `__init__`, `create_app`, `register_callbacks`, `run`
   - CC target: ≤10

2. **`PlotlyMapFigureBuilder`** – Figure construction (walls, devices, clients, heatmap)
   - Purpose: Build Plotly figures for all map layers
   - Methods: `build_walls_figure`, `build_device_scatter`, `build_client_scatter`, `build_heatmap_figure`
   - CC target: ≤10 per method

3. **`PlotlyMapCallbackManager`** – Callback coordination (~25 callbacks)
   - Purpose: Define and register all callback functions in organized groups
   - Methods: `register_layer_callbacks`, `register_heatmap_callbacks`, `register_control_callbacks`, `register_export_callbacks`
   - CC target: ≤10 per group

4. **`CoverageHeatmapRenderer`** – Heatmap algorithm (complex interpolation logic)
   - Purpose: Encapsulate signal/coverage interpolation algorithms
   - Methods: `interpolate_grid`, `apply_colorscale`, `smooth_heatmap`
   - CC target: ≤10 per method

5. **`DashTemplateManager`** – HTML/CSS template management
   - Purpose: Manage custom Dash templates, CSS, and styling
   - Methods: `get_template_path`, `get_custom_css`, `get_layout_html`
   - CC target: ≤10

6. **`PlotlyMapDataSerializer`** – Callback data transformation
   - Purpose: Handle JSON serialization/deserialization for callback data
   - Methods: `serialize_figure_state`, `deserialize_figure_state`, `validate_callback_inputs`
   - CC target: ≤10

### Data Flow (New Architecture)

```
MapsManager._launch_plotly_viewer()
  ├─> PlotlyMapViewer.__init__()
  │    ├─> DashTemplateManager.get_custom_css()
  │    ├─> DashTemplateManager.get_layout_html()
  │    └─> create Dash app
  │
  ├─> PlotlyMapFigureBuilder.build_walls_figure(svg)
  ├─> PlotlyMapFigureBuilder.build_device_scatter(devices)
  ├─> PlotlyMapFigureBuilder.build_client_scatter(clients)
  ├─> CoverageHeatmapRenderer.interpolate_grid(data)
  └─> PlotlyMapCallbackManager.register_*_callbacks(app)
      ├─> Layer callbacks (walls, devices, clients)
      ├─> Heatmap callbacks (algorithm, smoothing)
      ├─> Control callbacks (toggles, dropdowns)
      └─> Export callbacks (download, screenshot)
```

---

## Success Criteria

### Measurable Outcomes

- **SC-001**: Cyclomatic complexity of `MapsManager._launch_plotly_viewer` MUST reduce from 138 to ≤10.
- **SC-002**: Average cyclomatic complexity across all `MapsManager` methods MUST be ≤10.
- **SC-003**: All extracted classes MUST have cyclomatic complexity ≤10 per method (verified via radon/flake8-cognitive-complexity).
- **SC-004**: Test coverage for `src/maps/` MUST remain ≥70% (no decrease from current baseline).
- **SC-005**: All 100+ existing tests MUST pass without modification (zero test breakage).
- **SC-006**: All quality gates MUST pass: ruff lint, black format check, mypy strict, CodeQL scanning, pytest+cov.
- **SC-007**: Web UI integration tests MUST confirm identical functionality (walls render, callbacks execute, heatmap displays).
- **SC-008**: Performance regression MUST be <5% (Dash app initialization time measured before/after).
- **SC-009**: Callback data serialization MUST be identical (before/after JSON payloads byte-for-byte equivalent).
- **SC-010**: Documentation MUST be complete: docstrings for all classes/methods, architecture diagram in `docs/`.

---

## Assumptions

- **A-001**: Dash callback registry behavior is unchanged; callback decorators remain on class methods.
- **A-002**: Current HTML/CSS templates are preserved; no redesign of map UI.
- **A-003**: Heatmap interpolation algorithm (`scipy.interpolate`, etc.) is encapsulated; behavior must be identical.
- **A-004**: Device/client data structures (input format) remain unchanged.
- **A-005**: JSON serialization for callback data uses `json.dumps/loads` consistently; no third-party serializers.
- **A-006**: No external dependencies added; refactoring uses only existing imports.
- **A-007**: Existing `.env` configuration and environment variables are respected (no changes).
- **A-008**: Server threading model (Flask/Dash default) is preserved; no async/await additions.
- **A-009**: Map viewer is called only from `MapsManager._launch_plotly_viewer`; no other code paths depend on internal structure.
- **A-010**: Testing environment has required Plotly, Dash, and scipy libraries available.

---

## Implementation Constraints

### Dash Callback Architecture

- **Constraint 1**: Callback decorators (`@app.callback()`) MUST remain on methods to preserve Dash's decorator-based registration.
- **Constraint 2**: Callback state/inputs/outputs MUST use identical JSON serialization to current implementation.
- **Constraint 3**: Callback methods MUST be registered to the Dash app instance before `app.run_server()` is called.
- **Constraint 4**: Callback functions MUST accept identical parameter lists (order, types, defaults) to current implementation.
- **Constraint 5**: `ClientsideCallbackData` serialization (if used) MUST be preserved identically.
- **Constraint 6**: Store component state (dcc.Store) MUST serialize identically for backward compatibility.

### Method Signature Contracts

- **Constraint 7**: Public method `_launch_plotly_viewer(...)` signature MUST remain unchanged (all parameters, defaults, return type).
- **Constraint 8**: Internal helper methods may be refactored, but any called from outside must be stable.
- **Constraint 9**: All new classes MUST accept standard parameters (org_id, site_id, device_inventory, etc.) without breaking existing call sites.

### Data Serialization

- **Constraint 10**: Figure state (Plotly figure dicts) MUST serialize/deserialize identically across refactor.
- **Constraint 11**: Callback input data MUST use same JSON format (no new serialization schemes).
- **Constraint 12**: All numeric values (coordinates, signal strengths, etc.) MUST have identical precision (float64).

### Threading & Server

- **Constraint 13**: `app.run_server()` parameters (host, port, debug, threaded, etc.) MUST be identical.
- **Constraint 14**: Thread-safety model for callback data MUST be preserved (Flask's default thread-local storage).

---

## Extraction Phases (Smallest to Hardest)

### Phase 1: Template Management (Easiest, Low Risk)

**Effort**: 2–3 hours  
**Risk**: Low (no callback dependencies)  
**Scope**: Extract HTML/CSS template logic into `DashTemplateManager`

- Extract lines 3070–3200 (HTML/CSS setup)
- Create `PlotlyMapTemplateManager` class
- Methods: `get_custom_css()`, `get_template_html()`, `get_layout_structure()`
- Verify: Custom CSS and layout render identically in Dash app

**Validation**:

```python
def test_template_manager_css():
    mgr = DashTemplateManager(...)
    css = mgr.get_custom_css()
    assert "background-color" in css
    assert len(css) == len(ORIGINAL_CSS)  # Byte count identical
```

---

### Phase 2: Data Serialization (Low Risk)
**Effort**: 2–3 hours  
**Risk**: Low (utility functions, no callbacks)  
**Scope**: Extract callback data transformation into `PlotlyMapDataSerializer`

- Extract JSON serialization/deserialization logic
- Create `PlotlyMapDataSerializer` class
- Methods: `serialize_figure_state()`, `deserialize_callback_inputs()`, `validate_types()`
- Verify: Callback data payloads byte-for-byte identical

**Validation**:
```python
def test_data_serializer_roundtrip():
    serializer = PlotlyMapDataSerializer()
    original = {"figure": {...}, "heatmap": [...]}
    serialized = serializer.serialize(original)
    deserialized = serializer.deserialize(serialized)
    assert deserialized == original  # Exact match
```

---

### Phase 3: Heatmap Renderer (Medium Risk)
**Effort**: 4–5 hours  
**Risk**: Medium (algorithm correctness critical)  
**Scope**: Extract coverage heatmap rendering into `CoverageHeatmapRenderer`

- Extract lines 3700–4500+ (heatmap algorithm, interpolation)
- Create `CoverageHeatmapRenderer` class
- Methods: `interpolate_grid()`, `apply_colorscale()`, `smooth_heatmap()`, `validate_algorithm()`
- Verify: Heatmap algorithm produces identical output for test data

**Validation**:
```python
def test_heatmap_interpolation():
    renderer = CoverageHeatmapRenderer(site_id, algorithm='kriging')
    grid = renderer.interpolate_grid(TEST_DATA)
    expected = ORIGINAL_HEATMAP_OUTPUT
    assert np.allclose(grid, expected, rtol=1e-10)  # Numeric precision match
```

---

### Phase 4: Figure Builder (Medium Risk)
**Effort**: 5–6 hours  
**Risk**: Medium (figure structure must match exactly)  
**Scope**: Extract figure construction into `PlotlyMapFigureBuilder`

- Extract lines 3200–3700 (walls, devices, clients figure building)
- Create `PlotlyMapFigureBuilder` class
- Methods: `build_walls_figure()`, `build_device_scatter()`, `build_client_scatter()`, `build_combined_figure()`
- Verify: Plotly figures have identical structure, styling, hover text

**Validation**:
```python
def test_walls_figure_structure():
    builder = PlotlyMapFigureBuilder(svg_data, style_config)
    walls_fig = builder.build_walls_figure()
    expected_fig = ORIGINAL_WALLS_FIGURE
    assert walls_fig.to_json() == expected_fig.to_json()  # Exact JSON match
```

---

### Phase 5: Callback Management (Hardest, High Risk)
**Effort**: 8–10 hours  
**Risk**: High (25+ callbacks, state dependencies)  
**Scope**: Extract callback registration into `PlotlyMapCallbackManager`

- Extract lines 4500–8000 (~25 @app.callback decorators)
- Create `PlotlyMapCallbackManager` class
- Methods: `register_layer_callbacks()`, `register_heatmap_callbacks()`, `register_control_callbacks()`, `register_export_callbacks()`
- Preserve callback decorator syntax (decorate methods with @app.callback)
- Verify: Each callback executes identically; state/inputs/outputs unchanged

**Validation**:
```python
def test_layer_toggle_callback():
    app = create_test_app()
    mgr = PlotlyMapCallbackManager(app, data)
    mgr.register_layer_callbacks()
    # Simulate callback input, verify output
    result = callback_func(show_walls=True, ...)
    assert result == EXPECTED_CALLBACK_OUTPUT
```

---

### Phase 6: Main Viewer & Integration (Hardest, High Risk)
**Effort**: 6–8 hours  
**Risk**: High (integration point, end-to-end validation)  
**Scope**: Extract Dash app initialization into `PlotlyMapViewer`; integrate all components

- Create `PlotlyMapViewer` class orchestrating all components
- Methods: `__init__()`, `create_app()`, `register_all_callbacks()`, `run_server()`
- Integrate: TemplateManager, DataSerializer, HeatmapRenderer, FigureBuilder, CallbackManager
- Verify: Full integration test confirms identical behavior end-to-end

**Validation**:
```python
def test_full_integration_e2e():
    viewer = PlotlyMapViewer(org_id, site_id, device_inv, client_data)
    app = viewer.create_app()
    # Simulate Dash client interactions
    assert app.layout is not None
    assert len(app.callback_map) == EXPECTED_CALLBACK_COUNT
    # Run integration test suite
    result = run_integration_tests(app)
    assert result.all_passed
```

---

## Risk Areas & Mitigation

### Risk 1: Callback State Serialization Breaks
**Risk**: JSON serialization of callback state changes slightly, breaking data flow between callbacks.  
**Severity**: Critical  
**Mitigation**:
- Implement `PlotlyMapDataSerializer` early (Phase 2)
- Compare byte-for-byte JSON output before/after
- Unit test every callback input/output pair
- Acceptance test: `dcc.Store` component state must match exactly

**Validation Test**:
```python
def test_callback_state_byte_equality():
    """Verify callback state serialization is byte-for-byte identical"""
    test_cases = [CALLBACK_CASE_1, CALLBACK_CASE_2, ...]
    for case in test_cases:
        original_json = original_serialize(case)
        new_json = refactored_serialize(case)
        assert original_json == new_json, f"Mismatch: {case}"
```

---

### Risk 2: Heatmap Algorithm Diverges Numerically
**Risk**: Floating-point precision or interpolation order changes, producing slightly different heatmaps.  
**Severity**: High  
**Mitigation**:
- Extract heatmap logic into `CoverageHeatmapRenderer` (Phase 3) with comprehensive test data
- Use `np.allclose(rtol=1e-10)` for numeric comparison (tight tolerance)
- Document algorithm version and library versions (scipy, numpy)
- Snapshot test: compare heatmap output for 5+ real site data samples

**Validation Test**:
```python
def test_heatmap_algorithm_precision():
    """Verify heatmap interpolation produces identical numeric output"""
    for site_sample in HEATMAP_TEST_SAMPLES:
        original_grid = original_interpolate(site_sample)
        refactored_grid = refactored_interpolate(site_sample)
        assert np.allclose(original_grid, refactored_grid, rtol=1e-10)
```

---

### Risk 3: Callback Decorator Registration Fails
**Risk**: Moving `@app.callback` decorators to class methods breaks Dash's callback discovery.  
**Severity**: Critical  
**Mitigation**:
- Keep callback decorators on methods (don't move to separate registration)
- Test early in Phase 5: verify Dash app sees all callbacks
- Integration test: manually trigger each callback, verify execution
- Dash version verification: confirm compatibility with current Dash version

**Validation Test**:
```python
def test_callback_decorator_registration():
    """Verify Dash discovers all callbacks after refactoring"""
    app = create_test_app()
    mgr = PlotlyMapCallbackManager(app, ...)
    mgr.register_layer_callbacks()
    expected_callbacks = ORIGINAL_CALLBACK_COUNT
    actual_callbacks = len(app.callback_map)
    assert actual_callbacks == expected_callbacks, \
        f"Expected {expected_callbacks}, got {actual_callbacks}"
```

---

### Risk 4: Performance Regression (Initialization Time)
**Risk**: Additional object instantiation and method calls slow down app startup.  
**Severity**: Medium  
**Mitigation**:
- Benchmark app initialization time before/after (measure in milliseconds)
- Profile with `cProfile` to identify bottlenecks
- Lazy load heavy components if needed (e.g., defer heatmap interpolation until first callback)
- Acceptance criterion: <5% performance regression

**Validation Test**:
```python
def test_performance_no_regression():
    """Verify refactored app startup time is within 5% of original"""
    import timeit
    
    original_time = timeit.timeit(original_init, number=10) / 10
    refactored_time = timeit.timeit(refactored_init, number=10) / 10
    
    regression_pct = (refactored_time - original_time) / original_time * 100
    assert regression_pct < 5, f"Performance regressed {regression_pct}%"
```

---

### Risk 5: Breaking Public API Contracts
**Risk**: Changing `_launch_plotly_viewer` signature or return type breaks calling code.  
**Severity**: Critical  
**Mitigation**:
- Lock signature: no parameter additions/removals/renames
- Lock return type: must return identical Dash app object
- Integration test: confirm callers work identically
- Code review: explicit signature comparison before/after

**Validation Test**:
```python
def test_public_api_stable():
    """Verify _launch_plotly_viewer signature is unchanged"""
    import inspect
    
    original_sig = original_signature
    refactored_sig = refactored_signature
    
    assert str(original_sig) == str(refactored_sig), \
        f"Signature changed: {original_sig} -> {refactored_sig}"
```

---

### Risk 6: Test Coverage Decreases Below Threshold
**Risk**: Extracted methods lack unit tests, causing coverage to drop below 70%.  
**Severity**: High  
**Mitigation**:
- Mandatory unit tests for all extracted classes (Phase 2–5)
- Coverage report: run `pytest --cov=src/maps/ --cov-report=html`
- Acceptance criterion: coverage ≥70% or current baseline (whichever is higher)
- Focus on critical paths: callbacks, heatmap algorithm, figure building

**Validation Test**:
```python
def test_coverage_maintained():
    """Verify test coverage is >= 70% for src/maps/"""
    result = subprocess.run(
        ["pytest", "--cov=src/maps/", "--cov-report=term-missing"],
        capture_output=True, text=True
    )
    coverage_line = [l for l in result.stdout.split('\n') if 'TOTAL' in l][0]
    coverage_pct = int(coverage_line.split()[-1].rstrip('%'))
    assert coverage_pct >= 70, f"Coverage {coverage_pct}% below threshold"
```

---

## Testing Strategy

### Unit Tests (Per Component)

Each extracted class MUST have unit tests:

```python
# tests/maps/test_plotly_figure_builder.py
def test_build_walls_figure():
    builder = PlotlyMapFigureBuilder(svg_data, style_config)
    fig = builder.build_walls_figure()
    assert "Walls" in fig.to_json()
    
# tests/maps/test_coverage_heatmap_renderer.py
def test_interpolate_grid():
    renderer = CoverageHeatmapRenderer(site_id, algorithm='kriging')
    grid = renderer.interpolate_grid(TEST_DATA)
    assert grid.shape == EXPECTED_SHAPE
    
# tests/maps/test_plotly_map_callback_manager.py
def test_register_callbacks():
    mgr = PlotlyMapCallbackManager(app, data)
    mgr.register_layer_callbacks()
    assert "show_walls" in app.callback_map
```

### Integration Tests (Full Workflow)

```python
# tests/maps/test_plotly_map_viewer_integration.py
def test_viewer_initialization():
    viewer = PlotlyMapViewer(org_id, site_id, device_inv, client_data)
    app = viewer.create_app()
    assert app.layout is not None
    assert len(app.callback_map) >= 20  # ~25 callbacks

def test_callback_execution():
    """Simulate callback invocation and verify output"""
    app = create_test_app()
    result = app.callback_map[callback_id]([True, False], None)
    assert result is not None
```

### Regression Tests (Behavior Comparison)

```python
# tests/maps/test_refactor_regression.py
def test_figures_identical():
    """Compare Plotly figures before/after refactoring"""
    original_fig = original_build_walls()
    refactored_fig = refactored_build_walls()
    assert original_fig.to_json() == refactored_fig.to_json()

def test_heatmap_output_identical():
    """Compare heatmap output numerically"""
    original_grid = original_interpolate_heatmap(TEST_DATA)
    refactored_grid = refactored_interpolate_heatmap(TEST_DATA)
    assert np.allclose(original_grid, refactored_grid, rtol=1e-10)
```

---

## Acceptance Criteria Checklist

- [ ] **CC-001**: `MapsManager._launch_plotly_viewer` CC reduced to ≤10
- [ ] **CC-002**: Average MapsManager method CC ≤10
- [ ] **CC-003**: All extracted classes CC ≤10 per method (verified with radon/flake8-cognitive-complexity)
- [ ] **TEST-001**: All 100+ existing tests pass without modification
- [ ] **TEST-002**: New unit tests added for all extracted classes (≥70% coverage for new code)
- [ ] **QUALITY-001**: `ruff check` passes (zero violations)
- [ ] **QUALITY-002**: `black --check` passes (formatting compliant)
- [ ] **QUALITY-003**: `mypy --strict` passes (type annotations complete)
- [ ] **QUALITY-004**: CodeQL scanning passes (no security issues)
- [ ] **QUALITY-005**: `pytest --cov` reports ≥70% coverage for `src/maps/`
- [ ] **FUNC-001**: Dash app initializes identically (same templates, CSS, config)
- [ ] **FUNC-002**: All callbacks execute identically (inputs/outputs unchanged)
- [ ] **FUNC-003**: Plotly figures render identically (walls, devices, clients, heatmap)
- [ ] **FUNC-004**: Web UI integration tests confirm behavioral equivalence
- [ ] **FUNC-005**: Heatmap algorithm produces numeric output within 1e-10 tolerance
- [ ] **PERF-001**: App initialization time regression <5%
- [ ] **API-001**: `_launch_plotly_viewer` signature unchanged
- [ ] **API-002**: Return type (Dash app) unchanged
- [ ] **DOC-001**: Architecture diagram created in `docs/`
- [ ] **DOC-002**: Docstrings added to all classes/methods (Sphinx-compatible)
- [ ] **REVIEW-001**: Code review approved (no unaddressed feedback)
- [ ] **MERGE-001**: All CI checks green (lint, type, test, CodeQL, E2E)

---

## Implementation Notes (for AI agents)

### Pseudo-code Flow

```python
# Current: Single monolithic method
class MapsManager:
    def _launch_plotly_viewer(self):
        # 5,247 lines: templates, figures, callbacks, server startup
        # CC = 138 (unmanageable)
        pass

# Refactored: Modular architecture
class MapsManager:
    def _launch_plotly_viewer(self):
        viewer = PlotlyMapViewer(self.org_id, self.site_id, self.inventory)
        viewer.create_app()  # Dash app with all callbacks
        viewer.run_server()

class PlotlyMapViewer:
    def __init__(self, org_id, site_id, device_inventory, client_data):
        self.org_id = org_id
        self.site_id = site_id
        self.app = None
        self.template_mgr = DashTemplateManager(org_id)
        self.figure_builder = PlotlyMapFigureBuilder(device_inventory, client_data)
        self.heatmap_renderer = CoverageHeatmapRenderer(site_id)
        self.callback_mgr = PlotlyMapCallbackManager(self)
        self.serializer = PlotlyMapDataSerializer()
    
    def create_app(self):
        self.app = dash.Dash(...)
        self.app.layout = self._build_layout()
        self.callback_mgr.register_all_callbacks(self.app)
        return self.app
    
    def _build_layout(self):
        return html.Div([...])
    
    def run_server(self):
        self.app.run_server(...)

class PlotlyMapFigureBuilder:
    def build_walls_figure(self): ...
    def build_device_scatter(self): ...
    def build_client_scatter(self): ...

class CoverageHeatmapRenderer:
    def interpolate_grid(self): ...
    def apply_colorscale(self): ...

class PlotlyMapCallbackManager:
    def register_layer_callbacks(self, app): ...
    def register_heatmap_callbacks(self, app): ...
    def register_control_callbacks(self, app): ...
```

### Key File Locations

- **Source**: `src/maps/maps_manager.py` (lines 3010–8256)
- **New Classes**: Create in `src/maps/plotly_map_viewer.py` (new file)
- **Tests**: Add to `tests/maps/test_plotly_map_viewer*.py` (new files)
- **Docs**: Add architecture to `documentation/ARCHITECTURE.md`

### CI Integration

- **Linting**: `ruff check src/maps/` (zero violations)
- **Formatting**: `black --check src/maps/`
- **Type Safety**: `mypy --strict src/maps/`
- **Security**: CodeQL scanning in CI
- **Coverage**: `pytest --cov=src/maps/ --cov-report=html --cov-fail-under=70`

---

## Out of Scope (Non-Goals)

- ❌ Redesigning the map UI or Dash layout
- ❌ Changing dependencies (all existing imports preserved)
- ❌ Converting to async/await or threading changes
- ❌ Migrating to a different web framework (Dash only)
- ❌ Adding new features (refactoring only)
- ❌ Performance optimization (beyond regression testing)
- ❌ API changes visible to external callers

---

## Glossary

| Term | Definition |
|------|-----------|
| **CC** | Cyclomatic Complexity; measure of code path branches (target ≤10) |
| **Dash** | Python web framework for building interactive data visualizations |
| **Callback** | Dash function triggered by UI interaction (e.g., button click) |
| **dcc.Store** | Dash component for storing client-side state (JSON serializable) |
| **Plotly Figure** | Data structure representing a chart/plot (dict-like JSON) |
| **Interpolation** | Algorithm for estimating values between known data points (heatmap) |
| **State Serialization** | Converting Python objects to JSON for callback communication |
| **Regression** | Unintended behavior change compared to original |
| **E2E (End-to-End)** | Integration test covering full user workflow |

---

## References & Resources

- **Dash Documentation**: https://dash.plotly.com/
- **Plotly Figure Reference**: https://plotly.com/python/figure-structure/
- **Cyclomatic Complexity**: https://en.wikipedia.org/wiki/Cyclomatic_complexity
- **Radon CC Tool**: https://radon.readthedocs.io/
- **Project Standards**: `.github/copilot-instructions.md`, `agents.md`
- **Current Implementation**: `src/maps/maps_manager.py` (lines 3010–8256)

---

## Approval & Sign-Off

| Role | Status | Notes |
|------|--------|-------|
| **Specification** | ⏳ Draft | Awaiting clarification questions |
| **Architecture Review** | ⏳ Pending | Ready for technical review |
| **Test Plan** | ✅ Complete | Comprehensive unit + integration coverage |
| **Implementation** | ⏳ Ready | Extraction phases sequenced by risk |
| **Merge Approval** | ⏳ Pending | Awaiting CI/quality gate validation |

