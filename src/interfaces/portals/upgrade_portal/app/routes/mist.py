"""Mist API routes for listing sites and devices.

Implements GET /api/sites and GET /api/sites/:site_id/devices.
"""

import structlog  # WHY: structured logging
from flask import Blueprint, jsonify, request  # WHY: Flask routing and request handling

logger = structlog.get_logger(__name__)  # WHY: module-scoped logger


def create_mist_routes(mist_client=None):
    """Create Flask blueprint for Mist API routes.

    Args:
        mist_client: MistAPIClient instance.

    Returns:
        Flask blueprint for registration.

    WHY: factory function for route creation with dependency injection.
    """
    # WHY: create blueprint
    mist_bp = Blueprint("mist", __name__, url_prefix="/api")  # WHY: blueprint with API prefix

    @mist_bp.route("/sites", methods=["GET"])  # WHY: list sites route
    def get_sites():
        """Get list of sites for current organization.

        Query parameters:
            - org_id: Organization ID (required)

        Returns:
            200 OK with sites list; 400 Bad Request if org_id missing.

        WHY: endpoint for T-003 site dropdown selector.
        """
        # WHY: log request
        logger.info("get_sites_request")  # WHY: request event
        try:
            # WHY: extract org_id from query
            org_id = request.args.get("org_id")  # WHY: query parameter
            if not org_id:  # WHY: validate required parameter
                # WHY: bad request
                logger.warning("get_sites_missing_org_id")  # WHY: validation failure
                return jsonify({"error": "org_id is required"}), 400  # WHY: return error

            # WHY: check if mist client available
            if not mist_client:  # WHY: no client
                # WHY: service unavailable
                logger.error("mist_client_unavailable_get_sites")  # WHY: service error
                return jsonify({"error": "Mist API client not available"}), 503  # WHY: return error

            # WHY: call mist client to list sites
            logger.info("mist_list_sites_api_call", org_id=org_id)  # WHY: pre-call log
            sites = mist_client.list_sites(org_id)  # WHY: API call
            # WHY: check if call succeeded
            if sites is None:  # WHY: if call failed
                # WHY: API error
                logger.error("mist_list_sites_api_failed", org_id=org_id)  # WHY: API failure log
                return jsonify({"error": "Failed to retrieve sites from Mist"}), 502  # WHY: return error

            # WHY: log success
            logger.info("get_sites_success", org_id=org_id, count=len(sites))  # WHY: post-call log
            # WHY: return sites
            return jsonify({"sites": sites}), 200  # WHY: return result

        except Exception as e:
            # WHY: catch unexpected exceptions
            logger.error("get_sites_exception", error=str(e))  # WHY: exception log
            return jsonify({"error": "Internal server error"}), 500  # WHY: return error

    @mist_bp.route("/sites/<site_id>/devices", methods=["GET"])  # WHY: list devices route
    def get_site_devices(site_id):
        """Get list of devices for a site.

        Path parameters:
            - site_id: Site ID.

        Query parameters:
            - type: Device type filter ('all', 'ap', 'switch', 'gateway', default: 'all')

        Returns:
            200 OK with devices list; 400 Bad Request if site_id invalid.

        WHY: endpoint for T-003 device multi-select.
        """
        # WHY: log request
        logger.info("get_site_devices_request", site_id=site_id)  # WHY: request event
        try:
            # WHY: validate site_id
            if not site_id or not isinstance(site_id, str) or len(site_id) == 0:  # WHY: check format
                # WHY: bad request
                logger.warning("get_site_devices_invalid_site_id", site_id=site_id)  # WHY: validation failure
                return jsonify({"error": "site_id is required and must be non-empty"}), 400  # WHY: return error

            # WHY: extract device type filter
            device_type = request.args.get("type", "all")  # WHY: query parameter with default
            # WHY: validate device type
            valid_types = ["all", "ap", "switch", "gateway"]  # WHY: allowed types
            if device_type not in valid_types:  # WHY: check valid
                # WHY: bad request
                logger.warning("get_site_devices_invalid_type", type=device_type)  # WHY: validation failure
                return jsonify({"error": f"type must be one of {valid_types}"}), 400  # WHY: return error

            # WHY: check if mist client available
            if not mist_client:  # WHY: no client
                # WHY: service unavailable
                logger.error("mist_client_unavailable_get_devices")  # WHY: service error
                return jsonify({"error": "Mist API client not available"}), 503  # WHY: return error

            # WHY: call mist client to list devices
            logger.info("mist_list_devices_api_call", site_id=site_id, type=device_type)  # WHY: pre-call log
            devices = mist_client.list_site_devices(site_id, device_type)  # WHY: API call
            # WHY: check if call succeeded
            if devices is None:  # WHY: if call failed
                # WHY: API error
                logger.error("mist_list_devices_api_failed", site_id=site_id)  # WHY: API failure log
                return jsonify({"error": "Failed to retrieve devices from Mist"}), 502  # WHY: return error

            # WHY: log success
            logger.info("get_site_devices_success", site_id=site_id, count=len(devices))  # WHY: post-call log
            # WHY: return devices
            return jsonify({"devices": devices}), 200  # WHY: return result

        except Exception as e:
            # WHY: catch unexpected exceptions
            logger.error("get_site_devices_exception", site_id=site_id, error=str(e))  # WHY: exception log
            return jsonify({"error": "Internal server error"}), 500  # WHY: return error

    return mist_bp  # WHY: return blueprint
