"""Serve explicit tenant-scoped SLE requests through existing portal protections."""

import logging
from collections.abc import Callable

from flask import Response, current_app, render_template, request
from redis.exceptions import RedisError
from requests.exceptions import RequestException

from src.interfaces.wan_performance.collection.live_service import LiveService
from src.interfaces.wan_performance.collection.snapshot_records import SnapshotRecords
from src.interfaces.wan_performance.domain.measurement import MeasurementIdentity
from src.interfaces.wan_performance.integration.history_repository import OperatorDeclarations
from src.interfaces.wan_performance.presentation.inspection.reports import SleReader, SleResult

logger = logging.getLogger(__name__)


class ReplacementPages:
    """Expose independent operator policies through existing tenant and CSRF protections."""

    def __init__(self, service: Callable[[], LiveService]) -> None:
        """Use the current application's existing server-selected service resolver."""
        self.service = service

    def render(self) -> str | Response | tuple[str, int]:
        """Keep metadata operations isolated from network requests and observation writes."""
        identities: tuple[MeasurementIdentity, ...] = ()
        message, error, status = None, None, 200
        try:
            identities, org_id = self._membership()
            result = self._action(identities, org_id)
            if isinstance(result, Response):
                return result
            message = result
        except (ValueError, TypeError, KeyError):
            logger.exception("Rejected independent WAN replacement input.")
            error, status = "Check exact identity, supported JSON fields, UTC bounds, and the confirmation word.", 400
        except (ConnectionError, OSError, RedisError, RequestException):
            logger.exception("Independent WAN replacement cache membership is unavailable.")
            error, status = "Cached tenant membership is unavailable. No replacement action ran.", 503
        return self._page(identities, message, error), status

    def _membership(self) -> tuple[tuple[MeasurementIdentity, ...], str]:
        """Require existing cached identities in the selected tenant before exposing metadata state."""
        service = self.service()
        snapshot = service.store.cached(service.org_id)
        if snapshot is None or snapshot.get("org_id") != service.org_id:
            raise ConnectionError("Selected tenant cache membership is unavailable.")
        records = SnapshotRecords.build(snapshot)
        if any(
            record.provenance != "live" or record.identity.to_dict()["org_id"] != service.org_id for record in records
        ):
            raise ValueError("Cached replacement membership has invalid identity or provenance.")
        return tuple({record.identity.natural_key: record.identity for record in records}.values()), service.org_id

    @staticmethod
    def _action(identities: tuple[MeasurementIdentity, ...], org_id: str) -> str | Response | None:
        """Accept typed metadata confirmation or export existing isolated declarations."""
        store = current_app.extensions.setdefault("wan_operator_declarations", OperatorDeclarations())
        if not isinstance(store, OperatorDeclarations):
            raise TypeError("The operator declaration store has an invalid type.")
        if request.args.get("download") == "declarations":
            return Response(
                store.export(org_id),
                mimetype="application/json",
                headers={"Content-Disposition": 'attachment; filename="wan-operator-declarations.json"'},
            )
        if request.method == "POST":
            return store.accept(
                request.form.get("declaration", "").encode(), identities, request.form.get("confirmation", "")
            )
        return None

    @staticmethod
    def _page(identities: tuple[MeasurementIdentity, ...], message: str | None, error: str | None) -> str:
        """Keep declared metadata and process restart loss visibly separate from source measurements."""
        return render_template("wan_performance/replacements.html", identities=identities, message=message, error=error)


class SlePages:
    """Keep cache-only GET navigation separate from explicit protected SDK reads."""

    def __init__(self, service: Callable[[], LiveService]) -> None:
        """Use the same server-selected session resolver as other live WAN pages."""
        self.service = service

    def render(self) -> tuple[str, int]:
        """Expose raw supported observations and preserve errors and unknown coverage."""
        sites: tuple[str, ...] = ()
        result: SleResult | None = None
        error: str | None = None
        site_id, metric = request.form.get("site_id", ""), request.form.get("metric", "")
        status = 200
        try:
            service = self.service()
            sites = SleReader.sites(service)
            if request.method == "POST":
                result = SleReader.read(service, site_id, metric)
        except (ConnectionError, OSError, RedisError, RequestException, ValueError, TypeError):
            logger.exception("WAN SLE inspection failed.")
            error, status = (
                "Check cached site membership, enabled metric identifiers, shared admission, and the API response.",
                503,
            )
        return self._page(sites, result, (site_id, metric), error), status

    @staticmethod
    def _page(sites: tuple[str, ...], result: SleResult | None, selected: tuple[str, str], error: str | None) -> str:
        """Render only validated source fields without score or duration conversions."""
        return render_template(
            "wan_performance/sle.html", sites=sites, result=result, site_id=selected[0], metric=selected[1], error=error
        )
