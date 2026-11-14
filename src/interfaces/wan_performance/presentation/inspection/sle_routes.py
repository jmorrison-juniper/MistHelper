"""Serve explicit tenant-scoped SLE requests through existing portal protections."""

import logging
from collections.abc import Callable

from flask import render_template, request
from redis.exceptions import RedisError
from requests.exceptions import RequestException

from src.interfaces.wan_performance.collection.live_service import LiveService
from src.interfaces.wan_performance.presentation.inspection.sle import SleReader, SleResult

logger = logging.getLogger(__name__)


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
