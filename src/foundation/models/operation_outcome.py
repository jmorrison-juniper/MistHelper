"""Define explicit handler results for the serial operation outcome migration."""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True)
class OperationOutcome:
    """Keep an operation state independent of its operator-facing explanation."""

    state: Literal["completed", "no_output", "missing_input", "failed"]
    message: str
    detail: str | None = None

    def __post_init__(self) -> None:
        """Reject malformed results before a caller can interpret them."""
        if not isinstance(self.state, str):
            raise TypeError("Operation outcome state must be a string.")
        if self.state not in ("completed", "no_output", "missing_input", "failed"):
            raise ValueError("Operation outcome state is not supported.")
        self._validate_text("message", self.message)
        if self.detail is not None:
            self._validate_text("detail", self.detail)

    @staticmethod
    def _validate_text(field_name: str, value: str) -> None:
        """Require readable text without exposing supplied values in errors."""
        if not isinstance(value, str):
            raise TypeError(f"Operation outcome {field_name} must be a string.")
        if not value.strip():
            raise ValueError(f"Operation outcome {field_name} must not be blank.")
