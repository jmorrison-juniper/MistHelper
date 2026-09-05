"""Unit tests for pause/resume session management (T-016).

Test pause_session(), resume_session() with:
- Successful pause and resume
- Pause state capture and restoration
- 24-hour pause limit enforcement (FR-014)
- Database integration scenarios
"""

from datetime import UTC, datetime, timedelta  # WHY: timestamp handling
from unittest.mock import Mock  # WHY: mock database

from src.upgrade_portal.auth.session import (  # WHY: import under test
    PauseResumeManager,
    PauseState,
    ResumeResult,
)  # WHY: import classes under test


class TestPauseSessionWithDatabase:
    # WHY: test pause_session with database available

    def test_pause_session_success(self) -> None:
        # WHY: verify successful session pause with state capture
        """Pause session succeeds and captures upgrade progress state."""
        # WHY: create mock database router
        mock_db = Mock()  # WHY: mock database
        # WHY: setup mock to return upgrade run document
        mock_db.read.return_value = {  # WHY: upgrade run data
            "run_id": "run-1",  # WHY: run identifier
            "initiated_by": "user-1",  # WHY: user initiator
            "phase": "upgrading",  # WHY: current phase
            "device_statuses": [  # WHY: device list
                {"device_id": "dev-1", "status": "completed"},  # WHY: completed device
                {"device_id": "dev-2", "status": "upgrading"},  # WHY: active device
                {"device_id": "dev-3", "status": "pending"},  # WHY: pending device
            ],  # WHY: devices
            "current_device_id": "dev-2",  # WHY: active device
            "next_device_index": 1,  # WHY: next index
            "failed_devices": [],  # WHY: failed list
            "upgrade_strategy": "serial",  # WHY: strategy
            "retry_count": 0,  # WHY: retries
            "start_time": datetime.now(UTC).isoformat(),  # WHY: start time
            "last_poll_time": datetime.now(UTC).isoformat(),  # WHY: poll time
        }  # WHY: return value

        # WHY: create PauseResumeManager with mock database
        manager = PauseResumeManager(db_router=mock_db)  # WHY: manager instance

        # WHY: pause session
        pause_state = manager.pause_session(run_id="run-1")  # WHY: pause operation

        # WHY: verify pause state was created
        assert isinstance(pause_state, PauseState)  # WHY: check type
        # WHY: verify run ID
        assert pause_state.run_id == "run-1"  # WHY: check ID
        # WHY: verify user who paused
        assert pause_state.paused_by_user == "user-1"  # WHY: check user
        # WHY: verify phase was captured
        assert pause_state.current_phase == "upgrading"  # WHY: check phase
        # WHY: verify device count
        assert pause_state.device_count == 3  # WHY: check count
        # WHY: verify completed count
        assert pause_state.completed_count == 1  # WHY: check completed
        # WHY: verify database update was called
        mock_db.update.assert_called_once()  # WHY: verify update

    def test_pause_session_run_not_found(self) -> None:
        # WHY: verify error when upgrade run does not exist
        """Pause session fails when upgrade run not found."""
        # WHY: create mock database router
        mock_db = Mock()  # WHY: mock database
        # WHY: setup mock to return None (run not found)
        mock_db.read.return_value = None  # WHY: not found

        # WHY: create PauseResumeManager with mock database
        manager = PauseResumeManager(db_router=mock_db)  # WHY: manager instance

        # WHY: pause session and expect error
        try:  # WHY: error handling
            manager.pause_session(run_id="run-1")  # WHY: pause operation
            # WHY: should not reach here
            raise AssertionError("Expected ValueError")  # WHY: fail test
        except ValueError as e:  # WHY: catch error
            # WHY: verify error message
            assert "not found" in str(e).lower()  # WHY: check message


class TestResumeSessionWithDatabase:
    # WHY: test resume_session with database available

    def test_resume_session_success(self) -> None:
        # WHY: verify successful session resume within time limit
        """Resume session succeeds and restores progress state."""
        # WHY: create mock database router
        mock_db = Mock()  # WHY: mock database
        # WHY: setup mock to return upgrade run with pause state
        mock_db.read.return_value = {  # WHY: upgrade run data
            "run_id": "run-1",  # WHY: run identifier
            "pause_state": {  # WHY: pause state dict
                "run_id": "run-1",  # WHY: run ID
                "pause_timestamp": (datetime.now(UTC) - timedelta(hours=1)).isoformat(),  # WHY: 1 hour ago
                "paused_by_user": "user-1",  # WHY: user
                "current_phase": "upgrading",  # WHY: phase
                "device_count": 3,  # WHY: total devices
                "completed_count": 1,  # WHY: completed
                "current_device_id": "dev-2",  # WHY: active device
                "next_device_index": 1,  # WHY: next index
                "failed_devices": [],  # WHY: failed list
                "service_state": {  # WHY: service state
                    "strategy": "serial",  # WHY: strategy
                    "retry_count": 0,  # WHY: retries
                    "start_time": "2026-01-01T00:00:00",  # WHY: start time
                    "last_poll_time": "2026-01-01T00:10:00",  # WHY: poll time
                },  # WHY: state dict
            },  # WHY: pause state
        }  # WHY: return value

        # WHY: create PauseResumeManager with mock database
        manager = PauseResumeManager(db_router=mock_db)  # WHY: manager instance

        # WHY: resume session
        result = manager.resume_session(
            run_id="run-1",  # WHY: run ID
            new_token="new-token-123",  # WHY: new JWT token
        )  # WHY: resume operation

        # WHY: verify resume succeeded
        assert result.resumed is True  # WHY: check success
        # WHY: verify from_device position
        assert result.from_device == 1  # WHY: check position
        # WHY: verify device count
        assert result.device_count == 3  # WHY: check count
        # WHY: verify phase
        assert result.current_phase == "upgrading"  # WHY: check phase
        # WHY: verify database update was called
        mock_db.update.assert_called_once()  # WHY: verify update

    def test_resume_session_expired(self) -> None:
        # WHY: verify error when pause exceeds 24 hour limit
        """Resume session fails when pause time exceeds 24 hours (FR-014)."""
        # WHY: create mock database router
        mock_db = Mock()  # WHY: mock database
        # WHY: setup mock to return run with old pause state
        mock_db.read.return_value = {  # WHY: upgrade run data
            "run_id": "run-1",  # WHY: run identifier
            "pause_state": {  # WHY: pause state dict
                "run_id": "run-1",  # WHY: run ID
                "pause_timestamp": (datetime.now(UTC) - timedelta(hours=25)).isoformat(),  # WHY: 25 hours ago (expired)
                "paused_by_user": "user-1",  # WHY: user
                "current_phase": "upgrading",  # WHY: phase
                "device_count": 3,  # WHY: total devices
                "completed_count": 1,  # WHY: completed
                "next_device_index": 1,  # WHY: next index
                "failed_devices": [],  # WHY: failed list
                "service_state": {},  # WHY: state dict
            },  # WHY: pause state
        }  # WHY: return value

        # WHY: create PauseResumeManager with mock database
        manager = PauseResumeManager(db_router=mock_db)  # WHY: manager instance

        # WHY: resume session
        result = manager.resume_session(
            run_id="run-1",  # WHY: run ID
            new_token="new-token-123",  # WHY: new JWT token
        )  # WHY: resume operation

        # WHY: verify resume failed
        assert result.resumed is False  # WHY: check failure
        # WHY: verify reason
        assert result.reason == "pause_expired"  # WHY: check reason

    def test_resume_session_run_not_found(self) -> None:
        # WHY: verify error when upgrade run does not exist
        """Resume session fails when upgrade run not found."""
        # WHY: create mock database router
        mock_db = Mock()  # WHY: mock database
        # WHY: setup mock to return None (run not found)
        mock_db.read.return_value = None  # WHY: not found

        # WHY: create PauseResumeManager with mock database
        manager = PauseResumeManager(db_router=mock_db)  # WHY: manager instance

        # WHY: resume session
        result = manager.resume_session(
            run_id="run-1",  # WHY: run ID
            new_token="new-token-123",  # WHY: new JWT token
        )  # WHY: resume operation

        # WHY: verify resume failed
        assert result.resumed is False  # WHY: check failure
        # WHY: verify reason
        assert result.reason == "run_not_found"  # WHY: check reason

    def test_resume_session_no_pause_state(self) -> None:
        # WHY: verify error when no pause state found
        """Resume session fails when no pause state exists."""
        # WHY: create mock database router
        mock_db = Mock()  # WHY: mock database
        # WHY: setup mock to return run without pause state
        mock_db.read.return_value = {  # WHY: upgrade run data
            "run_id": "run-1",  # WHY: run identifier
            "pause_state": None,  # WHY: no pause state
        }  # WHY: return value

        # WHY: create PauseResumeManager with mock database
        manager = PauseResumeManager(db_router=mock_db)  # WHY: manager instance

        # WHY: resume session
        result = manager.resume_session(
            run_id="run-1",  # WHY: run ID
            new_token="new-token-123",  # WHY: new JWT token
        )  # WHY: resume operation

        # WHY: verify resume failed
        assert result.resumed is False  # WHY: check failure
        # WHY: verify reason
        assert result.reason == "no_pause_state"  # WHY: check reason


class TestPauseStateDataclass:
    # WHY: test PauseState dataclass

    def test_pause_state_creation(self) -> None:
        # WHY: verify PauseState can be created and accessed
        """PauseState represents pause progress snapshot."""
        # WHY: create pause state
        pause_time = datetime.now(UTC)  # WHY: pause time
        # WHY: construct pause state
        pause_state = PauseState(  # WHY: create state
            run_id="run-1",  # WHY: run ID
            pause_timestamp=pause_time,  # WHY: timestamp
            paused_by_user="user-1",  # WHY: user
            current_phase="upgrading",  # WHY: phase
            device_count=3,  # WHY: total devices
            completed_count=1,  # WHY: completed
            current_device_id="dev-2",  # WHY: active device
            next_device_index=1,  # WHY: next index
        )  # WHY: state creation

        # WHY: verify attributes
        assert pause_state.run_id == "run-1"  # WHY: check ID
        # WHY: verify timestamp
        assert pause_state.pause_timestamp == pause_time  # WHY: check time
        # WHY: verify user
        assert pause_state.paused_by_user == "user-1"  # WHY: check user
        # WHY: verify phase
        assert pause_state.current_phase == "upgrading"  # WHY: check phase
        # WHY: verify device count
        assert pause_state.device_count == 3  # WHY: check count
        # WHY: verify completed count
        assert pause_state.completed_count == 1  # WHY: check completed
        # WHY: verify current device
        assert pause_state.current_device_id == "dev-2"  # WHY: check device
        # WHY: verify next index
        assert pause_state.next_device_index == 1  # WHY: check index


class TestResumeResultDataclass:
    # WHY: test ResumeResult dataclass

    def test_resume_result_success(self) -> None:
        # WHY: verify ResumeResult can represent successful resume
        """ResumeResult represents successful resume."""
        # WHY: create resume result
        result = ResumeResult(  # WHY: create result
            resumed=True,  # WHY: success
            from_device=1,  # WHY: resume position
            device_count=3,  # WHY: total devices
            current_phase="upgrading",  # WHY: phase
        )  # WHY: result creation

        # WHY: verify success flag
        assert result.resumed is True  # WHY: check success
        # WHY: verify from_device
        assert result.from_device == 1  # WHY: check position
        # WHY: verify device count
        assert result.device_count == 3  # WHY: check count
        # WHY: verify phase
        assert result.current_phase == "upgrading"  # WHY: check phase
        # WHY: verify no reason for success
        assert result.reason is None  # WHY: check reason

    def test_resume_result_failure(self) -> None:
        # WHY: verify ResumeResult can represent failed resume
        """ResumeResult represents failed resume."""
        # WHY: create resume result
        result = ResumeResult(  # WHY: create result
            resumed=False,  # WHY: failure
            reason="pause_expired",  # WHY: reason
        )  # WHY: result creation

        # WHY: verify failure flag
        assert result.resumed is False  # WHY: check failure
        # WHY: verify reason
        assert result.reason == "pause_expired"  # WHY: check reason
        # WHY: verify from_device is None
        assert result.from_device is None  # WHY: check position
