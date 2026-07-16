"""Telemetry/summary-layer semantics for unregistered options (feature 1020, User Story 1).

Proves FR-002: an unregistered menu option surfaces through the systematic-test
option builder and skip-emission path with a named, non-empty skip_reason
(category ``unregistered``) — it appears in the unsafe/skip list with an
actionable reason, never silently dropped and never silently run.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import MistHelper

# WHY: a synthetic key injected into menu_actions to exercise the fail-closed path end-to-end.
_SYNTHETIC_KEY = "9998"


def _install_synthetic_option(monkeypatch):
    """Inject a synthetic, deliberately-unregistered option into menu_actions for the test scope."""
    patched = dict(MistHelper.menu_actions)  # WHY: copy so monkeypatch restores the original after the test.
    patched[_SYNTHETIC_KEY] = (lambda: None, "Synthetic unregistered test option")  # WHY: dummy handler + label.
    monkeypatch.setattr(MistHelper, "menu_actions", patched)  # WHY: swap in the augmented mapping.


class TestSystematicTestUnregisteredSemantics:
    """Guarantee unregistered options are skipped loudly at the telemetry/summary layer."""

    def test_unregistered_option_is_skipped_not_run(self, monkeypatch):
        """The synthetic key lands in the unsafe/skip list, never the safe (auto-run) list."""
        _install_synthetic_option(monkeypatch)

        safe_options, unsafe_list, all_options = MistHelper._build_systematic_test_options()

        assert _SYNTHETIC_KEY in all_options, "Synthetic option must be present in the full option set"
        assert _SYNTHETIC_KEY not in safe_options, "Unregistered option must never be auto-run in --test"
        assert _SYNTHETIC_KEY in unsafe_list, "Unregistered option must appear in the skip list"

    def test_unregistered_option_has_actionable_reason(self, monkeypatch):
        """The skip carries category 'unregistered' with a non-empty, named reason (FR-002)."""
        _install_synthetic_option(monkeypatch)

        assert MistHelper.OperationRegistry.skip_category(_SYNTHETIC_KEY) == "unregistered"
        reason = MistHelper.OperationRegistry.skip_reason(_SYNTHETIC_KEY)
        assert reason, "Unregistered skip must have a non-empty, actionable reason"

    def test_skip_emission_records_unregistered_category(self, monkeypatch):
        """The skip-emission path records the unregistered option with its category + reason in telemetry."""
        _install_synthetic_option(monkeypatch)
        emitter = MagicMock()  # WHY: spy on emit_test_skip without opening a real telemetry file.

        skip_count = MistHelper._systematic_test_emit_skips(emitter, [_SYNTHETIC_KEY])

        assert skip_count == 1, "The synthetic unregistered option must be counted as a skip"
        emitter.emit_test_skip.assert_called_once()  # WHY: it must be emitted, never silently dropped.
        _opt, _desc, reason, category, mode = emitter.emit_test_skip.call_args.args
        assert category == "unregistered", "Skip telemetry must record the fail-closed category"
        assert reason, "Skip telemetry must record a non-empty reason"
        assert mode == "systematic"
