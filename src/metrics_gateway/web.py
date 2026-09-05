"""The web application that serves the Prometheus endpoint.

Why:
    This module holds the Flask layer alone, and `service.py` holds the settings
    and the cache wiring. The split keeps Flask off the SNMP path. A
    `pass_persist` helper reads the settings and builds the cache, and it has no
    use for a web framework, so it must not pay to load one.
"""

from __future__ import annotations

import logging

from flask import Flask, Response

from src.metrics_gateway.cache import MetricsCache
from src.metrics_gateway.prometheus import CONTENT_TYPE, PrometheusRenderer

logger = logging.getLogger(__name__)

METRICS_ROUTE = "/metrics"  # The path a Prometheus scraper reads by convention.
HEALTH_ROUTE = "/healthz"  # The path a container health probe reads.

HEALTH_BODY = "ok\n"  # The whole answer of the health route.
HEALTH_CONTENT_TYPE = "text/plain; charset=utf-8"  # The media type of that answer.


def create_app(cache: MetricsCache) -> Flask:
    """Build the web application that serves the Prometheus endpoint.

    Args:
        cache: The source of the readings.

    Returns:
        The Flask application.
    """
    app = Flask(__name__)  # The application serves two routes and holds no session.
    renderer = PrometheusRenderer()  # One renderer serves every request.

    @app.get(METRICS_ROUTE)
    def metrics() -> Response:
        """Answer a Prometheus scrape from the cache.

        Returns:
            The exposition text, with the media type a scraper expects.
        """
        logger.debug("Answer a scrape of %s", METRICS_ROUTE)  # Log before the render.
        body = renderer.render(cache.snapshot())  # The cache refreshes itself only when the reading is stale.
        # WHY: `mimetype` makes Flask append its own charset, which produces a header that
        # names `charset=utf-8` twice. `content_type` sends the value unchanged.
        return Response(body, content_type=CONTENT_TYPE)

    @app.get(HEALTH_ROUTE)
    def healthz() -> Response:
        """Report that the process is alive, without reading Mist Cloud.

        Why:
            A health probe that calls a cloud API reports the health of the
            cloud. A container would then restart during a Mist outage, which
            loses the last good reading the cache still holds.

        Returns:
            A short plain text answer.
        """
        return Response(HEALTH_BODY, content_type=HEALTH_CONTENT_TYPE)

    logger.info("The metrics gateway serves %s and %s", METRICS_ROUTE, HEALTH_ROUTE)  # Log the route list.
    return app
