# Implementation Plan: Reduce CC in _launch_plotly_viewer (Issue #293)

**Issue**: #293  
**Spec**: `specs/190-reduce-cc-plotly-viewer/spec.md`  
**Target Complexity**: CC ≤10 per method (from current 138)  
**Timeline**: 6 phases, 2–4 weeks estimated  
**Status**: Ready for Phase 1 kickoff  

---

## Executive Summary

This plan decomposes `MapsManager._launch_plotly_viewer` (5,247 lines, CC=138) into 6 focused classes, each with CC ≤10. The approach is incremental, low-risk, and preserves all functionality:

1. **Phase 1 – Templates** (2–3 hrs, LOW RISK): Extract HTML/CSS → `DashTemplateManager`
2. **Phase 2 – Serialization** (2–3 hrs, LOW RISK): Extract JSON handling → `PlotlyMapDataSerializer`
3. **Phase 3 – Heatmap** (4–5 hrs, MEDIUM RISK): Extract interpolation → `CoverageHeatmapRenderer`
4. **Phase 4 – Figures** (5–6 hrs, MEDIUM RISK): Extract figure building → `PlotlyMapFigureBuilder`
5. **Phase 5 – Callbacks** (8–10 hrs, HIGH RISK): Extract ~25 callbacks → `PlotlyMapCallbackManager`
6. **Phase 6 – Integration** (6–8 hrs, HIGH RISK): Orchestrate all → `PlotlyMapViewer`, test E2E

**Total Estimated Effort**: 27–35 hours (≈1 developer-week)

---

## Part 1: Detailed Class Architecture

### 1.1 Class Hierarchy & Method Signatures

#### Class 1: `DashTemplateManager` (Phase 1)

**Purpose**: Centralize HTML/CSS template management and custom styling  
**Location**: `src/maps/plotly_map_templates.py`  
**CC Target**: ≤5 (utility class, mostly lookups)

```python
class DashTemplateManager:
    """Manages custom Dash templates, CSS styling, and HTML layout."""
    
    def __init__(self, org_id: str, base_template_dir: str = "src/maps/templates"):
        """
        Initialize template manager.
        
        Args:
            org_id: Organization ID (for org-specific templates, if any)
            base_template_dir: Root directory for template files
        """
        self.org_id = org_id
        self.base_template_dir = base_template_dir
        self._template_cache: Dict[str, str] = {}
    
    def get_custom_css(self) -> str:
        """
        Retrieve custom CSS styling for the map viewer.
        
        Returns:
            CSS string (inline or file-based)
        
        Raises:
            FileNotFoundError: If CSS file not found
        """
        pass
    
    def get_custom_js(self) -> str:
        """
        Retrieve custom JavaScript (if any).
        
        Returns:
            JS string or empty string
        """
        pass
    
    def get_layout_html(self) -> Dict[str, Any]:
        """
        Build the main Dash HTML layout structure.
        
        Returns:
            Dict with layout components (dcc.Graph, dcc.Store, html.Div, etc.)
        """
        pass
    
    def get_app_meta(self) -> Dict[str, str]:
        """
        Get metadata for Dash app (title, favicon, etc.).
        
        Returns:
            Dict with 'title', 'favicon_url', etc.
        """
        pass
    
    def validate_template(self) -> bool:
        """
        Validate that all templates are syntactically correct.
        
        Returns:
            True if valid, raises exception otherwise
        """
        pass
```

**Dependencies**: None (isolated utility)  
**Call Sites**: `PlotlyMapViewer.__init__`

---

#### Class 2: `PlotlyMapDataSerializer` (Phase 2)

**Purpose**: Handle JSON serialization/deserialization of callback data  
**Location**: `src/maps/plotly_map_serializer.py`  
**CC Target**: ≤7 (handles multiple data types)

```python
class PlotlyMapDataSerializer:
    """
    Encapsulates callback data transformation and JSON serialization.
    Ensures byte-for-byte compatibility with original implementation.
    """
    
    def __init__(self):
        """Initialize serializer with default JSON encoder/decoder."""
        self._encoder = json.JSONEncoder(default=self._encode_defaults)
        self._decoder = json.JSONDecoder()
    
    def serialize_figure_state(self, figure_dict: Dict[str, Any]) -> str:
        """
        Serialize Plotly figure dict to JSON string.
        
        Args:
            figure_dict: Plotly figure (dict from `go.Figure().to_dict()`)
        
        Returns:
            JSON string (byte-for-byte identical to original)
        
        Raises:
            TypeError: If figure contains non-serializable objects
        """
        pass
    
    def deserialize_figure_state(self, json_str: str) -> Dict[str, Any]:
        """
        Deserialize JSON string back to Plotly figure dict.
        
        Args:
            json_str: JSON string from callback
        
        Returns:
            Plotly figure dict
        
        Raises:
            json.JSONDecodeError: If JSON malformed
        """
        pass
    
    def serialize_callback_inputs(self, inputs: Dict[str, Any]) -> str:
        """
        Serialize callback input dictionary (dcc.Store, inputs, etc.).
        
        Args:
            inputs: Dict of callback inputs
        
        Returns:
            JSON string
        """
        pass
    
    def deserialize_callback_inputs(self, json_str: str) -> Dict[str, Any]:
        """
        Deserialize callback input dictionary.
        
        Args:
            json_str: JSON string
        
        Returns:
            Dict of callback inputs
        """
        pass
    
    def validate_numeric_precision(self, 
                                    original: Dict[str, Any], 
                                    refactored: Dict[str, Any],
                                    rtol: float = 1e-10) -> bool:
        """
        Validate that numeric values match within tolerance.
        
        Args:
            original: Original serialized data
            refactored: Refactored serialized data
            rtol: Relative tolerance for float comparison
        
        Returns:
            True if all numerics within tolerance
        
        Raises:
            AssertionError: If mismatch detected
        """
        pass
    
    def _encode_defaults(self, obj: Any) -> Any:
        """Handle non-standard types during JSON encoding."""
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.integer, np.floating)):
            return float(obj)
        elif isinstance(obj, datetime.datetime):
            return obj.isoformat()
        else:
            raise TypeError(f"Object of type {type(obj)} not JSON serializable")
```

**Dependencies**: `json`, `numpy`, `datetime`  
**Call Sites**: `PlotlyMapCallbackManager` (all callbacks), `CoverageHeatmapRenderer`

---

#### Class 3: `CoverageHeatmapRenderer` (Phase 3)

**Purpose**: Encapsulate heatmap interpolation and rendering logic  
**Location**: `src/maps/plotly_map_heatmap.py`  
**CC Target**: ≤10 per method (complex algorithm)

```python
class CoverageHeatmapRenderer:
    """
    Renders coverage heatmaps using interpolation algorithms.
    Supports Kriging, IDW, RBF, and other interpolation methods.
    """
    
    def __init__(self, 
                 site_id: str, 
                 algorithm: str = 'kriging',
                 interpolation_method: str = 'thin_plate',
                 grid_resolution: int = 100):
        """
        Initialize heatmap renderer.
        
        Args:
            site_id: Site identifier (for site-specific config)
            algorithm: Interpolation algorithm ('kriging', 'idw', 'rbf')
            interpolation_method: RBF method if algorithm='rbf' ('thin_plate', 'multiquadric', etc.)
            grid_resolution: Resolution of interpolated grid (NxN)
        
        Raises:
            ValueError: If algorithm unsupported
        """
        self.site_id = site_id
        self.algorithm = algorithm
        self.interpolation_method = interpolation_method
        self.grid_resolution = grid_resolution
        self._interpolator = None
        self._validate_algorithm()
    
    def interpolate_grid(self, 
                        data: Dict[str, Any]) -> np.ndarray:
        """
        Interpolate coverage signal data to regular grid.
        
        Args:
            data: Dict with keys:
                - 'x_coords': array of X coordinates
                - 'y_coords': array of Y coordinates
                - 'signal_strengths': array of signal values
                - 'bounds': {'x_min', 'x_max', 'y_min', 'y_max'} (optional)
        
        Returns:
            Interpolated grid (shape: (grid_resolution, grid_resolution))
        
        Raises:
            ValueError: If data insufficient for interpolation
            RuntimeError: If interpolation algorithm fails
        """
        pass
    
    def apply_colorscale(self, 
                        grid: np.ndarray,
                        colorscale: str = 'Viridis',
                        min_val: Optional[float] = None,
                        max_val: Optional[float] = None) -> List[List[float]]:
        """
        Convert interpolated grid to colorscaled values [0, 1].
        
        Args:
            grid: Interpolated grid (NxN)
            colorscale: Plotly colorscale name
            min_val: Minimum value for scaling (auto-detect if None)
            max_val: Maximum value for scaling (auto-detect if None)
        
        Returns:
            Normalized grid (values in [0, 1])
        """
        pass
    
    def smooth_heatmap(self, 
                      grid: np.ndarray, 
                      kernel_size: int = 3) -> np.ndarray:
        """
        Apply Gaussian smoothing to heatmap grid.
        
        Args:
            grid: Interpolated grid
            kernel_size: Gaussian kernel size (must be odd)
        
        Returns:
            Smoothed grid
        """
        pass
    
    def build_heatmap_figure(self,
                            grid: np.ndarray,
                            colorscale: str = 'Viridis') -> go.Figure:
        """
        Build complete Plotly heatmap figure.
        
        Args:
            grid: Interpolated grid (NxN)
            colorscale: Plotly colorscale name
        
        Returns:
            Plotly Figure object
        """
        pass
    
    def validate_algorithm(self) -> bool:
        """
        Validate that algorithm is supported and working.
        
        Returns:
            True if valid
        
        Raises:
            ValueError: If algorithm broken or unavailable
        """
        pass
    
    def get_algorithm_config(self) -> Dict[str, Any]:
        """
        Get current algorithm configuration (for debugging/logging).
        
        Returns:
            Dict with algorithm params
        """
        pass
    
    def _validate_algorithm(self):
        """Internal validation of algorithm selection."""
        if self.algorithm not in ['kriging', 'idw', 'rbf']:
            raise ValueError(f"Unsupported algorithm: {self.algorithm}")
```

**Dependencies**: `scipy.interpolate`, `numpy`, `plotly.graph_objects`  
**Call Sites**: `PlotlyMapFigureBuilder.build_heatmap_figure`, `PlotlyMapCallbackManager` (heatmap callbacks)

---

#### Class 4: `PlotlyMapFigureBuilder` (Phase 4)

**Purpose**: Build Plotly figures for all map layers (walls, devices, clients, heatmap)  
**Location**: `src/maps/plotly_map_figures.py`  
**CC Target**: ≤10 per method

```python
class PlotlyMapFigureBuilder:
    """
    Builds Plotly figures for map visualization layers.
    Consolidates figure construction logic from _launch_plotly_viewer.
    """
    
    def __init__(self,
                 svg_data: Optional[str] = None,
                 device_inventory: Optional[Dict[str, Any]] = None,
                 client_data: Optional[Dict[str, Any]] = None,
                 style_config: Optional[Dict[str, Any]] = None):
        """
        Initialize figure builder.
        
        Args:
            svg_data: SVG floor plan (walls)
            device_inventory: Device metadata (APs, switches, gateways)
            client_data: Connected clients
            style_config: Styling overrides (colors, fonts, sizes)
        """
        self.svg_data = svg_data
        self.device_inventory = device_inventory or {}
        self.client_data = client_data or {}
        self.style_config = style_config or {}
    
    def build_walls_figure(self) -> go.Figure:
        """
        Build Plotly figure for walls/floor plan.
        
        Returns:
            Plotly Figure with SVG overlay and styling
        
        Raises:
            ValueError: If SVG data invalid
        """
        pass
    
    def build_device_scatter(self, 
                           device_type_filter: Optional[List[str]] = None) -> go.Scatter:
        """
        Build scatter trace for devices (APs, switches, gateways).
        
        Args:
            device_type_filter: List of device types to include (None = all)
        
        Returns:
            Plotly scatter trace
        
        Raises:
            ValueError: If device data malformed
        """
        pass
    
    def build_client_scatter(self, 
                           include_disconnected: bool = False) -> go.Scatter:
        """
        Build scatter trace for connected clients.
        
        Args:
            include_disconnected: Include disconnected clients
        
        Returns:
            Plotly scatter trace
        """
        pass
    
    def build_heatmap_figure(self,
                            heatmap_renderer: 'CoverageHeatmapRenderer',
                            data: Dict[str, Any]) -> go.Heatmap:
        """
        Build heatmap trace using renderer.
        
        Args:
            heatmap_renderer: CoverageHeatmapRenderer instance
            data: Heatmap data (coordinates, signal strengths)
        
        Returns:
            Plotly heatmap trace
        """
        pass
    
    def build_combined_figure(self,
                             layers: List[str],
                             heatmap_renderer: Optional['CoverageHeatmapRenderer'] = None) -> go.Figure:
        """
        Build combined figure with multiple layers.
        
        Args:
            layers: List of layers to include ('walls', 'devices', 'clients', 'heatmap')
            heatmap_renderer: Renderer (required if 'heatmap' in layers)
        
        Returns:
            Complete Plotly Figure
        
        Raises:
            ValueError: If layer unsupported or dependencies missing
        """
        pass
    
    def validate_figure_structure(self, 
                                  figure: go.Figure,
                                  expected_traces: Optional[List[str]] = None) -> bool:
        """
        Validate figure structure matches expected output.
        
        Args:
            figure: Plotly figure to validate
            expected_traces: Expected trace names (e.g., ['walls', 'devices'])
        
        Returns:
            True if valid
        
        Raises:
            AssertionError: If structure invalid
        """
        pass
    
    def get_figure_json(self, figure: go.Figure) -> str:
        """
        Export figure to JSON string (for caching/comparison).
        
        Args:
            figure: Plotly figure
        
        Returns:
            JSON representation
        """
        pass
```

**Dependencies**: `plotly.graph_objects`, `numpy`, `CoverageHeatmapRenderer`  
**Call Sites**: `PlotlyMapViewer.create_layout`, `PlotlyMapCallbackManager` (figure update callbacks)

---

#### Class 5: `PlotlyMapCallbackManager` (Phase 5)

**Purpose**: Register and organize ~25 callback functions  
**Location**: `src/maps/plotly_map_callbacks.py`  
**CC Target**: ≤10 per callback group (high complexity, so split into groups)

```python
class PlotlyMapCallbackManager:
    """
    Manages callback registration and execution for Plotly map viewer.
    Organizes ~25 callbacks into logical groups:
    - Layer toggles (walls, devices, clients)
    - Heatmap algorithm selection and parameters
    - Export functions (download, screenshot)
    - Control interactions (search, filter)
    """
    
    def __init__(self,
                 app: dash.Dash,
                 viewer: 'PlotlyMapViewer',
                 serializer: 'PlotlyMapDataSerializer'):
        """
        Initialize callback manager.
        
        Args:
            app: Dash app instance
            viewer: PlotlyMapViewer parent (for access to builders/renderers)
            serializer: Data serializer for callback inputs/outputs
        """
        self.app = app
        self.viewer = viewer
        self.serializer = serializer
        self._registered_callbacks = []
    
    def register_all_callbacks(self) -> int:
        """
        Register all callback groups.
        
        Returns:
            Total number of callbacks registered
        
        Raises:
            RuntimeError: If callback registration fails
        """
        count = 0
        count += self.register_layer_callbacks()
        count += self.register_heatmap_callbacks()
        count += self.register_control_callbacks()
        count += self.register_export_callbacks()
        return count
    
    def register_layer_callbacks(self) -> int:
        """
        Register layer toggle callbacks (show/hide walls, devices, clients).
        
        Returns:
            Number of callbacks registered (typically 3–5)
        
        Example callback:
            @self.app.callback(
                Output('walls-layer', 'visible'),
                Input('walls-toggle', 'n_clicks'),
                State('walls-layer', 'visible')
            )
            def toggle_walls(n_clicks, current_visible):
                return not current_visible
        """
        pass
    
    def register_heatmap_callbacks(self) -> int:
        """
        Register heatmap control callbacks (algorithm, smoothing, colorscale).
        
        Returns:
            Number of callbacks registered (typically 5–10)
        
        Example callback:
            @self.app.callback(
                Output('heatmap-trace', 'figure'),
                [Input('heatmap-algorithm-dropdown', 'value'),
                 Input('smoothing-slider', 'value')],
                [State('heatmap-data-store', 'data')]
            )
            def update_heatmap(algorithm, smoothing, stored_data):
                renderer = CoverageHeatmapRenderer(..., algorithm=algorithm)
                grid = renderer.interpolate_grid(json.loads(stored_data))
                grid = renderer.smooth_heatmap(grid, kernel_size=smoothing)
                return renderer.build_heatmap_figure(grid)
        """
        pass
    
    def register_control_callbacks(self) -> int:
        """
        Register control callbacks (search, filter, zoom, pan).
        
        Returns:
            Number of callbacks registered (typically 3–5)
        """
        pass
    
    def register_export_callbacks(self) -> int:
        """
        Register export callbacks (download CSV, screenshot).
        
        Returns:
            Number of callbacks registered (typically 2–3)
        """
        pass
    
    def validate_callback_count(self, expected_count: int = 25) -> bool:
        """
        Validate that expected number of callbacks are registered.
        
        Args:
            expected_count: Expected callback count (default 25)
        
        Returns:
            True if actual count matches expected
        
        Raises:
            AssertionError: If mismatch
        """
        actual = len(self._registered_callbacks)
        assert actual == expected_count, \
            f"Expected {expected_count} callbacks, got {actual}"
        return True
    
    def get_callback_list(self) -> List[str]:
        """
        Get list of registered callback IDs.
        
        Returns:
            List of callback identifiers
        """
        pass
```

**Key Constraint**: Callback decorators MUST remain on methods to preserve Dash's discovery mechanism.

**Dependencies**: `dash`, `PlotlyMapViewer`, `PlotlyMapDataSerializer`, `CoverageHeatmapRenderer`  
**Call Sites**: `PlotlyMapViewer.create_app`

---

#### Class 6: `PlotlyMapViewer` (Phase 6)

**Purpose**: Main orchestrator; initializes Dash app and coordinates all components  
**Location**: `src/maps/plotly_map_viewer.py` (new file)  
**CC Target**: ≤10 (mostly delegation)

```python
class PlotlyMapViewer:
    """
    Main orchestrator for Plotly map viewer.
    Initializes Dash app, registers callbacks, and manages server lifecycle.
    
    Replaces the core logic of _launch_plotly_viewer with a modular design.
    """
    
    def __init__(self,
                 org_id: str,
                 site_id: str,
                 device_inventory: Dict[str, Any],
                 client_data: Dict[str, Any],
                 svg_data: Optional[str] = None,
                 style_config: Optional[Dict[str, Any]] = None,
                 heatmap_algorithm: str = 'kriging'):
        """
        Initialize map viewer.
        
        Args:
            org_id: Organization ID
            site_id: Site ID
            device_inventory: Device metadata
            client_data: Client data
            svg_data: SVG floor plan (optional)
            style_config: Styling overrides (optional)
            heatmap_algorithm: Heatmap interpolation algorithm
        """
        self.org_id = org_id
        self.site_id = site_id
        self.device_inventory = device_inventory
        self.client_data = client_data
        self.svg_data = svg_data
        self.style_config = style_config or {}
        self.heatmap_algorithm = heatmap_algorithm
        
        # Initialize components
        self.template_mgr = DashTemplateManager(org_id)
        self.figure_builder = PlotlyMapFigureBuilder(
            svg_data, device_inventory, client_data, style_config
        )
        self.heatmap_renderer = CoverageHeatmapRenderer(
            site_id, algorithm=heatmap_algorithm
        )
        self.serializer = PlotlyMapDataSerializer()
        
        self.app = None
        self.callback_mgr = None
    
    def create_app(self) -> dash.Dash:
        """
        Create and configure Dash app.
        
        Returns:
            Configured Dash app (ready to run)
        
        Raises:
            RuntimeError: If app creation fails
        """
        pass
    
    def _create_layout(self) -> dash.html.Div:
        """
        Build Dash layout structure.
        
        Returns:
            Layout Div containing all components
        """
        pass
    
    def _register_callbacks(self) -> int:
        """
        Register all callbacks.
        
        Returns:
            Number of callbacks registered
        """
        pass
    
    def run_server(self,
                   host: str = '0.0.0.0',
                   port: int = 8050,
                   debug: bool = False,
                   threaded: bool = True) -> None:
        """
        Launch Dash server.
        
        Args:
            host: Server hostname
            port: Server port
            debug: Debug mode flag
            threaded: Enable threading
        
        Raises:
            RuntimeError: If server startup fails
        """
        pass
    
    def validate_app(self) -> bool:
        """
        Validate app configuration and callbacks.
        
        Returns:
            True if valid
        
        Raises:
            AssertionError: If validation fails
        """
        pass
```

**Dependencies**: All 5 extracted classes  
**Call Sites**: `MapsManager._launch_plotly_viewer`

---

### 1.2 Method Extraction Mapping

| Current Code (lines) | Target Class | Target Method | Est. Effort |
|---|---|---|---|
| 3070–3200 (HTML/CSS) | `DashTemplateManager` | `get_custom_css`, `get_layout_html` | 1 hr |
| 3200–3300 (JSON utils) | `PlotlyMapDataSerializer` | `serialize_*`, `deserialize_*` | 1.5 hrs |
| 3700–4500 (heatmap algo) | `CoverageHeatmapRenderer` | `interpolate_grid`, `apply_colorscale` | 4 hrs |
| 3300–3700 (figure build) | `PlotlyMapFigureBuilder` | `build_*_figure` | 5 hrs |
| 4500–8000 (callbacks) | `PlotlyMapCallbackManager` | `register_*_callbacks` | 8 hrs |
| 3010–3070, 8000–8256 (orchestration) | `PlotlyMapViewer` + `MapsManager._launch_plotly_viewer` | `create_app`, `run_server`, orchestration | 6 hrs |

---

## Part 2: File Structure

### New Files to Create

```
src/maps/
  ├── plotly_map_templates.py        (NEW - Phase 1)
  │   └── class DashTemplateManager
  │
  ├── plotly_map_serializer.py       (NEW - Phase 2)
  │   └── class PlotlyMapDataSerializer
  │
  ├── plotly_map_heatmap.py          (NEW - Phase 3)
  │   └── class CoverageHeatmapRenderer
  │
  ├── plotly_map_figures.py          (NEW - Phase 4)
  │   └── class PlotlyMapFigureBuilder
  │
  ├── plotly_map_callbacks.py        (NEW - Phase 5)
  │   └── class PlotlyMapCallbackManager
  │
  ├── plotly_map_viewer.py           (NEW - Phase 6)
  │   └── class PlotlyMapViewer
  │
  └── maps_manager.py                (MODIFIED - Refactor _launch_plotly_viewer)
```

### Modified Files

```
src/maps/maps_manager.py
  - Lines 3010–8256: Replace with call to PlotlyMapViewer
  - Imports: Add new imports for extracted classes
  - CC reduction: 138 → ≤10
```

### Test Files to Create

```
tests/maps/
  ├── test_plotly_map_templates.py        (Phase 1)
  ├── test_plotly_map_serializer.py       (Phase 2)
  ├── test_plotly_map_heatmap.py          (Phase 3)
  ├── test_plotly_map_figures.py          (Phase 4)
  ├── test_plotly_map_callbacks.py        (Phase 5)
  ├── test_plotly_map_viewer.py           (Phase 6)
  ├── test_plotly_map_viewer_regression.py (Regression tests, all phases)
  └── test_plotly_map_viewer_integration.py (E2E tests, all phases)
```

---

## Part 3: Dependency Graph

### Data Flow Diagram

```
MapsManager._launch_plotly_viewer(org_id, site_id, device_inv, client_data)
    │
    └─> PlotlyMapViewer(org_id, site_id, device_inv, client_data)
        │
        ├─> DashTemplateManager(org_id)
        │   ├─> get_custom_css() → CSS string
        │   ├─> get_layout_html() → Layout dict
        │   └─> get_app_meta() → Meta dict
        │
        ├─> PlotlyMapFigureBuilder(svg, device_inv, client_data, style_config)
        │   ├─> build_walls_figure() → Figure
        │   ├─> build_device_scatter() → Trace
        │   ├─> build_client_scatter() → Trace
        │   └─> build_heatmap_figure(heatmap_renderer, data) → Figure
        │       │
        │       └─> CoverageHeatmapRenderer.build_heatmap_figure(grid)
        │
        ├─> CoverageHeatmapRenderer(site_id, algorithm='kriging')
        │   ├─> interpolate_grid(data) → np.ndarray
        │   ├─> smooth_heatmap(grid, kernel_size) → np.ndarray
        │   └─> apply_colorscale(grid, colorscale) → np.ndarray
        │
        ├─> PlotlyMapDataSerializer()
        │   ├─> serialize_figure_state(fig_dict) → JSON string
        │   ├─> deserialize_callback_inputs(json_str) → Dict
        │   └─> validate_numeric_precision(original, refactored) → bool
        │
        └─> PlotlyMapCallbackManager(app, viewer, serializer)
            ├─> register_layer_callbacks() → int (3–5 callbacks)
            ├─> register_heatmap_callbacks() → int (5–10 callbacks)
            ├─> register_control_callbacks() → int (3–5 callbacks)
            └─> register_export_callbacks() → int (2–3 callbacks)
                │
                └─> Each callback uses:
                    ├─> PlotlyMapFigureBuilder
                    ├─> CoverageHeatmapRenderer
                    └─> PlotlyMapDataSerializer

Callback I/O Flow:
  Dash UI Input → Callback function → Serializer.deserialize() → Processing
                  ↓
                  PlotlyMapFigureBuilder / CoverageHeatmapRenderer
                  ↓
                  Serializer.serialize() → Callback Output → Dash UI
```

### Class Dependency Matrix

| Class | Depends On | Used By |
|---|---|---|
| `DashTemplateManager` | None | `PlotlyMapViewer` |
| `PlotlyMapDataSerializer` | `json`, `numpy` | All callbacks, `CoverageHeatmapRenderer` |
| `CoverageHeatmapRenderer` | `scipy`, `numpy` | `PlotlyMapFigureBuilder`, `PlotlyMapCallbackManager` |
| `PlotlyMapFigureBuilder` | `CoverageHeatmapRenderer`, `plotly` | `PlotlyMapViewer`, `PlotlyMapCallbackManager` |
| `PlotlyMapCallbackManager` | All above + `dash` | `PlotlyMapViewer` |
| `PlotlyMapViewer` | All above | `MapsManager._launch_plotly_viewer` |

---

## Part 4: Migration Strategy

### Step-by-Step Copy → Extract → Test → Validate → Remove

#### Phase 1: Templates (Low Risk)

**Step 1.1**: Copy current HTML/CSS code from lines 3070–3200
```python
# Current code in _launch_plotly_viewer:
custom_css = """
    ... CSS here ...
"""
layout = html.Div([...])  # ~130 lines

# New file: src/maps/plotly_map_templates.py
class DashTemplateManager:
    def get_custom_css(self):
        return "... CSS here ..."
    
    def get_layout_html(self):
        return html.Div([...])
```

**Step 1.2**: Write unit tests for `DashTemplateManager`
```python
def test_get_custom_css():
    mgr = DashTemplateManager(org_id="test-org")
    css = mgr.get_custom_css()
    assert "background-color" in css
    assert len(css) == len(ORIGINAL_CSS)  # Byte count match
```

**Step 1.3**: Update `MapsManager._launch_plotly_viewer` to use new class
```python
# In MapsManager._launch_plotly_viewer:
from src.maps.plotly_map_templates import DashTemplateManager
template_mgr = DashTemplateManager(self.org_id)
custom_css = template_mgr.get_custom_css()
layout = template_mgr.get_layout_html()
```

**Step 1.4**: Run regression tests
```bash
pytest tests/maps/test_plotly_map_viewer_integration.py -v
```

**Step 1.5**: Compare web UI visually (CSS rendering)
- Launch app, inspect browser styles
- Verify CSS unchanged

---

#### Phase 2: Serialization (Low Risk)

**Step 2.1**: Identify JSON serialization patterns (grep)
```bash
grep -n "json.dumps\|json.loads" src/maps/maps_manager.py | head -20
```

**Step 2.2**: Extract to `PlotlyMapDataSerializer`
```python
# New class in src/maps/plotly_map_serializer.py
class PlotlyMapDataSerializer:
    def serialize_figure_state(self, fig_dict):
        return json.dumps(fig_dict, default=self._encode_defaults)
    
    def _encode_defaults(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        # ... etc
```

**Step 2.3**: Test roundtrip (serialize → deserialize)
```python
def test_serialize_deserialize_roundtrip():
    serializer = PlotlyMapDataSerializer()
    original = {"figure": {"data": [...]}, "heatmap": [...]}
    json_str = serializer.serialize_figure_state(original)
    deserialized = serializer.deserialize_figure_state(json_str)
    assert deserialized == original
```

**Step 2.4**: Replace all `json.dumps/loads` calls in `_launch_plotly_viewer`
```python
# Before:
callback_data = json.dumps(fig_dict)

# After:
callback_data = self.serializer.serialize_figure_state(fig_dict)
```

---

#### Phase 3: Heatmap (Medium Risk)

**Step 3.1**: Identify heatmap algorithm code (lines ~3700–4500)
```bash
grep -n "def.*heatmap\|scipy.interpolate\|kriging\|idw" src/maps/maps_manager.py
```

**Step 3.2**: Copy heatmap algorithm into `CoverageHeatmapRenderer`
```python
# New class in src/maps/plotly_map_heatmap.py
class CoverageHeatmapRenderer:
    def interpolate_grid(self, data):
        # Copy kriging / IDW algorithm here
        from scipy.interpolate import Rbf
        # ... implementation
        return interpolated_grid  # shape (NxN)
```

**Step 3.3**: Generate test data snapshot from original
```bash
# Run original code, capture output
python -c "
from src.maps.maps_manager import MapsManager
mgr = MapsManager(...)
result = mgr._launch_plotly_viewer()
# Save heatmap output to JSON file
import json
with open('tests/data/heatmap_output_baseline.json', 'w') as f:
    json.dump(result['heatmap_grid'], f)
"
```

**Step 3.4**: Unit test heatmap with baseline data
```python
def test_heatmap_interpolation_matches_original():
    import numpy as np
    import json
    
    renderer = CoverageHeatmapRenderer(site_id='test-site', algorithm='kriging')
    grid_new = renderer.interpolate_grid(TEST_DATA)
    
    with open('tests/data/heatmap_output_baseline.json') as f:
        grid_original = np.array(json.load(f))
    
    assert np.allclose(grid_new, grid_original, rtol=1e-10)
```

**Step 3.5**: Replace heatmap code in `_launch_plotly_viewer`
```python
# Before:
interpolated_grid = kriging_interpolate(data, ...)  # ~200 lines inline

# After:
heatmap_renderer = CoverageHeatmapRenderer(site_id, algorithm='kriging')
interpolated_grid = heatmap_renderer.interpolate_grid(data)
```

---

#### Phase 4: Figures (Medium Risk)

**Step 4.1**: Extract figure building (lines ~3300–3700)
```python
# New class in src/maps/plotly_map_figures.py
class PlotlyMapFigureBuilder:
    def build_walls_figure(self):
        # Copy from _launch_plotly_viewer lines 3300-3350
        # Build Plotly figure from SVG
        return go.Figure(...)
    
    def build_device_scatter(self):
        # Copy from _launch_plotly_viewer lines 3350-3450
        return go.Scatter(...)
```

**Step 4.2**: Test figure JSON equivalence
```python
def test_walls_figure_json_match():
    builder = PlotlyMapFigureBuilder(svg_data, style_config)
    fig_new = builder.build_walls_figure()
    
    fig_original = original_build_walls_figure()
    
    # Compare JSON representation
    assert fig_new.to_json() == fig_original.to_json()
```

**Step 4.3**: Replace figure code in `_launch_plotly_viewer`
```python
# Before:
walls_fig = go.Figure(...)  # ~50 lines
device_trace = go.Scatter(...)  # ~50 lines

# After:
figure_builder = PlotlyMapFigureBuilder(svg_data, device_inv, client_data)
walls_fig = figure_builder.build_walls_figure()
device_trace = figure_builder.build_device_scatter()
```

---

#### Phase 5: Callbacks (High Risk)

**Step 5.1**: Identify all callback definitions (lines ~4500–8000)
```bash
grep -n "@app.callback" src/maps/maps_manager.py | wc -l
# Should be ~25
```

**Step 5.2**: Group callbacks by category
```python
# Group 1: Layer toggles (@app.callback for walls, devices, clients)
# Group 2: Heatmap controls (algorithm dropdown, smoothing slider)
# Group 3: Interactions (search, filter, zoom)
# Group 4: Export (download CSV, screenshot)
```

**Step 5.3**: Extract callback groups into `PlotlyMapCallbackManager`
```python
# New class in src/maps/plotly_map_callbacks.py
class PlotlyMapCallbackManager:
    def register_layer_callbacks(self):
        @self.app.callback(Output(...), Input(...))
        def toggle_walls(...):
            # Copy callback code here
            pass
    
    def register_heatmap_callbacks(self):
        @self.app.callback(Output(...), [Input(...)])
        def update_heatmap(...):
            # Copy callback code here
            pass
```

**Step 5.4**: Test each callback group
```python
def test_layer_toggle_callback():
    app = create_test_app()
    mgr = PlotlyMapCallbackManager(app, viewer, serializer)
    mgr.register_layer_callbacks()
    
    # Verify callback was registered
    assert 'show_walls' in app.callback_map
    
    # Simulate callback invocation
    result = app.callback_map['show_walls']([True], None)
    assert result is not None
```

**Step 5.5**: Replace callbacks in `_launch_plotly_viewer`
```python
# Before: 25 callbacks defined inline (~3500 lines)
@app.callback(Output(...), Input(...))
def callback1(...):
    pass

@app.callback(Output(...), Input(...))
def callback2(...):
    pass
# ... repeat 23 more times

# After:
callback_mgr = PlotlyMapCallbackManager(app, viewer, serializer)
callback_mgr.register_all_callbacks()
```

---

#### Phase 6: Integration (High Risk)

**Step 6.1**: Create `PlotlyMapViewer` orchestrator
```python
# New class in src/maps/plotly_map_viewer.py
class PlotlyMapViewer:
    def __init__(self, org_id, site_id, device_inv, client_data, ...):
        self.template_mgr = DashTemplateManager(org_id)
        self.figure_builder = PlotlyMapFigureBuilder(...)
        self.heatmap_renderer = CoverageHeatmapRenderer(site_id)
        self.serializer = PlotlyMapDataSerializer()
    
    def create_app(self):
        app = dash.Dash(...)
        app.layout = self._create_layout()
        self.callback_mgr = PlotlyMapCallbackManager(app, self, self.serializer)
        self.callback_mgr.register_all_callbacks()
        return app
```

**Step 6.2**: Update `MapsManager._launch_plotly_viewer` to use `PlotlyMapViewer`
```python
# Before: 5,247 lines of direct implementation
def _launch_plotly_viewer(self, ...):
    # HTML/CSS setup (~130 lines)
    # Figure building (~400 lines)
    # Heatmap algorithm (~800 lines)
    # ~25 callbacks (~3500 lines)
    # Server startup (~50 lines)
    pass

# After: Delegation to PlotlyMapViewer
def _launch_plotly_viewer(self, ...):
    viewer = PlotlyMapViewer(
        org_id=self.org_id,
        site_id=self.site_id,
        device_inventory=self.device_inventory,
        client_data=self.client_data,
        svg_data=self.svg_data
    )
    app = viewer.create_app()
    viewer.run_server(host='0.0.0.0', port=8050, debug=False)
```

**Step 6.3**: Run full integration test suite
```bash
pytest tests/maps/test_plotly_map_viewer_integration.py -v
pytest tests/maps/test_plotly_map_viewer_regression.py -v
```

**Step 6.4**: Confirm web UI still works
- Launch refactored app
- Test UI interactions (button clicks, callbacks)
- Compare outputs to original

---

## Part 5: Callback Registration Pattern

### Key Constraint: Decorators Must Remain on Methods

**Why**: Dash discovers callbacks via decorator inspection at import time. Decorators MUST be on the actual callback function, not registered programmatically.

### Pattern: Grouped Callback Registration

```python
class PlotlyMapCallbackManager:
    """
    Organizes ~25 callbacks into groups for manageability.
    Each group registers 3–10 related callbacks.
    """
    
    def __init__(self, app, viewer, serializer):
        self.app = app
        self.viewer = viewer
        self.serializer = serializer
    
    # ===== LAYER CALLBACKS (3–5 callbacks) =====
    def register_layer_callbacks(self) -> int:
        """Toggle visibility of map layers (walls, devices, clients)."""
        count = 0
        
        # Callback 1: Toggle Walls
        @self.app.callback(
            Output('walls-layer', 'visible'),
            Input('toggle-walls-button', 'n_clicks'),
            State('walls-layer', 'visible')
        )
        def toggle_walls_callback(n_clicks, current_visible):
            return not current_visible if n_clicks else current_visible
        
        count += 1
        
        # Callback 2: Toggle Devices
        @self.app.callback(
            Output('devices-layer', 'visible'),
            Input('toggle-devices-button', 'n_clicks'),
            State('devices-layer', 'visible')
        )
        def toggle_devices_callback(n_clicks, current_visible):
            return not current_visible if n_clicks else current_visible
        
        count += 1
        
        # Callback 3: Toggle Clients
        @self.app.callback(
            Output('clients-layer', 'visible'),
            Input('toggle-clients-button', 'n_clicks'),
            State('clients-layer', 'visible')
        )
        def toggle_clients_callback(n_clicks, current_visible):
            return not current_visible if n_clicks else current_visible
        
        count += 1
        
        return count
    
    # ===== HEATMAP CALLBACKS (5–10 callbacks) =====
    def register_heatmap_callbacks(self) -> int:
        """Heatmap algorithm, smoothing, colorscale controls."""
        count = 0
        
        # Callback 4: Update heatmap on algorithm change
        @self.app.callback(
            Output('heatmap-figure', 'figure'),
            [Input('heatmap-algorithm-dropdown', 'value'),
             Input('heatmap-smoothing-slider', 'value')],
            State('heatmap-data-store', 'data')
        )
        def update_heatmap(algorithm, smoothing, stored_data):
            if stored_data is None:
                return empty_figure()
            
            data = self.serializer.deserialize_callback_inputs(stored_data)
            renderer = self.viewer.heatmap_renderer
            renderer.algorithm = algorithm
            grid = renderer.interpolate_grid(data)
            grid = renderer.smooth_heatmap(grid, kernel_size=smoothing)
            return renderer.build_heatmap_figure(grid)
        
        count += 1
        
        # Callback 5: Update colorscale
        @self.app.callback(
            Output('heatmap-figure', 'figure'),
            Input('heatmap-colorscale-dropdown', 'value'),
            State('heatmap-figure', 'figure')
        )
        def update_colorscale(colorscale, current_figure):
            # Update figure's colorscale
            pass
        
        count += 1
        
        # ... more heatmap callbacks (smoothing, min/max range, etc.)
        
        return count
    
    # ===== CONTROL CALLBACKS (3–5 callbacks) =====
    def register_control_callbacks(self) -> int:
        """Search, filter, pan/zoom controls."""
        count = 0
        # ... callback definitions
        return count
    
    # ===== EXPORT CALLBACKS (2–3 callbacks) =====
    def register_export_callbacks(self) -> int:
        """Download CSV, screenshot, etc."""
        count = 0
        # ... callback definitions
        return count
```

### Callback Preservation Rules

1. **Decorator location**: `@self.app.callback(...)` remains on methods (not moved elsewhere)
2. **Method scope**: Callbacks are methods of `PlotlyMapCallbackManager` (access `self` for context)
3. **Closure over state**: Callback methods use `self.viewer`, `self.serializer` for data access
4. **Input/Output IDs**: Must exactly match Dash component IDs in layout
5. **Data flow**: Callback inputs → deserialize → process → serialize → callback outputs

---

## Part 6: Test Strategy

### Unit Tests (Per Phase)

#### Phase 1: Templates

```python
# tests/maps/test_plotly_map_templates.py

def test_get_custom_css():
    """CSS string matches original byte-for-byte."""
    mgr = DashTemplateManager(org_id="test-org")
    css = mgr.get_custom_css()
    assert len(css) == len(ORIGINAL_CSS)
    assert "background-color" in css

def test_get_layout_html():
    """Layout structure contains expected components."""
    mgr = DashTemplateManager(org_id="test-org")
    layout = mgr.get_layout_html()
    assert layout is not None
    # Add more assertions for specific components
```

#### Phase 2: Serialization

```python
# tests/maps/test_plotly_map_serializer.py

def test_serialize_deserialize_figure():
    """Round-trip serialization produces exact match."""
    serializer = PlotlyMapDataSerializer()
    original_fig = {"data": [...], "layout": {...}}
    json_str = serializer.serialize_figure_state(original_fig)
    deserialized = serializer.deserialize_figure_state(json_str)
    assert deserialized == original_fig

def test_numeric_precision_validation():
    """Numeric comparison with tolerance."""
    serializer = PlotlyMapDataSerializer()
    data1 = {"grid": [[1.0, 2.0], [3.0, 4.0]]}
    data2 = {"grid": [[1.0000000001, 2.0], [3.0, 4.0]]}
    assert serializer.validate_numeric_precision(data1, data2, rtol=1e-9)
```

#### Phase 3: Heatmap

```python
# tests/maps/test_plotly_map_heatmap.py

def test_interpolate_grid_shape():
    """Grid output shape matches resolution."""
    renderer = CoverageHeatmapRenderer(site_id="test", algorithm="kriging")
    grid = renderer.interpolate_grid(TEST_DATA)
    assert grid.shape == (100, 100)  # Default resolution

def test_heatmap_algorithm_matches_original():
    """Interpolated grid numerically identical to original."""
    renderer = CoverageHeatmapRenderer(site_id="test", algorithm="kriging")
    grid_new = renderer.interpolate_grid(TEST_DATA)
    grid_original = load_baseline_heatmap()
    assert np.allclose(grid_new, grid_original, rtol=1e-10)

def test_colorscale_range():
    """Colorscale output values in [0, 1]."""
    renderer = CoverageHeatmapRenderer(site_id="test")
    grid = np.random.rand(100, 100)
    scaled = renderer.apply_colorscale(grid)
    assert np.all(scaled >= 0) and np.all(scaled <= 1)
```

#### Phase 4: Figures

```python
# tests/maps/test_plotly_map_figures.py

def test_walls_figure_structure():
    """Walls figure has correct Plotly structure."""
    builder = PlotlyMapFigureBuilder(svg_data=TEST_SVG)
    fig = builder.build_walls_figure()
    assert len(fig.data) > 0
    assert fig.data[0].name == "Walls"

def test_device_scatter_trace():
    """Device scatter includes all devices."""
    inventory = {
        "devices": [
            {"id": "ap1", "x": 10, "y": 20, "type": "AP"},
            {"id": "ap2", "x": 30, "y": 40, "type": "AP"}
        ]
    }
    builder = PlotlyMapFigureBuilder(device_inventory=inventory)
    trace = builder.build_device_scatter()
    assert len(trace.x) == 2
    assert trace.x[0] == 10

def test_combined_figure_all_layers():
    """Combined figure includes all requested layers."""
    builder = PlotlyMapFigureBuilder(svg_data=TEST_SVG, ...)
    renderer = CoverageHeatmapRenderer(site_id="test")
    fig = builder.build_combined_figure(
        layers=['walls', 'devices', 'clients', 'heatmap'],
        heatmap_renderer=renderer
    )
    # Verify all traces present
    assert len(fig.data) >= 4
```

#### Phase 5: Callbacks

```python
# tests/maps/test_plotly_map_callbacks.py

def test_callback_registration_count():
    """All callbacks are registered."""
    app = dash.Dash(__name__)
    viewer = PlotlyMapViewer(...)
    mgr = PlotlyMapCallbackManager(app, viewer, PlotlyMapDataSerializer())
    count = mgr.register_all_callbacks()
    assert count == 25  # or expected count

def test_layer_toggle_callback():
    """Layer toggle callback invocation."""
    app = dash.Dash(__name__)
    viewer = PlotlyMapViewer(...)
    mgr = PlotlyMapCallbackManager(app, viewer, PlotlyMapDataSerializer())
    mgr.register_layer_callbacks()
    
    # Simulate callback
    result = app.callback_map['toggle_walls']([1], True)
    assert result == False  # Toggled

def test_heatmap_update_callback():
    """Heatmap update with new algorithm."""
    app = dash.Dash(__name__)
    viewer = PlotlyMapViewer(...)
    mgr = PlotlyMapCallbackManager(app, viewer, PlotlyMapDataSerializer())
    mgr.register_heatmap_callbacks()
    
    # Simulate callback with test data
    stored_data = json.dumps(TEST_HEATMAP_DATA)
    result = app.callback_map['update_heatmap']('idw', 3, stored_data)
    assert result is not None  # Figure produced
```

#### Phase 6: Integration

```python
# tests/maps/test_plotly_map_viewer.py

def test_viewer_initialization():
    """Viewer creates Dash app with all components."""
    viewer = PlotlyMapViewer(
        org_id="test-org",
        site_id="test-site",
        device_inventory={...},
        client_data={...}
    )
    app = viewer.create_app()
    assert app is not None
    assert app.layout is not None

def test_app_callback_count():
    """App has all 25 callbacks registered."""
    viewer = PlotlyMapViewer(...)
    app = viewer.create_app()
    assert len(app.callback_map) == 25  # Expected count
```

### Regression Tests (Behavior Comparison)

```python
# tests/maps/test_plotly_map_viewer_regression.py

def test_figure_json_equivalence():
    """Refactored figures JSON-identical to original."""
    # Build with original code
    original_fig = original_build_walls_figure()
    
    # Build with refactored code
    builder = PlotlyMapFigureBuilder(svg_data=TEST_SVG)
    refactored_fig = builder.build_walls_figure()
    
    # Compare JSON
    assert original_fig.to_json() == refactored_fig.to_json()

def test_heatmap_grid_numeric_equivalence():
    """Heatmap interpolation numerically identical."""
    original_grid = original_interpolate_heatmap(TEST_DATA)
    
    renderer = CoverageHeatmapRenderer(site_id="test", algorithm="kriging")
    refactored_grid = renderer.interpolate_grid(TEST_DATA)
    
    assert np.allclose(original_grid, refactored_grid, rtol=1e-10)

def test_callback_state_serialization_identical():
    """Callback state serialization byte-for-byte identical."""
    test_state = {"figure": {...}, "heatmap": [...]}
    
    original_json = original_serialize(test_state)
    
    serializer = PlotlyMapDataSerializer()
    refactored_json = serializer.serialize_figure_state(test_state)
    
    assert original_json == refactored_json
```

### Integration Tests (End-to-End)

```python
# tests/maps/test_plotly_map_viewer_integration.py

def test_full_workflow_map_rendering():
    """Full workflow: create app, render map, interact with UI."""
    viewer = PlotlyMapViewer(
        org_id="test-org",
        site_id="test-site",
        device_inventory=FULL_DEVICE_INVENTORY,
        client_data=FULL_CLIENT_DATA
    )
    app = viewer.create_app()
    
    # Verify app structure
    assert app.layout is not None
    assert len(app.callback_map) >= 20
    
    # Simulate UI interaction: toggle walls
    # (requires accessing callback via app.callback_map)

def test_callback_chain_execution():
    """Callbacks execute in sequence with correct data flow."""
    app = create_test_app_with_viewer()
    
    # Simulate user clicking "toggle heatmap" button
    # Verify heatmap figure is updated
    # Verify data flows through callbacks correctly

def test_error_handling_invalid_data():
    """App handles invalid input gracefully."""
    viewer = PlotlyMapViewer(
        org_id="test-org",
        site_id="test-site",
        device_inventory={},  # Empty
        client_data={}
    )
    app = viewer.create_app()
    # Should not crash; should show empty or default figure
```

---

## Part 7: Quality Gate Checklist

| Gate | Tool | Command | Pass Criteria |
|---|---|---|---|
| **Lint** | `ruff` | `ruff check src/maps/plotly_map*.py` | Zero violations |
| **Format** | `black` | `black --check src/maps/plotly_map*.py` | All formatted |
| **Type Check** | `mypy` | `mypy --strict src/maps/plotly_map*.py` | All types annotated, zero errors |
| **Security** | `bandit` | `bandit -r src/maps/plotly_map*.py` | No high-severity findings |
| **Dependency CVE** | `pip-audit` | `pip-audit` | No new vulnerabilities |
| **Unit Tests** | `pytest` | `pytest tests/maps/test_plotly_map*.py -v` | All pass |
| **Coverage** | `pytest-cov` | `pytest --cov=src/maps/ --cov-report=html` | ≥70% coverage |
| **Complexity** | `radon` | `radon cc src/maps/plotly_map*.py -a` | All methods ≤10 CC |
| **Code Quality** | `CodeQL` | GitHub Actions CI | Zero security findings |
| **Regression** | Custom | `pytest tests/maps/test_*_regression.py -v` | All pass (figure/heatmap/callback equivalence) |

---

## Part 8: Effort Estimation (Per Phase)

| Phase | Component | Activities | Hours | Risk |
|---|---|---|---|---|
| **1** | Templates | Extract, unit test, integrate | 2–3 | LOW |
| **2** | Serialization | Extract JSON, unit test, integrate | 2–3 | LOW |
| **3** | Heatmap | Extract algorithm, test precision, baseline | 4–5 | MEDIUM |
| **4** | Figures | Extract builders, test equivalence, integrate | 5–6 | MEDIUM |
| **5** | Callbacks | Extract groups, test each, state handling | 8–10 | HIGH |
| **6** | Integration | Orchestrate, E2E test, QA | 6–8 | HIGH |
| **Buffer** | (Debugging, refactoring, review) | — | 3–5 | — |
| **TOTAL** | | — | **30–40 hours** | — |

**Timeline**: 1–2 developer-weeks (assuming 20–40 hrs/week)

---

## Part 9: Risk Mitigation (High-Risk Phases)

### Risk 1: Callback State Corruption (Phase 5, Severity: CRITICAL)

**Problem**: Callback state serialization changes, breaking data flow between callbacks.

**Mitigation Strategy**:
1. Implement `PlotlyMapDataSerializer` in Phase 2 (before callbacks)
2. Unit test every callback input/output roundtrip
3. Snapshot test: save original callback states, compare refactored
4. Byte-for-byte JSON comparison

**Validation**:
```python
def test_callback_state_byte_exact():
    """Verify JSON serialization is 100% identical."""
    test_cases = [
        {"figure": {...}},
        {"heatmap": {...}},
        {"state": {...}}
    ]
    
    for case in test_cases:
        original_json = original_serialize(case)
        refactored_json = new_serialize(case)
        assert original_json == refactored_json, f"Mismatch in {case.keys()}"
```

**Rollback**: If serialization diverges, revert Phase 2 & 5, use original `json.dumps/loads` until fixed.

---

### Risk 2: Heatmap Algorithm Numerical Divergence (Phase 3, Severity: HIGH)

**Problem**: Floating-point precision or interpolation library versions change output slightly.

**Mitigation Strategy**:
1. Snapshot baseline heatmap output for 5+ real sites
2. Extract algorithm in isolated `CoverageHeatmapRenderer` class
3. Use tight tolerance: `np.allclose(rtol=1e-10, atol=1e-12)`
4. Document library versions (scipy, numpy) in requirements.txt
5. Test early and often

**Validation**:
```python
def test_heatmap_precision_within_tolerance():
    """Heatmap grid numerically identical within 1e-10 tolerance."""
    for site_sample in BASELINE_SAMPLES:
        original = original_interpolate(site_sample)
        refactored = refactored_interpolate(site_sample)
        max_diff = np.max(np.abs(original - refactored))
        assert max_diff < 1e-10, f"Tolerance exceeded: {max_diff}"
```

**Rollback**: If precision diverges beyond tolerance, investigate scipy version or interpolation parameters; do not merge until fixed.

---

### Risk 3: Dash Callback Registration Failure (Phase 5, Severity: CRITICAL)

**Problem**: Callback decorators on class methods don't register; Dash sees no callbacks.

**Mitigation Strategy**:
1. Early test: register single callback in test class, verify Dash discovers it
2. Use `@self.app.callback(...)` decorator syntax (standard Dash pattern)
3. Verify app.callback_map has expected count after registration
4. Integration test: trigger each callback, verify output

**Validation**:
```python
def test_dash_discovers_callbacks():
    """Dash callback_map includes all registered callbacks."""
    app = dash.Dash(__name__)
    mgr = PlotlyMapCallbackManager(app, viewer, serializer)
    count = mgr.register_all_callbacks()
    
    expected = 25  # or verify count
    actual = len(app.callback_map)
    assert actual == expected, f"Dash found {actual} callbacks, expected {expected}"
```

**Rollback**: If Dash doesn't discover callbacks, revert to programmatic registration via `app.callback()` or reassess decorator placement.

---

### Risk 4: Performance Regression (Phase 5–6, Severity: MEDIUM)

**Problem**: Additional object instantiation and method calls slow app startup >5%.

**Mitigation Strategy**:
1. Benchmark original startup time (measure in milliseconds)
2. Benchmark refactored startup time
3. Accept <5% regression
4. Profile with cProfile to identify bottlenecks
5. Lazy load expensive components if needed

**Validation**:
```python
def test_startup_performance_no_regression():
    """App startup time regression < 5%."""
    import timeit
    
    original_time = timeit.timeit(
        lambda: original_launch_plotly_viewer(),
        number=5
    ) / 5
    
    refactored_time = timeit.timeit(
        lambda: refactored_launch_plotly_viewer(),
        number=5
    ) / 5
    
    regression_pct = (refactored_time - original_time) / original_time * 100
    assert regression_pct < 5, f"Regression: {regression_pct}%"
```

**Mitigation**: If regression >5%, profile and optimize hot paths (e.g., defer heatmap preprocessing).

---

### Risk 5: Breaking Public API (Phase 6, Severity: CRITICAL)

**Problem**: `MapsManager._launch_plotly_viewer` signature or return type changes, breaking callers.

**Mitigation Strategy**:
1. Lock signature: no parameter additions/removals/renames
2. Lock return type: must return Dash app object
3. Integration test: existing callers work identically
4. Code review: explicit before/after signature comparison

**Validation**:
```python
def test_public_api_signature_unchanged():
    """_launch_plotly_viewer signature locked."""
    import inspect
    
    original_sig = inspect.signature(original_launch_plotly_viewer)
    refactored_sig = inspect.signature(refactored_launch_plotly_viewer)
    
    assert str(original_sig) == str(refactored_sig), \
        f"Signature changed: {original_sig} -> {refactored_sig}"

def test_return_type_unchanged():
    """_launch_plotly_viewer returns Dash app."""
    result = MapsManager._launch_plotly_viewer(...)
    assert isinstance(result, dash.Dash), f"Expected Dash app, got {type(result)}"
```

**Rollback**: If signature changes needed, update callers in same PR; do not break API contracts.

---

## Part 10: Rollback & Abort Scenarios

### Scenario A: Serialization Breaks Callbacks (Phase 2–5)

**Symptom**: Callbacks fail with `TypeError: Object not JSON serializable` or state data corrupted.

**Abort Procedure**:
1. Revert Phase 2 (`PlotlyMapDataSerializer`)
2. Restore original `json.dumps/loads` in `_launch_plotly_viewer`
3. Re-run integration tests
4. Investigate root cause (numpy types, custom objects, etc.)

**Recovery**:
```bash
git checkout HEAD~1 src/maps/plotly_map_serializer.py
git checkout HEAD~1 src/maps/maps_manager.py
pytest tests/maps/test_plotly_map_viewer_integration.py
```

---

### Scenario B: Heatmap Algorithm Diverges (Phase 3)

**Symptom**: Heatmap visual output changes noticeably; client complains about accuracy loss.

**Abort Procedure**:
1. Check baseline heatmap test data
2. Investigate scipy version or interpolation parameters
3. If unfixable, revert Phase 3 (`CoverageHeatmapRenderer`)
4. Keep original heatmap code in `_launch_plotly_viewer`

**Recovery**:
```bash
git checkout HEAD~1 src/maps/plotly_map_heatmap.py
# Restore heatmap code to _launch_plotly_viewer
pytest tests/maps/test_plotly_map_heatmap.py
```

---

### Scenario C: Callbacks Don't Register (Phase 5)

**Symptom**: App initializes but UI buttons/inputs don't trigger callbacks; no errors.

**Abort Procedure**:
1. Verify `app.callback_map` has expected callbacks
2. Check decorator syntax (`@self.app.callback(...)` correct?)
3. If decorators on methods don't work, try alternative registration pattern
4. Revert Phase 5 and reassess

**Recovery**:
```bash
# Debug: print callback map
python -c "
from src.maps.plotly_map_viewer import PlotlyMapViewer
viewer = PlotlyMapViewer(...)
app = viewer.create_app()
print(f'Callbacks registered: {len(app.callback_map)}')
print(list(app.callback_map.keys()))
"
```

---

### Scenario D: Full Rollback (Any Phase)

**Abort Procedure** (nuclear option):
```bash
# Revert all phases
git reset --hard HEAD~6  # Assumes 6 commits (1 per phase)

# OR selectively revert specific files
git checkout HEAD~1 src/maps/plotly_map_templates.py
git checkout HEAD~2 src/maps/plotly_map_serializer.py
git checkout HEAD~3 src/maps/plotly_map_heatmap.py
git checkout HEAD~4 src/maps/plotly_map_figures.py
git checkout HEAD~5 src/maps/plotly_map_callbacks.py
git checkout HEAD~6 src/maps/plotly_map_viewer.py

# Re-run original implementation
pytest tests/maps/ -v
```

---

## Conclusion

This implementation plan provides a low-risk, incremental approach to decomposing a massive 5,247-line method into 6 focused classes. Each phase is independent, testable, and can be rolled back if issues arise. 

**Key Success Factors**:
1. **Incremental extraction** (smallest to hardest)
2. **Byte-for-byte equivalence testing** (prevent regressions)
3. **Early quality gate validation** (linting, types, coverage)
4. **Comprehensive test coverage** (unit, integration, regression)
5. **Clear rollback procedures** (risk mitigation)

**Next Steps**:
- Run speckit.tasks to break this plan into actionable subtasks
- Assign Phase 1 to first implementer
- Execute phases sequentially, merging each before starting next
- Monitor CI/CD and quality gates throughout

---

**Generated**: 2026-05-13  
**Status**: Ready for Phase 1 Kickoff  
**Approved By**: (pending technical review)
