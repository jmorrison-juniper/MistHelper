"""
Unit test scaffolding for DeviceUtilityCommands.clear_policy_hit_count (Menu #153)

Tests target node handling and model capability detection. Marked xfail until capability checks are implemented.
"""

import pytest
from unittest.mock import MagicMock
import MistHelper


@pytest.mark.xfail(reason="Model capability detection / node handling not implemented")
def test_clear_policy_includes_node_when_required(monkeypatch):
    monkeypatch.setattr(
        MistHelper.DeviceUtilityCommands,
        "_select_site_and_device",
        lambda action, *args, **kwargs: ("site1", "dev-ssr120", "SSR120"),
    )

    # Simulate user input for Node
    monkeypatch.setattr(MistHelper.InputUtils, "safe_input", lambda prompt, context=None, **kwargs: "node0" if "Node" in prompt else "")

    captured = {}

    def fake_clear(session, site_id, device_id, body):
        captured["body"] = body
        return MagicMock()

    monkeypatch.setattr(
        MistHelper.mistapi.api.v1.sites.devices, "clearSiteDevicePolicyHitCount", fake_clear
    )

    MistHelper.DeviceUtilityCommands.clear_policy_hit_count()

    assert captured.get("body", {}).get("node") in ("node0", "node1")
