"""Exercise actual imported readers and their conversion decisions."""

from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

from src.upgrade_portal.api import numeric_input
from src.upgrade_portal.upgrade import options

FIELDS = (
    "max_failure_percentage",
    "p2p_cluster_size",
    "p2p_parallelism",
    "rrm_first_batch_percentage",
    "rrm_max_batch_percentage",
    "canary_phases",
    "max_failures",
    "start_time",
    "reboot_at",
    "start_time_after",
    "reboot_at_after",
)
NOW = 1_900_000_000


class ReaderCases:
    """Build valid surroundings for each numeric control."""

    @staticmethod
    def payload(field: str, token: str) -> dict[str, object]:
        """Select the strategy and list shape that reaches the requested reader."""
        payload: dict[str, object] = {"strategy": "canary", "canary_phases": "100"}
        if field.startswith("rrm_"):
            payload = {"strategy": "rrm"}
        if field in ("start_time", "reboot_at"):
            token += "s"
        payload[field] = token
        return payload

    @staticmethod
    def clock() -> int:
        """Return a fixed clock so schedule assertions cannot age."""
        return NOW

    @staticmethod
    def read(field: str, token: str) -> object:
        """Reach one actual reader without converting an unrelated valid control."""
        if field.endswith("_after"):
            return options._read_stored_duration(token, field.removesuffix("_after"))
        if field in ("start_time", "reboot_at"):
            return options.parse_duration_seconds(token + "s", field)
        if field in ("canary_phases", "max_failures"):
            return options._read_number_list({field: token}, field)
        highest = 1000 if field.startswith("p2p_") else 100
        return options._read_whole_number({field: token}, field, highest)


@pytest.mark.parametrize("field", FIELDS)
@pytest.mark.parametrize(
    "token",
    ("5²", "⁵", "７", "٧", "7" * 5000),
    ids=("mixed-superscript", "superscript", "fullwidth", "arabic", "5000-digits"),
)
def test_each_numeric_control_refuses_before_conversion(
    field: str, token: str, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Each malformed token names its control without conversion or value disclosure."""
    caplog.set_level(logging.DEBUG)
    conversion = Mock(side_effect=AssertionError("The refusal attempted integer conversion."))
    monkeypatch.setattr(numeric_input, "int", conversion, raising=False)
    monkeypatch.setattr(options, "int", conversion, raising=False)
    with pytest.raises(options.BadOptionError) as failure:
        ReaderCases.read(field, token)
    control = field.removesuffix("_after")
    assert failure.value.field == control
    assert options.OPTION_HELP[control][0] in str(failure.value)
    assert token not in str(failure.value)
    assert token not in caplog.text
    assert "invalid literal" not in caplog.text
    assert "sys.set_int_max_str_digits" not in caplog.text
    conversion.assert_not_called()


@pytest.mark.parametrize("field", FIELDS)
@pytest.mark.parametrize("token", ("5²", "7" * 5000), ids=("superscript", "5000-digits"))
def test_actual_mapper_names_the_refused_control(field: str, token: str) -> None:
    """The whole mapper preserves the reader's named refusal."""
    with pytest.raises(options.BadOptionError) as failure:
        options.build_options(ReaderCases.payload(field, token), now=ReaderCases.clock)
    control = field.removesuffix("_after")
    assert failure.value.field == control
    assert options.OPTION_HELP[control][0] in str(failure.value)
    assert token not in str(failure.value)


@pytest.mark.parametrize("field", ("start_time", "reboot_at"))
@pytest.mark.parametrize("token", ("٧" * 10, "7" * 5000))
@pytest.mark.parametrize("replay", (False, True), ids=("clock", "stored-replay"))
def test_epoch_tokens_refuse_without_conversion(
    field: str, token: str, replay: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An epoch token receives the same named refusal during save and replay."""
    conversion = Mock(side_effect=AssertionError("The epoch refusal attempted conversion."))
    monkeypatch.setattr(options, "int", conversion, raising=False)
    with pytest.raises(options.BadOptionError) as failure:
        options.build_options({field: token}, now=None if replay else ReaderCases.clock)
    assert failure.value.field == field
    assert options.OPTION_HELP[field][0] in str(failure.value)
    conversion.assert_not_called()


@pytest.mark.parametrize("field,highest", (("max_failure_percentage", 100), ("p2p_cluster_size", 1000)))
def test_excessive_finite_value_refuses_before_conversion(
    field: str, highest: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A value above a supported maximum never reaches integer conversion."""
    conversion = Mock(side_effect=AssertionError("The excessive value attempted conversion."))
    monkeypatch.setattr(numeric_input, "int", conversion, raising=False)
    with pytest.raises(options.BadOptionError) as failure:
        options._read_whole_number({field: str(highest + 1)}, field, highest)
    assert failure.value.field == field
    conversion.assert_not_called()


@pytest.mark.parametrize("value", (None, "", " "))
def test_empty_controls_keep_defaults(value: object) -> None:
    """Absent numeric choices preserve the original option defaults."""
    baseline = options.build_options({}, now=ReaderCases.clock)
    assert options.build_options(dict.fromkeys(FIELDS, value), now=ReaderCases.clock) == baseline


@pytest.mark.parametrize("highest", (100, 1000))
@pytest.mark.parametrize("boundary", ("zero", "maximum", "leading-zero"))
def test_supported_scalar_boundaries(highest: int, boundary: str) -> None:
    """A supported boundary keeps its integer value."""
    value = {"zero": "0", "maximum": str(highest), "leading-zero": "01"}[boundary]
    assert options._read_whole_number({"p2p_cluster_size": value}, "p2p_cluster_size", highest) == int(value)


@pytest.mark.parametrize("shape", ("1,10,50,100,", [1, 10, 50, 100], (1, 10, 50, 100)))
def test_list_shapes_and_trailing_comma_keep_their_meaning(shape: object) -> None:
    """The mapper preserves ordered phase shares and supported list representations."""
    chosen = options.build_options({"strategy": "canary", "canary_phases": shape, "max_failures": "0,0,0,0"})
    assert chosen.canary.canary_phases == (1, 10, 50, 100)
    assert chosen.canary.max_failures == (0, 0, 0, 0)


def test_single_site_failure_count_has_no_invented_cloud_cap() -> None:
    """The mapper preserves the existing unrestricted single-site count range."""
    chosen = options.build_options({"strategy": "canary", "canary_phases": "100", "max_failures": str(2**64)})
    assert chosen.canary.max_failures == (2**64,)


@pytest.mark.parametrize("unit,multiplier", tuple(options.DURATION_UNIT_SECONDS.items()))
def test_duration_units_keep_the_existing_horizon(unit: str, multiplier: int) -> None:
    """Each unit accepts its last supported whole value and refuses the next value."""
    highest = options.START_TIME_HORIZON_SECONDS // multiplier
    assert options.parse_duration_seconds(f"{highest}{unit}", "start_time") == highest * multiplier
    with pytest.raises(options.BadOptionError) as failure:
        options.parse_duration_seconds(f"{highest + 1}{unit}", "start_time")
    assert failure.value.field == "start_time"


def test_stored_seconds_and_no_clock_epoch_replay_keep_their_meaning() -> None:
    """Stored seconds remain durations, while stored epochs remain absolute moments."""
    duration = options.build_options(
        {"start_time_after": str(options.START_TIME_HORIZON_SECONDS)}, now=ReaderCases.clock
    )
    assert duration.schedule.start_time_after == options.START_TIME_HORIZON_SECONDS
    assert duration.start_time == NOW + options.START_TIME_HORIZON_SECONDS
    epoch = options.build_options({"start_time": str(2**64)}, now=None)
    assert epoch.start_time == 2**64
    assert epoch.schedule.start_time_after is None


@pytest.mark.parametrize("highest", (100, 1000, options.START_TIME_HORIZON_SECONDS))
def test_finite_raw_width_refuses_even_excessive_leading_zeros(highest: int, monkeypatch: pytest.MonkeyPatch) -> None:
    """The explicit representation restriction runs before the shared conversion."""
    conversion = Mock(side_effect=AssertionError("An excessive raw token attempted conversion."))
    monkeypatch.setattr(numeric_input, "int", conversion, raising=False)
    with pytest.raises(options.BadOptionError) as failure:
        options.OptionNumberReader.read("0" * (len(str(highest)) + 1), "start_time", highest)
    assert failure.value.field == "start_time"
    conversion.assert_not_called()


def test_active_representation_limit_is_unchanged() -> None:
    """The reader refuses excessive representations without changing interpreter policy."""
    before = sys.get_int_max_str_digits()
    assert before > 0
    with pytest.raises(options.BadOptionError) as failure:
        options.OptionNumberReader.read("7" * (before + 1), "max_failures")
    assert failure.value.field == "max_failures"
    assert sys.get_int_max_str_digits() == before


def test_disabled_representation_limit_preserves_unbounded_business_values() -> None:
    """An isolated interpreter accepts 5000-digit unbounded values without a cloud cap."""
    root = Path(__file__).resolve().parents[4]
    script = (
        "import sys\n"
        "from src.upgrade_portal.upgrade import options\n"
        "assert sys.get_int_max_str_digits() == 0\n"
        "token = '7' * 5000\n"
        "count = options.build_options({'strategy':'canary','canary_phases':'100','max_failures':token})\n"
        "epoch = options.build_options({'start_time':token}, now=None)\n"
        "assert count.canary.max_failures == (int(token),)\n"
        "assert epoch.start_time == int(token)\n"
        "assert epoch.schedule.start_time_after is None\n"
        "assert sys.get_int_max_str_digits() == 0\n"
        "print('Checked 2 unbounded controls with the real disabled conversion limit.')\n"
    )
    result = subprocess.run(
        [sys.executable, "-X", "int_max_str_digits=0", "-c", script],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "Checked 2 unbounded controls with the real disabled conversion limit.\n"


def test_final_conversion_failure_is_named_and_value_free(monkeypatch: pytest.MonkeyPatch) -> None:
    """A narrow conversion failure never carries Python's raw error text."""
    conversion = Mock(side_effect=ValueError("invalid literal: sensitive entered value"))
    monkeypatch.setattr(options, "int", conversion, raising=False)
    with pytest.raises(options.BadOptionError) as failure:
        options.OptionNumberReader.read("7", "max_failures")
    assert failure.value.field == "max_failures"
    assert "sensitive entered value" not in str(failure.value)
    assert failure.value.__suppress_context__ is True
