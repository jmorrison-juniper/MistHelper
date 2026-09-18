"""Fact extractor classes for Juniper source segments."""

from __future__ import annotations  # Keep annotations cheap during factory imports.

import logging  # Record extractor actions for factory observability.
import re  # Mine deterministic fact patterns from Markdown source.
from abc import ABC, abstractmethod  # Define the extractor interface.

from src.juniper_skills.rewrite import CardClassMark  # Use the locked card classes.

from .models import ExtractedFact, SourceLine  # Share extraction records.


class FactExtractor(ABC):
    """Interface for one deterministic fact class extractor."""

    fact_type = "fact"  # Give subclasses a stable default fact type.

    def extract(self, lines: tuple[SourceLine, ...], source_key: str) -> tuple[ExtractedFact, ...]:
        """Return candidate facts for one source document."""
        logging.info("Running %s", self.__class__.__name__)  # Log before extractor work starts.
        facts = tuple(self._extract(lines, source_key))  # Run the concrete extractor implementation.
        logging.debug("%s emitted %d facts", self.__class__.__name__, len(facts))  # Log the fact count.
        return facts  # Return immutable facts for the engine.

    @abstractmethod
    def _extract(self, lines: tuple[SourceLine, ...], source_key: str) -> list[ExtractedFact]:
        """Return candidate facts for the concrete fact class."""

    def _fact(self, mark: CardClassMark, fact: str, line: SourceLine, source_key: str) -> ExtractedFact:
        """Return one candidate fact with a precise page citation."""
        citation = f"[{source_key} p.{line.page}]"  # Build the exact citation string.
        span = line.text[:160]  # Keep a bounded source span for dedup priority only.
        return ExtractedFact(self.fact_type, mark, fact, citation, span)  # Return the candidate fact.

    def _mark_for(self, text: str) -> CardClassMark:
        """Return the required card class from source language."""
        lowered = text.lower()  # Normalize modal words for classification.
        if re.search(r"\b(must|cannot|required|requires|do not|only|never)\b", lowered):  # Find hard rules.
            return CardClassMark.MUST  # Mark source requirements as mandatory cards.
        if re.search(r"\b(should|recommend|recommended|best practice)\b", lowered):  # Find advice language.
            return CardClassMark.SHOULD  # Mark recommendations as SHOULD cards.
        return CardClassMark.INFO  # Mark plain facts as informational cards.

    def _snippet(self, text: str, size: int = 4) -> str:
        """Return a short source phrase that stays below the guard clear line."""
        words = re.findall(r"[A-Za-z][A-Za-z0-9._/-]*", text)  # Keep technical words in source order.
        return " ".join(words[:size])  # Limit copied prose so adjacent cards stay below the warning band.


class CommandFactExtractor(FactExtractor):
    """Extract Junos commands and their visible arguments."""

    fact_type = "command"  # Name command facts for dedup keys.

    def _extract(self, lines: tuple[SourceLine, ...], source_key: str) -> list[ExtractedFact]:
        facts: list[ExtractedFact] = []  # Collect command facts in source order.
        for line in lines:  # Check every page-tagged source line.
            command = self._command(line.text)  # Find a CLI command or configuration command.
            if command:  # Only command-like lines create command facts.
                facts.extend(self._command_facts(command, line, source_key))  # Emit command and argument facts.
        return facts  # Return command facts for the engine.

    def _command(self, text: str) -> str:
        """Return the command text from one source line, or an empty string."""
        stripped = text.strip().strip("`")  # Remove Markdown edge code marks without changing the command.
        prompt_match = re.match(
            r"(?:[\w.-]+@[\w.-]+[>#]\s*)?((?:show|set|delete|edit|run|commit|request|clear|ping|traceroute)\b.+)",
            stripped,
        )  # Detect CLI.
        if prompt_match:  # Prompt lines carry the command after the prompt.
            return self._safe_command(prompt_match.group(1).strip())  # Keep only command-shaped text.
        return ""  # Return no command for ordinary prose.

    def _safe_command(self, command: str) -> str:
        """Return command text only when the line is not prose."""
        if re.search(r",\s+(and|or)\s+|\.\s+If\b|\bcommands?\.\s+If\b", command):  # Detect prose lists.
            return ""  # Do not preserve a prose sentence as a command.
        if command.startswith("set ") and not re.match(
            r"set\s+(interfaces|protocols|routing-options|policy-options|security|vlans|groups|switch-options|forwarding-options|system|class-of-service)\b",
            command,
        ):  # Validate set roots.
            return ""  # Reject prose that starts with the verb set.
        return command  # Return the command when it passes the prose filters.

    def _command_facts(self, command: str, line: SourceLine, source_key: str) -> list[ExtractedFact]:
        """Return command and argument cards for one command line."""
        fact = f"Use command `{command}` exactly as shown by the source."  # Preserve the full command verbatim.
        facts = [self._fact(CardClassMark.INFO, fact, line, source_key)]  # Emit the command card first.
        for token in self._argument_tokens(command):  # Add the visible options and arguments.
            detail = f"Command `{command}` includes argument `{token}`."  # Preserve each argument exactly.
            facts.append(self._fact(CardClassMark.INFO, detail, line, source_key))  # Add the argument fact.
        return facts  # Return all facts for the command line.

    def _argument_tokens(self, command: str) -> tuple[str, ...]:
        """Return visible command options and arguments."""
        tokens = tuple(part for part in command.split()[1:] if self._is_argument(part))  # Keep non-verb tokens.
        return tokens[:12]  # Bound one very long line while keeping every useful prefix token.

    def _is_argument(self, token: str) -> bool:
        """Return whether one token is useful as a command argument."""
        return bool(re.search(r"[-_/{}=*.:0-9A-Za-z]", token) and token not in {"|", ">"})  # Drop separators.


class ConfigurationFactExtractor(FactExtractor):
    """Extract configuration statements and hierarchy paths."""

    fact_type = "configuration"  # Name configuration facts for dedup keys.

    def _extract(self, lines: tuple[SourceLine, ...], source_key: str) -> list[ExtractedFact]:
        facts: list[ExtractedFact] = []  # Collect configuration facts in source order.
        for line in lines:  # Check every page-tagged source line.
            statement = self._statement(line.text)  # Find a configuration statement.
            if statement:  # Only configuration-like lines create cards.
                facts.append(self._configuration_fact(statement, line, source_key))  # Store the statement and path.
        return facts  # Return configuration facts for the engine.

    def _statement(self, text: str) -> str:
        """Return a configuration statement from one source line."""
        stripped = text.strip().strip("`")  # Remove Markdown code edges while preserving inner syntax.
        if re.match(r"^(set|delete|deactivate|activate)\s+", stripped):  # Detect flat Junos config syntax.
            return stripped  # Keep the full statement exactly.
        if re.match(r"^[a-z][a-z0-9-]+(\s+[a-z0-9_.:/-]+)*\s*[;{]$", stripped):  # Detect hierarchy syntax.
            return stripped  # Keep the hierarchy statement exactly.
        return ""  # Return no configuration statement for ordinary lines.

    def _configuration_fact(self, statement: str, line: SourceLine, source_key: str) -> ExtractedFact:
        """Return one configuration card with the hierarchy path."""
        path = " ".join(statement.replace(";", "").replace("{", "").split()[:6])  # Preserve the visible path prefix.
        fact = f"Configure hierarchy `{path}` with statement `{statement}`."  # State the path and syntax.
        return self._fact(CardClassMark.INFO, fact, line, source_key)  # Return the configuration fact.


class NumericFactExtractor(FactExtractor):
    """Extract numeric limits, defaults, ranges, timers, and thresholds."""

    fact_type = "numeric"  # Name numeric facts for dedup keys.
    _PATTERN = re.compile(
        r"\b(?:default|range|timer|threshold|limit|maximum|minimum)?\s*\d+(?:\.\d+)?(?:\s*(?:VLANs|MACs|routes|bytes|seconds|minutes|hours|days|Gbps|Mbps|kbps|dBm|dB|ms|sec|%|V|W|A))?",
        re.IGNORECASE,
    )  # Find numeric facts.

    def _extract(self, lines: tuple[SourceLine, ...], source_key: str) -> list[ExtractedFact]:
        facts: list[ExtractedFact] = []  # Collect numeric facts in source order.
        for line in lines:  # Check every page-tagged source line.
            for match in self._PATTERN.finditer(line.text):  # Emit each numeric instance on the line.
                facts.append(self._numeric_fact(match.group(0).strip(), line, source_key))  # Store one value fact.
        return facts  # Return numeric facts for the engine.

    def _numeric_fact(self, value: str, line: SourceLine, source_key: str) -> ExtractedFact:
        """Return one numeric card with a short context."""
        context = self._snippet(line.text)  # Keep copied prose below the clear threshold.
        fact = f"Numeric value `{value}` applies in source context {context}."  # Preserve the value.
        return self._fact(self._mark_for(line.text), fact, line, source_key)  # Return the numeric fact.


class TableRowFactExtractor(FactExtractor):
    """Extract one fact for each Markdown table row."""

    fact_type = "table-row"  # Name table row facts for dedup keys.

    def _extract(self, lines: tuple[SourceLine, ...], source_key: str) -> list[ExtractedFact]:
        facts: list[ExtractedFact] = []  # Collect table facts in source order.
        headers: dict[int, tuple[str, ...]] = {}  # Track the last header for each source page.
        for line in lines:  # Walk in order so each body row receives the active header.
            headers = self._headers(headers, line)  # Update headers when the line is a table header.
            fact = self._row_fact(headers.get(line.page, tuple()), line, source_key)  # Try to emit a row fact.
            if fact:  # Divider rows and headers do not create body facts.
                facts.append(fact)  # Store the table row as one fact.
        return facts  # Return table row facts for the engine.

    def _headers(self, headers: dict[int, tuple[str, ...]], line: SourceLine) -> dict[int, tuple[str, ...]]:
        """Return updated table headers after one line."""
        if self._is_table(line.text) and not self._is_divider(line.text):  # A table line can be a header or a row.
            cells = self._cells(line.text)  # Split Markdown cells.
            if line.page not in headers:  # The first table row on a page is the header.
                headers[line.page] = cells  # Store the page-local header.
        if not self._is_table(line.text):  # Non-table content ends the page-local table header.
            headers.pop(line.page, None)  # Avoid applying one table header to a later table.
        return headers  # Return the mutable header map for the next line.

    def _row_fact(self, headers: tuple[str, ...], line: SourceLine, source_key: str) -> ExtractedFact | None:
        """Return a row fact when one table body row exists."""
        if not headers or not self._is_table(line.text) or self._is_divider(line.text):  # Require a real body row.
            return None  # Skip non-row lines.
        cells = self._cells(line.text)  # Split the current table row.
        if cells == headers:  # The header row is structure, not a fact.
            return None  # Do not duplicate the header as data.
        pairs = self._pairs(headers, cells)  # Attach each cell to its header.
        fact = "Table row states " + ", ".join(pairs) + "."  # Restate row data as structured facts.
        return self._fact(CardClassMark.INFO, fact, line, source_key)  # Return the table row fact.

    def _cells(self, text: str) -> tuple[str, ...]:
        """Return non-empty Markdown table cells."""
        return tuple(cell.strip() for cell in text.strip().strip("|").split("|") if cell.strip())  # Keep cells.

    def _is_divider(self, text: str) -> bool:
        """Return whether a table line is a Markdown divider."""
        return bool(re.match(r"^\s*\|?\s*:?-{3,}", text))  # Detect divider rows.

    def _is_table(self, text: str) -> bool:
        """Return whether a line is a Markdown table row."""
        return text.strip().startswith("|") and text.strip().endswith("|")  # Detect table syntax.

    def _pairs(self, headers: tuple[str, ...], cells: tuple[str, ...]) -> tuple[str, ...]:
        """Return header and value pairs for one row."""
        count = min(len(headers), len(cells))  # Avoid index errors on uneven PDF tables.
        return tuple(self._pair(headers[index], cells[index]) for index in range(count))  # Preserve safe cells.

    def _pair(self, header: str, cell: str) -> str:
        """Return one safe table header and value pair."""
        value = self._safe_cell(cell)  # Shorten prose cells without changing identifiers.
        return f"`{header}` is {value}"  # Preserve the header and safe cell value.

    def _safe_cell(self, cell: str) -> str:
        """Return a safe table cell value for publication."""
        words = re.findall(r"[A-Za-z]+", cell)  # Count prose words to avoid copied sentences.
        if len(words) > 7:  # Long table descriptions are protected prose.
            return self._snippet(cell)  # Restate long cells as a short clear-band phrase.
        return f"`{cell}`"  # Keep short cells exact because they are structured data.


class OutputFieldFactExtractor(FactExtractor):
    """Extract output fields and short meanings from tables and lists."""

    fact_type = "output-field"  # Name output field facts for dedup keys.

    def _extract(self, lines: tuple[SourceLine, ...], source_key: str) -> list[ExtractedFact]:
        facts: list[ExtractedFact] = []  # Collect output field facts in source order.
        for line in lines:  # Check every line for field definitions.
            field = self._field(line.text)  # Try to find a field and meaning pair.
            if field:  # Only detected fields create cards.
                facts.append(self._field_fact(field, line, source_key))  # Store the field meaning.
        return facts  # Return output field facts for the engine.

    def _field(self, text: str) -> tuple[str, str] | None:
        """Return one output field and meaning pair."""
        table = [cell.strip() for cell in text.strip().strip("|").split("|") if cell.strip()]  # Split possible cells.
        if len(table) >= 2 and re.search(r"\b(field|description|meaning)\b", text, re.IGNORECASE):  # Detect tables.
            return table[0], self._snippet(table[1])  # Keep the meaning below the clear threshold.
        match = re.match(r"^\s*`?([A-Za-z][\w./-]{1,40})`?\s+[-:]\s+(.+)$", text.strip())  # Detect list fields.
        if match:  # A bullet or definition list can define an output field.
            return match.group(1), self._snippet(match.group(2))  # Return a short meaning phrase.
        return None  # Return no field for ordinary prose.

    def _field_fact(self, field: tuple[str, str], line: SourceLine, source_key: str) -> ExtractedFact:
        """Return one output field card."""
        fact = f"Output field `{field[0]}` means {field[1]} in this source."  # Preserve field and meaning.
        return self._fact(CardClassMark.INFO, fact, line, source_key)  # Return the output field fact.


class ConstraintFactExtractor(FactExtractor):
    """Extract caveats, warnings, restrictions, and failure modes."""

    fact_type = "constraint"  # Name constraint facts for dedup keys.
    _SIGNAL = re.compile(
        r"\b(must|cannot|do not|only|requires|required|if you do not|warning|caution|fails?|failure)\b", re.IGNORECASE
    )  # Find constraints.

    def _extract(self, lines: tuple[SourceLine, ...], source_key: str) -> list[ExtractedFact]:
        facts: list[ExtractedFact] = []  # Collect constraint facts in source order.
        for line in lines:  # Check every line for required behavior.
            if self._SIGNAL.search(line.text):  # A signal word marks a possible caveat or failure.
                facts.append(self._constraint_fact(line, source_key))  # Store the hard rule or caveat.
        return facts  # Return constraint facts for the engine.

    def _constraint_fact(self, line: SourceLine, source_key: str) -> ExtractedFact:
        """Return one constraint card."""
        context = self._snippet(line.text)  # Keep copied prose below the clear threshold.
        fact = f"Constraint applies to source context {context}. Read the cited page before action."  # Restate.
        return self._fact(self._mark_for(line.text), fact, line, source_key)  # Return the classified constraint.


class PrerequisiteFactExtractor(FactExtractor):
    """Extract prerequisites and ordering requirements."""

    fact_type = "prerequisite"  # Name prerequisite facts for dedup keys.
    _SIGNAL = re.compile(
        r"\b(before|after|prerequisite|prior to|first|then|requires|required)\b", re.IGNORECASE
    )  # Find ordering.

    def _extract(self, lines: tuple[SourceLine, ...], source_key: str) -> list[ExtractedFact]:
        facts: list[ExtractedFact] = []  # Collect prerequisite facts in source order.
        for line in lines:  # Check every line for ordering language.
            if self._SIGNAL.search(line.text):  # Ordering words create a prerequisite card.
                facts.append(self._ordering_fact(line, source_key))  # Store one prerequisite fact.
        return facts  # Return prerequisite facts for the engine.

    def _ordering_fact(self, line: SourceLine, source_key: str) -> ExtractedFact:
        """Return one ordering card."""
        context = self._snippet(line.text)  # Keep copied prose below the clear threshold.
        fact = f"Ordering requirement applies to source context {context}."  # Restate the ordering signal.
        return self._fact(self._mark_for(line.text), fact, line, source_key)  # Return the classified fact.


class DefinitionFactExtractor(FactExtractor):
    """Extract definitions of terms."""

    fact_type = "definition"  # Name definition facts for dedup keys.

    def _extract(self, lines: tuple[SourceLine, ...], source_key: str) -> list[ExtractedFact]:
        facts: list[ExtractedFact] = []  # Collect definition facts in source order.
        for line in lines:  # Check every line for term definitions.
            term = self._definition(line.text)  # Try to parse a term and a short meaning.
            if term:  # Only definition-shaped text creates cards.
                facts.append(self._definition_fact(term, line, source_key))  # Store one definition fact.
        return facts  # Return definition facts for the engine.

    def _definition(self, text: str) -> tuple[str, str] | None:
        """Return a term and short meaning from one line."""
        match = re.match(
            r"^\s*(?:[-*]\s*)?`?([A-Z][A-Za-z0-9 /_-]{1,50})`?\s+(?:is|are|refers to|means)\s+(.+)$", text.strip()
        )  # Detect definitions.
        if not match:  # Most lines are not term definitions.
            return None  # Return no definition.
        return match.group(1).strip(), self._snippet(match.group(2))  # Keep the term exact and meaning short.

    def _definition_fact(self, term: tuple[str, str], line: SourceLine, source_key: str) -> ExtractedFact:
        """Return one definition card."""
        fact = f"Term `{term[0]}` means {term[1]} in this source."  # Preserve the term and a short meaning.
        return self._fact(CardClassMark.INFO, fact, line, source_key)  # Return the definition fact.


class PlatformReleaseFactExtractor(FactExtractor):
    """Extract platform and release qualifiers."""

    fact_type = "platform-release"  # Name platform and release facts for dedup keys.
    _PATTERN = re.compile(
        r"\b(on|for|from|starting in|introduced in)\s+"
        r"((?:Junos\s+OS\s+)?\d+\.\d+[A-Za-z0-9.-]*|[A-Z]{2,6}\s+Series|"
        r"EX\d{4}|QFX\d{4}|SRX\d{3,4}|MX\d{3,4})",
        re.IGNORECASE,
    )  # Find qualifiers.

    def _extract(self, lines: tuple[SourceLine, ...], source_key: str) -> list[ExtractedFact]:
        facts: list[ExtractedFact] = []  # Collect platform and release facts in source order.
        for line in lines:  # Check every line for platform and release text.
            for match in self._PATTERN.finditer(line.text):  # Emit each qualifier instance.
                facts.append(self._qualifier_fact(match.group(0), line, source_key))  # Store the qualifier fact.
        return facts  # Return platform and release facts for the engine.

    def _qualifier_fact(self, qualifier: str, line: SourceLine, source_key: str) -> ExtractedFact:
        """Return one qualifier card."""
        context = self._snippet(line.text)  # Keep copied prose below the clear threshold.
        fact = f"Qualifier `{qualifier}` scopes source context {context}."  # Preserve the qualifier.
        return self._fact(CardClassMark.INFO, fact, line, source_key)  # Return the qualifier fact.
