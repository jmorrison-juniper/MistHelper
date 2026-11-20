"""Serve explicit tenant-scoped SLE requests through existing portal protections."""

import logging
import sqlite3
from collections.abc import Callable

from arango.exceptions import ArangoError
from flask import Response, abort, current_app, render_template, request
from redis.exceptions import RedisError
from requests.exceptions import RequestException

from src.interfaces.wan_performance.collection.live_service import LiveService
from src.interfaces.wan_performance.collection.snapshot_records import SnapshotRecords
from src.interfaces.wan_performance.domain.measurement import MeasurementIdentity
from src.interfaces.wan_performance.integration.history_repository import (
    ArchiveImporter,
    OperatorDeclarations,
    SyntheticArchiveStore,
)
from src.interfaces.wan_performance.presentation.inspection.reports import SleReader, SleResult

logger = logging.getLogger(__name__)


class ReplacementAdmission:
    """Bound replacement bodies before CSRF reads fields or spools files."""

    BODY_BYTES = 8 * 1024 * 1024 + 65536
    FIELD_BYTES = 128 * 1024
    PARTS = 5

    @staticmethod
    def apply(endpoint: str | None, _values: dict[str, object] | None) -> None:
        """Use URL preprocessing to protect only replacement POST requests."""
        if endpoint is None or not endpoint.endswith(".replacements") or request.method != "POST":
            return
        logger.info("Checking replacement request admission.")
        existing = request.max_content_length
        bound = ReplacementAdmission.BODY_BYTES if existing is None else min(existing, ReplacementAdmission.BODY_BYTES)
        if request.content_length is None:
            logger.warning("Rejected replacement request with unknown content length.")
            abort(411, description="A replacement upload requires a known content length.")
        if request.content_length > bound:
            logger.warning("Rejected replacement request exceeding %d bytes.", bound)
            abort(413, description="The replacement request exceeds the body limit.")
        request.max_content_length = bound
        memory, parts = request.max_form_memory_size, request.max_form_parts
        request.max_form_memory_size = (
            ReplacementAdmission.FIELD_BYTES if memory is None else min(memory, ReplacementAdmission.FIELD_BYTES)
        )
        request.max_form_parts = ReplacementAdmission.PARTS if parts is None else min(parts, ReplacementAdmission.PARTS)
        logger.debug("Admitted replacement body of %d bytes with bounded multipart parsing.", request.content_length)


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
        except (ConnectionError, OSError, RedisError, RequestException, sqlite3.Error, ArangoError):
            logger.exception("Independent WAN replacement storage or membership is unavailable.")
            error, status = (
                "Replacement storage or membership failed. Check the action logs. Commit status may be unknown.",
                503,
            )
        return (
            render_template("wan_performance/replacements.html", identities=identities, message=message, error=error),
            status,
        )

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

    def _action(self, identities: tuple[MeasurementIdentity, ...], org_id: str) -> str | Response | None:
        """Accept typed metadata confirmation or export existing isolated declarations."""
        store = current_app.extensions.setdefault("wan_operator_declarations", OperatorDeclarations())
        synthetic = current_app.extensions.setdefault("wan_synthetic_archives", SyntheticArchiveStore())
        if not isinstance(store, OperatorDeclarations):
            raise TypeError("The operator declaration store has an invalid type.")
        if not isinstance(synthetic, SyntheticArchiveStore):
            raise TypeError("The synthetic archive store has an invalid type.")
        if request.method == "POST" and request.form.get("action", "declaration") not in {"declaration", "archive"}:
            raise ValueError("Select a supported declaration or archive action.")
        if request.args.get("download") == "declarations":
            return Response(
                store.export(org_id),
                mimetype="application/json",
                headers={"Content-Disposition": 'attachment; filename="wan-operator-declarations.json"'},
            )
        if request.args.get("download") == "synthetic":
            return Response(
                synthetic.export(org_id, request.args.get("digest", "")),
                mimetype="application/json",
                headers={"Content-Disposition": 'attachment; filename="wan-synthetic-archive.json"'},
            )
        if request.method == "POST" and request.form.get("action") == "archive":
            return self._archive(identities, synthetic)
        if request.method == "POST":
            return store.accept(
                request.form.get("declaration", "").encode(), identities, request.form.get("confirmation", "")
            )
        return None

    def _archive(self, identities: tuple[MeasurementIdentity, ...], synthetic: SyntheticArchiveStore) -> str:
        """Read one bounded upload and keep synthetic state separate from reviewed live append admission."""
        upload = request.files.get("archive")
        if upload is None:
            raise ValueError("Select one UTF-8 projection archive.")
        payload = upload.stream.read(8 * 1024 * 1024 + 1)
        confirmation = request.form.get("archive_confirmation", "")
        if confirmation == "IMPORT_SYNTHETIC":
            digest = synthetic.accept(payload, identities, confirmation)
            return f"Synthetic archive retained in process state. Export digest: {digest}."
        if confirmation != "IMPORT":
            raise ValueError("Type IMPORT_SYNTHETIC or IMPORT for the matching archive provenance.")
        importer = ArchiveImporter(lambda: self.service().history, current_app.config.get("WAN_ARCHIVE_REVIEWS", {}))
        return importer.apply(payload, identities, confirmation)


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
