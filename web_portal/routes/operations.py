"""Operations routes for the MistHelper web portal.

Handles operation listing, execution, status tracking,
and SSE event streaming for real-time progress updates.
"""

import json
import logging

from flask import (
    Blueprint,
    Response,
    current_app,
    jsonify,
    render_template,
    request,
)

# Module-level logger so every helper identifies its source file in log output.
logger = logging.getLogger(__name__)

operations_bp = Blueprint("operations", __name__)


@operations_bp.route("/operations")
def operations_page():
    """Render the operations menu page."""
    return render_template("operations.html")


@operations_bp.route("/api/operations/list")
def list_operations():
    """Return categorized list of non-destructive operations."""

    menu_actions = current_app.config.get("MENU_ACTIONS", {})
    executor = _get_executor()
    categories = executor.build_category_list(menu_actions)
    total = sum(len(cat["operations"]) for cat in categories)
    return jsonify({"categories": categories, "total_count": total})


@operations_bp.route("/api/operations/run", methods=["POST"])
def run_operation():
    """Start an operation execution in a background thread."""
    data = request.get_json(silent=True) or {}
    menu_number = str(data.get("menu_number", ""))
    parameters = data.get("parameters", {})
    input_answers = parameters.get("input_answers", [])
    if input_answers:
        parameters["input_answers"] = input_answers
    executor = _get_executor()
    result = executor.start_operation(menu_number, parameters)
    if "error" in result:
        # Only a second run of the same operation is a conflict. Every other
        # refusal is a bad request, which covers an unknown menu number and an
        # operation whose safety category keeps it off the portal.
        status = 409 if "already running" in result["error"].lower() else 400
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


@operations_bp.route("/api/operations/stop/<run_id>", methods=["POST"])
def stop_operation(run_id):
    """Request graceful stop of a running operation."""
    executor = _get_executor()
    result = executor.stop_operation(run_id)
    if "error" in result:
        return jsonify(result), 404
    return jsonify(result)


@operations_bp.route("/api/operations/stream")
def operation_stream():
    """SSE endpoint for real-time operation progress events.

    Handles the race condition where fast operations complete before the
    SSE subscriber connects by checking run status on initial connect
    and on each heartbeat timeout.
    """
    run_id = request.args.get("run_id")
    event_bus = current_app.config.get("EVENT_BUS")
    executor = current_app.config.get("OPERATION_EXECUTOR")
    if event_bus is None:
        return jsonify({"error": "Event bus not available"}), 503

    def generate():
        subscriber_id = event_bus.subscribe(run_id)
        try:
            # Check if operation already completed before SSE connected
            replay = _build_replay(executor, run_id)
            if replay:
                yield from replay
                return

            while True:
                event = event_bus.poll(subscriber_id, timeout=5)
                if event is None:
                    # Check if operation completed while waiting
                    replay = _build_replay(executor, run_id)
                    if replay:
                        yield from replay
                        break
                    yield _format_sse("heartbeat", {"timestamp": ""})
                    continue
                yield _format_sse(event["type"], event["data"])
                if event["type"] in ("complete", "error_event"):
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


@operations_bp.route("/api/operations/sites")
def list_sites():
    """Return org sites for site selector dropdowns."""
    apisession = current_app.config.get("APISESSION")
    org_id = current_app.config.get("ORG_ID")
    sites = _fetch_org_sites(apisession, org_id)
    return jsonify({"sites": sites, "total_count": len(sites)})


@operations_bp.route("/api/operations/sites/<site_id>/devices")
def list_site_devices(site_id):
    """Return devices at a site, filtered by type."""
    device_type = request.args.get("type", "all")
    apisession = current_app.config.get("APISESSION")
    devices = _fetch_site_devices(apisession, site_id, device_type)
    return jsonify(
        {
            "devices": devices,
            "total_count": len(devices),
            "site_id": site_id,
        }
    )


@operations_bp.route("/api/operations/sites/<site_id>/clients")
def list_site_clients(site_id):
    """Return clients at a site (wireless + wired merged)."""
    apisession = current_app.config.get("APISESSION")
    clients = _fetch_site_clients(apisession, site_id)
    return jsonify(
        {
            "clients": clients,
            "total_count": len(clients),
            "site_id": site_id,
        }
    )


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


def _build_replay(executor, run_id: str):
    """Build replay events if the operation already finished.

    Returns a list of SSE-formatted strings (log lines + final event)
    if the run is terminal, or None if still in progress.
    """
    if not run_id or not executor:
        return None
    status = executor.get_run_status(run_id)
    if not status or status["status"] not in ("completed", "failed"):
        return None
    events = []
    for entry in status.get("log_messages") or []:
        msg = entry.get("message", entry) if isinstance(entry, dict) else entry
        lvl = entry.get("level", "info") if isinstance(entry, dict) else "info"
        events.append(
            _format_sse(
                "log",
                {
                    "run_id": run_id,
                    "message": msg,
                    "level": lvl,
                },
            )
        )
    for entry in status.get("debug_messages") or []:
        msg = entry.get("message", entry) if isinstance(entry, dict) else entry
        lvl = entry.get("level", "debug") if isinstance(entry, dict) else "debug"
        events.append(
            _format_sse(
                "debug_log",
                {
                    "run_id": run_id,
                    "message": msg,
                    "level": lvl,
                },
            )
        )
    if status["status"] == "completed":
        events.append(
            _format_sse(
                "complete",
                {
                    "run_id": run_id,
                    "status": "completed",
                    "message": "Operation completed",
                    "output_files": status.get("output_files", []),
                    "duration_seconds": _calc_duration(status),
                },
            )
        )
    else:
        events.append(
            _format_sse(
                "error_event",
                {
                    "run_id": run_id,
                    "status": "failed",
                    "message": status.get("error_message", "Operation failed"),
                    "duration_seconds": _calc_duration(status),
                },
            )
        )
    return events


def _calc_duration(status: dict) -> float:
    """Calculate operation duration from started/completed timestamps."""
    started = status.get("started_at") or 0
    completed = status.get("completed_at") or 0
    if started and completed:
        return round(completed - started, 1)
    return 0


def _format_sse(event_type: str, data: dict) -> str:
    """Format a dict as an SSE event string."""
    payload = json.dumps(data)
    return f"event: {event_type}\ndata: {payload}\n\n"


def _fetch_org_sites(apisession, org_id: str) -> list:
    """Fetch organization sites from Mist API."""
    if not apisession or not org_id:
        return []
    try:
        import mistapi

        response = mistapi.api.v1.orgs.sites.listOrgSites(apisession, org_id)
        sites = response.data if hasattr(response, "data") else []
        return [
            {
                "id": site.get("id", ""),
                "name": site.get("name", ""),
                "address": site.get("address", ""),
                "country_code": site.get("country_code", ""),
                "timezone": site.get("timezone", ""),
            }
            for site in sites
        ]
    except Exception:
        # Use logger.exception() so the full traceback appears at ERROR level.
        # Name the org ID so the operator can find the failing request in logs.
        logger.exception("Failed to list sites for org %s", org_id)
        # Return [] because the route call site reads len() directly and cannot
        # handle a non-list.  The log record above makes the failure visible.
        return []


def _fetch_site_devices(apisession, site_id: str, device_type: str) -> list:
    """Fetch devices for a site from Mist API."""
    if not apisession or not site_id:
        return []
    try:
        import mistapi

        kwargs = {"site_id": site_id}
        if device_type and device_type != "all":
            kwargs["type"] = device_type
        else:
            kwargs["type"] = "all"
        response = mistapi.api.v1.sites.devices.listSiteDevices(apisession, **kwargs)
        devices = response.data if hasattr(response, "data") else []
        return [
            {
                "id": device.get("id", ""),
                "mac": device.get("mac", ""),
                "name": device.get("name", ""),
                "model": device.get("model", ""),
                "type": device.get("type", ""),
                "status": device.get("status", ""),
            }
            for device in devices
        ]
    except Exception:
        # Use logger.exception() so the full traceback appears at ERROR level.
        # Name the site ID and device type so the operator can trace the request.
        logger.exception("Failed to list devices for site %s (type=%s)", site_id, device_type)
        # Return [] because the route reads len() directly on this result.
        return []


def _fetch_site_clients(apisession, site_id: str) -> list:
    """Fetch wireless and wired clients for a site."""
    if not apisession or not site_id:
        return []
    clients = []
    try:
        import mistapi

        wireless = _fetch_wireless_clients(mistapi, apisession, site_id)
        wired = _fetch_wired_clients(mistapi, apisession, site_id)
        clients = wireless + wired
    except Exception as client_error:
        logging.debug("Could not fetch site clients: %s", client_error)
    return clients


def _fetch_wireless_clients(mistapi, apisession, site_id: str) -> list:
    """Fetch wireless clients for a site."""
    try:
        response = mistapi.api.v1.sites.clients.searchSiteWirelessClients(apisession, site_id)
        raw = response.data if hasattr(response, "data") else []
        results = raw.get("results", []) if isinstance(raw, dict) else raw
        return [
            {
                "mac": client.get("mac", ""),
                "hostname": client.get("hostname", ""),
                "ip": client.get("ip", ""),
                "type": "wireless",
                "ssid": client.get("ssid", ""),
                "ap_name": (
                    client.get("ap", [None])[0] if isinstance(client.get("ap"), list) else client.get("ap_name", "")
                ),
            }
            for client in results
        ]
    except Exception:
        # Use logger.exception() so the full traceback appears at ERROR level.
        # Name the site ID so the operator can cross-reference with the Mist portal.
        logger.exception("Failed to list wireless clients for site %s", site_id)
        # Return [] because _fetch_site_clients concatenates both lists and
        # cannot handle a non-list return type without being rewritten.
        return []


def _fetch_wired_clients(mistapi, apisession, site_id: str) -> list:
    """Fetch wired clients for a site."""
    try:
        response = mistapi.api.v1.sites.clients.searchSiteWiredClients(apisession, site_id)
        raw = response.data if hasattr(response, "data") else []
        results = raw.get("results", []) if isinstance(raw, dict) else raw
        return [
            {
                "mac": client.get("mac", ""),
                "hostname": client.get("hostname", ""),
                "ip": client.get("ip", ""),
                "type": "wired",
                "ssid": "",
                "ap_name": "",
            }
            for client in results
        ]
    except Exception:
        # Use logger.exception() so the full traceback appears at ERROR level.
        # Name the site ID so the operator knows which site's wired query failed.
        logger.exception("Failed to list wired clients for site %s", site_id)
        # Return [] because _fetch_site_clients concatenates both lists and
        # cannot handle a non-list return type without being rewritten.
        return []
