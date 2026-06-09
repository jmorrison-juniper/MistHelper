"""Unit tests for wave D of the Plotly viewer callback extraction.

Covers the 3 live-refresh callbacks now on :class:`MapViewerCallbacks`:

* :py:meth:`MapViewerCallbacks.update_countdown_display` -- pure time math
  for the per-second countdown label.
* :py:meth:`MapViewerCallbacks.update_clients_traces` -- refresh WiFi /
  wired client traces and label annotations from the Mist API.
* :py:meth:`MapViewerCallbacks.update_coverage_heatmap` -- refresh the
  RF coverage heatmap trace from the Mist coverage API.

Uses the same dash-stub + autouse fixture pattern as
``tests/maps/test_viewer_callbacks_wave_a.py`` and
``tests/maps/test_viewer_callbacks_wave_b_c.py``.
"""

from __future__ import annotations

import importlib.machinery
import sys
import types
from collections.abc import Iterator
from typing import Any

import pytest


def _build_dash_stub() -> types.ModuleType:
    """Construct a synthetic ``dash`` module exposing the names we need."""
    dash_stub = types.ModuleType("dash")  # Synthetic module object
    dash_stub.__spec__ = importlib.machinery.ModuleSpec("dash", loader=None)
    dash_stub.Input = lambda *a, **k: ("Input", a, k)  # type: ignore[attr-defined]
    dash_stub.Output = lambda *a, **k: ("Output", a, k)  # type: ignore[attr-defined]
    dash_stub.State = lambda *a, **k: ("State", a, k)  # type: ignore[attr-defined]
    dash_stub.no_update = "__NO_UPDATE__"  # type: ignore[attr-defined]
    dash_stub.callback_context = types.SimpleNamespace(triggered=[])  # type: ignore[attr-defined]
    dash_stub.html = types.SimpleNamespace(  # type: ignore[attr-defined]
        P=lambda *a, **k: {"P": (a, k)},
        Div=lambda *a, **k: {"Div": (a, k)},
        H3=lambda *a, **k: {"H3": (a, k)},
        Span=lambda *a, **k: {"Span": (a, k)},
    )
    return dash_stub


sys.modules["dash"] = _build_dash_stub()  # Install before launcher imports run

from src.maps.launcher import MapViewerCallbacks, MapViewerState  # noqa: E402


@pytest.fixture(autouse=True)
def _dash_stub() -> Iterator[types.ModuleType]:
    """Per-test: install fresh stub, restore original on teardown."""
    original = sys.modules.get("dash")  # Snapshot for restoration
    stub = _build_dash_stub()  # Fresh stub for this test
    sys.modules["dash"] = stub
    try:
        yield stub
    finally:
        if original is None:
            sys.modules.pop("dash", None)
        else:
            sys.modules["dash"] = original


class _FakeCallbackManager:
    """Minimal stand-in for PlotlyMapCallbackManager."""

    def apply_layer_toggles(self, **_kwargs: Any) -> dict[str, Any]:
        return {}

    def build_click_details(self, **_kwargs: Any) -> dict[str, Any]:
        return {}


class _FakeResponse:
    """Stand-in for a mistapi API response with a status code and JSON payload."""

    def __init__(self, status_code: int, data: Any = None) -> None:
        self.status_code = status_code  # HTTP status returned by Mist
        self.data = data  # Parsed JSON payload (for coverage API)


class _FakeMistapi:
    """Captures listSiteWirelessClientsStats / listSiteZones / getSiteMap calls."""

    def __init__(
        self,
        clients: list[dict[str, Any]] | None = None,
        zones: list[dict[str, Any]] | None = None,
        wall_nodes: list[dict[str, Any]] | None = None,
        clients_status: int = 200,
        zones_status: int = 200,
        map_status: int = 200,
    ) -> None:
        self._clients = clients or []
        self._zones = zones or []
        self._wall_nodes = wall_nodes or []
        self.clients_calls: list[dict[str, Any]] = []
        self.zones_calls: list[dict[str, Any]] = []
        self.map_calls: list[dict[str, Any]] = []
        self._clients_status = clients_status
        self._zones_status = zones_status
        self._map_status = map_status

        def _list_clients(session: Any, site_id: str, limit: int) -> _FakeResponse:
            self.clients_calls.append({"session": session, "site_id": site_id, "limit": limit})
            return _FakeResponse(self._clients_status)

        def _list_zones(session: Any, site_id: str) -> _FakeResponse:
            self.zones_calls.append({"session": session, "site_id": site_id})
            return _FakeResponse(self._zones_status)

        def _get_site_map(session: Any, site_id: str, map_id: str) -> _FakeResponse:
            self.map_calls.append({"session": session, "site_id": site_id, "map_id": map_id})
            return _FakeResponse(self._map_status, data={"wall_path": {"nodes": self._wall_nodes}})

        clients_ns = types.SimpleNamespace(listSiteWirelessClientsStats=_list_clients)
        zones_ns = types.SimpleNamespace(listSiteZones=_list_zones)
        maps_ns = types.SimpleNamespace(getSiteMap=_get_site_map)
        sites_ns = types.SimpleNamespace(stats=clients_ns, zones=zones_ns, maps=maps_ns)
        v1_ns = types.SimpleNamespace(sites=sites_ns)
        self.api = types.SimpleNamespace(v1=v1_ns)

    def get_all(self, response: Any, mist_session: Any) -> list[dict[str, Any]]:  # noqa: ARG002
        if response in (None,):
            return []
        # Route based on which endpoint produced the response by status code only is unreliable;
        # tests inject distinct lists, so we use a simple heuristic: walk all candidates.
        if self.clients_calls and not self.zones_calls:
            return self._clients
        if self.zones_calls and not self.clients_calls:
            return self._zones
        # When both have been called this turn, return clients first time, zones second.
        # In practice update_clients_traces calls clients before zones, so order works.
        if len(self.zones_calls) >= 1 and len(self.clients_calls) >= 1:
            # Whichever was called last is what get_all is paired with.
            return self._zones if self.zones_calls else self._clients
        return self._clients


class _FakeCoverageSession:
    """Stand-in for mistapi session with mist_get for the coverage URL."""

    def __init__(self, response: _FakeResponse) -> None:
        self.calls: list[dict[str, Any]] = []
        self._response = response

    def mist_get(self, url: str, query: dict[str, Any]) -> _FakeResponse:
        self.calls.append({"url": url, "query": query})
        return self._response


class _RecordedCallback:
    def __init__(self, args: tuple, kwargs: dict[str, Any]) -> None:
        self.args = args
        self.kwargs = kwargs
        self.bound_func: Any = None


class _FakeDashApp:
    """Minimal Dash app stub that records callback registrations."""

    def __init__(self) -> None:
        self.registered: list[_RecordedCallback] = []

    def callback(self, *args: Any, **kwargs: Any):
        record = _RecordedCallback(args=args, kwargs=kwargs)
        self.registered.append(record)

        def _decorator(func: Any) -> Any:
            record.bound_func = func
            return func

        return _decorator


def _make_state(**overrides: Any) -> MapViewerState:
    """Build a MapViewerState with sensible defaults for tests."""
    defaults: dict[str, Any] = {
        "callback_manager": _FakeCallbackManager(),
        "zones": [],
        "map_id": "test-map-id",
        "site_id": "test-site-id",
        "api_session_ref": object(),
        "ppm": 10.0,
        "mistapi_ref": _FakeMistapi(),
        "maps_manager_ref": object(),
    }
    defaults.update(overrides)
    return MapViewerState(**defaults)


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def test_register_with_wires_sixteen_callbacks_total() -> None:
    """register_with wires 5 wave-A + 4 wave-B + 4 wave-C + 3 wave-D = 16."""
    callbacks = MapViewerCallbacks(state=_make_state())
    app = _FakeDashApp()

    callbacks.register_with(app)

    assert len(app.registered) == 16
    bound_names = {record.bound_func.__name__ for record in app.registered}
    expected_wave_d = {"update_countdown_display", "update_clients_traces", "update_coverage_heatmap"}
    assert expected_wave_d.issubset(bound_names)


def test_register_with_wave_d_uses_prevent_initial_call() -> None:
    """All three wave-D callbacks set prevent_initial_call=True."""
    callbacks = MapViewerCallbacks(state=_make_state())
    app = _FakeDashApp()

    callbacks.register_with(app)

    wave_d = {"update_countdown_display", "update_clients_traces", "update_coverage_heatmap"}
    for record in app.registered:
        if record.bound_func.__name__ in wave_d:
            assert record.kwargs.get("prevent_initial_call") is True


# ---------------------------------------------------------------------------
# update_countdown_display
# ---------------------------------------------------------------------------


def test_update_countdown_display_off_when_no_refresh_times() -> None:
    callbacks = MapViewerCallbacks(state=_make_state())
    assert callbacks.update_countdown_display(0, None, ["enabled"]) == "Auto-refresh: Off"


def test_update_countdown_display_off_when_toggle_disabled() -> None:
    callbacks = MapViewerCallbacks(state=_make_state())
    refresh_times = {"client_last_refresh": 0.0, "coverage_last_refresh": 0.0}
    assert callbacks.update_countdown_display(0, refresh_times, []) == "Auto-refresh: Off"
    assert callbacks.update_countdown_display(0, refresh_times, None) == "Auto-refresh: Off"


def test_update_countdown_display_returns_seconds_and_minutes_format() -> None:
    """At t == last_refresh, remaining = full cadence (30s / 5:00)."""
    import time

    callbacks = MapViewerCallbacks(state=_make_state())
    now = time.time()
    refresh_times = {"client_last_refresh": now, "coverage_last_refresh": now}
    result = callbacks.update_countdown_display(0, refresh_times, ["enabled"])
    # Format: "Clients: Ns | RF: M:SS" — exact N varies by clock, but format must match.
    assert result.startswith("Clients: ")
    assert " | RF: " in result
    assert ":" in result.split(" | RF: ")[1]


# ---------------------------------------------------------------------------
# update_clients_traces
# ---------------------------------------------------------------------------


def test_update_clients_traces_skips_when_no_trigger() -> None:
    callbacks = MapViewerCallbacks(state=_make_state())
    fig: dict[str, Any] = {"data": []}
    result_fig, result_times = callbacks.update_clients_traces(0, None, {}, fig, [], {})
    assert result_fig == "__NO_UPDATE__"
    assert result_times == "__NO_UPDATE__"


def test_update_clients_traces_skips_when_site_id_missing(_dash_stub: types.ModuleType) -> None:
    _dash_stub.callback_context.triggered = [{"prop_id": "client-refresh-interval.n_intervals"}]
    callbacks = MapViewerCallbacks(state=_make_state())
    fig: dict[str, Any] = {"data": []}
    config = {"map_id": "m1"}  # missing site_id
    result_fig, result_times = callbacks.update_clients_traces(1, None, config, fig, [], {})
    assert result_fig == "__NO_UPDATE__"
    assert "client_last_refresh" in result_times


def test_update_clients_traces_updates_wifi_trace(_dash_stub: types.ModuleType) -> None:
    """Happy path: WiFi client trace gets new x/y/hovertext from API."""
    _dash_stub.callback_context.triggered = [{"prop_id": "client-refresh-interval.n_intervals"}]
    fake_mistapi = _FakeMistapi(
        clients=[
            {"map_id": "m1", "x": 100, "y": 200, "mac": "aa:bb", "hostname": "h1", "wired": False},
            {"map_id": "m1", "x": 300, "y": 400, "mac": "cc:dd", "wired": True},
            {"map_id": "OTHER", "x": 0, "y": 0, "mac": "ee:ff"},  # filtered out
        ]
    )
    callbacks = MapViewerCallbacks(state=_make_state(mistapi_ref=fake_mistapi))
    fig: dict[str, Any] = {
        "data": [
            {"name": "Clients", "x": [], "y": [], "hovertext": []},
            {"name": "Wired Clients", "x": [], "y": [], "hovertext": []},
        ],
        "layout": {"annotations": []},
    }
    config = {"site_id": "s1", "map_id": "m1"}

    result_fig, result_times = callbacks.update_clients_traces(1, None, config, fig, [], {})

    assert result_fig is fig  # mutated in place
    assert fig["data"][0]["x"] == [100]
    assert fig["data"][0]["y"] == [200]
    assert fig["data"][1]["x"] == [300]
    assert fig["data"][1]["y"] == [400]
    assert "client_last_refresh" in result_times


def test_update_clients_traces_returns_no_update_on_api_failure(_dash_stub: types.ModuleType) -> None:
    _dash_stub.callback_context.triggered = [{"prop_id": "manual-refresh-btn.n_clicks"}]
    fake_mistapi = _FakeMistapi(clients_status=500)
    callbacks = MapViewerCallbacks(state=_make_state(mistapi_ref=fake_mistapi))
    fig: dict[str, Any] = {"data": []}
    config = {"site_id": "s1", "map_id": "m1"}
    result_fig, result_times = callbacks.update_clients_traces(1, 1, config, fig, [], {})
    assert result_fig == "__NO_UPDATE__"
    assert "client_last_refresh" in result_times


# ---------------------------------------------------------------------------
# update_coverage_heatmap
# ---------------------------------------------------------------------------


def test_update_coverage_heatmap_skips_on_initial_tick() -> None:
    callbacks = MapViewerCallbacks(state=_make_state())
    fig: dict[str, Any] = {"data": []}
    result_fig, result_times = callbacks.update_coverage_heatmap(0, {}, fig, [], {})
    assert result_fig == "__NO_UPDATE__"
    assert result_times == "__NO_UPDATE__"


def test_update_coverage_heatmap_skips_when_site_id_missing() -> None:
    callbacks = MapViewerCallbacks(state=_make_state())
    fig: dict[str, Any] = {"data": []}
    result_fig, result_times = callbacks.update_coverage_heatmap(1, {"map_id": "m1"}, fig, [], {})
    assert result_fig == "__NO_UPDATE__"
    assert "coverage_last_refresh" in result_times


def test_update_coverage_heatmap_skips_on_api_error() -> None:
    callbacks = MapViewerCallbacks(state=_make_state(api_session_ref=_FakeCoverageSession(_FakeResponse(500))))
    fig: dict[str, Any] = {"data": []}
    result_fig, _ = callbacks.update_coverage_heatmap(1, {"site_id": "s1", "map_id": "m1"}, fig, [], {})
    assert result_fig == "__NO_UPDATE__"


def test_update_coverage_heatmap_updates_trace_happy_path() -> None:
    payload = {
        "result_def": ["x", "y", "max_rssi"],
        "results": [
            [0, 0, -60],
            [1, 0, -70],
            [0, 1, -80],
            [1, 1, -90],
        ],
    }
    session = _FakeCoverageSession(_FakeResponse(200, data=payload))
    callbacks = MapViewerCallbacks(state=_make_state(api_session_ref=session))
    fig: dict[str, Any] = {
        "data": [{"name": "RF Coverage", "x": [], "y": [], "z": [], "visible": False}],
    }
    config = {"site_id": "s1", "map_id": "m1", "ppm": 10}

    result_fig, result_times = callbacks.update_coverage_heatmap(1, config, fig, ["rf_heatmap"], {})

    assert result_fig is fig  # mutated in place
    trace = fig["data"][0]
    assert trace["zmin"] == -90
    assert trace["zmax"] == -60
    assert trace["visible"] is True
    assert trace["x"] == [0, 10]
    assert trace["y"] == [0, 10]
    assert "coverage_last_refresh" in result_times


def test_update_coverage_heatmap_skips_when_result_def_missing_xy() -> None:
    payload = {"result_def": ["something_else"], "results": [[0]]}
    session = _FakeCoverageSession(_FakeResponse(200, data=payload))
    callbacks = MapViewerCallbacks(state=_make_state(api_session_ref=session))
    fig: dict[str, Any] = {"data": []}
    result_fig, _ = callbacks.update_coverage_heatmap(1, {"site_id": "s1", "map_id": "m1"}, fig, [], {})
    assert result_fig == "__NO_UPDATE__"
