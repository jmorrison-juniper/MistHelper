"""Readers and writers of the runbook, the OpenAPI file, and the evidence record of the smoke test.

The module reads the runbook and the OpenAPI file once each. It removes identifiers, tokens, and
contact data from each evidence value. It writes the evidence record as UTF-8 JSON.

Why: the document checks and the evidence share one set of rules. So one path, heading, or
identifier is judged the same way in every check and in the file that the operator keeps.
"""

from __future__ import annotations  # Postpone annotation evaluation, so the classes can name each other.

import json  # Parse the OpenAPI file and write the evidence record.
import re  # Find headings, table cells, Mist API paths, and identifiers in text.
from dataclasses import dataclass, field  # Declare the frozen value objects of this module.
from datetime import UTC, datetime  # Name the evidence file by its time in UTC.
from pathlib import Path  # Build every file path with the path library.
from typing import Any  # Type the JSON values, which can be objects, arrays, or scalars.
from urllib.parse import urlsplit  # Read the host name of each server URL.

import structlog  # Structured logging of each file read and each file write.

logger = structlog.get_logger(__name__)  # Module logger, so each event names this module.


class MarkdownTables:  # Read table rows under headings, and skip fenced examples.
    """Read the rows of the tables under each heading of one Markdown text.

    Why: the runbook keeps each fact in a table under one heading. A fenced example can repeat a
    heading or a table row, so the fences are removed before any row is read.
    """

    def __init__(self, text: str) -> None:  # Keep only prose lines, so fenced examples never count.
        """Keep the lines of the text that are outside each code fence.

        Args:
            text: Full Markdown text, already decoded from UTF-8.
        """
        kept: list[str] = []  # Lines outside every code fence.
        inside_fence = False  # True between two fence markers.
        for line in text.splitlines():  # Check each line once.
            if line.lstrip().startswith(("```", "~~~")):  # A fence marker switches the state.
                inside_fence = not inside_fence  # Switch between inside and outside the fence.
                continue  # The marker line itself is not prose, so the loop skips it.
            if not inside_fence:  # Only the prose lines are kept.
                kept.append(line)  # Keep the prose line.
        self.prose_lines: tuple[str, ...] = tuple(kept)  # The lines that the parser reads.

    def rows_after_heading(  # Read a table only when its header matches the contract.
        self, heading: str, header: tuple[str, ...]
    ) -> tuple[tuple[str, ...], ...]:
        """Return the data rows of the first table under a heading whose header row matches.

        Why: the contract names each header row exactly. A table with another header, or with no
        separator row, is not read, so the check can report the missing rows.

        Args:
            heading: Heading text, without the # markers.
            header: Header cells of the table, in order.

        Returns:
            The data rows, each as a tuple of trimmed cells. Empty when no table matches.
        """
        section = self.section_lines(heading)  # Read only the lines under this heading.
        for index, line in enumerate(section):  # Search the section for the header row.
            if self._cells(line) != header:  # Skip each line that is not the header row.
                continue  # The line is not the header, so the search goes on.
            if index + 1 >= len(section) or not self._is_separator(section[index + 1]):  # Needs a separator.
                return ()  # Without a separator row, the table is not read.
            rows: list[tuple[str, ...]] = []  # Data rows of this table.
            for row_line in section[index + 2 :]:  # Read the rows after the separator row.
                cells = self._cells(row_line)  # Split the row into cells.
                if cells is None:  # The first line that is not a row ends the table.
                    break  # Leave the loop, because the table has ended.
                rows.append(cells)  # Keep the data row.
            return tuple(rows)  # The data rows of the table, in order.
        return ()  # No table under this heading has the header.

    def section_lines(  # Stop at the next heading, so each table has one heading.
        self, heading: str
    ) -> tuple[str, ...]:
        """Return the prose lines under one heading, up to the next heading.

        Why: each table belongs to the heading above it, so the search for a table stops at the next
        heading of any level.

        Args:
            heading: Heading text, without the # markers.

        Returns:
            The lines of the section. Empty when the heading is absent.
        """
        section: list[str] = []  # Lines under the heading.
        inside = False  # True after the matching heading.
        for line in self.prose_lines:  # Walk the prose once.
            match = re.match(r"^#{1,3} (.*)$", line)  # A heading has one to three markers and one space.
            if match is not None:  # A heading line starts or ends a section.
                if inside:  # The next heading ends the section.
                    break  # Leave the loop, because the section has ended.
                inside = match.group(1).strip() == heading  # Start the section at the matching heading.
            elif inside:  # Keep each line of the section.
                section.append(line)  # Add the line to the section.
        return tuple(section)  # The lines of the section, in order.

    @staticmethod
    def _cells(line: str) -> tuple[str, ...] | None:  # Split a row into cells, so a non-row ends the table.
        """Return the trimmed cells of a table row, or None when the line is not a row.

        Why: a table row starts and ends with a pipe. Any other line ends the table.

        Args:
            line: One line of the text.

        Returns:
            The cell texts, or None when the line is not a table row.
        """
        stripped = line.strip()  # Ignore the white space around the row.
        if len(stripped) < 2 or not stripped.startswith("|") or not stripped.endswith("|"):  # Pipe at both ends.
            return None  # The line is not a table row.
        return tuple(cell.strip() for cell in stripped[1:-1].split("|"))  # Trim each cell of the row.

    @staticmethod
    def _is_separator(line: str) -> bool:  # Detect the dash row that must follow a table header.
        """Return True when a line is the separator row of a Markdown table.

        Why: the separator row holds dashes, colons, pipes, and spaces only. A row with other text is
        a data row, not a separator.

        Args:
            line: One line of the text.

        Returns:
            True when the line is a separator row.
        """
        stripped = line.strip()  # Ignore the white space around the row.
        return "-" in stripped and set(stripped) <= set("|-: ")  # Dashes, colons, pipes, and spaces only.


@dataclass(frozen=True)
class RunbookClaims:  # Hold runbook facts read once, so checks share one parse.
    """Facts of one runbook file, read once and kept as plain values.

    Why: the offline document test and the live smoke test check the same facts. One parse of the
    file keeps both checks on one text, and each fact follows runbook-structure.md. Create the object
    with from_path.
    """

    path: Path  # Runbook file that was read.
    headings: tuple[tuple[int, str], ...]  # Each heading as (level, text), in document order.
    h2_headings: tuple[str, ...]  # Texts of the level-2 headings, in document order.
    api_paths: tuple[str, ...]  # Each Mist API path of the file without its query, sorted and unique.
    endpoint_paths: tuple[str, ...]  # The first /api/v1/ path of each Appendix A row, in table order.
    catalog_names: dict[str, tuple[str, ...]]  # Names of each Appendix B table, keyed by catalog key.
    regional_hosts: tuple[str, ...]  # Each API host of the section 5.5 table, in table order.
    identifier_fields: dict[str, tuple[str, ...]]  # Identifier fields of each family, keyed by its heading.

    @classmethod
    def from_path(cls, path: Path) -> RunbookClaims:  # Parse the runbook once, and fail on an unreadable file.
        """Read the runbook once, and parse each fact that the checks use.

        Why: a missing or unreadable runbook is a configuration fault for the caller to report. The error
        names the file only, so the message never shows the full folder of the user.

        Args:
            path: Runbook file, which is UTF-8 Markdown.

        Returns:
            The parsed facts.

        Raises:
            ValueError: The file cannot be read as UTF-8 text.
        """
        logger.info("Reading the runbook %s", path.name)  # Log before the file read.
        try:  # The read fails for a missing file or for text that is not UTF-8.
            text = path.read_text(encoding="utf-8")  # Read the whole file once.
            tables = MarkdownTables(text)  # Split the text into prose and tables.
            matches = (re.match(r"^(#{1,3}) (.+)$", line) for line in tables.prose_lines)  # Heading candidates.
            headings = tuple((len(m.group(1)), m.group(2).strip()) for m in matches if m is not None)  # Level, text.
            endpoint_paths, regional_hosts = cls._endpoints_and_hosts(tables)  # Appendix A and section 5.5.
        except (OSError, UnicodeDecodeError) as error:  # The file cannot be read as text.
            logger.exception("Runbook %s cannot be read", path.name)  # Keep the traceback for the operator.
            raise ValueError(f"runbook cannot be read: {path.name}") from error  # Name the file only.
        claims = cls(  # Build the facts from the values that were parsed above.
            path=path,  # The file that was read.
            headings=headings,  # Each heading, in order.
            h2_headings=tuple(title for level, title in headings if level == 2),  # Level-2 headings only.
            api_paths=tuple(sorted(set(re.findall(r"/api/v1/[A-Za-z0-9_{}/.\-]*[A-Za-z0-9_}]", text)))),  # Anywhere.
            endpoint_paths=endpoint_paths,  # The first API path of each row.
            catalog_names=cls._catalog_names(tables),  # Names of the Appendix B tables.
            regional_hosts=regional_hosts,  # Each API host of section 5.5.
            identifier_fields=cls._identifier_fields(tables),  # Identifier fields of the family tables.
        )
        logger.debug("Runbook %s parsed with %s headings", path.name, len(headings))  # Log the heading count.
        return claims  # The parsed facts of the runbook.

    @staticmethod
    def _endpoints_and_hosts(  # Read endpoint paths and API hosts from their own tables.
        tables: MarkdownTables,
    ) -> tuple[tuple[str, ...], tuple[str, ...]]:
        """Return the endpoint paths of Appendix A and the API hosts of section 5.5.

        Why: the endpoint paths and the regional hosts are checked against the live Mist cloud and against
        the OpenAPI file. Each one comes from its own table, with the header that the contract names.

        Args:
            tables: Parsed tables of the runbook.

        Returns:
            The endpoint paths in table order, and the API hosts in table order.
        """
        endpoint_rows = tables.rows_after_heading(  # The rows of Appendix A, under the Appendix A heading.
            "Appendix A. Endpoint Reference", ("Method", "Path", "Scope", "Purpose", "Verification")
        )
        regional_rows = tables.rows_after_heading(  # The rows of section 5.5, under its heading.
            "5.5 Regional API Hosts", ("Region", "API host", "Verification")
        )
        paths = tuple(  # The first API path of each row, in table order.
            values[0]
            for values in (RunbookClaims._backticked(" ".join(row), "/api/v1/") for row in endpoint_rows)
            if values
        )
        hosts = tuple(  # The backticked API host of each row, in table order.
            host for row in regional_rows if len(row) > 1 for host in RunbookClaims._backticked(row[1])
        )
        return paths, hosts  # The endpoint paths and the API hosts, each in table order.

    @staticmethod
    def _backticked(  # Pull backticked values, which the contract uses for names.
        text: str, prefix: str = ""
    ) -> tuple[str, ...]:
        """Return the backticked values of a text that start with a prefix.

        Why: the contract names each path, host, and field inside backticks. A cell can hold more than one
        value, so each value is returned in order.

        Args:
            text: Text that can hold backticked values.
            prefix: Only values that start with this text are returned.

        Returns:
            The matching values, in order.
        """
        return tuple(value for value in re.findall(r"`([^`]+)`", text) if value.startswith(prefix))  # Values.

    @staticmethod
    def _catalog_names(  # Read the Appendix B names of each catalog for comparison.
        tables: MarkdownTables,
    ) -> dict[str, tuple[str, ...]]:
        """Return the first backticked name of each row of each Appendix B table.

        Why: each Appendix B table names one catalog key of the live Mist catalog. The smoke test
        compares these names with the catalog, so the names are kept per key.

        Args:
            tables: Parsed tables of the runbook.

        Returns:
            The names per catalog key. A table that is absent gives an empty tuple.
        """
        names: dict[str, tuple[str, ...]] = {}  # Names per catalog key.
        catalog_headings = (  # Each Appendix B heading with its catalog key, in the contract order.
            ("B.1 Alarm Types", "alarm_defs"),
            ("B.2 Device Event Types", "device_events"),
            ("B.3 Mist Edge Event Types", "mxedge_events"),
            ("B.4 System Event Types", "system_events"),
            ("B.5 Webhook Topics", "webhook_topics"),
        )
        for heading, key in catalog_headings:  # Read each table in the contract order.
            rows = tables.rows_after_heading(heading, ("Name", "Use in this runbook"))  # The table under the heading.
            firsts = [RunbookClaims._backticked(row[0]) for row in rows if row]  # Backticked names per row.
            names[key] = tuple(values[0] for values in firsts if values)  # The first name of each row.
        return names  # The names per catalog key.

    @staticmethod
    def _identifier_fields(  # Read identifier fields per family, or none when absent.
        tables: MarkdownTables,
    ) -> dict[str, tuple[str, ...]]:
        """Return the identifier fields of each family table, keyed by the family heading.

        Why: the checks read each family only through its identifier fields. A row that says none gives
        an empty tuple, so no field is expected.

        Args:
            tables: Parsed tables of the runbook.

        Returns:
            The identifier fields per family heading.
        """
        fields: dict[str, tuple[str, ...]] = {}  # Fields per family heading.
        family_headings = (  # The four family headings of the contract.
            "6.1 Alarm Search",
            "6.2 Device Event Search",
            "6.3 Mist Edge Event Search",
            "6.4 System Event Search",
        )
        for heading in family_headings:  # Read each family table.
            rows = tables.rows_after_heading(heading, ("Fact", "Value"))  # The table under the heading.
            values = [row[1] for row in rows if len(row) > 1 and row[0] == "Identifier fields"]  # The field row.
            fields[heading] = RunbookClaims._backticked(values[0]) if values else ()  # Names, or none.
        return fields  # The identifier fields per family heading.


@dataclass(frozen=True)
class OpenApiIndex:  # Hold GET operations and servers, read once from OpenAPI.
    """GET operations and server hosts of one OpenAPI file, read once.

    Why: SMK-02 checks each runbook path against the OpenAPI file. The query names of each operation
    decide which parameters a check may send, so one index serves every check. Create the object with
    from_path.
    """

    path: Path  # OpenAPI file that was read.
    operations: dict[str, tuple[str, list[Any]]]  # Normalized path to (operationId, raw parameter objects).
    references: dict[str, Any]  # Reusable parameter objects, keyed by their $ref text.
    servers: tuple[str, ...]  # Server URLs, in file order.
    placeholder: re.Pattern[str] = field(  # Matches one {...} segment, so that {org_id} and {id} match.
        default=re.compile(r"\{[^{}/]*\}"),
        init=False,
        repr=False,
    )

    @classmethod
    def from_path(cls, path: Path) -> OpenApiIndex:  # Parse the OpenAPI file once, before any request can run.
        """Load the OpenAPI JSON once, and index each GET operation and each server host.

        Why: a missing or invalid file stops the run before any request. The error names the file only.

        Args:
            path: OpenAPI JSON file.

        Returns:
            The index of the file.

        Raises:
            ValueError: The file cannot be read as JSON, or it has no paths object.
        """
        logger.info("Reading the OpenAPI file %s", path.name)  # Log before the file read.
        try:  # The read fails for a missing file, bad text, or invalid JSON.
            document = json.loads(path.read_text(encoding="utf-8"))  # Parse the whole file once.
            if not isinstance(document, dict) or not isinstance(document.get("paths"), dict):  # Needs the paths.
                raise ValueError(f"OpenAPI file has no paths object: {path.name}")  # Stop with a clear message.
            components = document.get("components", {}).get("parameters", {})  # Reusable parameter objects by name.
        except (OSError, json.JSONDecodeError, UnicodeDecodeError) as error:  # The file cannot be read as JSON.
            logger.exception("OpenAPI file %s cannot be read as JSON", path.name)  # Keep the traceback.
            raise ValueError(f"OpenAPI file cannot be read: {path.name}") from error  # Name the file only.
        operations = {  # Normalized path to (operationId, raw parameters) of each GET operation.
            cls.placeholder.sub("{}", template): (
                str(item["get"].get("operationId", "")),
                [*item.get("parameters", []), *item["get"].get("parameters", [])],
            )
            for template, item in document["paths"].items()
            if isinstance(item, dict) and isinstance(item.get("get"), dict)
        }
        logger.debug("OpenAPI file %s indexed with %s GET paths", path.name, len(operations))  # Log the count.
        return cls(  # Build the index from the parsed document.
            path=path,
            operations=operations,  # The file that was read, and the GET operations by path.
            references={f"#/components/parameters/{name}": value for name, value in components.items()},
            servers=tuple(str(s.get("url", "")) for s in document.get("servers", []) if isinstance(s, dict)),
        )

    def has_get(self, path: str) -> bool:  # Normalize placeholders, so names that differ still match.
        """Return True when the path has a GET operation, after each placeholder is normalized.

        Why: a runbook path names its placeholders as {org_id}, while the OpenAPI file can name the same
        segment as {id}. Normalizing each segment makes the two forms match.

        Args:
            path: Path of the runbook, with or without placeholders.

        Returns:
            True when the OpenAPI file has a GET operation at the path.
        """
        return self.placeholder.sub("{}", path) in self.operations  # Compare the normalized forms.

    def query_parameters(self, path: str) -> tuple[str, ...]:  # List query names, so checks send only named parameters.
        """Return the query parameter names of the GET operation at a path.

        Why: the checks send only the parameters that the OpenAPI file names for the operation.

        Args:
            path: Path of the operation, with or without placeholders.

        Returns:
            The names of the query parameters. Empty when the path has no GET operation.
        """
        entry = self.operations.get(self.placeholder.sub("{}", path))  # The indexed operation, if any.
        if entry is None:  # A path without a GET operation has no query names.
            return ()  # No query name exists for a missing operation.
        # Resolve each $ref parameter, and keep only the parameters that travel in the query string.
        resolved = [  # Each parameter, with its $ref resolved to the reusable object.
            {**p, **self.references.get(str(p.get("$ref", "")), {})} for p in entry[1] if isinstance(p, dict)
        ]
        return tuple(  # The query names, without repeats and in order.
            dict.fromkeys(str(p["name"]) for p in resolved if p.get("in") == "query" and "name" in p)
        )

    def operation_id(self, path: str) -> str:  # Return the operationId, so a check can match the SDK name.
        """Return the operationId of the GET operation at a path.

        Why: the operationId names the SDK function of the operation, so a check can compare the two.

        Args:
            path: Path of the operation, with or without placeholders.

        Returns:
            The operationId. Empty when the path has no GET operation.
        """
        entry = self.operations.get(self.placeholder.sub("{}", path))  # The indexed operation, if any.
        return entry[0] if entry is not None else ""  # The identifier, or an empty text.

    def server_hosts(self) -> tuple[str, ...]:  # List server hosts, because only listed hosts are accepted.
        """Return the host names of the servers list, in file order.

        Why: the smoke test accepts a regional host only when the OpenAPI file lists it.

        Returns:
            The unique host names of the servers list.
        """
        hosts = [urlsplit(url).hostname or "" for url in self.servers]  # The host name of each server URL.
        return tuple(dict.fromkeys(host for host in hosts if host))  # Unique host names, in file order.


@dataclass(frozen=True)
class EvidenceRedactor:  # Scrub identifiers and tokens before any value is written.
    """Remove identifiers, tokens, and contact data from evidence values before they are written.

    Why: the evidence record must hold no identifier and no token. The redactor runs on every string of
    the record, so each value that reaches the file has passed the same rules.
    """

    organization_id: str  # Organization identifier, written as org-1.
    site_ids: tuple[str, ...]  # Site identifiers, written as site-1, site-2, and so on.
    token_value: str = field(repr=False)  # Token value, removed wherever it appears. An empty value removes nothing.
    top_level_keys: tuple[str, ...] = field(  # The fourteen top-level keys of the evidence contract.
        default=(
            "schema_version",
            "generated_at",
            "tool",
            "host",
            "organization_label",
            "settings",
            "request_count",
            "request_budget",
            "sdk_retry_possible",
            "outcome_class",
            "exit_code",
            "checks",
            "catalogs",
            "observations",
        ),
        init=False,
        repr=False,
    )
    section_keys: dict[str, tuple[str, ...]] = field(  # The keys of each object section, from the contract.
        default_factory=lambda: {
            "tool": ("name", "module", "version"),
            "settings": (
                "call_timeout_seconds",
                "window_minutes",
                "delay_minutes",
                "max_pages",
                "max_requests",
                "max_retries",
                "site_scope",
                "runbook",
                "openapi",
                "runbook_explicit",
                "env_file_given",
            ),
            "observations": (
                "q1_device_type_default",
                "q2_mist_edge_window",
                "q3_limit_5000",
                "q4_next_form",
                "q5_distinct_type",
                "q6_last_trouble_present",
                "q7_response_headers",
                "q8_alarm_status_values",
                "device_event_types_by_device_type",
            ),
        },
        init=False,
        repr=False,
    )
    check_keys: tuple[str, ...] = field(  # The twelve keys of each check item.
        default=(
            "check_id",
            "title",
            "status",
            "detail",
            "request_count",
            "http_statuses",
            "record_count",
            "page_count",
            "stop_reason",
            "field_names",
            "header_names",
            "retry_after_seconds",
        ),
        init=False,
        repr=False,
    )
    catalog_keys: tuple[str, ...] = field(  # The six catalog names of the evidence contract.
        default=("alarm_defs", "device_events", "mxedge_events", "system_events", "ap_led_status", "webhook_topics"),
        init=False,
        repr=False,
    )
    uuid_pattern: re.Pattern[str] = field(  # UUID in the 8-4-4-4-12 form.
        default=re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.IGNORECASE),
        init=False,
        repr=False,
    )
    mac_pattern: re.Pattern[str] = field(  # MAC address with colons, with dashes, or as twelve hex digits.
        default=re.compile(r"\b(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}\b|\b[0-9a-f]{12}\b", re.IGNORECASE),
        init=False,
        repr=False,
    )
    email_pattern: re.Pattern[str] = field(  # Email address with a local part, an at sign, and a domain.
        default=re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
        init=False,
        repr=False,
    )
    token_word_pattern: re.Pattern[str] = field(  # The word Token, a space, and twenty or more characters.
        default=re.compile(r"\bToken [A-Za-z0-9]{20,}", re.IGNORECASE),
        init=False,
        repr=False,
    )
    token_run_pattern: re.Pattern[str] = field(  # A run of thirty-two or more letters or digits.
        default=re.compile(r"[A-Za-z0-9]{32,}"),
        init=False,
        repr=False,
    )

    def scrub(self, value: Any) -> Any:  # Scrub each string at every depth, since records nest.
        """Replace identifiers and tokens in a value, at every depth of objects and arrays.

        Why: the record holds nested objects and arrays, so each string at each depth is scrubbed. A detail
        text is cut to 200 characters after the replacements, as the contract requires.

        Args:
            value: Any JSON-like value.

        Returns:
            A new value of the same shape, with each string scrubbed.
        """
        if isinstance(value, dict):  # Scrub each key and each value of an object.
            clean: dict[str, Any] = {}  # The scrubbed object.
            for key, item in value.items():  # Each entry of the object.
                scrubbed = self.scrub(item)  # Scrub the value at its own depth.
                if key == "detail" and isinstance(scrubbed, str):  # A detail is kept to 200 characters.
                    scrubbed = scrubbed[:200]  # Cut after the replacements.
                clean[self._scrub_text(str(key))] = scrubbed  # Scrub the key as well as the value.
            return clean  # The scrubbed object.
        if isinstance(value, (list, tuple)):  # Scrub each item of an array.
            return [self.scrub(item) for item in value]  # Each item, scrubbed at its own depth.
        if isinstance(value, str):  # Scrub a text value.
            return self._scrub_text(value)  # The scrubbed text.
        return value  # Numbers, booleans, and null need no scrub.

    def allow(  # Keep allowlisted keys only, so response bodies stay out.
        self, record: dict[str, Any]
    ) -> dict[str, Any]:
        """Keep only the allowlisted keys of the evidence record, and scrub each remaining value.

        Why: the allowlist keeps response bodies out of the file. Each catalog keeps its counts and its items,
        but no item keeps its example member.

        Args:
            record: Evidence record with every key that the run built.

        Returns:
            A new record with the allowed keys only, and with each value scrubbed.
        """
        logger.info("Filtering the evidence record with %s keys", len(record))  # Log before the transform.
        kept = {key: record[key] for key in self.top_level_keys if key in record}  # The top-level allowlist.
        result: dict[str, Any] = self.scrub(self._keep_nested(kept))  # Filter the sections, then scrub each value.
        logger.debug("Filtered evidence record keeps %s top-level keys", len(result))  # Log the result.
        return result  # The filtered and scrubbed record.

    def _keep_nested(  # Filter check items and catalogs to their contract keys.
        self, kept: dict[str, Any]
    ) -> dict[str, Any]:
        """Keep only the allowed keys of each check item, and filter the catalogs.

        Why: each check item is a fixed record of the contract, so it keeps only its own keys. The catalogs
        have their own rule for the example member.

        Args:
            kept: Record after the top-level and section filters.

        Returns:
            The same record with its check items and catalogs filtered.
        """
        for section, allowed in self.section_keys.items():  # Filter each object section with its own keys.
            if isinstance(kept.get(section), dict):  # Only an object section is filtered.
                kept[section] = {key: item for key, item in kept[section].items() if key in allowed}  # Keep allowed.
        if isinstance(kept.get("checks"), list):  # Each check item keeps its own keys.
            kept["checks"] = [  # Only object items are kept, each with its allowed keys.
                {key: item[key] for key in item.keys() & self.check_keys}  # Keys that the item and the allowlist share.
                for item in kept["checks"]
                if isinstance(item, dict)
            ]
        if isinstance(kept.get("catalogs"), dict):  # The catalogs keep their counts and their items.
            kept["catalogs"] = self._keep_catalogs(kept["catalogs"])  # Filter the known catalogs.
        return kept  # The record with its nested values filtered.

    def _keep_catalogs(  # Keep known catalogs, and drop the example field of items.
        self, catalogs: dict[str, Any]
    ) -> dict[str, Any]:
        """Keep the known catalogs, with their counts, and their items without the example member.

        Why: catalog items are generic Mist data, but the example member of each item is never written.

        Args:
            catalogs: The catalogs object of the evidence record.

        Returns:
            The known catalogs, each with the status code, the item count, and the items.
        """
        return {  # One entry for each known catalog that the record holds.
            name: {
                "status_code": entry.get("status_code"),  # The HTTP status of the catalog request.
                "item_count": entry.get("item_count"),  # The number of items in the catalog.
                "items": [  # Each item without its example member.
                    {key: value for key, value in item.items() if key != "example"}
                    for item in entry.get("items", [])
                    if isinstance(item, dict)
                ],
            }
            for name, entry in catalogs.items()
            if name in self.catalog_keys and isinstance(entry, dict)
        }

    def _scrub_text(self, text: str) -> str:  # Replace known values first, so no pattern splits them.
        """Replace the identifiers, the token value, and each token-like or contact pattern.

        Why: the identifiers take their labels first, so the label stays and the value is removed. The
        generic patterns run after the token value, so no later pattern can split a known value.

        Args:
            text: Text to scrub.

        Returns:
            The scrubbed text.
        """
        result = text  # Start the chain from the input text, so each replacement builds on the one before.
        labels = [  # Identifiers and the token value, each with its replacement text, in the contract order.
            (self.organization_id, "org-1"),
            *((site_id, f"site-{number}") for number, site_id in enumerate(self.site_ids, start=1)),
            (self.token_value, "[redacted]"),
        ]
        for identifier, label in labels:  # Replace each identifier and the token value, in any letter case.
            if not identifier:  # An empty value would match everywhere, so it is skipped.
                continue  # Nothing to replace for an empty value.
            for variant in (identifier, identifier.replace("-", "")):  # The form with hyphens and without.
                result = re.sub(re.escape(variant), label, result, flags=re.IGNORECASE)  # Replace the variant.
        for pattern in (  # Token-like and contact patterns, in the contract order.
            self.uuid_pattern,
            self.mac_pattern,
            self.email_pattern,
            self.token_word_pattern,
            self.token_run_pattern,
        ):
            result = pattern.sub("[redacted]", result)  # Replace each match with the marker.
        return result  # The scrubbed text.


@dataclass(frozen=True)
class EvidenceWriter:  # Write the evidence file in fixed form, for plain diffs.
    """Write one evidence record as UTF-8 JSON with sorted keys and a final newline.

    Why: the evidence file is the only output of the smoke test. A fixed encoding, sorted keys, and a final
    newline let two runs be compared with a plain text diff.
    """

    output_path: Path  # File to write. Its parent folder is created when it is missing.

    def write(self, record: dict[str, Any]) -> Path:  # Write only a record that the allowlist has filtered.
        """Write the record, and return the path of the written file.

        Why: the record must already be filtered by EvidenceRedactor.allow, so this method writes only what
        the allowlist kept.

        Args:
            record: Evidence record to write.

        Returns:
            The path of the written file.

        Raises:
            ValueError: The record is not an object.
            OSError: The file or its folder cannot be written.
        """
        text = self._serialize(record)  # Validate the record and encode it before any file is touched.
        logger.info("Writing the evidence file %s", self.output_path.name)  # Log before the file write.
        self._store(text)  # Create the folder and write the UTF-8 text.
        logger.debug("Wrote %s characters to the evidence file %s", len(text), self.output_path.name)  # Log result.
        return self.output_path  # The path of the written file.

    @staticmethod
    def _serialize(record: dict[str, Any]) -> str:  # Encode the record in fixed form, so runs compare as text.
        """Return the record as UTF-8 JSON text with sorted keys and a final newline.

        Why: the sorted keys and the final newline let two runs be compared with a plain text diff.

        Args:
            record: Evidence record to encode.

        Returns:
            The JSON text of the record.

        Raises:
            ValueError: The record is not an object.
        """
        if not isinstance(record, dict):  # Validate the input before any file is touched.
            raise ValueError("evidence record must be an object")  # Refuse the value before any write.
        return json.dumps(record, sort_keys=True, indent=2, ensure_ascii=False) + "\n"  # Sorted keys, final newline.

    def _store(self, text: str) -> None:  # Create the parent folder, so a new run does not fail.
        """Create the parent folder of the output path and write the text to the file.

        Why: the operator sees the evidence file in its folder, so the folder is created when it is missing.

        Args:
            text: JSON text to write.

        Raises:
            OSError: The file or its folder cannot be written.
        """
        self.output_path.parent.mkdir(parents=True, exist_ok=True)  # Create the folder that holds the file.
        self.output_path.write_text(text, encoding="utf-8")  # Write the UTF-8 text.

    @staticmethod
    def default_path(  # Name the file in UTC, without colons that Windows rejects.
        output_root: Path, moment: datetime
    ) -> Path:
        """Return the default evidence path for one moment, named in UTC as YYYYMMDDTHHMMSSZ.

        Why: the UTC name sorts in time order, and a colon is not valid in a Windows file name, so the
        name has no colons.

        Args:
            output_root: Repository root that holds the test-artifacts folder.
            moment: Time of the run. It must have a time zone.

        Returns:
            The default path under test-artifacts/netcool-runbook-smoke/.

        Raises:
            ValueError: The moment has no time zone.
        """
        if moment.tzinfo is None:  # A naive time has no known offset, so it cannot be named in UTC.
            raise ValueError("moment must have a time zone")  # Refuse the naive time.
        utc_moment = moment.astimezone(UTC)  # Convert the moment to UTC.
        stamp = utc_moment.strftime("%Y%m%dT%H%M%SZ")  # The file-name form of the UTC time.
        return output_root / "test-artifacts" / "netcool-runbook-smoke" / f"{stamp}.json"  # The default path.
