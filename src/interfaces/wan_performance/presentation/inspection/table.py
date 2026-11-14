"""Filter authorized cached identities without changing history selection or metric meaning."""

import csv
import io
import logging
from collections.abc import Mapping
from dataclasses import dataclass

from flask import Response, abort, request, url_for

from src.interfaces.wan_performance.domain.measurement import HourlyMeasurement

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TableOptions:
    """Keep independently defined lexical ordering and bounded page controls explicit."""

    query: str = ""
    sort: str = "site_id"
    descending: bool = False
    page: int = 1

    @classmethod
    def parse(cls, arguments: Mapping[str, str]) -> TableOptions:
        """Reject invalid table controls instead of changing their meaning silently."""
        query, sort = arguments.get("q", ""), arguments.get("sort", "site_id")
        direction, page = arguments.get("direction", "asc"), arguments.get("page", "1")
        if len(query) > 128 or any(not character.isprintable() for character in query):
            raise ValueError("The identity filter must use at most 128 printable characters.")
        if sort not in {"site_id", "gateway_id", "port_name", "peer_mac"} or direction not in {"asc", "desc"}:
            raise ValueError("Use a displayed identity column and an ascending or descending lexical order.")
        if not page.isascii() or not page.isdecimal() or len(page) > 6 or int(page) < 1:
            raise ValueError("The table page must be an integer from 1 through 999999.")
        return cls(query, sort, direction == "desc", int(page))

    def url(self, **changes: str | int) -> str:
        """Preserve the complete route and query scope when changing table controls."""
        allowed = {"gateway_id", "site_id", "path_key", "q", "sort", "direction", "page", "download"}
        arguments = {name: value for name, value in request.args.items() if name in allowed}
        arguments.update(request.view_args or {})
        arguments.update({name: str(value) for name, value in changes.items()})
        return url_for(request.endpoint or "wan_performance.live.overview", _external=False, **arguments)

    @classmethod
    def from_request(cls) -> TableOptions:
        """Report invalid controls as client errors before reading any cache or history."""
        try:
            return cls.parse(request.args)
        except ValueError as failure:
            logger.error("Rejected WAN table controls: %s", failure)
            abort(400, description=str(failure))


@dataclass(frozen=True)
class RecordTable:
    """Keep the full scoped selection separate from a ten-row display page."""

    options: TableOptions
    matching: tuple[HourlyMeasurement, ...]

    @classmethod
    def build(cls, records: tuple[HourlyMeasurement, ...], options: TableOptions) -> RecordTable:
        """Filter identity text and sort with the complete identity as a tie key."""
        logger.info("Filter and order %s authorized cached WAN observations.", len(records))
        matching = tuple(record for record in records if cls.matches(record, options.query))
        ordered = tuple(
            sorted(
                matching,
                key=lambda record: (
                    record.identity.to_dict().get(options.sort, "").casefold(),
                    record.identity.natural_key,
                ),
                reverse=options.descending,
            )
        )
        logger.debug("Selected %s matching cached WAN observations.", len(ordered))
        return cls(options, ordered)

    @staticmethod
    def matches(record: HourlyMeasurement, query: str) -> bool:
        """Search displayed identifiers and the path key without interpreting metric values."""
        values = record.identity.to_dict()
        fields = ("site_id", "gateway_id", "port_name", "peer_mac", "tunnel_identity")
        return any(query.casefold() in values.get(field, "").casefold() for field in fields)

    @property
    def rows(self) -> tuple[HourlyMeasurement, ...]:
        """Return at most ten records without changing the underlying selection."""
        start = (self.options.page - 1) * 10
        return self.matching[start : start + 10]

    @property
    def pages(self) -> int:
        """Report one empty page when the filter has no matches."""
        return max(1, (len(self.matching) + 9) // 10)

    def export(self, error: str | None) -> Response | None:
        """Reject invalid pages and export only a successfully read cached selection."""
        if self.options.page > self.pages:
            abort(400, description="The table page exceeds the matching cached observations.")
        if request.args.get("download") != "csv":
            return None
        if error:
            abort(503, description="The cached export is unavailable.")
        return CachedCsv.response(self.matching)


class CachedCsv:
    """Export explicit cached observations, never a new API query or historical backfill."""

    IDENTITY = ("org_id", "site_id", "gateway_id", "port_name", "peer_mac", "peer_port_id", "tunnel_identity")
    HEADER = (
        *IDENTITY,
        "observation_hour_utc",
        "collected_at_utc",
        "provenance",
        "metric",
        "value",
        "unit",
        "missing_reason",
    )

    @classmethod
    def response(cls, records: tuple[HourlyMeasurement, ...]) -> Response:
        """Serialize every filtered cached record, including explicit missing-value reasons."""
        logger.info("Export %s authorized cached WAN observations as CSV.", len(records))
        output = io.StringIO(newline="")
        writer = csv.writer(output)
        writer.writerow(cls.HEADER)
        for record in records:
            cls.write(output, record)
        logger.debug("Serialized %s authorized cached WAN observations.", len(records))
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={
                "Content-Disposition": 'attachment; filename="cached-wan-observations.csv"',
                "Cache-Control": "no-store",
            },
        )

    @classmethod
    def write(cls, output: io.StringIO, record: HourlyMeasurement) -> None:
        """Write whitelisted fields only, with one row per metric."""
        identity = record.identity.to_dict()
        context = [identity.get(field, "") for field in cls.IDENTITY]
        context += [record.hour_start_utc.isoformat(), record.collected_at_utc.isoformat(), record.provenance]
        for name, metric in sorted(record.metrics.items()):
            values = [*context, name, metric.value, metric.unit, metric.missing_reason]
            csv.writer(output).writerow([cls.cell(value) for value in values])

    @staticmethod
    def cell(value: str | float | None) -> str | float:
        """Preserve missing cells and neutralize spreadsheet formulas in text fields."""
        if value is None:
            return ""
        if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
            return "'" + value
        return value
