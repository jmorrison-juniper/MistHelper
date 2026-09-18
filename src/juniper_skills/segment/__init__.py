"""Segment Juniper source Markdown into bounded topic inputs."""

from src.juniper_skills.segment.commands import CommandBlockDetector, CommandDetectionResult  # Export command tools.
from src.juniper_skills.segment.parts import JoinedDocument, PartSetJoiner  # Export part join tools.
from src.juniper_skills.segment.repair import DefectRepairResult, OrphanWordRepairer  # Export repair tools.
from src.juniper_skills.segment.segmenter import (
    DocumentSegmenter,
    SegmenterResult,
    TopicSegment,
)  # Export segment tools.

__all__ = [  # Keep the public import surface explicit for other factory agents.
    "CommandBlockDetector",  # Let callers re-fence command samples before rewriting.
    "CommandDetectionResult",  # Let callers inspect command block counts and text.
    "DefectRepairResult",  # Let callers report measured repair counts.
    "DocumentSegmenter",  # Let callers build contract-sized topic units.
    "JoinedDocument",  # Let callers inspect the ordered source document.
    "OrphanWordRepairer",  # Let tests and callers repair converter line defects.
    "PartSetJoiner",  # Let the inventory agent provide grouped parts.
    "SegmenterResult",  # Let callers read aggregate segmentation metrics.
    "TopicSegment",  # Let callers write topic files with page metadata.
]
