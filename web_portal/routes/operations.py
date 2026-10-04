"""Operations routes for the MistHelper web portal.

Handles operation listing, execution, status tracking,
and SSE event streaming for real-time progress updates.
"""

import json
import logging
import os
import time

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

# Seconds one event stream may hold a worker thread before it closes itself.
# Gunicorn runs a fixed thread pool, and one open stream holds one thread for
# its whole life. Without this cap, a few forgotten browser tabs take every
# thread and the portal stops answering. The browser EventSource client
# reconnects on its own, so a closed stream costs the operator nothing.
DEFAULT_STREAM_MAX_SECONDS = 300.0

# Seconds the poll waits for one event before it writes a heartbeat.
STREAM_POLL_TIMEOUT_SECONDS = 5


def _stream_max_seconds() -> float:
    """Read the stream lifetime cap from the environment."""
    raw = os.environ.get("PORTAL_STREAM_MAX_SECONDS")  # Operator override for a slow site.
    if raw is None:
        return DEFAULT_STREAM_MAX_SECONDS  # No override, so use the shipped default.
    try:
        parsed = float(raw)  # Accept a fractional value, so a test can use a short cap.
    except ValueError:
        # Name the bad value, so the operator can correct the environment file.
        logger.warning("PORTAL_STREAM_MAX_SECONDS is not a number: %r. Using %.0fs.", raw, DEFAULT_STREAM_MAX_SECONDS)
        return DEFAULT_STREAM_MAX_SECONDS
    if parsed <= 0:
        # A zero or negative cap would close every stream at once, so refuse it.
        logger.warning("PORTAL_STREAM_MAX_SECONDS must be above zero. Using %.0fs.", DEFAULT_STREAM_MAX_SECONDS)
        return DEFAULT_STREAM_MAX_SECONDS
    return parsed


# Reasons a pick list came back empty. An empty control with no explanation
# made an operator think the portal had stalled, so every empty list now
# carries one of these. Issue #3163.
NO_SESSION_REASON = "The portal holds no Mist API session. Check the API token in the environment file."
NO_ORG_REASON = "The portal holds no organization identifier. Set MIST_ORG_ID in the environment file."
NO_SITE_REASON = "No site was chosen, so the portal cannot list this data."
NO_ROWS_REASON = "The Mist API answered with no rows for this request."
API_ERROR_REASON = "The Mist API request failed with {error}. Read the portal error log for the full report."
ALL_SITES_EMPTY_REASON = "Every site holds no hardware. Add show_empty=1 to list them."

# WHY: the request may ask for the hidden sites. These are the accepted raw values.
SHOW_EMPTY_VALUES = ("1", "true", "yes", "on")

# WHY: the site statistics record names the device count in these fields.
DEVICE_COUNT_FIELD = "num_devices"
DEVICE_COUNT_PARTS = ("num_ap", "num_switch", "num_gateway")


class PickList(list):
    """A list of pick list rows that also knows why it holds no row.

    The selector endpoints used to answer with an empty list and no reason.
    An operator then read a blank control as a stalled portal. This type
    stays a plain list for every reader that counts rows or sorts them, and
    it carries the reason for the route that must explain the blank control.
    Issue #3163.
    """

    def __init__(self, items=(), reason: str | None = None) -> None:
        """Store the rows and the reason the list may be empty."""
        super().__init__(items)  # Keep list behavior, so every existing caller still works.
        self.reason = reason  # Hold the explanation for the route that renders the control.


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

    The stream closes itself after a fixed time. One stream holds one worker
    thread, so an unbounded stream lets a few browser tabs take the whole
    pool. The browser reconnects on its own after the close.
    """
    run_id = request.args.get("run_id")
    event_bus = current_app.config.get("EVENT_BUS")
    executor = _get_executor()  # Build the executor if no earlier request built it, matching the other routes.
    if event_bus is None:
        return jsonify({"error": "Event bus not available"}), 503
    if executor.get_run_status(run_id) is None:
        # An unknown run never sends an event, so the stream would heartbeat
        # forever and hold a thread for nothing. Refuse it instead.
        logger.warning("Refused an event stream for the unknown run %r.", run_id)
        return jsonify({"error": "Unknown run_id"}), 404

    max_seconds = _stream_max_seconds()  # Read the cap once, so the whole stream uses one value.

    def generate():
        subscriber_id = event_bus.subscribe(run_id)
        deadline = time.monotonic() + max_seconds  # Fix the close time before the first poll.
        try:
            # Check if operation already completed before SSE connected
            replay = _build_replay(executor, run_id)
            if replay:
                yield from replay
                return

            while True:
                if time.monotonic() >= deadline:
                    # Report the close, so a reader can tell it apart from a crash.
                    logger.info("Closing the event stream for run %s after %.0fs.", run_id, max_seconds)
                    yield _format_sse("stream_timeout", {"run_id": run_id})
                    break
                event = event_bus.poll(subscriber_id, timeout=STREAM_POLL_TIMEOUT_SECONDS)
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
    apisession = current_app.config.get("APISESSION")  # The portal holds one Mist session.
    org_id = current_app.config.get("ORG_ID")  # The portal serves one organization.
    show_empty = _read_show_empty(request.args.get("show_empty"))  # Issue #3840: the operator can ask for every site.
    logger.info("Listing sites for org %s with show_empty=%s", org_id, show_empty)  # Log before the read.
    sites = _fetch_org_sites(apisession, org_id, show_empty)  # Read the sites, then drop the empty ones.
    payload = _pick_list_payload("sites", sites)  # Build the standard pick list body.
    hidden = getattr(sites, "empty_hidden", 0)  # Read the count of the sites that the filter removed.
    payload["empty_sites_hidden"] = hidden  # State the hidden count, so the page can explain it.
    logger.debug("Listed %d sites and hid %d", len(sites), payload["empty_sites_hidden"])  # Log after the read.
    return jsonify(payload)


@operations_bp.route("/api/operations/sites/<site_id>/devices")
def list_site_devices(site_id):
    """Return devices at a site, filtered by type."""
    device_type = request.args.get("type", "all")
    apisession = current_app.config.get("APISESSION")
    devices = _fetch_site_devices(apisession, site_id, device_type)
    payload = _pick_list_payload("devices", devices)
    payload["site_id"] = site_id  # Echo the site, so the page can prove which request answered.
    return jsonify(payload)


@operations_bp.route("/api/operations/sites/<site_id>/clients")
def list_site_clients(site_id):
    """Return clients at a site (wireless + wired merged)."""
    apisession = current_app.config.get("APISESSION")
    clients = _fetch_site_clients(apisession, site_id)
    payload = _pick_list_payload("clients", clients)
    payload["site_id"] = site_id  # Echo the site, so the page can prove which request answered.
    return jsonify(payload)


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
                    "message": status.get("completion_message") or "Operation completed",  # Preserve no-output reason.
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


def display_label(entry: dict, fields: tuple[str, ...]) -> str:
    """Return the text the dropdown shows for one entry.

    Why:
        A sort must order the list by the text the operator reads. Sorting by a
        hidden field would leave the visible list in no order at all, which is
        the defect this helper repairs.

    Args:
        entry: One dropdown row.
        fields: The label fields, in the order the page prefers them.

    Returns:
        The first field that holds text, or an empty string.
    """
    for field in fields:  # The page shows the first of these that carries text.
        value = str(entry.get(field) or "").strip()
        if value:
            return value
    return ""


def sort_by_name(entries: list, fields: tuple[str, ...] = ("name",)) -> list:
    """Return dropdown entries in the order of the label the page shows.

    Why:
        The Mist API returns a site, a device, and a client in its own order,
        and that order is neither the name order nor stable between calls. An
        engineer who looks for one site then reads the whole list. Issue #3083
        records the defect.

    Warning: the label fields must match the fields that
    ``web_portal/static/js/operations.js`` renders. A client carries its name in
    ``hostname`` and not in ``name``, so a sort that read ``name`` alone would
    treat every client as unnamed and change nothing.

    Rules:
        The order ignores letter case, so ``alpha`` and ``Alpha`` sit together.
        An entry with no label sorts last, because a blank row must never hide a
        named one at the top of the list. An unlabelled entry stays in the list,
        because it carries an identifier that an operator may still need.

    Args:
        entries: The dropdown rows.
        fields: The label fields, in the order the page prefers them.

    Returns:
        A new list in label order.
    """
    return sorted(
        entries,
        key=lambda entry: (not display_label(entry, fields), display_label(entry, fields).casefold()),
    )


# WHY: the page renders `device.name || device.mac`, so the sort reads both.
DEVICE_LABEL_FIELDS = ("name", "mac")

# WHY: the page renders the client hostname and falls back to the MAC address.
CLIENT_LABEL_FIELDS = ("hostname", "mac")


def _pick_list_payload(key: str, items: PickList) -> dict:
    """Return the JSON body for one pick list, naming the reason it is empty."""
    payload = {key: list(items), "total_count": len(items)}  # The page reads the count to size the control.
    if not items:
        # An empty control with no reason made an operator think the portal
        # had stalled. Name the cause, so the page can show it. Issue #3163.
        payload["reason"] = items.reason or NO_ROWS_REASON
    return payload


def _read_show_empty(value: str | None) -> bool:
    """Return True when the request asks for the sites that hold no hardware."""
    if value is None:  # The argument is absent, so the portal hides the empty sites.
        return False
    return value.strip().casefold() in SHOW_EMPTY_VALUES  # Accept the documented raw values.


def _read_site_device_count(record: dict) -> int:
    """Return the device count that one site statistics record names."""
    total = record.get(DEVICE_COUNT_FIELD)  # The record usually names one total.
    if isinstance(total, int):  # Trust the total when the record supplies it.
        return total
    parts = [record.get(name) for name in DEVICE_COUNT_PARTS]  # Fall back to the per-type counts.
    return sum(part for part in parts if isinstance(part, int))  # Ignore an absent or odd part.


def _fetch_org_site_counts(apisession, org_id: str) -> dict[str, int]:
    """Return a site identifier to device count map, or an empty map on any fault."""
    try:
        import mistapi  # Import here, so the module loads without the SDK.

        logger.info("Reading site statistics for org %s", org_id)  # Log before the read.
        response = mistapi.api.v1.orgs.stats.listOrgSiteStats(apisession, org_id)  # Read the counts.
        records = response.data if hasattr(response, "data") else []  # Read the rows defensively.
    except Exception as error:  # A count fault must not hide a site.
        logger.warning("Could not read site statistics for org %s: %s", org_id, type(error).__name__)
        return {}  # An empty map disables the filter, so no site disappears without proof.
    counts = {str(row.get("id", "")): _read_site_device_count(row) for row in records if row.get("id")}
    logger.debug("Read device counts for %d sites", len(counts))  # Log after the read.
    return counts


def _build_site_row(site: dict) -> dict:
    """Return the five fields that the site picker shows for one site."""
    return {
        "id": site.get("id", ""),  # The picker posts this identifier back to the portal.
        "name": site.get("name", ""),  # The operator reads the name, not the identifier.
        "address": site.get("address", ""),  # The address separates two sites with one name.
        "country_code": site.get("country_code", ""),  # The country helps a global operator.
        "timezone": site.get("timezone", ""),  # The time zone explains an odd event time.
    }


def _drop_empty_sites(rows: list[dict], counts: dict[str, int]) -> tuple[list[dict], int]:
    """Return the sites that hold hardware, plus the count of the hidden sites."""
    if not counts:  # No count was observed, so a zero is not proof that a site is empty.
        return rows, 0
    kept = [row for row in rows if counts.get(row.get("id", ""), 0) > 0]  # Keep a proven non-zero site.
    return kept, len(rows) - len(kept)  # Name the hidden count, so the page can explain it.


def _fetch_org_sites(apisession, org_id: str, show_empty: bool = False) -> PickList:
    """Fetch organization sites from Mist API, hiding the sites that hold no hardware."""
    if not apisession:
        # Name the missing piece, so an operator does not read an empty list as a stall.
        logger.warning("Cannot list the sites, because the portal holds no Mist API session.")
        return PickList(reason=NO_SESSION_REASON)
    if not org_id:
        logger.warning("Cannot list the sites, because the portal holds no organization identifier.")
        return PickList(reason=NO_ORG_REASON)
    try:
        import mistapi

        response = mistapi.api.v1.orgs.sites.listOrgSites(apisession, org_id)
        sites = response.data if hasattr(response, "data") else []
        rows = sort_by_name([_build_site_row(site) for site in sites])  # Issue #3083: list by name.
        if show_empty:  # The operator asked for every site, so keep them all.
            return PickList(rows)
        counts = _fetch_org_site_counts(apisession, org_id)  # Read the device count for each site.
        kept, hidden = _drop_empty_sites(rows, counts)  # Issue #3840: hide a proven empty site.
        picks = PickList(kept, reason=ALL_SITES_EMPTY_REASON if hidden and not kept else None)
        picks.empty_hidden = hidden  # Carry the hidden count, so the route can state it.
        return picks
    except Exception as error:  # Keep the site selector usable when the Mist API request fails.
        # Use logger.exception() so the full traceback appears at ERROR level.
        # Name the org ID so the operator can find the failing request in logs.
        logger.exception(
            "Failed to list sites for org %s with %s: %s", org_id, type(error).__name__, error
        )  # Log the exception class and text for issue triage.
        # Return an empty list because the route reads len() directly and cannot
        # handle a non-list. The log record above makes the failure visible.
        return PickList(reason=API_ERROR_REASON.format(error=type(error).__name__))


def _fetch_site_devices(apisession, site_id: str, device_type: str) -> PickList:
    """Fetch devices for a site from Mist API."""
    if not apisession:
        # Name the missing piece, so an operator does not read an empty list as a stall.
        logger.warning("Cannot list the devices, because the portal holds no Mist API session.")
        return PickList(reason=NO_SESSION_REASON)
    if not site_id:
        logger.warning("Cannot list the devices, because no site was chosen.")
        return PickList(reason=NO_SITE_REASON)
    try:
        import mistapi

        kwargs = {"site_id": site_id}
        if device_type and device_type != "all":
            kwargs["type"] = device_type
        else:
            kwargs["type"] = "all"
        response = mistapi.api.v1.sites.devices.listSiteDevices(apisession, **kwargs)
        devices = response.data if hasattr(response, "data") else []
        return PickList(
            sort_by_name(
                [
                    {
                        "id": device.get("id", ""),
                        "mac": device.get("mac", ""),
                        "name": device.get("name", ""),
                        "model": device.get("model", ""),
                        "type": device.get("type", ""),
                        "status": device.get("status", ""),
                    }
                    for device in devices
                ],
                DEVICE_LABEL_FIELDS,
            )
        )  # Issue #3083: the dropdown lists the devices by the label it shows.
    except Exception as error:  # Keep the device selector usable when the Mist API request fails.
        # Use logger.exception() so the full traceback appears at ERROR level.
        # Name the site ID and device type so the operator can trace the request.
        logger.exception(
            "Failed to list devices for site %s type %s with %s: %s", site_id, device_type, type(error).__name__, error
        )  # Log the exception class and text for issue triage.
        # Return an empty list because the route reads len() directly on this result.
        return PickList(reason=API_ERROR_REASON.format(error=type(error).__name__))


def _fetch_site_clients(apisession, site_id: str) -> PickList:
    """Fetch wireless and wired clients for a site."""
    if not apisession:
        # Name the missing piece, so an operator does not read an empty list as a stall.
        logger.warning("Cannot list the clients, because the portal holds no Mist API session.")
        return PickList(reason=NO_SESSION_REASON)
    if not site_id:
        logger.warning("Cannot list the clients, because no site was chosen.")
        return PickList(reason=NO_SITE_REASON)
    try:
        import mistapi

        wireless = _fetch_wireless_clients(mistapi, apisession, site_id)
        wired = _fetch_wired_clients(mistapi, apisession, site_id)
        # Issue #3083: a plain concatenation put every wireless client before
        # every wired one, whatever its name. One sort interleaves both types.
        # A client carries its name in `hostname`, so the sort must read that.
        merged = sort_by_name(list(wireless) + list(wired), CLIENT_LABEL_FIELDS)
        if merged:
            return PickList(merged)  # At least one source answered, so the control has rows.
        # Both sources came back empty. Issue #3163: report a failed source as a
        # failure, never as "no rows". A caught failure in both helpers used to
        # reach the operator as an empty control with a misleading reason.
        failure = wireless.reason or wired.reason
        return PickList(reason=failure) if failure else PickList()
    except Exception as client_error:
        # This was a debug record on the root logger, so an operator never saw
        # the cause of an empty client list. Report it at ERROR. Issue #3163.
        logger.exception(
            "Failed to list clients for site %s with %s: %s", site_id, type(client_error).__name__, client_error
        )
        return PickList(reason=API_ERROR_REASON.format(error=type(client_error).__name__))


def _fetch_wireless_clients(mistapi, apisession, site_id: str) -> PickList:
    """Fetch wireless clients for a site."""
    try:
        response = mistapi.api.v1.sites.clients.searchSiteWirelessClients(apisession, site_id)
        raw = response.data if hasattr(response, "data") else []
        results = raw.get("results", []) if isinstance(raw, dict) else raw
        return PickList(
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
        )
    except Exception as error:  # Keep the client list usable when the wireless query fails.
        # Use logger.exception() so the full traceback appears at ERROR level.
        # Name the site ID so the operator can cross-reference with the Mist portal.
        logger.exception(
            "Failed to list wireless clients for site %s with %s: %s", site_id, type(error).__name__, error
        )  # Log the exception class and text for issue triage.
        # Carry the reason, so the caller can tell a failure from a true zero count.
        return PickList(reason=API_ERROR_REASON.format(error=type(error).__name__))


def _fetch_wired_clients(mistapi, apisession, site_id: str) -> PickList:
    """Fetch wired clients for a site."""
    try:
        # Issue #3233: this call named `mistapi.api.v1.sites.clients`, which holds
        # no wired search in mistapi 0.64.0. The call raised AttributeError, so
        # every client pick list lost its wired half, and a site with only wired
        # clients offered an empty list. The function lives in `wired_clients`.
        response = mistapi.api.v1.sites.wired_clients.searchSiteWiredClients(apisession, site_id)
        raw = response.data if hasattr(response, "data") else []
        results = raw.get("results", []) if isinstance(raw, dict) else raw
        return PickList(
            {
                "mac": client.get("mac", ""),
                "hostname": client.get("hostname", ""),
                "ip": client.get("ip", ""),
                "type": "wired",
                "ssid": "",
                "ap_name": "",
            }
            for client in results
        )
    except Exception as error:  # Keep the client list usable when the wired query fails.
        # Use logger.exception() so the full traceback appears at ERROR level.
        # Name the site ID so the operator knows which site's wired query failed.
        logger.exception(
            "Failed to list wired clients for site %s with %s: %s", site_id, type(error).__name__, error
        )  # Log the exception class and text for issue triage.
        # Carry the reason, so the caller can tell a failure from a true zero count.
        return PickList(reason=API_ERROR_REASON.format(error=type(error).__name__))
