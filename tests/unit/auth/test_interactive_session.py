"""Unit tests for interactive session extraction module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.auth.interactive_session import InteractiveSessionManager


def _build_state() -> dict:
    """Build default mutable state used by tests."""
    return {
        "apisession": None,
        "mistapi": None,
        "msp_privileges": [],
        "selected_msp": None,
        "org_id": None,
    }


def test_initialize_session_requires_email() -> None:
    """Initialization should fail when email is empty."""
    state = _build_state()
    fake_mistapi = MagicMock()
    state["mistapi"] = fake_mistapi
    safe_input = MagicMock(side_effect=["1", ""])  # cloud selection then blank email
    manager = InteractiveSessionManager(state, safe_input, MagicMock(return_value=[]), MagicMock())

    result = manager.initialize_mist_session_interactive()

    assert result is False
    assert state["apisession"] is None


@patch("src.auth.interactive_session.getpass.getpass", return_value="password123")
def test_initialize_session_success_sets_state(_mock_getpass: MagicMock) -> None:
    """Successful login should persist session in shared state."""
    state = _build_state()
    fake_login_session = MagicMock()
    fake_login_session._apitoken = []
    fake_login_session.login_with_return.return_value = {"authenticated": True}
    fake_mistapi = MagicMock()
    fake_mistapi.APISession.return_value = fake_login_session
    state["mistapi"] = fake_mistapi

    detected = [{"msp_id": "msp-1", "msp_name": "Test MSP", "role": "admin"}]
    manager = InteractiveSessionManager(
        state,
        MagicMock(side_effect=["1", "user@example.com"]),
        MagicMock(return_value=detected),
        MagicMock(),
    )

    result = manager.initialize_mist_session_interactive()

    assert result is True
    assert state["apisession"] is fake_login_session
    assert state["msp_privileges"] == detected


def test_select_msp_and_org_skip_calls_org_selector() -> None:
    """Blank MSP selection should delegate to direct org selector."""
    state = _build_state()
    state["msp_privileges"] = [
        {"msp_id": "msp-1", "msp_name": "MSP A", "role": "admin"},
        {"msp_id": "msp-2", "msp_name": "MSP B", "role": "read"},
    ]

    select_org = MagicMock()
    manager = InteractiveSessionManager(state, MagicMock(return_value=""), MagicMock(return_value=[]), select_org)

    manager.select_msp_and_org()

    select_org.assert_called_once()


def test_select_msp_and_org_updates_org_id() -> None:
    """Selecting MSP and org number should update state org_id."""
    state = _build_state()
    state["apisession"] = MagicMock()
    state["msp_privileges"] = [{"msp_id": "msp-1", "msp_name": "MSP A", "role": "admin"}]
    state["mistapi"] = MagicMock()

    response = MagicMock()
    response.data = [
        {"id": "org-1", "name": "Org One"},
        {"id": "org-2", "name": "Org Two"},
    ]
    state["mistapi"].api.v1.msps.orgs.listMspOrgs.return_value = response

    safe_input = MagicMock(side_effect=["2"])  # choose org 2 by list index
    manager = InteractiveSessionManager(state, safe_input, MagicMock(return_value=[]), MagicMock())

    manager.select_msp_and_org()

    assert state["selected_msp"]["msp_id"] == "msp-1"
    assert state["org_id"] == "org-2"
