"""Model helpers for SSR registration command output."""

from __future__ import annotations  # WHY: keep annotations import-safe during bootstrap.

from collections.abc import Mapping  # WHY: validate dynamic JSON payload shape.
from dataclasses import dataclass  # WHY: hold the three response fields with names.
from typing import Any  # WHY: Mist response payloads can hold dynamic JSON values.


@dataclass(frozen=True, slots=True)
class RegistrationCommandSet:
    """Normalized SSR registration command response.

    Attributes:
        conductor_cmd: The command used from a Session Smart Conductor.
        registration_code: The registration code returned by Mist.
        router_shell_cmd: The command used from the SSR shell.
    """

    conductor_cmd: str  # WHY: this command can register through conductor tooling.
    registration_code: str  # WHY: this secret code must never enter logs.
    router_shell_cmd: str  # WHY: this command can register directly from the router shell.

    @classmethod
    def from_payload(cls, payload: Any) -> RegistrationCommandSet:
        """Build a command set from a Mist response body.

        Args:
            payload: The JSON data returned by Mist.

        Returns:
            A normalized command set with missing fields as empty strings.
        """
        data = payload if isinstance(payload, Mapping) else {}  # WHY: reject unexpected shapes safely.
        return cls(  # WHY: one constructor call keeps the field order visible.
            conductor_cmd=cls._read_text(data, "conductor_cmd"),  # WHY: normalize optional command text.
            registration_code=cls._read_text(data, "registration_code"),  # WHY: normalize optional secret text.
            router_shell_cmd=cls._read_text(data, "router_shell_cmd"),  # WHY: normalize optional command text.
        )

    @staticmethod
    def _read_text(data: Mapping[str, Any], key: str) -> str:
        """Return one response field as stripped text.

        Args:
            data: The response mapping.
            key: The field to read.

        Returns:
            The stripped string value, or an empty string.
        """
        value = data.get(key, "")  # WHY: missing fields should not crash the operation.
        return value.strip() if isinstance(value, str) else ""  # WHY: only text is safe to print.

    def has_text(self) -> bool:
        """Return whether any printable command text exists."""
        return bool(
            self.conductor_cmd or self.registration_code or self.router_shell_cmd
        )  # WHY: empty output is unusable.

    def to_text(self) -> str:
        """Return the command set as console and file text."""
        lines = ["SSR registration commands"]  # WHY: title the sensitive output for the operator.
        self._append_value(
            lines, "Conductor command", self.conductor_cmd
        )  # WHY: include conductor command when present.
        self._append_value(
            lines, "Router shell command", self.router_shell_cmd
        )  # WHY: include router command when present.
        self._append_value(
            lines, "Registration code", self.registration_code
        )  # WHY: include code for manual onboarding.
        return "\n".join(lines) + "\n"  # WHY: final newline makes console and file output clean.

    @staticmethod
    def _append_value(lines: list[str], label: str, value: str) -> None:
        """Append one labeled value when it is present.

        Args:
            lines: The output lines that receive the label and value.
            label: The human-readable label.
            value: The value from Mist.
        """
        if not value:  # WHY: omit missing response fields from the operator output.
            return  # WHY: no blank section should appear in the command output.
        lines.append(f"\n{label}:")  # WHY: a blank line separates command sections.
        lines.append(value)  # WHY: the operator must copy the exact command text.
