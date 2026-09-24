"""Record the insight metric requests that the Mist API refused, and report them to the operator.

mistapi 0.64.0 does not raise an exception for an HTTP status of 400 or more.
It returns a response that holds the status in ``status_code`` and the error
body in ``data``. An export must read the status before it treats the body as
metric data. Issue #3267 records the defect that this module repairs.
"""

from __future__ import annotations  # WHY: Keep the annotations cheap to evaluate.

import logging  # WHY: Write the warning lines and the operator lines through the standard logger.
from dataclasses import dataclass  # WHY: A frozen record keeps each refusal unchanged after the log stores it.

logger = logging.getLogger(__name__)  # WHY: Name the logger for this module so a reader can filter by source.

_REFUSED_STATUS_FLOOR = 400  # WHY: Each HTTP status of 400 or more is a refusal.


@dataclass(frozen=True, slots=True)
class MetricRefusal:
    """One metric request that the Mist API refused."""

    metric: str  # WHY: The metric name that the request named.
    status_code: int  # WHY: The HTTP status of the refusal.
    reason: str  # WHY: The refusal text of the error body, in ASCII on one line.


class MetricRefusalLog:
    """Collect the metric requests that the Mist API refused during one export run."""

    REASON_KEYS = ("detail", "error", "message")  # WHY: A Mist error body holds its reason in one of these keys.
    REASON_LIMIT = 200  # WHY: Keep each operator line short.
    NO_REASON = "The error body holds no reason."  # WHY: An operator line must never end with an empty reason.

    def __init__(self, scope_label: str) -> None:
        """Start an empty log for one export run."""
        self.scope_label = scope_label  # WHY: The operator lines name the scope, for example "device insight".
        self.refusals: list[MetricRefusal] = []  # WHY: The refusals of the current run, in request order.

    def clear(self) -> None:
        """Remove the refusals of an earlier run, so that each run starts empty."""
        logger.debug("Clearing %s earlier %s refusals", len(self.refusals), self.scope_label)  # WHY: Trace reset.
        self.refusals.clear()  # WHY: A new run must not report the refusals of an earlier run.

    def record(self, metric: str, response: object) -> bool:
        """Store the response as a refusal if its HTTP status is 400 or more. Return True for a refusal."""
        status_code = getattr(response, "status_code", None)  # WHY: A mistapi APIResponse holds the HTTP status.
        if not isinstance(status_code, int) or status_code < _REFUSED_STATUS_FLOOR:  # WHY: Not a refusal.
            return False  # WHY: No integer status, or a status below 400, keeps the old path of the caller.
        refusal = MetricRefusal(metric, status_code, self.reason(getattr(response, "data", None)))  # WHY: Store.
        self.refusals.append(refusal)  # WHY: The report at the end of the run lists each refusal.
        logger.warning(  # WHY: Keep a record of each refusal in the log file.
            "The Mist API refused %s metric %s with HTTP %s: %s",
            self.scope_label,
            metric,
            status_code,
            refusal.reason,
        )
        return True  # WHY: Tell the caller that the body is an error body, not metric data.

    def report(self, target_name: str) -> None:
        """Tell the operator which metrics the Mist API refused, with the status and the reason of each."""
        if not self.refusals:  # WHY: A run without a refusal adds no operator line.
            return  # WHY: Nothing to report.
        count = len(self.refusals)  # WHY: The heading states the number of refused metrics.
        # WHY: An operator line starts with "!". Route it through the logger for capture and redirection.
        logger.info("! The Mist API refused %s %s metrics for %s:", count, self.scope_label, target_name)
        for refusal in self.refusals:  # WHY: One line for each refused metric, in request order.
            logger.info("!   %s: HTTP %s, %s", refusal.metric, refusal.status_code, refusal.reason)  # WHY: Detail.
        logger.debug("Reported %s %s refusals for %s", count, self.scope_label, target_name)  # WHY: Trace result.

    @classmethod
    def reason(cls, body: object) -> str:
        """Return the refusal text of an error body in ASCII, on one line, and no longer than REASON_LIMIT."""
        text = cls._reason_text(body)  # WHY: Read the first reason that the body holds.
        ascii_text = text.encode("ascii", "replace").decode("ascii")  # WHY: The project logs hold ASCII only.
        one_line = " ".join(ascii_text.split())  # WHY: A line break in the body must not forge a second log line.
        return one_line[: cls.REASON_LIMIT] or cls.NO_REASON  # WHY: Keep the line short and never empty.

    @classmethod
    def _reason_text(cls, body: object) -> str:
        """Return the first reason text of a body, or an empty text when the body holds none."""
        if isinstance(body, str):  # WHY: A plain text body is its own reason.
            return body  # WHY: Use the text as it is. The caller makes it safe for the log.
        if not isinstance(body, dict):  # WHY: A list or None holds no named reason.
            return ""  # WHY: The caller replaces an empty text with NO_REASON.
        for key in cls.REASON_KEYS:  # WHY: Read the known keys in a fixed order.
            value = body.get(key)  # WHY: A missing key gives None.
            if value:  # WHY: Skip an empty value, and read the next key.
                return str(value)  # WHY: The reason can arrive as a number or a list, so make it text.
        return ""  # WHY: The caller replaces an empty text with NO_REASON.
