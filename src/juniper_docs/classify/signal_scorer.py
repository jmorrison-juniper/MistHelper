"""Derive a content sub-category label from three weighted signal groups.

The scorer scores a bounded text sample against the product-family, task-type,
and technology-domain groups. It counts each keyword with a word boundary, so a
short token cannot match inside a longer, unrelated word (Defect A). A keyword
that appears in the file name outweighs a keyword that appears only in the body
by ``NAME_WEIGHT``, so the true subject of the document wins the product family
(Defect A).

The caller passes the file name through the ``source_name`` argument of
``score``. The argument has an empty default, so an old call site keeps working.
The runner already holds the local path, so a follow-up agent changes one line
in ``src/juniper_docs/harvest/runner.py``::

    result = self.classify.scorer.score(text, Path(local_path).name)

The scorer keeps the middle label segment only when one task type leads the
runner-up by ``TASK_MARGIN``, so a ubiquitous ``configuration`` token does not
force a constant middle segment (Defect B). The technology-domain group holds a
signal for the GPU or AI cluster topic and a signal for the EVPN VXLAN fabric
topic, so the flagship data-center documents keep their distinct subject
(Defect C).

The confidence value is the weighted hit count divided by the sample length in
thousands of characters, so the number means the strength of the match and not
the length of the document (Defect D). When no group reaches the threshold, or
the sample is empty, the scorer returns the fixed fallback label and empty
scores (FR-023, FR-023a, FR-023b, FR-025a).

The result object holds the label, the detected signal names, and the numeric
scores only. It never holds the body text, so the privacy invariant is
structural (FR-024, SC-005).
"""

from __future__ import annotations  # Enable modern union syntax on every annotation.

import logging  # Trace each scoring for observability.
import re  # Match each keyword on a word boundary.

from src.juniper_docs.models import ContentAnalysisResult  # The derived metadata record.

_LOGGER = logging.getLogger(__name__)  # Module logger for the signal scorer.

FALLBACK_LABEL = "unclassified-content"  # The fixed label for weak or unreadable input.
CONFIDENCE_THRESHOLD = 0.25  # The minimum weighted hits per 1000 characters for a label.
NAME_WEIGHT = 20.0  # A file-name hit outweighs a body hit by this factor.
TASK_MARGIN = 2.0  # Keep the task segment only when the winner leads by this ratio.
SEGMENT_FLOOR = 0.5  # The minimum normalized strength for one label segment to be kept.
_LENGTH_UNIT = 1000.0  # Normalize the score by the sample length in this many characters.
_TASK_GROUP = "task_type"  # The one group that the lead-margin gate protects.

# The signal groups run in this fixed order, so the label is reproducible. Each
# signal maps to the keywords counted on a word boundary in the lowercased text.
_SIGNAL_GROUPS: dict[str, dict[str, tuple[str, ...]]] = {
    "product_family": {
        "ex": ("ex series", "ex4300", "ex9200"),
        "qfx": ("qfx",),
        "srx": ("srx",),
        "mx": ("mx series", "mx480", "mx960", "mx204"),
        "acx": ("acx",),
        "ptx": ("ptx",),
        "mist": ("mist",),
        "apstra": ("apstra",),
        "junos-space": ("junos space",),
        "paragon": ("paragon",),
        "contrail": ("contrail",),
    },
    "task_type": {
        "configuration": ("configuration", "configure", "config"),
        "monitoring": ("monitoring", "monitor"),
        "troubleshooting": ("troubleshooting", "troubleshoot"),
        "hardware-installation": ("hardware installation", "installation", "install"),
        "licensing": ("licensing", "license"),
        "interoperability": ("interoperability", "interoperate"),
    },
    "technology_domain": {
        "routing": ("routing", "route"),
        "switching": ("switching", "switch"),
        "security": ("security", "firewall", "screen"),
        "wireless": ("wireless", "wifi", "access point"),
        "automation": ("automation", "automate", "ansible"),
        "telemetry": ("telemetry", "streaming telemetry"),
        "gpu-cluster": (
            "gpu",
            "gpus",
            "gpudirect",
            "rdma",
            "roce",
            "rocev2",
            "roce v2",
            "nccl",
            "ai cluster",
            "ai data center",
            "backend fabric",
            "collective",
            "tensor",
            "training",
            "inference",
            "weka",
            "dpf",
        ),
        "evpn-vxlan": (
            "evpn",
            "vxlan",
            "vtep",
            "vni",
            "type-5",
            "type 5",
            "type-2",
            "type 2",
            "multitenancy",
            "multi-tenancy",
        ),
    },
}
_GROUP_ORDER = ("product_family", "task_type", "technology_domain")  # Label segment order.


def _compile_group(signals: dict[str, tuple[str, ...]]) -> dict[str, re.Pattern[str]]:
    """Return one compiled word-boundary alternation for each signal in a group."""
    compiled: dict[str, re.Pattern[str]] = {}  # Signal name to its compiled pattern.
    for name, keywords in signals.items():  # Build one pattern for each signal.
        parts = sorted((re.escape(word) for word in keywords), key=len, reverse=True)
        alternation = "|".join(parts)  # Join the escaped keywords into one alternation.
        compiled[name] = re.compile(rf"\b(?:{alternation})\b")  # Word-boundary hits.
    return compiled  # The scorer counts hits with these patterns.


# Precompile the patterns once at import, so each score call stays fast.
_COMPILED_GROUPS: dict[str, dict[str, re.Pattern[str]]] = {
    group: _compile_group(signals) for group, signals in _SIGNAL_GROUPS.items()
}


class SignalScorer:
    """Score a text sample and build a reproducible content sub-category label."""

    def __init__(self, threshold: float = CONFIDENCE_THRESHOLD) -> None:
        """Store the confidence threshold for a non-fallback label.

        Args:
            threshold: The minimum weighted hits per 1000 characters for a label.
        """
        self.threshold = threshold  # The normalized floor for a non-fallback label.

    def score(self, text: str, source_name: str = "") -> ContentAnalysisResult:
        """Return the derived metadata, or the fallback for weak or empty input.

        Args:
            text: The bounded, in-memory PDF text sample.
            source_name: The file name of the PDF, an authoritative subject hint.

        Returns:
            The label, the detected signal names, and the numeric scores.
        """
        _LOGGER.info("Scoring a %d character sample named %r", len(text), source_name)  # Intent.
        if not text.strip():  # The PDF yielded no readable text.
            return self._fallback()  # An empty sample yields the fallback label.
        best = self._best_per_group(text.lower(), source_name.lower())  # Rank each group.
        strength = self._strength(best, len(text))  # The length-normalized confidence.
        _LOGGER.debug("Scored strength %.3f across %d groups", strength, len(best))  # Result.
        if strength < self.threshold:  # No group cleared the normalized threshold.
            return self._fallback()  # Weak evidence yields the fallback label.
        return self._build(best, len(text))  # Build the label from the top signals.

    @staticmethod
    def _best_per_group(text: str, name: str) -> dict[str, tuple[str, float, float]]:
        """Return the top signal, its weighted score, and the runner-up score."""
        best: dict[str, tuple[str, float, float]] = {}  # Group to winner and runner-up.
        for group, patterns in _COMPILED_GROUPS.items():  # Rank each group in turn.
            scored = {sig: _weighted(text, name, pat) for sig, pat in patterns.items()}
            ranked = sorted(scored.items(), key=lambda item: item[1], reverse=True)
            runner_up = ranked[1][1] if len(ranked) > 1 else 0.0  # The second-place score.
            best[group] = (ranked[0][0], ranked[0][1], runner_up)  # Winner and runner-up.
        return best  # The builder turns these into a label and scores.

    @staticmethod
    def _strength(best: dict[str, tuple[str, float, float]], length: int) -> float:
        """Return the weighted winner hits per 1000 characters of the sample."""
        total = sum(hits for _, hits, _ in best.values())  # The weighted winner hits.
        return total / max(length / _LENGTH_UNIT, 1.0)  # Normalize by the sample length.

    @staticmethod
    def _build(best: dict[str, tuple[str, float, float]], length: int) -> ContentAnalysisResult:
        """Return the label and normalized scores from the top signal in each group."""
        divisor = max(length / _LENGTH_UNIT, 1.0)  # The same length normalizer as the gate.
        segments: list[str] = []  # The label segments in the fixed group order.
        scores: dict[str, float] = {}  # The normalized per-signal scores keyed by group.
        for group in _GROUP_ORDER:  # Walk the groups in the label order.
            name, hits, runner_up = best[group]  # The winner and the runner-up score.
            if not _keep_segment(group, hits, runner_up, divisor):  # Skip a weak segment.
                continue  # Omit this group from the label.
            segments.append(name)  # Add the winning signal name to the label.
            scores[f"{group}:{name}"] = round(hits / divisor, 4)  # Record the strength.
        label = "__".join(segments) or FALLBACK_LABEL  # Join the segments into the label.
        return ContentAnalysisResult(label, tuple(segments), scores, is_fallback=False)

    @staticmethod
    def _fallback() -> ContentAnalysisResult:
        """Return the fixed fallback result with empty scores."""
        return ContentAnalysisResult(FALLBACK_LABEL, (), {}, is_fallback=True)  # Safe result.


def _weighted(text: str, name: str, pattern: re.Pattern[str]) -> float:
    """Return the weighted hit count for one signal in the body and the file name."""
    body_hits = len(pattern.findall(text))  # Count the word-boundary hits in the body.
    name_hits = len(pattern.findall(name))  # Count the word-boundary hits in the file name.
    return float(body_hits) + NAME_WEIGHT * float(name_hits)  # The file name weighs far more.


def _keep_segment(group: str, hits: float, runner_up: float, divisor: float = 1.0) -> bool:
    """Return whether the winning signal earns a place in the label.

    A segment must clear an absolute strength floor, because one stray keyword
    in a long document otherwise attaches a misleading token. A document about
    data center design scored 0.105 for ``licensing`` on a single incidental
    hit, which produced a label that sent the reader to the wrong folder.
    """
    if hits <= 0:  # A group with no signal above zero is omitted.
        return False  # Omit an empty group.
    if hits / divisor < SEGMENT_FLOOR:  # One stray keyword must not name the document.
        return False  # Drop a segment that no strong signal supports.
    if group == _TASK_GROUP and hits < TASK_MARGIN * runner_up:  # No clear task lead.
        return False  # Drop the task segment when no task type leads by the margin.
    return True  # Keep a group that leads clearly.
