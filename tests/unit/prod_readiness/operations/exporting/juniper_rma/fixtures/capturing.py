"""Capturing exporter and scripted operator answers, shared by the offline and the live Juniper menu tests."""

from __future__ import annotations  # WHY: postponed annotations keep forward references readable on Python 3.13.

from dataclasses import dataclass, field  # WHY: the captured export record and its write list.
from typing import Any  # WHY: the captured rows are loosely typed.


@dataclass
class CapturedWrite:
    """One export that a workflow asked the exporter to write."""

    filename: str  # WHY: the file name passed to the exporter.
    api: str  # WHY: the operation name passed with the export.
    fieldnames: list[str]  # WHY: the header that the exporter receives.
    rows: list[dict[str, Any]]  # WHY: the rows that the exporter receives.


@dataclass
class CapturingExporter:
    """A stand-in for DataExporter that records each write and writes no file."""

    writes: list[CapturedWrite] = field(default_factory=list)  # WHY: every write, in order.

    def write_with_format_selection(  # WHY: the same signature as the shared exporter.
        self,
        data: list[dict[str, Any]],
        filename_or_table: str,
        api_function_name: str,
        fieldnames: list[str] | None = None,
        backend_options: object | None = None,
    ) -> bool:
        """Record the write and report success."""
        del backend_options  # WHY: the options do not change what is recorded.
        self.writes.append(  # WHY: keep the header and the rows exactly as received.
            CapturedWrite(filename_or_table, api_function_name, list(fieldnames or []), list(data))
        )
        return True  # WHY: the exporter reports that the file was written.


class ScriptedAnswers:
    """Return the scripted answer for each prompt context. A prompt without an answer gets Enter."""

    def __init__(self, answers: dict[str, str]) -> None:
        """Store the answers keyed by the prompt context."""
        self._answers = answers  # WHY: the script for this test.

    def __call__(self, prompt: str, context: str) -> str:
        """Return the scripted answer for the context. The prompt text is not checked."""
        del prompt  # WHY: the context names each question, so the text is not needed.
        return self._answers.get(context, "")  # WHY: a missing answer is an empty answer, the Enter key.
