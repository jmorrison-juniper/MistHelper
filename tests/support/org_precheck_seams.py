"""A stand-in for the pre-check adopter seam of the upgrade routes (issue #3243).

Why:
    A multi-site upgrade now starts only when each selected site holds a
    verified pre-check capture. The start route reads the capture of each site
    through the adopter seam. A contract test must reach no database, so this
    module answers that seam from memory. A fixture that submits a multi-site
    upgrade installs the stand-in, and a test that proves the refusal removes a
    site from it.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, MutableMapping
from typing import Any

from src.upgrade_portal.app.routes.upgrade import PRECHECK_ADOPTER_KEY

logger = logging.getLogger(__name__)  # The seam logs under this module.

STAND_IN_TIER = 2  # The standard tier, which the start route stores with each capture.


class PrecheckAdopterStandIn:
    """Answer one verified pre-check capture for each known site.

    Attributes:
        captures: The capture identifier of each site that holds one.
        reads: The site of each read, in call order.
        edges: The run, the capture, and the role of each edge write.
    """

    def __init__(self, site_ids: Iterable[str] = (), tier: int = STAND_IN_TIER) -> None:
        """Give each named site one capture.

        Args:
            site_ids: The sites that hold a pre-check capture.
            tier: The tier of each capture.
        """
        self.captures = {site_id: f"pre-{site_id}" for site_id in site_ids}  # One stable key for each site.
        self.tier = tier  # The tier that the pair reader answers.
        self.reads: list[str] = []  # A test reads the order of the calls.
        self.edges: list[tuple[str, str, str]] = []  # A test reads each edge that a run wrote.

    def install(self, config: MutableMapping[str, Any]) -> PrecheckAdopterStandIn:
        """Put the stand-in into the configuration of one application.

        Args:
            config: The configuration of the Flask application.

        Returns:
            This stand-in, so a fixture keeps one handle.
        """
        config[PRECHECK_ADOPTER_KEY] = self  # The routes read the seam through this key.
        return self  # The fixture removes a site later to prove a refusal.

    def forget(self, site_id: str) -> None:
        """Remove the capture of one site.

        Args:
            site_id: The site that then holds no pre-check capture.
        """
        self.captures.pop(site_id, None)  # The next read of the site answers an empty key.

    def newest_precheck(self, site_id: str) -> str:
        """Return the capture key of one site.

        Args:
            site_id: The site to read.

        Returns:
            The capture key, or an empty string when the site holds none.
        """
        return self.newest_precheck_tier(site_id)[0]  # The pair reader owns the record of the read.

    def newest_precheck_tier(self, site_id: str) -> tuple[str, int]:
        """Return the capture key and the tier of one site.

        Args:
            site_id: The site to read.

        Returns:
            The capture key and the tier. The key is empty when the site holds none.
        """
        self.reads.append(site_id)  # A test proves which sites the route read.
        logger.debug("precheck stand-in: site %s reads %r", site_id, self.captures.get(site_id, ""))
        return self.captures.get(site_id, ""), self.tier  # The production adopter answers the same shape.

    def write_capture_edge(self, run_id: str, capture_id: str, role: str) -> None:
        """Record one edge write.

        Args:
            run_id: The run that the edge starts at.
            capture_id: The capture that the edge points at.
            role: The role of the edge.
        """
        self.edges.append((run_id, capture_id, role))  # No database stores the edge.
