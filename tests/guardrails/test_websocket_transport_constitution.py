"""Guard the temporary owned WebSocket transport constitution exception."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

from pathlib import Path  # Build repository paths without platform-specific separators.


class WebSocketConstitutionGuard:
    """Check the constitution and the existing SDK contract test."""

    def __init__(self, repository_root: Path) -> None:
        """Store the repository root for stable policy reads."""
        self.repository_root = repository_root  # Keep all guarded paths relative to one verified root.

    def constitution_failures(self, text: str) -> tuple[str, ...]:
        """Return missing temporary-exception requirements."""
        requirements = (  # Keep each binding policy phrase explicit for review.
            "Temporary Owned WebSocket Transport",
            "only for an affected flow",
            "reviewed supported mistapi release",
            "preserves the first output and split",
            "Contract tests MUST prove both output contracts",
        )
        return tuple(requirement for requirement in requirements if requirement not in text)  # Report every gap.

    def contract_failures(self, text: str) -> tuple[str, ...]:
        """Return missing private mistapi session contract fields."""
        requirements = (  # Pin the existing test and its four private session fields.
            "test_api_session_private_transport_attributes",
            '"_cloud_uri", "_apitoken", "_apitoken_index", "_session"',
        )
        return tuple(requirement for requirement in requirements if requirement not in text)  # Report every gap.

    def repository_failures(self) -> tuple[int, tuple[str, ...]]:
        """Return the checked file count and each policy failure."""
        constitution = self.repository_root / ".specify/memory/constitution.md"  # Name the governance source.
        contract = self.repository_root / "tests/contract/websocket_streams/test_ws_sdk_contract.py"  # Name the guard.
        assert constitution.is_file() and contract.is_file(), "The WebSocket policy guard cannot read both inputs."
        failures = self.constitution_failures(constitution.read_text(encoding="utf-8"))  # Check the exception.
        failures += self.contract_failures(contract.read_text(encoding="utf-8"))  # Check the private SDK seam.
        return 2, failures  # Report the measured input count with all failures.


class TestWebSocketTransportConstitution:
    """Prove the exception, return condition, and SDK seam stay guarded."""

    @staticmethod
    def guard() -> WebSocketConstitutionGuard:
        """Return a guard rooted at the checked out repository."""
        repository_root = Path(__file__).resolve().parents[2]  # Find the repository from tests/guardrails.
        return WebSocketConstitutionGuard(repository_root)  # Use the real repository inputs.

    def test_repository_policy_is_complete(self) -> None:
        """Require the temporary exception and the existing SDK contract."""
        checked, failures = self.guard().repository_failures()  # Measure both policy inputs.
        assert checked == 2 and not failures, f"Checked {checked} WebSocket policy files: {failures}"

    def test_missing_return_condition_fails(self) -> None:
        """Prove the guard rejects a constitution without the return condition."""
        text = "Temporary Owned WebSocket Transport only for an affected flow"  # Omit the return requirements.
        failures = self.guard().constitution_failures(text)  # Exercise the failing policy path.
        assert "reviewed supported mistapi release" in failures  # Reject a permanent owned transport.

    def test_missing_private_session_field_fails(self) -> None:
        """Prove the guard rejects a weakened private-session contract."""
        text = 'test_api_session_private_transport_attributes "_cloud_uri", "_apitoken"'  # Omit two fields.
        failures = self.guard().contract_failures(text)  # Exercise the failing contract path.
        assert len(failures) == 1  # Reject an incomplete four-field seam.
