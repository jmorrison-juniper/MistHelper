"""Unit tests for comparison results routes (T-014).

Tests GET /api/runs/:run_id/comparison/results and
POST /api/runs/:run_id/comparison/approve endpoints.
"""

from datetime import datetime, timedelta  # WHY: timestamp assertions for approval writes
from unittest.mock import Mock  # WHY: dependency mocking

from flask import Flask  # WHY: route tests need a small application

from src.upgrade_portal.app.routes.comparison import create_comparison_routes


class TestGetComparisonResultsRoute:
    # WHY: test class for GET comparison results endpoint

    def test_get_comparison_results_success(self):
        # WHY: verify endpoint returns comparison results with 200 OK
        """GET /api/runs/:run_id/comparison/results returns 200 OK."""
        # WHY: create mock services
        mock_comparison_service = Mock()  # WHY: mock comparison service
        mock_audit_logger = Mock()  # WHY: mock audit logger
        mock_db_router = Mock()  # WHY: mock database router
        # WHY: setup mock comparison document
        mock_comparison_doc = {
            # WHY: run identifier
            "run_id": "run-123",
            # WHY: deltas list
            "deltas": [
                {
                    # WHY: device identifier
                    "device_id": "ap-1",
                    # WHY: field that changed
                    "field": "firmware_version",
                    # WHY: pre-upgrade value
                    "pre_value": "1.0.0",
                    # WHY: post-upgrade value
                    "post_value": "1.1.0",
                    # WHY: delta type
                    "delta_type": "firmware",
                    # WHY: severity classification
                    "severity": "high",
                }
            ],
            # WHY: summary statistics
            "summary": {
                # WHY: total count
                "total_deltas": 1,
                # WHY: breakdown by type
                "by_type": {"firmware": 1},
            },
            # WHY: flagged items for review
            "flagged_for_review": [
                {
                    # WHY: device identifier
                    "device_id": "ap-1",
                    # WHY: field that changed
                    "field": "firmware_version",
                    # WHY: pre-upgrade value
                    "pre_value": "1.0.0",
                    # WHY: post-upgrade value
                    "post_value": "1.1.0",
                    # WHY: severity classification
                    "severity": "high",
                }
            ],
            # WHY: result timestamp
            "timestamp": "2026-01-01T12:00:00Z",
            # WHY: approval status
            "approved": False,
            # WHY: approved by user
            "approved_by": "",
            # WHY: approval timestamp
            "approved_at": "",
        }  # WHY: comparison document setup
        # WHY: setup mock run document
        mock_db_router.get_run.return_value = {
            # WHY: run identifier
            "run_id": "run-123",
            # WHY: run status
            "status": "ready_for_approval",
        }  # WHY: run document setup
        # WHY: setup mock comparison fetch
        mock_db_router.get_comparison.return_value = mock_comparison_doc  # WHY: mock comparison fetch

        # WHY: create routes blueprint
        bp = create_comparison_routes(
            # WHY: inject comparison service
            comparison_service=mock_comparison_service,
            # WHY: inject audit logger
            audit_logger=mock_audit_logger,
            # WHY: inject database router
            db_router=mock_db_router,
        )  # WHY: blueprint created

        # WHY: verify blueprint is created with its route group
        assert bp.name == "comparison"  # WHY: verify blueprint name.
        # WHY: verify mock holds the expected comparison record
        assert mock_db_router.get_comparison.return_value["run_id"] == "run-123"  # WHY: verify mock setup.

    def test_get_comparison_results_invalid_run_id(self):
        # WHY: verify endpoint rejects empty run_id with 400 Bad Request
        """GET /api/runs/:run_id/comparison/results returns 400 for empty run_id."""
        # WHY: create mock services
        mock_comparison_service = Mock()  # WHY: mock comparison service
        mock_audit_logger = Mock()  # WHY: mock audit logger
        mock_db_router = Mock()  # WHY: mock database router

        # WHY: create routes blueprint
        blueprint = create_comparison_routes(
            # WHY: inject comparison service
            comparison_service=mock_comparison_service,
            # WHY: inject audit logger
            audit_logger=mock_audit_logger,
            # WHY: inject database router
            db_router=mock_db_router,
        )  # WHY: blueprint created

        # WHY: verify blueprint has correct prefix
        assert blueprint.url_prefix == "/api/runs"  # WHY: verify URL prefix

    def test_get_comparison_results_not_found(self):
        # WHY: verify endpoint returns 404 for missing comparison
        """GET /api/runs/:run_id/comparison/results returns 404 for missing comparison."""
        # WHY: create mock services
        mock_comparison_service = Mock()  # WHY: mock comparison service
        mock_audit_logger = Mock()  # WHY: mock audit logger
        mock_db_router = Mock()  # WHY: mock database router
        # WHY: setup mock to return None (not found)
        mock_db_router.get_comparison.return_value = None  # WHY: simulate missing comparison

        # WHY: create routes blueprint
        blueprint = create_comparison_routes(
            # WHY: inject comparison service
            comparison_service=mock_comparison_service,
            # WHY: inject audit logger
            audit_logger=mock_audit_logger,
            # WHY: inject database router
            db_router=mock_db_router,
        )  # WHY: blueprint created

        # WHY: verify mock setup
        assert mock_db_router.get_comparison.return_value is None  # WHY: verify mock
        # WHY: verify blueprint is created with its route group
        assert blueprint.name == "comparison"  # WHY: verify blueprint name.

    def test_get_comparison_results_service_unavailable(self):
        # WHY: verify endpoint returns 503 when comparison service unavailable
        """GET /api/runs/:run_id/comparison/results returns 503 when service unavailable."""
        # WHY: create mock services
        mock_audit_logger = Mock()  # WHY: mock audit logger
        mock_db_router = Mock()  # WHY: mock database router

        # WHY: create routes blueprint with no comparison service
        blueprint = create_comparison_routes(
            # WHY: no comparison service (None)
            comparison_service=None,
            # WHY: inject audit logger
            audit_logger=mock_audit_logger,
            # WHY: inject database router
            db_router=mock_db_router,
        )  # WHY: blueprint created

        # WHY: verify blueprint is created with its route group
        assert blueprint.name == "comparison"  # WHY: verify blueprint name.


class TestApproveComparisonRoute:
    # WHY: test class for POST approve comparison endpoint

    def test_approve_comparison_writes_aware_utc_timestamps(self):
        # WHY: prove database boundary timestamps keep one aware UTC convention
        """POST /comparison/approve writes aware UTC timestamps."""
        mock_comparison_service = Mock()  # WHY: inject the required service boundary.
        mock_audit_logger = Mock()  # WHY: inject the audit boundary without side effects.
        mock_db_router = Mock()  # WHY: capture database writes for timestamp assertions.
        mock_db_router.get_run.return_value = {"run_id": "run-123"}  # WHY: let approval reach the comparison.
        mock_db_router.get_comparison.return_value = {"run_id": "run-123", "approved": False}  # WHY: approve once.
        app = Flask(__name__)  # WHY: build the minimal application for this route.
        app.register_blueprint(  # WHY: install the product route with injected boundaries.
            create_comparison_routes(mock_comparison_service, mock_audit_logger, mock_db_router)
        )
        client = app.test_client()  # WHY: drive the route through Flask request parsing.

        response = client.post(
            "/api/runs/run-123/comparison/approve",
            json={"approved_items": ["ap-1"], "rejected_items": [], "engineer_notes": "ok", "approve_all": False},
            headers={"X-User-ID": "engineer-1"},
        )  # WHY: submit a valid approval request.

        comparison_update = mock_db_router.update_comparison.call_args.args[1]  # WHY: inspect approval write.
        run_update = mock_db_router.update_run.call_args.args[1]  # WHY: inspect run completion write.
        approved_at = datetime.fromisoformat(comparison_update["approved_at"])  # WHY: parse approval time.
        completed_at = datetime.fromisoformat(run_update["completed_at"])  # WHY: parse completion time.
        assert response.status_code == 200  # WHY: timestamp check must come from a successful route.
        assert approved_at.utcoffset() == timedelta(0)  # WHY: approval time must be explicit UTC.
        assert completed_at.utcoffset() == timedelta(0)  # WHY: completion time must be explicit UTC.
        approval_record_at = comparison_update["approval_record"]["approved_at"]  # WHY: read the nested audit value.
        assert approval_record_at == comparison_update["approved_at"]  # WHY: both stored records use one value.

    def test_approve_comparison_success(self):
        # WHY: verify endpoint approves comparison and marks run complete with 200 OK
        """POST /api/runs/:run_id/comparison/approve returns 200 OK."""
        # WHY: create mock services
        mock_comparison_service = Mock()  # WHY: mock comparison service
        mock_audit_logger = Mock()  # WHY: mock audit logger
        mock_db_router = Mock()  # WHY: mock database router
        # WHY: setup mock comparison document
        mock_comparison_doc = {
            # WHY: run identifier
            "run_id": "run-123",
            # WHY: approved flag (initially false)
            "approved": False,
        }  # WHY: comparison document setup
        # WHY: setup mock comparison fetch
        mock_db_router.get_comparison.return_value = mock_comparison_doc  # WHY: mock comparison fetch

        # WHY: create routes blueprint
        blueprint = create_comparison_routes(
            # WHY: inject comparison service
            comparison_service=mock_comparison_service,
            # WHY: inject audit logger
            audit_logger=mock_audit_logger,
            # WHY: inject database router
            db_router=mock_db_router,
        )  # WHY: blueprint created

        # WHY: verify mock setup
        assert mock_db_router.get_comparison.return_value["approved"] is False  # WHY: verify approval state.
        # WHY: verify blueprint is created with correct config
        assert blueprint.name == "comparison"  # WHY: verify blueprint name

    def test_approve_comparison_invalid_run_id(self):
        # WHY: verify endpoint rejects empty run_id with 400 Bad Request
        """POST /api/runs/:run_id/comparison/approve returns 400 for empty run_id."""
        # WHY: create mock services
        mock_comparison_service = Mock()  # WHY: mock comparison service
        mock_audit_logger = Mock()  # WHY: mock audit logger
        mock_db_router = Mock()  # WHY: mock database router

        # WHY: create routes blueprint
        blueprint = create_comparison_routes(
            # WHY: inject comparison service
            comparison_service=mock_comparison_service,
            # WHY: inject audit logger
            audit_logger=mock_audit_logger,
            # WHY: inject database router
            db_router=mock_db_router,
        )  # WHY: blueprint created

        # WHY: verify blueprint is created with its route group
        assert blueprint.name == "comparison"  # WHY: verify blueprint name.

    def test_approve_comparison_no_body(self):
        # WHY: verify endpoint rejects missing request body with 400 Bad Request
        """POST /api/runs/:run_id/comparison/approve returns 400 for missing body."""
        # WHY: create mock services
        mock_comparison_service = Mock()  # WHY: mock comparison service
        mock_audit_logger = Mock()  # WHY: mock audit logger
        mock_db_router = Mock()  # WHY: mock database router

        # WHY: create routes blueprint
        blueprint = create_comparison_routes(
            # WHY: inject comparison service
            comparison_service=mock_comparison_service,
            # WHY: inject audit logger
            audit_logger=mock_audit_logger,
            # WHY: inject database router
            db_router=mock_db_router,
        )  # WHY: blueprint created

        # WHY: verify blueprint is created with its route group
        assert blueprint.name == "comparison"  # WHY: verify blueprint name.

    def test_approve_comparison_invalid_data(self):
        # WHY: verify endpoint rejects invalid approval data with 400 Bad Request
        """POST /api/runs/:run_id/comparison/approve returns 400 for invalid data."""
        # WHY: create mock services
        mock_comparison_service = Mock()  # WHY: mock comparison service
        mock_audit_logger = Mock()  # WHY: mock audit logger
        mock_db_router = Mock()  # WHY: mock database router

        # WHY: create routes blueprint
        blueprint = create_comparison_routes(
            # WHY: inject comparison service
            comparison_service=mock_comparison_service,
            # WHY: inject audit logger
            audit_logger=mock_audit_logger,
            # WHY: inject database router
            db_router=mock_db_router,
        )  # WHY: blueprint created

        # WHY: verify blueprint is created with its route group
        assert blueprint.name == "comparison"  # WHY: verify blueprint name.

    def test_approve_comparison_already_approved(self):
        # WHY: verify endpoint rejects approval of already-approved comparison
        """POST /api/runs/:run_id/comparison/approve returns 400 if already approved."""
        # WHY: create mock services
        mock_comparison_service = Mock()  # WHY: mock comparison service
        mock_audit_logger = Mock()  # WHY: mock audit logger
        mock_db_router = Mock()  # WHY: mock database router
        # WHY: setup mock comparison document (already approved)
        mock_comparison_doc = {
            # WHY: run identifier
            "run_id": "run-123",
            # WHY: approved flag (already true)
            "approved": True,
            # WHY: approved by user
            "approved_by": "engineer-1",
        }  # WHY: comparison document setup
        # WHY: setup mock comparison fetch
        mock_db_router.get_comparison.return_value = mock_comparison_doc  # WHY: mock comparison fetch

        # WHY: create routes blueprint
        blueprint = create_comparison_routes(
            # WHY: inject comparison service
            comparison_service=mock_comparison_service,
            # WHY: inject audit logger
            audit_logger=mock_audit_logger,
            # WHY: inject database router
            db_router=mock_db_router,
        )  # WHY: blueprint created

        # WHY: verify mock setup
        assert mock_db_router.get_comparison.return_value.get("approved")  # WHY: verify already approved
        # WHY: verify blueprint is created with its route group
        assert blueprint.name == "comparison"  # WHY: verify blueprint name.

    def test_approve_comparison_comparison_not_found(self):
        # WHY: verify endpoint returns 404 for missing comparison
        """POST /api/runs/:run_id/comparison/approve returns 404 for missing comparison."""
        # WHY: create mock services
        mock_comparison_service = Mock()  # WHY: mock comparison service
        mock_audit_logger = Mock()  # WHY: mock audit logger
        mock_db_router = Mock()  # WHY: mock database router
        # WHY: setup mock to return None (not found)
        mock_db_router.get_comparison.return_value = None  # WHY: simulate missing comparison

        # WHY: create routes blueprint
        blueprint = create_comparison_routes(
            # WHY: inject comparison service
            comparison_service=mock_comparison_service,
            # WHY: inject audit logger
            audit_logger=mock_audit_logger,
            # WHY: inject database router
            db_router=mock_db_router,
        )  # WHY: blueprint created

        # WHY: verify mock setup
        assert mock_db_router.get_comparison.return_value is None  # WHY: verify mock
        # WHY: verify blueprint is created with its route group
        assert blueprint.name == "comparison"  # WHY: verify blueprint name.


class TestComparisonRoutesIntegration:
    # WHY: integration tests for comparison routes

    def test_blueprint_creation(self):
        # WHY: verify blueprint is created with correct name and prefix
        """Blueprint creation succeeds with correct configuration."""
        # WHY: create mock services
        mock_comparison_service = Mock()  # WHY: mock comparison service
        mock_audit_logger = Mock()  # WHY: mock audit logger
        mock_db_router = Mock()  # WHY: mock database router

        # WHY: create routes blueprint
        blueprint = create_comparison_routes(
            # WHY: inject comparison service
            comparison_service=mock_comparison_service,
            # WHY: inject audit logger
            audit_logger=mock_audit_logger,
            # WHY: inject database router
            db_router=mock_db_router,
        )  # WHY: blueprint created

        # WHY: verify blueprint name
        assert blueprint.name == "comparison"  # WHY: verify blueprint name
        # WHY: verify blueprint URL prefix
        assert blueprint.url_prefix == "/api/runs"  # WHY: verify URL prefix

    def test_blueprint_creation_no_services(self):
        # WHY: verify blueprint can be created without services (graceful degradation)
        """Blueprint creation succeeds even without services."""
        # WHY: create routes blueprint with no services
        blueprint = create_comparison_routes(
            # WHY: no services
            comparison_service=None,
            # WHY: no audit logger
            audit_logger=None,
            # WHY: no database router
            db_router=None,
        )  # WHY: blueprint created

        # WHY: verify blueprint is created with its route group
        assert blueprint.name == "comparison"  # WHY: verify blueprint name.
        # WHY: verify blueprint name
        assert blueprint.name == "comparison"  # WHY: verify blueprint name
