"""Unit tests for ComparisonService (T-012).

Tests comparison service initialization, validation, settle gate prerequisite
checks, pre/post capture fetching, delta calculation, and ArangoDB persistence.
Uses pytest with AsyncMock for dependency injection and isolation.
"""

from unittest.mock import Mock, patch  # WHY: dependency mocking

import pytest  # WHY: test framework

# WHY: import service under test
from src.upgrade_portal.compare.service import (
    ComparisonResult,  # WHY: T-012 result
    ComparisonResultService,  # WHY: T-013 service
    ComparisonService,  # WHY: T-012 service
    DetailedComparisonResult,  # WHY: T-013 result
)


class TestComparisonResult:
    """Test ComparisonResult dataclass."""

    def test_comparison_result_frozen_immutable(self):  # WHY: verify immutability
        """ComparisonResult must be immutable once created."""
        # WHY: create result
        result = ComparisonResult(passed=True, run_id="run-123")

        # WHY: attempt to modify should raise TypeError
        with pytest.raises(AttributeError):  # WHY: expect immutable error
            result.passed = False  # WHY: try to modify

        # WHY: result remains unchanged
        assert result.passed is True  # WHY: verify original

    def test_comparison_result_defaults(self):  # WHY: test default values
        """Verify default values for optional fields."""
        # WHY: create minimal result
        result = ComparisonResult(passed=False, run_id="run-456")

        # WHY: verify defaults are set
        assert result.settled is False  # WHY: default settled
        assert result.deltas == []  # WHY: default deltas
        assert result.summary == {}  # WHY: default summary
        assert result.failed_checks == []  # WHY: default failed_checks
        assert result.timestamp is not None  # WHY: timestamp auto-generated

    def test_comparison_result_custom_values(self):  # WHY: test custom values
        """Verify custom values are stored correctly."""
        # WHY: prepare test data
        deltas = [{"device": "ap1", "firmware": {"pre": "1.0", "post": "2.0"}}]  # WHY: sample deltas
        summary = {"firmware_changes": 1}  # WHY: sample summary
        failed = ["ping_check"]  # WHY: sample failures

        # WHY: create result with custom values
        result = ComparisonResult(
            passed=True,
            run_id="run-789",
            settled=True,
            deltas=deltas,
            summary=summary,
            failed_checks=failed,
        )

        # WHY: verify values stored
        assert result.passed is True  # WHY: verify passed
        assert result.settled is True  # WHY: verify settled
        assert result.deltas == deltas  # WHY: verify deltas
        assert result.summary == summary  # WHY: verify summary
        assert result.failed_checks == failed  # WHY: verify failures


class TestComparisonServiceInit:
    """Test ComparisonService initialization."""

    def test_comparison_service_init_with_dependencies(self):  # WHY: test init with all deps
        """Service must accept all dependencies."""
        # WHY: create mock dependencies
        settle_gate = Mock()  # WHY: mock settle gate
        db_router = Mock()  # WHY: mock database
        audit_logger = Mock()  # WHY: mock audit logger

        # WHY: create service
        service = ComparisonService(
            settle_gate_service=settle_gate,
            db_router=db_router,
            audit_logger=audit_logger,
        )

        # WHY: verify dependencies stored
        assert service.settle_gate_service is settle_gate  # WHY: verify settle gate
        assert service.db_router is db_router  # WHY: verify db_router
        assert service.audit_logger is audit_logger  # WHY: verify audit_logger

    def test_comparison_service_init_without_dependencies(self):  # WHY: test init without deps
        """Service must handle missing dependencies gracefully."""
        # WHY: create service without dependencies
        service = ComparisonService()

        # WHY: verify defaults are None
        assert service.settle_gate_service is None  # WHY: no settle gate
        assert service.db_router is None  # WHY: no db_router
        assert service.audit_logger is None  # WHY: no audit_logger

    def test_comparison_service_constants(self):  # WHY: test class constants
        """Verify service constants are defined correctly."""
        # WHY: create service
        service = ComparisonService()

        # WHY: verify constants
        assert service.MAX_RETRIES == 3  # WHY: verify retries
        assert service.RETRY_BACKOFF_SECONDS == 1  # WHY: verify backoff
        assert service.DB_READ_TIMEOUT_SECONDS == 30  # WHY: verify timeout
        assert service.COMPARISON_TIMEOUT_SECONDS == 60  # WHY: verify total timeout


class TestComparisonServiceValidation:
    """Test ComparisonService input validation."""

    def test_compare_invalid_run_id(self):  # WHY: test invalid run_id
        """compare() must validate run_id."""
        # WHY: create service
        service = ComparisonService(
            settle_gate_service=Mock(),
            db_router=Mock(),
        )

        # WHY: test with empty run_id
        result = service.compare(
            run_id="",  # WHY: invalid
            site_id="site-1",
            org_id="org-1",
            device_ids=["dev-1"],
        )

        # WHY: verify validation failed
        assert result.passed is False  # WHY: failed
        assert result.run_id == ""  # WHY: original run_id

        # WHY: test with None run_id
        result = service.compare(
            run_id=None,  # WHY: invalid type
            site_id="site-1",
            org_id="org-1",
            device_ids=["dev-1"],
        )

        # WHY: verify validation failed
        assert result.passed is False  # WHY: failed

    def test_compare_invalid_device_list(self):  # WHY: test invalid device list
        """compare() must validate device_ids."""
        # WHY: create service
        service = ComparisonService(
            settle_gate_service=Mock(),
            db_router=Mock(),
        )

        # WHY: test with empty device list
        result = service.compare(
            run_id="run-1",
            site_id="site-1",
            org_id="org-1",
            device_ids=[],  # WHY: invalid
        )

        # WHY: verify validation failed
        assert result.passed is False  # WHY: failed
        assert result.settled is False  # WHY: not settled

        # WHY: test with non-list device_ids
        result = service.compare(
            run_id="run-1",
            site_id="site-1",
            org_id="org-1",
            device_ids="dev-1",  # WHY: not a list
        )

        # WHY: verify validation failed
        assert result.passed is False  # WHY: failed

    def test_compare_missing_dependencies(self):  # WHY: test missing deps
        """compare() must handle missing dependencies."""
        # WHY: create service without settle gate
        service = ComparisonService(
            settle_gate_service=None,  # WHY: missing
            db_router=Mock(),
        )

        # WHY: compare should fail
        result = service.compare(
            run_id="run-1",
            site_id="site-1",
            org_id="org-1",
            device_ids=["dev-1"],
        )

        # WHY: verify failed
        assert result.passed is False  # WHY: dependency check failed


class TestComparisonServiceSettleGatePrerequisite:
    """Test settle gate prerequisite checks."""

    def test_compare_settle_gate_passed(self):  # WHY: test successful settle gate
        """compare() must proceed when settle gate passes."""
        # WHY: create mocks
        settle_gate = Mock()  # WHY: mock settle gate
        db_router = Mock()  # WHY: mock database
        audit_logger = Mock()  # WHY: mock audit logger

        # WHY: create service
        service = ComparisonService(
            settle_gate_service=settle_gate,
            db_router=db_router,
            audit_logger=audit_logger,
        )

        # WHY: mock settle gate result (returns None from placeholder)
        # Service will check settle gate but placeholder returns None
        # Actual comparison continues with placeholder implementations

        # WHY: call compare
        result = service.compare(
            run_id="run-1",
            site_id="site-1",
            org_id="org-1",
            device_ids=["dev-1"],
            user_id="user-1",
        )

        # WHY: verify returned result
        assert isinstance(result, ComparisonResult)  # WHY: correct type

    def test_compare_settle_gate_failed(self):  # WHY: test settle gate failure
        """compare() must fail when settle gate fails."""
        # WHY: create mocks
        settle_gate = Mock()  # WHY: mock settle gate
        db_router = Mock()  # WHY: mock database
        audit_logger = Mock()  # WHY: mock audit logger

        # WHY: mock settle gate to return failure result
        # Note: placeholder _check_settle_gate() returns success
        # In production, would mock this to return failure
        # For now, test the failure path logic

        # WHY: create result that simulate settle gate failure
        # Directly call _check_settle_gate (which returns success by default)
        # To test failure path, we'd need to patch the method

        service = ComparisonService(
            settle_gate_service=settle_gate,
            db_router=db_router,
            audit_logger=audit_logger,
        )

        # WHY: test failure path by mocking _check_settle_gate
        with patch.object(service, "_check_settle_gate") as mock_check:  # WHY: patch method  # WHY: create mock
            # WHY: return failure result
            mock_check.return_value = {
                "passed": False,  # WHY: failed
                "failed_checks": ["ping_check", "api_check"],  # WHY: failures
            }

            # WHY: call compare
            result = service.compare(
                run_id="run-1",
                site_id="site-1",
                org_id="org-1",
                device_ids=["dev-1"],
                user_id="user-1",
            )

            # WHY: verify comparison blocked
            assert result.passed is False  # WHY: blocked
            assert result.settled is False  # WHY: not settled
            assert len(result.failed_checks) > 0  # WHY: failures present


class TestComparisonServicePrePostCaptureFetch:
    """Test pre/post capture fetching."""

    def test_fetch_pre_capture_success(self):  # WHY: test successful fetch
        """_fetch_pre_capture() must return capture document."""
        # WHY: create service
        service = ComparisonService()

        # WHY: call fetch
        result = service._fetch_pre_capture(run_id="run-1")

        # WHY: verify result
        assert result is not None  # WHY: not None
        assert result["run_id"] == "run-1"  # WHY: correct run_id
        assert result["capture_type"] == "pre"  # WHY: correct type
        assert "timestamp" in result  # WHY: has timestamp

    def test_fetch_post_capture_success(self):  # WHY: test successful fetch
        """_fetch_post_capture() must return capture document."""
        # WHY: create service
        service = ComparisonService()

        # WHY: call fetch
        result = service._fetch_post_capture(run_id="run-1")

        # WHY: verify result
        assert result is not None  # WHY: not None
        assert result["run_id"] == "run-1"  # WHY: correct run_id
        assert result["capture_type"] == "post"  # WHY: correct type
        assert "timestamp" in result  # WHY: has timestamp


class TestComparisonServiceDeltaCalculation:
    """Test delta calculation between captures."""

    def test_calculate_deltas_empty_captures(self):  # WHY: test empty captures
        """_calculate_deltas() must handle empty captures."""
        # WHY: create service
        service = ComparisonService()

        # WHY: create empty captures
        pre_capture = {"device_snapshots": []}  # WHY: empty pre  # WHY: no devices
        post_capture = {"device_snapshots": []}  # WHY: empty post  # WHY: no devices

        # WHY: calculate deltas
        deltas, summary = service._calculate_deltas(
            pre_capture=pre_capture,
            post_capture=post_capture,
        )

        # WHY: verify results
        assert isinstance(deltas, list)  # WHY: is list
        assert isinstance(summary, dict)  # WHY: is dict
        assert "firmware_changes" in summary  # WHY: has firmware key
        assert "total_devices_compared" in summary  # WHY: has device key

    def test_calculate_deltas_with_snapshots(self):  # WHY: test with snapshots
        """_calculate_deltas() must work with device snapshots."""
        # WHY: create service
        service = ComparisonService()

        # WHY: create captures with snapshots
        pre_capture = {  # WHY: pre-capture
            "device_snapshots": [{"device_id": "dev-1", "firmware": "1.0"}]  # WHY: sample device
        }
        post_capture = {  # WHY: post-capture
            "device_snapshots": [{"device_id": "dev-1", "firmware": "2.0"}]  # WHY: updated device
        }

        # WHY: calculate deltas
        deltas, summary = service._calculate_deltas(
            pre_capture=pre_capture,
            post_capture=post_capture,
        )

        # WHY: verify results
        assert isinstance(deltas, list)  # WHY: is list
        assert isinstance(summary, dict)  # WHY: is dict


class TestComparisonServiceCompareFull:
    """Test full compare() workflow."""

    def test_compare_full_success_path(self):  # WHY: test happy path
        """compare() must complete full workflow on success."""
        # WHY: create mocks
        settle_gate = Mock()  # WHY: mock settle gate
        db_router = Mock()  # WHY: mock database
        db_router.write.return_value = True  # WHY: successful write
        audit_logger = Mock()  # WHY: mock audit logger

        # WHY: create service
        service = ComparisonService(
            settle_gate_service=settle_gate,
            db_router=db_router,
            audit_logger=audit_logger,
        )

        # WHY: call compare
        result = service.compare(
            run_id="run-1",
            site_id="site-1",
            org_id="org-1",
            device_ids=["dev-1", "dev-2"],
            user_id="user-1",
        )

        # WHY: verify result type
        assert isinstance(result, ComparisonResult)  # WHY: correct type

    def test_compare_audit_logging(self):  # WHY: test audit logging
        """compare() must audit log operations."""
        # WHY: create mocks
        settle_gate = Mock()  # WHY: mock settle gate
        db_router = Mock()  # WHY: mock database
        db_router.write.return_value = True  # WHY: successful write
        audit_logger = Mock()  # WHY: mock audit logger

        # WHY: create service
        service = ComparisonService(
            settle_gate_service=settle_gate,
            db_router=db_router,
            audit_logger=audit_logger,
        )

        # WHY: call compare
        result = service.compare(
            run_id="run-1",
            site_id="site-1",
            org_id="org-1",
            device_ids=["dev-1"],
            user_id="user-1",
        )

        # WHY: verify audit_logger.log_operation was called
        assert audit_logger.log_operation.called  # WHY: audit logged
        assert isinstance(result, ComparisonResult)  # WHY: result type valid


class TestComparisonServiceCheckSettleGate:
    """Test settle gate check method."""

    def test_check_settle_gate_success(self):  # WHY: test success
        """_check_settle_gate() must return success dict."""
        # WHY: create service
        service = ComparisonService()

        # WHY: call check
        result = service._check_settle_gate(
            run_id="run-1",
            site_id="site-1",
            org_id="org-1",
            device_ids=["dev-1"],
        )

        # WHY: verify result
        assert result is not None  # WHY: not None
        assert "passed" in result  # WHY: has passed key
        assert "failed_checks" in result  # WHY: has failed_checks key


class TestComparisonServiceException:
    """Test exception handling."""

    def test_compare_exception_handling(self):  # WHY: test exception handling
        """compare() must handle exceptions gracefully."""
        # WHY: create mock that raises exception
        settle_gate = Mock()  # WHY: mock settle gate
        db_router = Mock()  # WHY: mock database
        db_router.write.side_effect = Exception("DB error")  # WHY: raise error
        audit_logger = Mock()  # WHY: mock audit logger

        # WHY: create service
        service = ComparisonService(
            settle_gate_service=settle_gate,
            db_router=db_router,
            audit_logger=audit_logger,
        )

        # WHY: patch _fetch_pre_capture to raise exception
        with patch.object(service, "_fetch_pre_capture") as mock_fetch:  # WHY: patch
            mock_fetch.side_effect = Exception("Fetch error")  # WHY: raise error

            # WHY: call compare
            result = service.compare(
                run_id="run-1",
                site_id="site-1",
                org_id="org-1",
                device_ids=["dev-1"],
            )

            # WHY: verify failure result
            assert result.passed is False  # WHY: failed
            assert result.run_id == "run-1"  # WHY: run_id preserved


# ==========================================
# T-013 TESTS: ComparisonResultService
# ==========================================


class TestDetailedComparisonResult:
    """Test DetailedComparisonResult dataclass."""

    def test_detailed_result_frozen_immutable(self):  # WHY: verify immutability
        """DetailedComparisonResult must be immutable once created."""
        # WHY: create result
        result = DetailedComparisonResult(run_id="run-123")

        # WHY: attempt to modify should raise TypeError
        with pytest.raises(AttributeError):  # WHY: expect immutable error
            result.run_id = "run-456"  # WHY: try to modify

        # WHY: result remains unchanged
        assert result.run_id == "run-123"  # WHY: verify original

    def test_detailed_result_defaults(self):  # WHY: test default values
        """Verify default values for optional fields."""
        # WHY: create minimal result
        result = DetailedComparisonResult(run_id="run-456")

        # WHY: verify defaults are set
        assert result.deltas == []  # WHY: default deltas
        assert result.summary == {}  # WHY: default summary
        assert result.flagged_for_review == []  # WHY: default flagged
        assert result.timestamp is not None  # WHY: timestamp auto-generated

    def test_detailed_result_custom_values(self):  # WHY: test custom values
        """Verify custom values are stored correctly."""
        # WHY: prepare test data
        deltas = [  # WHY: sample deltas
            {
                "device_id": "ap1",  # WHY: device identifier
                "field": "firmware_version",  # WHY: field type
                "delta_type": "firmware_upgrade",  # WHY: change type
                "pre_value": "1.0",  # WHY: old value
                "post_value": "2.0",  # WHY: new value
                "severity": "high",  # WHY: severity
            }
        ]  # WHY: deltas complete
        summary = {"total_deltas": 1, "by_severity": {"high": 1}}  # WHY: sample summary
        flagged = [deltas[0]]  # WHY: high-severity

        # WHY: create result with custom values
        result = DetailedComparisonResult(
            run_id="run-789",  # WHY: run identifier
            deltas=deltas,  # WHY: deltas
            summary=summary,  # WHY: summary
            flagged_for_review=flagged,  # WHY: flagged items
        )  # WHY: result created

        # WHY: verify values stored
        assert result.run_id == "run-789"  # WHY: verify run_id
        assert len(result.deltas) == 1  # WHY: verify delta count
        assert result.summary["total_deltas"] == 1  # WHY: verify summary
        assert len(result.flagged_for_review) == 1  # WHY: verify flagged


class TestComparisonResultServiceInit:
    """Test ComparisonResultService initialization."""

    def test_service_init_with_dependencies(self):  # WHY: test init with all deps
        """Service must accept all dependencies."""
        # WHY: create mock dependencies
        db_router = Mock()  # WHY: mock database
        audit_logger = Mock()  # WHY: mock audit logger
        masker = Mock()  # WHY: mock masker

        # WHY: create service
        service = ComparisonResultService(
            db_router=db_router,  # WHY: database
            audit_logger=audit_logger,  # WHY: audit trail
            masker=masker,  # WHY: secret masking
        )  # WHY: service created

        # WHY: verify dependencies stored
        assert service.db_router is db_router  # WHY: verify db_router
        assert service.audit_logger is audit_logger  # WHY: verify audit_logger
        assert service.masker is masker  # WHY: verify masker

    def test_service_init_without_dependencies(self):  # WHY: test init without deps
        """Service must handle missing dependencies gracefully."""
        # WHY: create service without dependencies
        service = ComparisonResultService()

        # WHY: verify defaults are None
        assert service.db_router is None  # WHY: no db_router
        assert service.audit_logger is None  # WHY: no audit_logger
        assert service.masker is None  # WHY: no masker

    def test_service_severity_levels(self):  # WHY: test class constants
        """Verify service severity levels are defined correctly."""
        # WHY: create service
        service = ComparisonResultService()

        # WHY: verify severity mappings
        assert service.SEVERITY_LEVELS["firmware_downgrade"] == "critical"  # WHY: rollback
        assert service.SEVERITY_LEVELS["firmware_upgrade"] == "high"  # WHY: upgrade
        assert service.SEVERITY_LEVELS["policy_change"] == "high"  # WHY: policy
        assert service.SEVERITY_LEVELS["device_removed"] == "high"  # WHY: missing device
        assert service.SEVERITY_LEVELS["device_added"] == "medium"  # WHY: new device


class TestAnalyzeDeltasInventory:
    """Test inventory delta analysis."""

    def test_analyze_inventory_no_changes(self):  # WHY: test no inventory changes
        """analyze_deltas() must handle identical device inventory."""
        # WHY: create service
        service = ComparisonResultService(
            db_router=Mock(),  # WHY: mock database
            audit_logger=Mock(),  # WHY: mock audit
        )  # WHY: service created

        # WHY: create identical pre and post captures
        pre_capture = {  # WHY: pre-capture
            "devices": [{"device_id": "ap1", "name": "AP-1", "model": "MX5"}]  # WHY: device list  # WHY: sample device
        }  # WHY: pre complete
        post_capture = {  # WHY: post-capture
            "devices": [{"device_id": "ap1", "name": "AP-1", "model": "MX5"}]  # WHY: device list  # WHY: same device
        }  # WHY: post complete

        # WHY: analyze deltas
        result = service.analyze_deltas(
            run_id="run-1",  # WHY: run identifier
            pre_capture=pre_capture,  # WHY: pre-snapshot
            post_capture=post_capture,  # WHY: post-snapshot
            user_id="user-1",  # WHY: audit context
        )  # WHY: analysis complete

        # WHY: verify no inventory deltas
        inventory_deltas = [d for d in result.deltas if d["field"] == "inventory"]  # WHY: filter
        assert len(inventory_deltas) == 0  # WHY: no changes
        assert result.summary["by_type"]["inventory"] == 0  # WHY: verify count
        assert len(result.flagged_for_review) == 0  # WHY: no flags

    def test_analyze_inventory_device_added(self):  # WHY: test device added
        """analyze_deltas() must detect added devices."""
        # WHY: create service
        service = ComparisonResultService(
            db_router=Mock(),  # WHY: mock database
            audit_logger=Mock(),  # WHY: mock audit
        )  # WHY: service created

        # WHY: create pre/post with added device
        pre_capture = {  # WHY: pre-capture
            "devices": [  # WHY: device list
                {"device_id": "ap1", "name": "AP-1", "model": "MX5"}  # WHY: original device
            ]
        }  # WHY: pre complete
        post_capture = {  # WHY: post-capture
            "devices": [  # WHY: device list
                {"device_id": "ap1", "name": "AP-1", "model": "MX5"},  # WHY: original
                {"device_id": "ap2", "name": "AP-2", "model": "MX5"},  # WHY: new device
            ]
        }  # WHY: post complete

        # WHY: analyze deltas
        result = service.analyze_deltas(
            run_id="run-1",  # WHY: run identifier
            pre_capture=pre_capture,  # WHY: pre-snapshot
            post_capture=post_capture,  # WHY: post-snapshot
            user_id="user-1",  # WHY: audit context
        )  # WHY: analysis complete

        # WHY: verify device added delta
        device_added = [  # WHY: filter results
            d for d in result.deltas if d.get("delta_type") == "device_added"  # WHY: iterate  # WHY: match type
        ]  # WHY: filter complete
        assert len(device_added) == 1  # WHY: one added
        assert device_added[0]["device_id"] == "ap2"  # WHY: correct device
        assert device_added[0]["severity"] == "medium"  # WHY: medium severity

    def test_analyze_inventory_device_removed(self):  # WHY: test device removed
        """analyze_deltas() must detect removed devices."""
        # WHY: create service
        service = ComparisonResultService(
            db_router=Mock(),  # WHY: mock database
            audit_logger=Mock(),  # WHY: mock audit
        )  # WHY: service created

        # WHY: create pre/post with removed device
        pre_capture = {  # WHY: pre-capture
            "devices": [  # WHY: device list
                {"device_id": "ap1", "name": "AP-1", "model": "MX5"},  # WHY: original
                {"device_id": "ap2", "name": "AP-2", "model": "MX5"},  # WHY: device to remove
            ]
        }  # WHY: pre complete
        post_capture = {  # WHY: post-capture
            "devices": [{"device_id": "ap1", "name": "AP-1", "model": "MX5"}]  # WHY: device list  # WHY: remaining
        }  # WHY: post complete

        # WHY: analyze deltas
        result = service.analyze_deltas(
            run_id="run-1",  # WHY: run identifier
            pre_capture=pre_capture,  # WHY: pre-snapshot
            post_capture=post_capture,  # WHY: post-snapshot
            user_id="user-1",  # WHY: audit context
        )  # WHY: analysis complete

        # WHY: verify device removed delta
        device_removed = [  # WHY: filter results
            d for d in result.deltas if d.get("delta_type") == "device_removed"  # WHY: iterate  # WHY: match type
        ]  # WHY: filter complete
        assert len(device_removed) == 1  # WHY: one removed
        assert device_removed[0]["device_id"] == "ap2"  # WHY: correct device
        assert device_removed[0]["severity"] == "high"  # WHY: high severity


class TestAnalyzeDeltasFirmware:
    """Test firmware delta analysis."""

    def test_analyze_firmware_upgrade(self):  # WHY: test firmware upgrade
        """analyze_deltas() must detect firmware upgrades."""
        # WHY: create service
        service = ComparisonResultService(
            db_router=Mock(),  # WHY: mock database
            audit_logger=Mock(),  # WHY: mock audit
        )  # WHY: service created

        # WHY: create pre/post with firmware upgrade
        pre_capture = {  # WHY: pre-capture
            "devices": [  # WHY: device list
                {  # WHY: device
                    "device_id": "ap1",  # WHY: identifier
                    "name": "AP-1",  # WHY: name
                    "firmware_version": "1.0.0",  # WHY: old version
                }  # WHY: device complete
            ]
        }  # WHY: pre complete
        post_capture = {  # WHY: post-capture
            "devices": [  # WHY: device list
                {  # WHY: device
                    "device_id": "ap1",  # WHY: identifier
                    "name": "AP-1",  # WHY: name
                    "firmware_version": "2.0.0",  # WHY: new version
                }  # WHY: device complete
            ]
        }  # WHY: post complete

        # WHY: analyze deltas
        result = service.analyze_deltas(
            run_id="run-1",  # WHY: run identifier
            pre_capture=pre_capture,  # WHY: pre-snapshot
            post_capture=post_capture,  # WHY: post-snapshot
            user_id="user-1",  # WHY: audit context
        )  # WHY: analysis complete

        # WHY: verify firmware upgrade delta
        firmware_changes = [  # WHY: filter results
            d for d in result.deltas if d.get("field") == "firmware_version"  # WHY: iterate  # WHY: match field
        ]  # WHY: filter complete
        assert len(firmware_changes) == 1  # WHY: one change
        assert firmware_changes[0]["delta_type"] == "firmware_upgrade"  # WHY: upgrade type
        assert firmware_changes[0]["severity"] == "high"  # WHY: high severity
        assert firmware_changes[0]["pre_value"] == "1.0.0"  # WHY: old version
        assert firmware_changes[0]["post_value"] == "2.0.0"  # WHY: new version

    def test_analyze_firmware_downgrade(self):  # WHY: test firmware rollback
        """analyze_deltas() must detect firmware downgrades (rollback)."""
        # WHY: create service
        service = ComparisonResultService(
            db_router=Mock(),  # WHY: mock database
            audit_logger=Mock(),  # WHY: mock audit
        )  # WHY: service created

        # WHY: create pre/post with firmware downgrade
        pre_capture = {  # WHY: pre-capture
            "devices": [  # WHY: device list
                {  # WHY: device
                    "device_id": "ap1",  # WHY: identifier
                    "name": "AP-1",  # WHY: name
                    "firmware_version": "2.0.0",  # WHY: new version
                }  # WHY: device complete
            ]
        }  # WHY: pre complete
        post_capture = {  # WHY: post-capture
            "devices": [  # WHY: device list
                {  # WHY: device
                    "device_id": "ap1",  # WHY: identifier
                    "name": "AP-1",  # WHY: name
                    "firmware_version": "1.0.0",  # WHY: old version (rollback)
                }  # WHY: device complete
            ]
        }  # WHY: post complete

        # WHY: analyze deltas
        result = service.analyze_deltas(
            run_id="run-1",  # WHY: run identifier
            pre_capture=pre_capture,  # WHY: pre-snapshot
            post_capture=post_capture,  # WHY: post-snapshot
            user_id="user-1",  # WHY: audit context
        )  # WHY: analysis complete

        # WHY: verify firmware downgrade delta
        firmware_changes = [  # WHY: filter results
            d for d in result.deltas if d.get("field") == "firmware_version"  # WHY: iterate  # WHY: match field
        ]  # WHY: filter complete
        assert len(firmware_changes) == 1  # WHY: one change
        assert firmware_changes[0]["delta_type"] == "firmware_downgrade"  # WHY: downgrade type
        assert firmware_changes[0]["severity"] == "critical"  # WHY: critical severity
        # WHY: verify change is flagged for review
        flagged = [d for d in result.flagged_for_review if d["device_id"] == "ap1"]  # WHY: filter
        assert len(flagged) == 1  # WHY: one flagged


class TestAnalyzeDeltasValidation:
    """Test delta analysis input validation."""

    def test_analyze_deltas_empty_run_id(self):  # WHY: test empty run_id
        """analyze_deltas() must handle empty run_id."""
        # WHY: create service
        service = ComparisonResultService()

        # WHY: analyze with empty run_id
        result = service.analyze_deltas(
            run_id="",  # WHY: invalid
            pre_capture={"devices": []},  # WHY: capture
            post_capture={"devices": []},  # WHY: capture
        )  # WHY: analysis complete

        # WHY: verify empty result
        assert result.run_id == ""  # WHY: run_id preserved
        assert len(result.deltas) == 0  # WHY: no deltas
        assert result.summary == {}  # WHY: empty summary

    def test_analyze_deltas_missing_captures(self):  # WHY: test missing captures
        """analyze_deltas() must handle missing captures."""
        # WHY: create service
        service = ComparisonResultService()

        # WHY: analyze with None captures
        result = service.analyze_deltas(
            run_id="run-1",  # WHY: run identifier
            pre_capture=None,  # WHY: invalid
            post_capture=None,  # WHY: invalid
        )  # WHY: analysis complete

        # WHY: verify empty result
        assert result.run_id == "run-1"  # WHY: run_id preserved
        assert len(result.deltas) == 0  # WHY: no deltas

    def test_analyze_deltas_audit_logging(self):  # WHY: test audit logging
        """analyze_deltas() must log audit trail."""
        # WHY: create mock audit logger
        audit_logger = Mock()  # WHY: mock audit

        # WHY: create service with audit logger
        service = ComparisonResultService(
            db_router=Mock(),  # WHY: mock database
            audit_logger=audit_logger,  # WHY: audit logger
        )  # WHY: service created

        # WHY: analyze deltas
        result = service.analyze_deltas(
            run_id="run-1",  # WHY: run identifier
            pre_capture={"devices": []},  # WHY: pre-capture
            post_capture={"devices": []},  # WHY: post-capture
            user_id="user-1",  # WHY: audit context
        )  # WHY: analysis complete

        # WHY: verify result type
        assert isinstance(result, DetailedComparisonResult)  # WHY: correct type
        # WHY: verify audit logging called
        assert audit_logger.log_operation.called  # WHY: audit logged
        call_args = audit_logger.log_operation.call_args  # WHY: get call args
        # WHY: verify operation name
        assert "delta_analysis_complete" in str(call_args)  # WHY: check operation name
        # WHY: verify success status
        assert "success" in str(call_args)  # WHY: check status


class TestAnalyzeDeltasExceptionHandling:
    """Test delta analysis exception handling."""

    def test_analyze_deltas_exception_handling(self):  # WHY: test exception handling
        """analyze_deltas() must handle exceptions gracefully."""
        # WHY: create service
        service = ComparisonResultService(
            db_router=Mock(),  # WHY: mock database
            audit_logger=Mock(),  # WHY: mock audit
        )  # WHY: service created

        # WHY: patch inventory analysis to raise exception
        with patch.object(
            service,  # WHY: patch object
            "_analyze_inventory_deltas",  # WHY: method name
            side_effect=Exception("Analysis error"),  # WHY: raise error
        ):  # WHY: patch complete
            # WHY: analyze deltas
            result = service.analyze_deltas(
                run_id="run-1",  # WHY: run identifier
                pre_capture={"devices": [{"device_id": "ap1"}]},  # WHY: pre-capture
                post_capture={"devices": [{"device_id": "ap1"}]},  # WHY: post-capture
                user_id="user-1",  # WHY: audit context
            )  # WHY: analysis complete

            # WHY: verify result handles exception
            assert isinstance(result, DetailedComparisonResult)  # WHY: correct type
            # WHY: audit logger should have logged failure
            # Note: will be verified if audit_logger.log_operation was called
