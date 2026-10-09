"""Operator input and export output shared by the Juniper read menus (294 to 300).

Each menu asks for its values through the safe input helper, prints every field of every row
with the personal values masked, and writes the rows in full through the shared exporter.
Every printed and saved value is ASCII only.
"""

from __future__ import annotations  # WHY: postponed annotations keep forward references readable on Python 3.13.

import logging  # WHY: action log and operator messages for each prompt and export.
from collections.abc import Mapping, Sequence  # WHY: typed reply and column inputs.
from datetime import UTC, date, datetime  # WHY: the retrieval time and the date prompts.
from typing import Any  # WHY: the exporter is an injected object.

from src.foundation.runtime.config.source_dependency_resolver import (
    SourceDependencyResolver,  # WHY: the shared input helper.
)
from src.operations.exporting.export.data_exporter import (
    DataExporter,  # WHY: the export goes through the shared exporter.
)
from src.operations.exporting.juniper_rma.api.gateway import (
    JuniperTransportError,  # WHY: a failed call is reported, not raised.
)
from src.operations.exporting.juniper_rma.api.messages import (  # WHY: reply reading.
    ResponseOutcome,
    ResponseStatusReader,
)
from src.operations.exporting.juniper_rma.model.export_rows import (  # WHY: ASCII and log masks.
    ExportRowBuilder,
    PersonalDataMasker,
)
from src.operations.exporting.juniper_rma.model.service_request import (  # WHY: the input rule.
    FieldReader,
    IdentifierRule,
)
from src.operations.exporting.juniper_rma.settings import (
    JuniperServiceSession,  # WHY: the checked session for each menu.
)

logger = logging.getLogger(__name__)  # WHY: module logger for prompts and exports.


def utc_now_text() -> str:
    """Return the current UTC time as ISO 8601 text with whole seconds."""
    return datetime.now(UTC).isoformat(timespec="seconds")  # WHY: one retrieval time format for every export.


def records_of(result: Mapping[str, Any], key: str) -> list[dict[str, Any]]:
    """Return the object records of one list field of a reply. A missing list gives no records."""
    return FieldReader.items(result, key)  # WHY: the null-safe list reader of the model layer.


class JuniperMenuInput:
    """Read operator answers through the safe input helper. A rejected answer returns None."""

    @staticmethod
    def text(prompt: str, context: str) -> str:
        """Return the trimmed answer. A blank answer returns an empty string."""
        answer = SourceDependencyResolver.InputUtils.safe_input(  # WHY: the safe input helper handles end of file.
            prompt,
            default_value="",
            allow_empty=True,
            context=context,
        )
        return str(answer or "").strip()  # WHY: spaces around the answer are not part of it.

    @classmethod
    def identifier(cls, label: str, context: str, required: bool = True) -> str | None:
        """Return a valid identifier. A blank optional answer returns an empty string. Otherwise None."""
        suffix = "" if required else "; Enter to skip"  # WHY: an optional value says that Enter skips it.
        raw = cls.text(f"Enter the {label} (1 to 40 letters, digits, or hyphens{suffix}): ", context)  # WHY: prompt.
        if not raw:  # WHY: a blank answer means skip or cancel.
            return None if required else ""  # WHY: a required value cancels, an optional value is empty.
        if not IdentifierRule.is_valid(raw):  # WHY: reject the value before any call.
            logger.warning(  # WHY: the rule only, never the value.
                "Input rejected: the menu could not run, because the %s breaks the 1 to 40 character rule",  # The rule.
                label,  # The label names the field.
            )
            return None  # WHY: no call is made.
        return raw  # WHY: the checked value.

    @classmethod
    def day(cls, label: str, default: date, context: str) -> date | None:
        """Return the date that the operator typed, or the default for a blank answer. None when it is invalid."""
        raw = cls.text(f"Enter the {label} as YYYY-MM-DD (Enter for {default.isoformat()}): ", context)  # WHY.
        if not raw:  # WHY: a blank answer keeps the default date.
            return default  # WHY: the default is a valid date.
        try:  # WHY: a malformed date is an input error, not a crash.
            return date.fromisoformat(raw)  # WHY: the checked date.
        except ValueError:  # WHY: reject the malformed text.
            logger.warning(  # WHY: the rule only, never the value.
                "Input rejected: the menu could not run, because the %s is not a YYYY-MM-DD date",  # The rule.
                label,  # The label names the field.
            )
            return None  # WHY: no call is made.


class CaseKeyPrompt:
    """Ask for a request number or a customer case number, and read the request detail with it."""

    KIND_REQUEST = "1"  # WHY: the operator choice for a request number.
    KIND_CASE = "2"  # WHY: the operator choice for a customer case number.
    NOT_FOUND_CODES = ("756", "757", "778")  # WHY: codes that mean no such request for this account.

    @classmethod
    def ask(cls) -> tuple[str, str] | None:
        """Return the key kind and the key value, or None when the operator cancels or the value is invalid."""
        kind = JuniperMenuInput.text(  # WHY: the key type first.
            "Enter 1 for a request number or 2 for a customer case number (Enter to cancel): ",
            "juniper_key_kind",
        )
        if kind not in (cls.KIND_REQUEST, cls.KIND_CASE):  # WHY: only two choices exist.
            return None  # WHY: the run is cancelled.
        label = "request number" if kind == cls.KIND_REQUEST else "customer case number"  # WHY: the prompt label.
        value = JuniperMenuInput.identifier(label, "juniper_key_value")  # WHY: the checked key value.
        return None if value is None else (kind, value)  # WHY: the pair, or None for a rejected value.

    @classmethod
    def read_detail(cls, session: JuniperServiceSession, kind: str, value: str) -> ResponseOutcome | None:
        """Read one request detail. Return None when the request is not found or the read fails."""
        logger.info("Juniper request detail read by %s", "request number" if kind == cls.KIND_REQUEST else "case")
        try:  # WHY: a transport failure is reported as a failed read.
            if kind == cls.KIND_REQUEST:  # WHY: the request number is the key.
                outcome = session.case.get_request(request_number=value)  # WHY: one detail call.
            else:  # WHY: the customer case number is the key.
                outcome = session.case.get_request(case_number=value)  # WHY: one detail call.
        except JuniperTransportError as error:  # WHY: keep the reason, never a secret.
            logger.error("Juniper request detail failed to complete: %s", error)  # WHY: the operator sees the reason.
            return None  # WHY: no detail.
        if outcome.is_usable:  # WHY: a usable reply carries the request.
            return outcome  # WHY: the caller reads the detail.
        if any(code in cls.NOT_FOUND_CODES for code in outcome.fault_codes):  # WHY: not found is not a fault.
            logger.info("No Juniper request matches this value for the account")  # WHY: the operator sees it.
            return None  # WHY: nothing to show.
        logger.error(  # WHY: the reason names what Juniper returned.
            "Juniper request detail failed to complete: %s",  # The message keeps the cause.
            ResponseStatusReader.explain(outcome),  # The explanation names the next step.
        )
        return None  # WHY: nothing to show.


class JuniperExportSink:
    """Print the rows of one read, then write them through the shared exporter. Output is ASCII only."""

    def __init__(self, exporter: Any = DataExporter) -> None:
        """Store the exporter. A test may inject a double."""
        self._exporter = exporter  # WHY: the shared exporter, or a test double.

    def publish(
        self,
        title: str,
        filename: str,
        api_name: str,
        columns: Sequence[str],
        rows: list[dict[str, str]],
    ) -> bool:
        """Print every field with personal values masked, then write the rows in full. Return True when written."""
        cleaned = ExportRowBuilder.ascii_rows(rows)  # WHY: FR-029 ASCII-only text before print or write.
        self._print(title, columns, cleaned)  # WHY: the operator sees every field of every row.
        if not cleaned:  # WHY: the exporter rejects empty data, so nothing is written.
            logger.info("No rows for %s, so no file was written", filename)  # WHY: the operator sees the reason.
            return False  # WHY: no file.
        logger.info("Writing %d row(s) to %s", len(cleaned), filename)  # WHY: action log before the write.
        written = self._exporter.write_with_format_selection(  # WHY: the shared export path.
            cleaned,
            filename,
            api_name,
            fieldnames=list(columns),  # WHY: the header is the full column list, in order.
        )
        logger.debug("Export of %s finished, written=%s", filename, bool(written))  # WHY: the result, not the data.
        return bool(written)  # WHY: the caller reports the outcome.

    @staticmethod
    def _print(title: str, columns: Sequence[str], rows: list[dict[str, str]]) -> None:
        """Log the count, then one line for each row with every column. Personal values are masked in the log."""
        logger.info("%s: %d row(s), %d column(s)", title, len(rows), len(columns))  # WHY: the counts.
        for index, row in enumerate(rows, start=1):  # WHY: one line for each row.
            fields = " | ".join(  # WHY: the log copy masks each personal value, the export keeps it in full.
                f"{column}={PersonalDataMasker.for_log(column, row.get(column, ''))}" for column in columns
            )  # WHY: every column, with the personal values masked.
            logger.info("%s row %d: %s", title, index, fields)  # WHY: the row, masked and ASCII.
