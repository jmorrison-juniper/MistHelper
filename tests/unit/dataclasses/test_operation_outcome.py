"""Verify the operation result contract before producer migration."""

import json
from dataclasses import FrozenInstanceError, asdict, fields
from typing import Any, Literal

import pytest

from src.foundation.models.operation_outcome import OperationOutcome


class TestOutcomeValues:
    """Preserve explicit states without interpreting operator text."""

    @pytest.mark.parametrize("state", ["completed", "no_output", "missing_input", "failed"])
    @pytest.mark.parametrize(
        "message",
        [
            "The requested work finished.",
            "Failed to read optional telemetry.",
            "No site selected.",
            "0 records returned no data.",
            "Could not read an optional measurement.",
        ],
    )
    def test_state_does_not_depend_on_message(
        self, state: Literal["completed", "no_output", "missing_input", "failed"], message: str
    ) -> None:
        """Retain all four states even when messages match old prose markers."""
        outcome = OperationOutcome(state, message)
        assert outcome.state == state
        assert outcome.message == message
        assert outcome.detail is None

    def test_preserves_supplied_text(self) -> None:
        """Keep meaningful text intact rather than silently normalizing it."""
        outcome = OperationOutcome("no_output", "  Nothing matched.\n", "  Filter: active\n")
        assert outcome.message == "  Nothing matched.\n"
        assert outcome.detail == "  Filter: active\n"

    @pytest.mark.parametrize("state", ["completed", "no_output", "missing_input", "failed"])
    def test_serialization_preserves_contract(
        self, state: Literal["completed", "no_output", "missing_input", "failed"]
    ) -> None:
        """Retain state and text through the JSON boundary used by future callers."""
        outcome = OperationOutcome(state, "The operation returned.", "Checked one operation.")
        serialized = json.loads(json.dumps(asdict(outcome)))
        assert serialized == {
            "state": state,
            "message": "The operation returned.",
            "detail": "Checked one operation.",
        }
        assert OperationOutcome(**serialized) == outcome

    def test_field_contract_and_slots(self) -> None:
        """Expose only the documented fields without a mutable instance dictionary."""
        outcome = OperationOutcome("completed", "Finished.")
        assert [field.name for field in fields(outcome)] == ["state", "message", "detail"]
        assert not hasattr(outcome, "__dict__")


class TestOutcomeValidation:
    """Reject malformed values at construction rather than treating them as success."""

    @pytest.mark.parametrize("state", ["", "success", "Completed", " completed ", "unknown"])
    def test_rejects_unknown_state(self, state: Any) -> None:
        """Report unsupported state values without echoing caller data."""
        with pytest.raises(ValueError, match="^Operation outcome state is not supported\\.$"):
            OperationOutcome(state, "Finished.")

    @pytest.mark.parametrize("state", [None, False, 1, [], {}])
    def test_rejects_non_string_state(self, state: Any) -> None:
        """Require string state values even when callers lack static checks."""
        with pytest.raises(TypeError, match="^Operation outcome state must be a string\\.$"):
            OperationOutcome(state, "Finished.")

    @pytest.mark.parametrize("field_name", ["message", "detail"])
    @pytest.mark.parametrize("value", [False, 1, [], {}])
    def test_rejects_non_string_text(self, field_name: str, value: Any) -> None:
        """Reject malformed required and optional text with a field-specific cause."""
        values: dict[str, Any] = {"state": "completed", "message": "Finished.", field_name: value}
        with pytest.raises(TypeError, match=f"^Operation outcome {field_name} must be a string\\.$"):
            OperationOutcome(**values)

    @pytest.mark.parametrize("field_name", ["message", "detail"])
    @pytest.mark.parametrize("value", ["", " ", "\t\r\n"])
    def test_rejects_blank_text(self, field_name: str, value: str) -> None:
        """Require an explanation with readable content for either text field."""
        values: dict[str, Any] = {"state": "completed", "message": "Finished.", field_name: value}
        with pytest.raises(ValueError, match=f"^Operation outcome {field_name} must not be blank\\.$"):
            OperationOutcome(**values)

    def test_rejects_absent_message(self) -> None:
        """Do not accept None as the required operator explanation."""
        values: dict[str, Any] = {"state": "failed", "message": None}
        with pytest.raises(TypeError, match="^Operation outcome message must be a string\\.$"):
            OperationOutcome(**values)


class TestOutcomeImmutability:
    """Keep the reported result stable after construction."""

    @pytest.mark.parametrize("field_name", ["state", "message", "detail"])
    def test_rejects_field_assignment(self, field_name: str) -> None:
        """Prevent a caller from silently changing the operation evidence."""
        outcome = OperationOutcome("failed", "The request failed.", "HTTP 503.")
        with pytest.raises(FrozenInstanceError):
            setattr(outcome, field_name, "changed")
        assert asdict(outcome) == {"state": "failed", "message": "The request failed.", "detail": "HTTP 503."}

    @pytest.mark.parametrize("field_name", ["state", "message", "detail"])
    def test_rejects_field_deletion(self, field_name: str) -> None:
        """Prevent removal of a field that a later caller must inspect."""
        outcome = OperationOutcome("missing_input", "A site is required.")
        with pytest.raises(FrozenInstanceError):
            delattr(outcome, field_name)
        assert asdict(outcome) == {"state": "missing_input", "message": "A site is required.", "detail": None}
