"""Renders a snapshot in the Prometheus text exposition format.

Why:
    This is the primary output path of the gateway, and it answers the four
    defects that the upstream `mist_snmp_gateway` records about its own SNMP
    path.

    First, it needs no MIB. A monitoring system reads the metric name and the
    help text straight out of the response. Second, it needs no Private
    Enterprise Number, so it cannot collide with another product the way the
    upstream OID `.1.3.6.1.4.1.65535` can. Third, it binds an unprivileged port,
    so MistHelper keeps running as the non-root container user. Fourth, it can
    run behind TLS, while SNMP v2c sends its community string in clear text.

    Prometheus, Grafana, Zabbix, LibreNMS, and Icinga all read this format, so
    the NOC keeps the dashboard it already has.
"""

from __future__ import annotations

import logging
import math
import re

from src.metrics_gateway.catalog import MetricKind
from src.metrics_gateway.samples import LabelPairs, MetricSample, MetricSnapshot

logger = logging.getLogger(__name__)

CONTENT_TYPE = "text/plain; version=0.0.4; charset=utf-8"  # The media type a Prometheus scraper expects.

# WHY: The exposition format defines this grammar for a metric name. A name that
# breaks it makes the scraper drop the whole response, not just the one line.
NAME_PATTERN = re.compile(r"^[a-zA-Z_:][a-zA-Z0-9_:]*$")

# WHY: A label value may hold any text, and a site name can hold a quotation
# mark, a backslash, or a line break. Each one would end the value early and
# corrupt every line that follows, so each one needs an escape.
_LABEL_ESCAPES = (("\\", "\\\\"), ('"', '\\"'), ("\n", "\\n"))

INFO_SUFFIX = "_info"  # A Prometheus informational metric ends its name this way by convention.


def escape_label_value(value: str) -> str:
    """Make a label value safe for the exposition format.

    Args:
        value: The raw text, such as a site name from Mist Cloud.

    Returns:
        The text with the backslash, the quotation mark, and the line break escaped.
    """
    escaped = value  # Start from the raw text and apply each rule in order.
    for target, replacement in _LABEL_ESCAPES:  # The backslash rule must run first, or it would double the others.
        escaped = escaped.replace(target, replacement)
    return escaped


def format_value(value: float) -> str:
    """Render one number the way the exposition format defines.

    Why:
        The format spells an infinity `+Inf` and a missing number `NaN`. Python
        writes `inf` and `nan`, and a scraper rejects both.

    Args:
        value: The number to render.

    Returns:
        The text of the number.
    """
    if math.isnan(value):  # The format has one spelling for a number that is not one.
        return "NaN"
    if math.isinf(value):  # The format spells the two infinities with a sign and a capital letter.
        return "+Inf" if value > 0 else "-Inf"
    if value.is_integer() and abs(value) < 2**53:  # A whole number reads better without a decimal tail.
        return str(int(value))
    return repr(value)  # `repr` keeps every digit that the float holds, and `str` does not.


class PrometheusRenderer:
    """Turns a snapshot into the body of a `/metrics` response."""

    def __init__(self) -> None:
        """Prepare the renderer."""
        logger.debug("Build the Prometheus renderer")  # Log the build, because a caller holds one for the process.

    @staticmethod
    def _render_labels(labels: LabelPairs) -> str:
        """Render the label set of one sample.

        Args:
            labels: The label pairs, in the order the renderer prints them.

        Returns:
            The label text in braces, or an empty string when there is no label.
        """
        if not labels:  # A sample without a label prints its name and its value alone.
            return ""
        pairs = ",".join(f'{name}="{escape_label_value(value)}"' for name, value in labels)
        return "{" + pairs + "}"

    def _render_sample(self, sample: MetricSample) -> str:
        """Render one reading as one line.

        Args:
            sample: The reading to render.

        Returns:
            The line, without the trailing line break.
        """
        name = sample.definition.name  # The name is also the first field of the line.
        return f"{name}{self._render_labels(sample.labels)} {format_value(sample.value)}"

    @staticmethod
    def _render_header(sample: MetricSample) -> list[str]:
        """Render the help line and the type line of one metric family.

        Why:
            A scraper prints the help text beside the alarm, so a NOC engineer
            reads the meaning of the number without opening this repository.

        Args:
            sample: Any reading of the family.

        Returns:
            The two header lines.
        """
        definition = sample.definition  # The family carries one help text and one type.
        # WHY: the exposition format defines `gauge`, `counter`, `histogram`, `summary`, and
        # `untyped` only. It defines no `info` type, and a scraper drops a family that names
        # one. An informational reading is a constant 1, which is a gauge.
        kind = MetricKind.GAUGE if definition.kind is MetricKind.INFO else definition.kind
        return [f"# HELP {definition.name} {definition.help_text}", f"# TYPE {definition.name} {kind.value}"]

    def render(self, snapshot: MetricSnapshot) -> str:
        """Render every reading of a snapshot.

        Why:
            A scraper needs the readings of one metric family to arrive
            together, under one help line and one type line. The renderer
            therefore groups the samples by name and keeps the order in which
            the collector first produced each family.

        Args:
            snapshot: The reading to render.

        Returns:
            The response body, ending in a line break.
        """
        grouped: dict[str, list[MetricSample]] = {}  # A dict keeps the first-seen order of the families.
        for sample in snapshot.samples:  # One pass groups every reading under its family name.
            grouped.setdefault(sample.definition.name, []).append(sample)
        lines: list[str] = []  # Collect the whole body, then join it once.
        for family in grouped.values():  # Walk the families in the order the collector produced them.
            lines.extend(self._render_header(family[0]))
            lines.extend(self._render_sample(sample) for sample in family)
        logger.debug("Render %d metric families as %d lines", len(grouped), len(lines))  # Log the result size.
        return "\n".join(lines) + "\n"  # The format needs a line break after the last line.
