"""Tests for the RRM optimize or reset model."""

from __future__ import annotations  # WHY: keep annotations lightweight during tests.

from src.site.rrm_reset.model import DEFAULT_SETTLE_SECONDS, RrmPlanDiffBuilder, RrmRunSettings, RrmSettleTime


def test_rrm_reset_diff_lists_changed_radios_only() -> None:
    """The diff contains only radios whose RF values changed."""
    before_rows = [  # WHY: fixture has one unchanged radio and one changed radio.
        {"site_id": "site-1", "ap": "ap-1", "band": "5", "curr_channel": 36, "curr_bandwidth": 20, "curr_power": 8},
        {"site_id": "site-1", "ap": "ap-2", "band": "5", "curr_channel": 40, "curr_bandwidth": 20, "curr_power": 8},
    ]
    after_rows = [  # WHY: ap-1 stays the same and ap-2 changes channel.
        {"site_id": "site-1", "ap": "ap-1", "band": "5", "curr_channel": 36, "curr_bandwidth": 20, "curr_power": 8},
        {"site_id": "site-1", "ap": "ap-2", "band": "5", "curr_channel": 44, "curr_bandwidth": 20, "curr_power": 8},
    ]
    diff_rows = RrmPlanDiffBuilder.build(before_rows, after_rows)  # WHY: build the operator diff.
    assert diff_rows == [  # WHY: only the changed radio belongs in the diff.
        {
            "site_id": "site-1",
            "ap": "ap-2",
            "band": "5",
            "change_type": "changed",
            "before_channel": "40",
            "after_channel": "44",
            "before_width": "20",
            "after_width": "20",
            "before_power": "8",
            "after_power": "8",
        }
    ]


def test_rrm_reset_diff_handles_menu_86_band_map_rows() -> None:
    """The diff repairs menu-86 rows from RRM band maps."""
    before_rows = [{"site_id": "site-1", "ap": "band_5", "band": "ap-1", "curr_channel": 36, "curr_power": 8}]
    after_rows = [{"site_id": "site-1", "ap": "band_5", "band": "ap-1", "curr_channel": 40, "curr_power": 8}]
    diff_rows = RrmPlanDiffBuilder.build(before_rows, after_rows)  # WHY: build diff from reused menu-86 helper rows.
    assert diff_rows[0]["ap"] == "ap-1"  # WHY: AP id comes from the row band field in this shape.
    assert diff_rows[0]["band"] == "5"  # WHY: band comes from the row AP field in this shape.
    assert diff_rows[0]["before_channel"] == "36"  # WHY: current channel is normalized to text.
    assert diff_rows[0]["after_channel"] == "40"  # WHY: changed current channel is normalized to text.


def test_rrm_reset_settle_time_default_and_override() -> None:
    """Settle time uses the default and a valid environment override."""
    assert RrmSettleTime.resolve(None) == DEFAULT_SETTLE_SECONDS  # WHY: missing env uses required default.
    assert RrmSettleTime.resolve("5") == 5  # WHY: valid env overrides the default.
    assert RrmSettleTime.resolve("bad") == DEFAULT_SETTLE_SECONDS  # WHY: invalid env falls back safely.


def test_rrm_reset_settings_request_body_uses_default_bands() -> None:
    """Request body includes the OpenAPI required bands."""
    settings = RrmRunSettings.build("optimize", dry_run=False, environ={"RRM_SETTLE_SECONDS": "0"})
    assert settings.action == "OPTIMIZE"  # WHY: action words normalize to uppercase.
    assert settings.request_body() == {"bands": ["24", "5", "6"]}  # WHY: schemas require band list.
