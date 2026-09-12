"""Guard the seam shape record of the upgrade portal.

Why:
    Issue #1991 records the fault these tests prevent. A stand-in answered a
    simpler shape than the real callee, both agreed with each other, and both
    disagreed with the cloud. The suite stayed green through four blocking
    defects.

    `src/upgrade_portal/app/seam_shapes.py` records the call that each route
    makes through each seam. That record only helps while it stays true, so the
    first test below compares every recorded call against the callable that the
    portal really falls back to. The rest prove that the guard refuses a stand-in
    of the wrong shape rather than passing it through.
"""

from __future__ import annotations

import inspect
from typing import Any

import pytest

from src.upgrade_portal.app import seam_shapes
from src.upgrade_portal.app.routes import auth, capture, review, select, upgrade

# The seams that hold an object with named methods rather than one callable. Each
# route guards these with its own method-name check, so no call record fits them.
OBJECT_SEAM_KEYS = ("RUN_STORE", "PRECHECK_ADOPTER", "LOCK_STORE_CLIENT")

# The floor of the record. A seam that leaves the record silently would restore
# the very gap that issue #1991 reports.
RECORDED_SEAM_FLOOR = 17


class TestTheRecordStaysTrue:
    """The recorded call must match the callable the portal really uses."""

    def test_the_record_holds_every_seam_of_every_route(self) -> None:
        """Each seam key that a route declares carries a record or a stated reason."""
        declared = {
            value
            for module in (auth, capture, review, select, upgrade)  # Every route module of the portal.
            for name, value in vars(module).items()  # Every module-level name.
            if name.endswith("_KEY") and isinstance(value, str)  # The seam constants only.
        }
        recorded = set(seam_shapes.SHAPE_INDEX) | set(OBJECT_SEAM_KEYS)  # The two accepted homes.
        # A route constant that names a template field rather than a seam never reaches a seam
        # reader, so the comparison runs the other way. Every recorded key must still be declared.
        assert set(seam_shapes.SHAPE_INDEX) <= declared | {"CAPTURE_LOADER"}, "A record names no seam."
        assert len(recorded) >= RECORDED_SEAM_FLOOR, "The seam record lost an entry."

    @pytest.mark.parametrize("shape", seam_shapes.SEAM_SHAPES, ids=lambda shape: shape.config_key)
    def test_the_fallback_answers_its_own_recorded_call(self, shape: seam_shapes.SeamShape) -> None:
        """The callable a real portal uses must answer the call the record states."""
        fallback = seam_shapes.fallback_callee(shape.config_key)  # None for a seam with no fallback.
        if fallback is None:  # Two seams record no fallback, and each states why.
            assert shape.fallback_module is None, f"The fallback of {shape.config_key} did not resolve."
            return  # Nothing more to compare for that seam.
        signature = inspect.signature(fallback)  # The declared shape of the real callable.
        answered = [call for call in shape.calls if seam_shapes.answers_call(signature, call)]
        assert answered, (
            f"The fallback {fallback.__name__}{signature} of the seam {shape.config_key} answers none "
            f"of its recorded calls."
        )


class TestTheGuardRefusesAWrongShape:
    """A stand-in that cannot answer the route call must not pass."""

    def test_a_stand_in_with_too_few_parameters_is_refused(self) -> None:
        """The lock reader takes two values, so a stand-in of one is refused."""
        differences = seam_shapes.shape_differences("SITE_LOCK_READER", lambda org_id: {})
        assert differences, "The guard accepted a stand-in that the route call cannot reach."

    def test_a_stand_in_with_too_many_required_parameters_is_refused(self) -> None:
        """A stand-in that demands a fourth value cannot answer a three-value call."""

        def wrong(session: Any, org_id: str, site_id: str, extra: str) -> dict[str, Any]:
            """Take one value more than the route ever passes."""
            return {}  # The body never runs, because the bind probe refuses first.

        assert seam_shapes.shape_differences("UPGRADE_OPTIONS_VIEW", wrong), "The guard accepted a wrong shape."

    def test_the_cloud_reader_must_accept_the_parameters_of_the_read(self) -> None:
        """The route passes cloud parameters by keyword, so a fixed name list is refused."""
        assert seam_shapes.shape_differences("MIST_READER", lambda name: []), "The guard accepted a fixed list."

    def test_the_defect_of_issue_1991_is_refused(self) -> None:
        """A device reader that names the site alone answers neither recorded call."""
        assert seam_shapes.shape_differences("DEVICE_READER", lambda site_id: []), "The guard accepted one value."


class TestTheGuardAcceptsEveryTrueShape:
    """A stand-in that answers the route call must pass without noise."""

    def test_the_two_device_reader_shapes_both_pass(self) -> None:
        """The route drops the session when the seam names none, so both shapes fit."""

        def with_session(session: Any, org_id: str, site_id: str) -> list[dict[str, Any]]:
            """Answer the shape of the real reader."""
            return []  # The body never runs.

        def without_session(org_id: str, site_id: str) -> list[dict[str, Any]]:
            """Answer the shape a contract stand-in uses."""
            return []  # The body never runs.

        assert seam_shapes.shape_differences("DEVICE_READER", with_session) == ()
        assert seam_shapes.shape_differences("DEVICE_READER", without_session) == ()

    def test_a_variadic_stand_in_answers_every_seam(self) -> None:
        """A stand-in that takes any call fits every recorded call."""

        def anything(*args: Any, **named: Any) -> Any:
            """Accept whatever the route passes."""
            return None  # The body never runs.

        for shape in seam_shapes.SEAM_SHAPES:  # Every seam, so no record refuses the open shape.
            assert seam_shapes.shape_differences(shape.config_key, anything) == (), shape.config_key

    def test_an_unknown_key_and_a_value_that_is_not_callable_stay_quiet(self) -> None:
        """The guard reports nothing for a key it does not record."""
        assert seam_shapes.check_stand_in("NO_SUCH_SEAM", lambda: None) == ()
        assert seam_shapes.check_stand_in("SITE_LOCK_READER", "not a callable") == ()


class TestStrictModeDecidesTheOutcome:
    """A test run raises on a difference, and a live portal warns instead."""

    def test_strict_mode_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A wrong stand-in stops a test run at the seam that reads it."""
        monkeypatch.setenv(seam_shapes.STRICT_VARIABLE, "1")
        with pytest.raises(seam_shapes.SeamShapeError, match="SITE_LOCK_READER"):
            seam_shapes.check_stand_in("SITE_LOCK_READER", lambda org_id: {})

    def test_a_live_portal_warns_and_keeps_working(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Warning: a live portal must keep working. A raise here would show a fault page to an operator."""
        monkeypatch.delenv(seam_shapes.STRICT_VARIABLE, raising=False)
        differences = seam_shapes.check_stand_in("SITE_LOCK_READER", lambda org_id: {})
        assert len(differences) == 1, "The live portal must report the difference and raise nothing."

    def test_the_test_suite_runs_in_strict_mode(self) -> None:
        """`tests/conftest.py` sets the variable, so every suite run holds the guard."""
        assert seam_shapes.strict_mode(), "The suite lost its strict seam guard."
