"""Quality gates for Juniper source documents and generated skill topics."""

from .cards import CardDeduplicationReport, CardDeduplicator  # Export card merge tools for package writers.
from .commands import CommandFenceCleaner, CommandFenceCleanReport  # Export command fence cleanup tools.
from .database import SourceQualityDatabase  # Export quarantine persistence for factory callers.
from .repair import (  # Export repair measurement tools.
    RepairAccuracyReport,
    SourceTextRepairer,
    WordFrequencyDictionary,
)
from .source_gate import SourceQualityGate, SourceQualityReport  # Export source quality gate tools.

__all__ = [  # Keep the public quality surface explicit for factory imports.
    "CardDeduplicationReport",  # Publish the card deduplication report model.
    "CardDeduplicator",  # Publish the card deduplicator class.
    "CommandFenceCleanReport",  # Publish the command cleanup report model.
    "CommandFenceCleaner",  # Publish the command cleanup class.
    "RepairAccuracyReport",  # Publish the repair accuracy model.
    "SourceQualityDatabase",  # Publish the quarantine database writer.
    "SourceQualityGate",  # Publish the source document gate.
    "SourceQualityReport",  # Publish the gate report model.
    "SourceTextRepairer",  # Publish the text repairer class.
    "WordFrequencyDictionary",  # Publish the dictionary builder class.
]
