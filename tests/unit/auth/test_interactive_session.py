"""Unit tests for LoginOrchestrator and MspOrgSelector collaborators."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.auth.interactive import LoginOrchestrator, MspOrgSelector


def _build_state() -> dict:
    """Build default mutable state used by tests."""
    return {  # Mutable state bag passed by reference to the collaborators
        "apisession": None,  # Will be populated on successful login
        "mistapi": None,  # Will be populated when a fake SDK is injected
        "msp_privileges": [],  # Will be populated by detect_msp_privileges callback
        "selected_msp": None,  # Will be populated by MspOrgSelector
        "org_id": None,  # Will be populated by MspOrgSelector
    }


def test_login_orchestrator_requires_email() -> None:
    """LoginOrchestrator.execute() should fail when email is empty."""
    state = _build_state()  # Fresh state bag for this test
    fake_mistapi = MagicMock()  # Stand-in mistapi SDK
    state["mistapi"] = fake_mistapi  # Inject SDK so the orchestrator resolves it from state
    safe_input = MagicMock(side_effect=["1", ""])  # Cloud selection then blank email triggers abort
    orchestrator = LoginOrchestrator(  # Build orchestrator with injected dependencies
        state=state,
        safe_input=safe_input,
        detect_msp_privileges=MagicMock(return_value=[]),
    )

    result = orchestrator.execute()  # Run the workflow; blank email should abort

    assert result is False  # Workflow must signal failure on blank email
    assert state["apisession"] is None  # State must not be mutated on failure


@patch("src.auth.interactive.credential_prompter.getpass.getpass", return_value="password123")
def test_login_orchestrator_success_sets_state(_mock_getpass: MagicMock) -> None:
    """Successful LoginOrchestrator.execute() should persist session in shared state."""
    state = _build_state()  # Fresh state bag for this test
    fake_login_session = MagicMock()  # Stand-in mistapi APISession instance
    fake_login_session._apitoken = []  # Empty token list -> credential-mode login
    fake_login_session.login_with_return.return_value = {"authenticated": True}  # Force success path
    fake_mistapi = MagicMock()  # Stand-in mistapi SDK module
    fake_mistapi.APISession.return_value = fake_login_session  # SDK returns our fake session on init
    state["mistapi"] = fake_mistapi  # Inject SDK into state for orchestrator to discover

    detected = [{"msp_id": "msp-1", "msp_name": "Test MSP", "role": "admin"}]  # Sample MSP grant
    orchestrator = LoginOrchestrator(  # Build orchestrator with injected dependencies
        state=state,
        safe_input=MagicMock(side_effect=["1", "user@example.com"]),  # Cloud choice then email
        detect_msp_privileges=MagicMock(return_value=detected),  # Return one MSP grant after login
    )

    result = orchestrator.execute()  # Run the full login workflow

    assert result is True  # Successful login must return True
    assert state["apisession"] is fake_login_session  # Session must be persisted into state
    assert state["msp_privileges"] == detected  # Detected MSP grants must be persisted into state


def test_msp_org_selector_skip_calls_fallback() -> None:
    """Blank MSP selection should delegate to the injected fallback org selector."""
    state = _build_state()  # Fresh state bag for this test
    state["msp_privileges"] = [  # Multiple MSPs present so the selector renders a picker
        {"msp_id": "msp-1", "msp_name": "MSP A", "role": "admin"},
        {"msp_id": "msp-2", "msp_name": "MSP B", "role": "read"},
    ]

    select_org = MagicMock()  # Stand-in for the non-MSP fallback callback
    selector = MspOrgSelector(  # Build selector with injected dependencies
        state=state,
        safe_input=MagicMock(return_value=""),  # Blank input skips MSP selection
        select_org_fallback=select_org,
    )

    selector.select()  # Run the MSP/org selection workflow

    select_org.assert_called_once()  # Fallback must be invoked exactly once on skip


def test_msp_org_selector_updates_org_id() -> None:
    """Selecting MSP and org number should update state['org_id']."""
    state = _build_state()  # Fresh state bag for this test
    state["apisession"] = MagicMock()  # Authenticated session required for MSP org listing
    state["msp_privileges"] = [{"msp_id": "msp-1", "msp_name": "MSP A", "role": "admin"}]  # Single MSP
    state["mistapi"] = MagicMock()  # Stand-in SDK; auto-picks single MSP, then lists its orgs

    response = MagicMock()  # Stand-in mistapi response object
    response.data = [  # Two-org list returned by the SDK
        {"id": "org-1", "name": "Org One"},
        {"id": "org-2", "name": "Org Two"},
    ]
    state["mistapi"].api.v1.msps.orgs.listMspOrgs.return_value = response  # Wire response into SDK

    safe_input = MagicMock(side_effect=["2"])  # Operator chooses org index 2
    selector = MspOrgSelector(  # Build selector with injected dependencies
        state=state,
        safe_input=safe_input,
        select_org_fallback=MagicMock(),
    )

    selector.select()  # Run the MSP/org selection workflow

    assert state["selected_msp"]["msp_id"] == "msp-1"  # Single MSP must be auto-selected
    assert state["org_id"] == "org-2"  # Org index 2 must be persisted into state
