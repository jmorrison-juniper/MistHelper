"""Unit tests for PlotlyMapCallbackManager."""

from src.maps.plotly_map_callback_manager import PlotlyMapCallbackManager


class _FakeHtml:
    @staticmethod
    def H3(text):
        return {"tag": "h3", "text": text}

    @staticmethod
    def P(text, **kwargs):
        return {"tag": "p", "text": text, "kwargs": kwargs}

    @staticmethod
    def Div(children):
        return {"tag": "div", "children": children}


def test_apply_layer_toggles_trace_visibility() -> None:
    """Layer toggles update trace visibility as expected."""
    manager = PlotlyMapCallbackManager()
    fig = {
        "data": [
            {"name": "Walls", "visible": True},
            {"name": "Wayfinding", "visible": True},
            {"name": "Clients", "visible": True},
            {"name": "Gateways", "visible": True},
        ],
        "layout": {"annotations": []},
    }

    updated = manager.apply_layer_toggles(
        current_fig=fig,
        infra_layers=["walls"],
        beacon_layers=[],
        client_layers=[],
        device_layers=["gateways"],
        filter_layers=[],
    )

    visibility = {trace["name"]: trace["visible"] for trace in updated["data"]}
    assert visibility["Walls"] is True
    assert visibility["Wayfinding"] is False
    assert visibility["Clients"] is False
    assert visibility["Gateways"] is True


def test_apply_layer_toggles_annotation_visibility() -> None:
    """Layer toggles update annotation visibility as expected."""
    manager = PlotlyMapCallbackManager()
    fig = {
        "data": [],
        "layout": {
            "annotations": [
                {"name": "Zone Label", "visible": True},
                {"name": "Access Points Label", "visible": True},
                {"name": "Clients Label", "visible": True},
            ]
        },
    }

    updated = manager.apply_layer_toggles(
        current_fig=fig,
        infra_layers=["zones"],
        beacon_layers=[],
        client_layers=[],
        device_layers=[],
        filter_layers=[],
    )

    annotations = {ann["name"]: ann["visible"] for ann in updated["layout"]["annotations"]}
    assert annotations["Zone Label"] is True
    assert annotations["Access Points Label"] is False
    assert annotations["Clients Label"] is False


def test_build_click_details_default_message() -> None:
    """Click detail renderer returns default prompt when no click data exists."""
    manager = PlotlyMapCallbackManager()
    result = manager.build_click_details(None, _FakeHtml)
    assert result[0]["text"] == "Device Info"


def test_build_click_details_parses_hover_text() -> None:
    """Click detail renderer parses hover text into detail rows."""
    manager = PlotlyMapCallbackManager()
    click_data = {"points": [{"hovertext": "<b>Device</b><br>Type: AP<br>MAC: aa:bb"}]}

    result = manager.build_click_details(click_data, _FakeHtml)
    assert result[0]["text"] == "Device Details"
    assert result[1]["tag"] == "div"
    assert len(result[1]["children"]) >= 1


def test_build_click_details_handles_empty_hover() -> None:
    """Click detail renderer returns fallback when hover text is empty."""
    manager = PlotlyMapCallbackManager()
    click_data = {"points": [{"hovertext": ""}]}

    result = manager.build_click_details(click_data, _FakeHtml)
    assert result[1]["children"][0]["text"] == "No device data available"
