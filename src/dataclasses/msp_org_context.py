"""Frozen dataclass that groups MSP / organization identity for device enrichment.

``_enrich_device_context`` in ``MistHelper.py`` took 6 parameters, exceeding the
5-Item Rule's max-5 limit. The four MSP/Org identity values that get stamped onto
each device record are grouped here so the method keeps only its per-call
arguments (the device record and the site lookup) and drops to 3 parameters.

Issue: https://github.com/jmorrison-juniper/MistHelper/issues/470
"""

from __future__ import annotations  # Enable PEP 604 union syntax on older runtimes.

from dataclasses import dataclass  # The standard library dataclass decorator.


@dataclass(frozen=True, slots=True)
class MspOrgContext:
    """MSP and organization identity stamped onto each enriched device record."""

    msp_id: str  # MSP (managed service provider) UUID the org belongs to.
    msp_name: str  # Human-readable MSP name.
    org_id: str  # Organization UUID the device belongs to.
    org_name: str  # Human-readable organization name.
