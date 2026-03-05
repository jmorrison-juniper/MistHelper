"""Operations routes for the MistHelper web portal.

Handles operation listing, execution, status tracking,
and SSE event streaming for real-time progress updates.
"""

import json

from flask import (
    Blueprint,
    Response,
    current_app,
    jsonify,
    render_template,
    request,
)

operations_bp = Blueprint("operations", __name__)


@operations_bp.route("/operations")
def operations_page():
    """Render the operations menu page."""
    return render_template("operations.html")


@operations_bp.route("/api/operations/list")
def list_operations():
    """Return categorized list of non-destructive operations."""
    from web_portal.services.operation import OperationExecutor
    menu_actions = current_app.config.get("MENU_ACTIONS", {})
    executor = _get_executor()
    categories = executor.build_category_list(menu_actions)
    total = sum(len(cat["operations"]) for cat in categories)
    return jsonify({"categories": categories, "total_count": total})


@operations_bp.route("/api/operations/run", methods=["POST"])
def run_operation():
    """Start an operation execution in a background thread."""
    data = request.get_json(silent=True) or {}
    menu_number = data.get("menu_number", "")
    parameters = data.get("parameters", {})
    executor = _get_executor()
    result = executor.start_operation(menu_number, parameters)
    if "error" in result:
        status = 400 if "destructive" in result["error"].lower() else 409
        return jsonify(result), status
    return jsonify(result), 202


@operations_bp.route("/api/operations/status/<run_id>")
def operation_status(run_id):
    """Get current status of a specific operation run."""
    executor = _get_executor()
    status = executor.get_run_status(run_id)
    if status is None:
        return jsonify({"error": "Run not found"}), 404
    return jsonify(status)


@operations_bp.route("/api/operations/active")
def active_operations():
    """List all currently running operations."""
    executor = _get_executor()
    active = executor.get_active_runs()
    return jsonify({"active": active})


@operations_bp.route("/api/operations/stream")
def operation_stream():
    """SSE endpoint for real-time operation progress events."""
    run_id = request.args.get("run_id")
    event_bus = current_app.config.get("EVENT_BUS")
    if event_bus is None:
        return jsonify({"error": "Event bus not available"}), 503

    def generate():
        subscriber_id = event_bus.subscribe(run_id)
        try:
            while True:
                event = event_bus.poll(subscriber_id, timeout=35)
                if event is None:
                    yield _format_sse("heartbeat", {"timestamp": ""})
                    continue
                yield _format_sse(event["type"], event["data"])
                if event["type"] in ("complete", "error"):
                    break
        finally:
            event_bus.unsubscribe(subscriber_id)

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@operations_bp.route("/api/operations/parameters/<menu_number>")
def operation_parameters(menu_number):
    """Get required parameters for an operation."""
    executor = _get_executor()
    params = executor.get_operation_parameters(menu_number)
    if params is None:
        return jsonify({"error": "Operation not found"}), 404
    return jsonify(params)


def _get_executor():
    """Retrieve or create the OperationExecutor singleton."""
    executor = current_app.config.get("OPERATION_EXECUTOR")
    if executor is None:
        from web_portal.services.operation import OperationExecutor
        executor = OperationExecutor(
            menu_actions=current_app.config.get("MENU_ACTIONS", {}),
            apisession=current_app.config.get("APISESSION"),
            org_id=current_app.config.get("ORG_ID"),
            event_bus=current_app.config.get("EVENT_BUS"),
        )
        current_app.config["OPERATION_EXECUTOR"] = executor
    return executor


def _format_sse(event_type: str, data: dict) -> str:
    """Format a dict as an SSE event string."""
    payload = json.dumps(data)
    return f"event: {event_type}\ndata: {payload}\n\n"
