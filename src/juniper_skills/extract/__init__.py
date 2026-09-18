"""Depth extraction engine for Juniper skill source documents."""

from .engine import FactExtractionEngine  # Export the main engine for factory callers.
from .extractors import (  # Export each extractor so tests can verify every fact class.
    CommandFactExtractor,
    ConfigurationFactExtractor,
    ConstraintFactExtractor,
    DefinitionFactExtractor,
    NumericFactExtractor,
    OutputFieldFactExtractor,
    PlatformReleaseFactExtractor,
    PrerequisiteFactExtractor,
    TableRowFactExtractor,
)
from .guard import CachedSourceSimilarityGuard  # Export the cached guard runner for large measurements.
from .models import DepthExtractionResult, ExtractedFact, TopicSplit  # Export result models for reports.

__all__ = [  # Keep the public surface explicit for skill factory imports.
    "CachedSourceSimilarityGuard",
    "CommandFactExtractor",
    "ConfigurationFactExtractor",
    "ConstraintFactExtractor",
    "DefinitionFactExtractor",
    "DepthExtractionResult",
    "ExtractedFact",
    "FactExtractionEngine",
    "NumericFactExtractor",
    "OutputFieldFactExtractor",
    "PlatformReleaseFactExtractor",
    "PrerequisiteFactExtractor",
    "TableRowFactExtractor",
    "TopicSplit",
]
