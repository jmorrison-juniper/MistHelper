"""Inventory builder for the Juniper documentation skill factory."""

from __future__ import annotations  # Permit modern collection hints without runtime cost.

import hashlib  # Compute content hashes for incremental requeue detection.
import logging  # Provide required action logging for each inventory step.
import re  # Detect converter split suffixes in file names.
import sqlite3  # Persist the factory queue in the locked SQLite store.
from collections import defaultdict  # Accumulate part and document groups by natural keys.
from pathlib import Path  # Use cross-platform paths for every filesystem path.

from src.juniper_skills.inventory.metadata import (
    FrontMatterParser,
    HarvesterMetadataLoader,
    TextKey,
)  # Reuse metadata readers.
from src.juniper_skills.inventory.models import (
    DocumentGroup,
    DuplicateDecision,
    InventoryResult,
    MarkdownPart,
    SourceRoot,
)  # Share typed inventory records across the package.


class CorpusScanner:
    """Scan growing source roots into physical Markdown parts."""

    def __init__(self, roots: list[SourceRoot], metadata: HarvesterMetadataLoader) -> None:
        self.roots = roots  # Keep the locked root list for repeatable scans.
        self.metadata = metadata  # Reuse the authoritative harvester metadata reader.
        self.parser = FrontMatterParser()  # Parse front matter with one shared parser.

    def scan(self) -> list[MarkdownPart]:
        logging.info("Starting corpus scan across %s roots", len(self.roots))  # Log scan start with root count.
        catalog = self.metadata.load_catalog()  # Load titles, categories, pages, and source PDF values.
        statuses = self.metadata.load_manifest_statuses()  # Load ok and review statuses from manifests.
        parts = self._scan_roots(catalog, statuses)  # Convert physical Markdown files into part records.
        logging.debug("Corpus scan found %s Markdown parts", len(parts))  # Report physical file count.
        return parts

    def _scan_roots(self, catalog: dict[str, dict[str, str]], statuses: dict[str, str]) -> list[MarkdownPart]:
        parts: list[MarkdownPart] = []  # Accumulate records from all available roots.
        for root in self.roots:  # Scan each locked source root independently.
            logging.info("Scanning source root %s", root.path)  # Log root access before discovery.
            found = self._scan_root(root, catalog, statuses) if root.path.exists() else []  # Missing roots are allowed.
            parts.extend(found)  # Keep all physical files because duplicate resolution happens later.
            logging.debug("Source root %s produced %s parts", root.name, len(found))  # Report per-root count.
        return parts

    def _scan_root(
        self,
        root: SourceRoot,
        catalog: dict[str, dict[str, str]],
        statuses: dict[str, str],
    ) -> list[MarkdownPart]:
        markdown_paths = sorted(
            path for path in root.path.rglob("*.md") if self._is_source_markdown(path)
        )  # Find inputs.
        parts = [self._read_part(root, path, catalog, statuses) for path in markdown_paths]  # Read metadata and hash.
        logging.debug("Read %s source Markdown files from %s", len(parts), root.name)  # Report root inventory count.
        return parts

    def _is_source_markdown(self, path: Path) -> bool:
        is_report = path.name.startswith("_")  # Exclude harvester reports and manifests from source parts.
        return not is_report  # Only document Markdown files enter the factory inventory.

    def _read_part(
        self,
        root: SourceRoot,
        path: Path,
        catalog: dict[str, dict[str, str]],
        statuses: dict[str, str],
    ) -> MarkdownPart:
        logging.info("Reading Markdown part %s", path)  # Log each file read before disk access.
        raw = path.read_bytes()  # Read bytes once so the content hash sees exact converter output.
        text = raw.decode("utf-8", errors="ignore")  # Decode with replacement so inventory survives bad glyphs.
        front_matter = self.parser.parse_text(text)  # Extract authoritative converter metadata when it exists.
        relative_path = path.relative_to(root.path).as_posix()  # Store a stable path independent of Windows separators.
        catalog_row = self._catalog_for(relative_path, front_matter, catalog)  # Attach harvester metadata.
        status = self._status_for(front_matter, catalog_row, statuses)  # Attach manifest review or ok status.
        body = self.parser.body_text(text)  # Measure skill input yield without front matter.
        part_key = f"{root.name}:{relative_path}"  # Use root and path as a natural physical key.
        content_hash = hashlib.sha256(raw).hexdigest()  # Detect reconverted files by exact content hash.
        part = MarkdownPart(
            part_key, root, path, relative_path, content_hash, len(raw), len(body), front_matter, catalog_row, status
        )  # Build the immutable record.
        logging.debug("Read part %s with %s bytes", part.part_key, part.size_bytes)  # Report the file size.
        return part

    def _catalog_for(
        self,
        relative_path: str,
        front_matter: dict[str, str],
        catalog: dict[str, dict[str, str]],
    ) -> dict[str, str]:
        keys = [relative_path, front_matter.get("source_file", ""), Path(relative_path).stem]  # Try precise keys first.
        for key in keys:  # Return the first catalog row that matches the part.
            row = catalog.get(TextKey.normalize(key)) if key else None  # Normalize the candidate key.
            if row:  # Stop when authoritative metadata exists.
                return row
        return {}

    def _status_for(self, front_matter: dict[str, str], catalog_row: dict[str, str], statuses: dict[str, str]) -> str:
        keys = [catalog_row.get("source_pdf", ""), front_matter.get("source_file", "")]  # Match manifest source keys.
        for key in keys:  # Prefer catalog source because it is authored by the harvester.
            status = statuses.get(TextKey.normalize(key)) if key else None  # Look up normalized manifest status.
            if status:  # Return the authoritative manifest status.
                return status
        return "unknown"


class PartSetGrouper:
    """Group physical parts that belong to one source document."""

    _hash_suffix = re.compile(r"-[0-9a-f]{8,16}(?:-\d+)?$", re.IGNORECASE)  # Detect converter hash suffixes.
    _number_suffix = re.compile(r"-\d+$")  # Detect numbered split suffixes.
    _part_name = re.compile(r"^part-\d+$", re.IGNORECASE)  # Detect part folders from large PDFs.

    def group(self, parts: list[MarkdownPart]) -> list[DocumentGroup]:
        logging.info("Grouping %s Markdown parts into documents", len(parts))  # Log grouping before computation.
        buckets: dict[str, list[MarkdownPart]] = defaultdict(list)  # Store part sets by measured grouping key.
        methods: dict[str, str] = {}  # Preserve the evidence type used for each group.
        for part in parts:  # Assign each part with the contract priority order.
            key, method = self._initial_part_key(part)  # First use exact source_file evidence.
            buckets[key].append(part)  # Add the physical part to its logical document bucket.
            methods[key] = method  # Record why this part joined the bucket.
        groups = self._merge_split_groups(buckets, methods)  # Merge measured split sets after exact grouping.
        logging.debug(
            "Grouped parts into %s document candidates", len(groups)
        )  # Report logical count before duplicates.
        return groups

    def _initial_part_key(self, part: MarkdownPart) -> tuple[str, str]:
        source_file = part.front_matter.get(
            "source_file", ""
        )  # Contract says shared source_file is strongest evidence.
        if source_file:  # Use exact source_file before weaker title or filename evidence.
            return f"{part.root.name}:source:{TextKey.normalize(source_file)}", "source_file"
        title = part.front_matter.get("title", "")  # Title is the second contract signal for split outputs.
        if title:  # Use title when no source file exists.
            return f"{part.root.name}:title:{TextKey.normalize(title)}", "title"
        stem = self._similar_stem(part.path)  # Fall back to suffix-aware filename similarity.
        return f"{part.root.name}:stem:{part.path.parent.as_posix()}:{stem}", "filename"

    def _merge_split_groups(
        self, buckets: dict[str, list[MarkdownPart]], methods: dict[str, str]
    ) -> list[DocumentGroup]:
        groups = [self._make_group(key, value, methods[key]) for key, value in buckets.items()]  # Build exact groups.
        split_keys = {
            self._split_merge_key(group) for group in groups if self._is_split_candidate(group)
        }  # Find splits.
        merged: dict[str, list[MarkdownPart]] = defaultdict(list)  # Store merged split part lists.
        group_methods: dict[str, str] = {}  # Preserve grouping evidence for merged groups.
        for group in groups:  # Merge only groups with measured split evidence.
            key = self._split_merge_key(group) if self._split_merge_key(group) in split_keys else group.group_key
            merged[key].extend(group.parts)  # Add exact group parts to the final group.
            group_methods[key] = "title" if key in split_keys else group.group_method  # State split merge evidence.
        return [self._make_group(key, value, group_methods[key]) for key, value in merged.items()]

    def _split_merge_key(self, group: DocumentGroup) -> str:
        first = group.parts[0]  # Use the first part because exact groups already share source evidence.
        title = TextKey.normalize(group.title)  # Title is the contract's second split signal.
        source = first.front_matter.get("source_file") or first.relative_path  # Use source name when available.
        stem = self._similar_stem(Path(source))  # Remove split suffixes for merge comparison.
        return f"{group.root.name}:split:{title}:{stem}"  # Keep split merges inside one source root.

    def _is_split_candidate(self, group: DocumentGroup) -> bool:
        return any(self._part_has_split_signal(part) for part in group.parts)  # Merge only measured split candidates.

    def _part_has_split_signal(self, part: MarkdownPart) -> bool:
        source = part.front_matter.get("source_file", "")  # Read the converter source file signal.
        has_part_field = bool(part.front_matter.get("part"))  # Part front matter is direct split evidence.
        return has_part_field or self._has_number_suffix(source) or self._has_number_suffix(part.relative_path)

    def _make_group(self, key: str, parts: list[MarkdownPart], method: str) -> DocumentGroup:
        first = parts[0]  # Use the first part as a deterministic source for shared metadata.
        title = self._title_for(parts)  # Prefer front matter title, then catalog title, then file stem.
        category = first.catalog.get("category") or self._category_for(first)  # Use catalog category when available.
        source_pdf = self._source_pdf_for(parts)  # Preserve source PDF evidence for duplicate detection.
        pages = self._pages_for(parts)  # Sum or read page count from authoritative metadata.
        status = self._status_for(parts)  # Keep review status if any part requires review.
        return DocumentGroup(key, title, category, source_pdf, first.root, parts, pages, status, method)

    def _title_for(self, parts: list[MarkdownPart]) -> str:
        for part in parts:  # Prefer a converter title because it ties split parts together.
            title = part.front_matter.get("title") or part.catalog.get(
                "title"
            )  # Read both authoritative metadata sources.
            if title:  # Return the first useful title.
                return title
        return parts[0].path.stem.replace("-", " ").title()  # Fall back to a readable file stem.

    def _category_for(self, part: MarkdownPart) -> str:
        return (
            Path(part.relative_path).parts[0] if Path(part.relative_path).parts else "uncategorized"
        )  # Use first folder.

    def _source_pdf_for(self, parts: list[MarkdownPart]) -> str:
        for part in parts:  # Prefer catalog source PDF for the document.
            source_pdf = part.catalog.get("source_pdf") or part.front_matter.get(
                "source_file"
            )  # Use measured metadata.
            if source_pdf:  # Return the first available source name.
                return source_pdf
        return parts[0].relative_path  # Use the Markdown path when no PDF evidence exists.

    def _pages_for(self, parts: list[MarkdownPart]) -> int:
        values = [
            self._int_value(part.catalog.get("pages") or part.front_matter.get("pages")) for part in parts
        ]  # Read pages.
        return max(values) if values else 0  # Split parts often repeat the source page count.

    def _status_for(self, parts: list[MarkdownPart]) -> str:
        return "review" if any(part.manifest_status == "review" for part in parts) else "ok"  # Review wins over ok.

    def _int_value(self, value: str | None) -> int:
        try:
            return int(value or "0")  # Convert missing metadata into zero pages.
        except ValueError:
            return 0  # Keep inventory running when a converter writes a bad page value.

    def _similar_stem(self, path: Path) -> str:
        stem = path.stem  # Start with the file name without extension.
        stem = self._hash_suffix.sub("", stem)  # Remove converter hash suffixes that identify split parts.
        stem = self._number_suffix.sub("", stem)  # Remove numeric suffixes such as "-2".
        return "part-set" if self._part_name.match(path.stem) else TextKey.normalize(stem)  # Normalize the final key.

    def _has_split_suffix(self, value: str) -> bool:
        stem = Path(value).stem  # Inspect only the source file name.
        return bool(self._hash_suffix.search(stem) or self._number_suffix.search(stem))  # Detect a split-like suffix.

    def _has_number_suffix(self, value: str) -> bool:
        stem = Path(value).stem  # Inspect only the source or Markdown file name.
        return bool(self._number_suffix.search(stem))  # Numeric suffixes are strong split evidence.


class DuplicateResolver:
    """Select one winner when several roots hold the same logical document."""

    def resolve(self, groups: list[DocumentGroup]) -> list[DuplicateDecision]:
        logging.info("Resolving duplicates across %s document candidates", len(groups))  # Log duplicate pass start.
        buckets: dict[str, list[DocumentGroup]] = defaultdict(list)  # Group documents by natural document key.
        for group in groups:  # Add every candidate to a duplicate bucket.
            buckets[self._canonical_key(group)].append(group)  # Use source PDF or title as duplicate evidence.
        decisions = [self._decide(key, value) for key, value in buckets.items()]  # Pick a winner for each bucket.
        logging.debug(
            "Duplicate resolver produced %s logical documents", len(decisions)
        )  # Report final document count.
        return decisions

    def _canonical_key(self, group: DocumentGroup) -> str:
        source_key = TextKey.normalize(group.source_pdf) if group.source_pdf else ""  # Prefer source PDF across roots.
        title_key = TextKey.normalize(group.title) if group.title else ""  # Use title when the source PDF is absent.
        return source_key or title_key or TextKey.normalize(group.group_key)  # Ensure every group has a stable key.

    def _decide(self, canonical_key: str, groups: list[DocumentGroup]) -> DuplicateDecision:
        logging.info("Selecting duplicate winner for %s", canonical_key)  # Log the natural document key.
        winner = max(groups, key=self._winner_score)  # Apply the stated, testable duplicate winner rule.
        losers = [group for group in groups if group is not winner]  # Keep loser records for audit and re-run safety.
        self._mark_groups(canonical_key, winner, losers)  # Write winner state back to group records.
        logging.debug("Duplicate key %s has %s losers", canonical_key, len(losers))  # Report duplicate loser count.
        return DuplicateDecision(canonical_key, winner, losers)

    def _winner_score(self, group: DocumentGroup) -> tuple[int, int, int]:
        return (
            group.root.rank,
            group.front_matter_parts,
            group.text_chars,
        )  # Prefer newest, metadata, then text yield.

    def _mark_groups(self, canonical_key: str, winner: DocumentGroup, losers: list[DocumentGroup]) -> None:
        winner.group_key = canonical_key  # Store the natural key used by the rest of the factory.
        winner.is_winner = True  # Mark the selected conversion as active.
        for loser in losers:  # Preserve every duplicate loser for the report and database.
            loser.duplicate_of = canonical_key  # Link the loser to the selected document.
            loser.is_winner = False  # Mark the conversion as inactive.


class PriorityScorer:
    """Score documents for conversion priority with tunable weights."""

    CATEGORY_WEIGHTS = {  # Give teaching documents higher queue priority than marketing documents.
        "cli-reference": 400,
        "guides": 320,
        "configuration-guides": 300,
        "api": 280,
        "flyers": 20,
    }

    STATUS_WEIGHTS = {"ok": 80, "review": -120, "unknown": 0}  # Prefer documents that passed harvester review.

    def score(self, group: DocumentGroup) -> int:
        logging.info("Scoring priority for %s", group.group_key)  # Log scoring before applying the rule.
        score = (
            self._category_score(group)
            + self._page_score(group)
            + self._status_score(group)
            + self._recency_score(group)
        )
        logging.debug("Priority score for %s is %s", group.group_key, score)  # Report the deterministic score.
        return score

    def _category_score(self, group: DocumentGroup) -> int:
        return self.CATEGORY_WEIGHTS.get(group.category, 100)  # Prefer documents that teach commands and operations.

    def _page_score(self, group: DocumentGroup) -> int:
        return min(group.pages, 2500) // 5  # Reward large teaching documents without letting one PDF dominate.

    def _status_score(self, group: DocumentGroup) -> int:
        return self.STATUS_WEIGHTS.get(group.status, 0)  # Prefer ok output and lower review output.

    def _recency_score(self, group: DocumentGroup) -> int:
        return group.root.rank * 25  # Prefer the newest conversion root as a recency signal.


class InventoryDatabase:
    """Persist the source document inventory and work queue in SQLite."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path  # Store the factory database path from the contract.

    def write(self, decisions: list[DuplicateDecision]) -> None:
        logging.info("Writing inventory database to %s", self.db_path)  # Log persistence before file operations.
        self.db_path.parent.mkdir(parents=True, exist_ok=True)  # Create the factory data folder if it is missing.
        with sqlite3.connect(self.db_path) as connection:  # Use a transaction so a crash loses at most one commit.
            self._create_schema(connection)  # Ensure the natural-key schema exists before upserts.
            changed = self._changed_parts(connection, decisions)  # Detect reconverted files before replacing hashes.
            self._write_documents(connection, decisions)  # Upsert document and part records.
            self._write_work_items(connection, decisions, changed)  # Queue changed documents for conversion.
        logging.debug(
            "Inventory database write finished with %s changed parts", len(changed)
        )  # Report requeue signal count.

    def _create_schema(self, connection: sqlite3.Connection) -> None:
        logging.info("Creating inventory database schema")  # Log schema creation before DDL.
        for statement in self._schema_statements():  # Create each table with a bounded statement.
            connection.execute(statement)  # Execute DDL inside the same inventory transaction.
        logging.debug("Inventory database schema is ready")  # Report DDL completion.

    def _schema_statements(self) -> list[str]:
        return [
            self._document_schema(),
            self._part_schema(),
            self._work_item_schema(),
        ]  # Return ordered DDL statements.

    def _document_schema(self) -> str:
        return """
            CREATE TABLE IF NOT EXISTS source_document (
                document_key TEXT PRIMARY KEY, title TEXT NOT NULL, category TEXT NOT NULL,
                source_pdf TEXT NOT NULL, root_name TEXT NOT NULL, pages INTEGER NOT NULL,
                status TEXT NOT NULL, group_method TEXT NOT NULL, part_count INTEGER NOT NULL,
                text_chars INTEGER NOT NULL, priority INTEGER NOT NULL, duplicate_losers INTEGER NOT NULL
            )
            """  # Store one row for each logical document after duplicate resolution.

    def _part_schema(self) -> str:
        return """
            CREATE TABLE IF NOT EXISTS source_part (
                part_key TEXT PRIMARY KEY, document_key TEXT NOT NULL, root_name TEXT NOT NULL,
                relative_path TEXT NOT NULL, content_hash TEXT NOT NULL, size_bytes INTEGER NOT NULL,
                text_chars INTEGER NOT NULL, has_front_matter INTEGER NOT NULL, is_winner INTEGER NOT NULL,
                duplicate_of TEXT NOT NULL, FOREIGN KEY(document_key) REFERENCES source_document(document_key)
            )
            """  # Store one row for each physical Markdown file.

    def _work_item_schema(self) -> str:
        return """
            CREATE TABLE IF NOT EXISTS work_item (
                document_key TEXT PRIMARY KEY, status TEXT NOT NULL, priority INTEGER NOT NULL,
                reason TEXT NOT NULL, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(document_key) REFERENCES source_document(document_key)
            )
            """  # Store one queue row for each logical document.

    def _changed_parts(self, connection: sqlite3.Connection, decisions: list[DuplicateDecision]) -> set[str]:
        logging.info("Checking existing part hashes for changes")  # Log incremental detection before reading state.
        rows = connection.execute("SELECT part_key, content_hash FROM source_part").fetchall()  # Read old hashes.
        old_hashes = {str(row[0]): str(row[1]) for row in rows}  # Build a comparison map by natural part key.
        changed = self._changed_document_keys(old_hashes, decisions)  # Convert changed parts to document keys.
        logging.debug("Detected %s changed documents from part hashes", len(changed))  # Report incremental queue count.
        return changed

    def _changed_document_keys(self, old_hashes: dict[str, str], decisions: list[DuplicateDecision]) -> set[str]:
        changed: set[str] = set()  # Store documents that need queue reset.
        for decision in decisions:  # Inspect only active logical documents.
            for part in decision.winner.parts:  # Compare each winning physical part hash.
                old_hash = old_hashes.get(part.part_key)  # Missing hash means a new input part exists.
                if old_hash != part.content_hash:  # Requeue new or changed converter output.
                    changed.add(decision.canonical_key)  # Queue the logical document, not one part.
        return changed

    def _write_documents(self, connection: sqlite3.Connection, decisions: list[DuplicateDecision]) -> None:
        logging.info("Upserting source document and part rows")  # Log data writes before executing SQL.
        for decision in decisions:  # Persist each logical document and its physical parts.
            self._upsert_document(connection, decision)  # Store one source_document row per logical document.
            self._upsert_parts(connection, decision)  # Store winner and loser part rows for audit.
        logging.debug("Upserted %s source documents", len(decisions))  # Report document row count.

    def _upsert_document(self, connection: sqlite3.Connection, decision: DuplicateDecision) -> None:
        group = decision.winner  # Use the selected duplicate winner as the active source document.
        connection.execute(
            """
            INSERT OR REPLACE INTO source_document
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                decision.canonical_key,
                group.title,
                group.category,
                group.source_pdf,
                group.root.name,
                group.pages,
                group.status,
                group.group_method,
                group.part_count,
                group.text_chars,
                group.priority,
                len(decision.losers),
            ),
        )  # Upsert by natural document key so repeated scans are incremental.

    def _upsert_parts(self, connection: sqlite3.Connection, decision: DuplicateDecision) -> None:
        groups = [decision.winner, *decision.losers]  # Preserve duplicate losers without activating them.
        for group in groups:  # Write all physical files linked to the winner document.
            for part in group.parts:  # Persist one row for each Markdown file.
                self._upsert_part(connection, decision.canonical_key, group, part)  # Store part metadata and hash.

    def _upsert_part(self, connection: sqlite3.Connection, key: str, group: DocumentGroup, part: MarkdownPart) -> None:
        connection.execute(
            """
            INSERT OR REPLACE INTO source_part
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                part.part_key,
                key,
                part.root.name,
                part.relative_path,
                part.content_hash,
                part.size_bytes,
                part.text_chars,
                1 if part.has_front_matter else 0,
                1 if group.is_winner else 0,
                group.duplicate_of,
            ),
        )  # Upsert by natural part key so reconverted content updates in place.

    def _write_work_items(
        self,
        connection: sqlite3.Connection,
        decisions: list[DuplicateDecision],
        changed: set[str],
    ) -> None:
        logging.info("Upserting priority work queue")  # Log queue writes before SQL execution.
        for decision in decisions:  # Ensure every logical document has one queue row.
            reason = self._queue_reason(decision, changed)  # Explain why the item is pending or preserved.
            status = (
                "pending" if decision.canonical_key in changed else self._existing_status(connection, decision)
            )  # Preserve work.
            connection.execute(
                """
                INSERT OR REPLACE INTO work_item (document_key, status, priority, reason, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (decision.canonical_key, status, decision.winner.priority, reason),
            )  # Use document key as the natural queue key.
        logging.debug("Upserted %s work items", len(decisions))  # Report queue size.

    def _existing_status(self, connection: sqlite3.Connection, decision: DuplicateDecision) -> str:
        row = connection.execute(
            "SELECT status FROM work_item WHERE document_key = ?", (decision.canonical_key,)
        ).fetchone()
        return str(row[0]) if row else "pending"  # New documents start pending.

    def _queue_reason(self, decision: DuplicateDecision, changed: set[str]) -> str:
        return (
            "content changed" if decision.canonical_key in changed else "inventory refreshed"
        )  # State requeue reason.


class InventoryReport:
    """Write a measured inventory report for operators."""

    def __init__(self, report_path: Path) -> None:
        self.report_path = report_path  # Store the report path under the factory data directory.

    def write(self, result: InventoryResult) -> None:
        logging.info("Writing inventory report to %s", self.report_path)  # Log report write before disk access.
        self.report_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure the report directory exists.
        lines = self._lines(result)  # Build report lines from measured inventory values.
        self.report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")  # Persist the report as UTF-8 Markdown.
        logging.debug("Inventory report wrote %s lines", len(lines))  # Report output length.

    def _lines(self, result: InventoryResult) -> list[str]:
        lines = self._summary_lines(result)  # Start with measured top-level counts.
        lines.extend(self._priority_rule_lines())  # State the rule that builds queue priority.
        lines.extend(self._part_set_lines(result))  # Add measured split part set evidence.
        lines.extend(self._duplicate_lines(result))  # Add measured duplicate resolution evidence.
        lines.extend(self._category_lines(result))  # Add category totals for planning.
        lines.extend(self._top_document_lines(result))  # Add the top 50 priority records.
        return lines

    def _summary_lines(self, result: InventoryResult) -> list[str]:
        return [
            "# Juniper corpus inventory report",
            "",
            "## Summary",
            "",
            "| Measure | Value |",
            "| - | -: |",
            f"| Source roots scanned | {result.roots_scanned} |",
            f"| Physical Markdown parts | {result.physical_parts} |",
            f"| Logical documents | {result.logical_documents} |",
            f"| Split part sets | {result.part_sets} |",
            f"| Duplicate conversions removed | {result.duplicate_losers} |",
        ]

    def _priority_rule_lines(self) -> list[str]:
        return [
            "",
            "## Priority rule",
            "",
            "Priority = category weight + page score + status score + recency score.",
            "The rule favors CLI reference, guide, configuration, and API documents.",
            "The rule lowers documents that need review and documents from older roots.",
        ]  # Explain the separate scorer class without repeating code.

    def _part_set_lines(self, result: InventoryResult) -> list[str]:
        lines = ["", "## Split part sets", "", "| Title | Root | Parts | Method |", "| - | - | -: | - |"]
        for group in result.part_set_details:  # Report every measured set and its part count.
            safe_title = group.title.replace("|", "\\|")  # Escape source titles for Markdown tables.
            lines.append(f"| {safe_title} | {group.root.name} | {group.part_count} | {group.group_method} |")
        return lines

    def _duplicate_lines(self, result: InventoryResult) -> list[str]:
        lines = ["", "## Duplicate conversions", "", "| Title | Winner root | Losers |", "| - | - | -: |"]
        for decision in result.duplicate_details:  # Report each logical document that had loser conversions.
            safe_title = decision.winner.title.replace("|", "\\|")  # Escape source titles for Markdown tables.
            lines.append(f"| {safe_title} | {decision.winner.root.name} | {len(decision.losers)} |")
        return lines

    def _category_lines(self, result: InventoryResult) -> list[str]:
        lines = [
            "",
            "## Category totals",
            "",
            "| Category | Documents |",
            "| - | -: |",
        ]  # Create category table header.
        for category, count in sorted(result.category_totals.items()):  # Sort for stable report diffs.
            lines.append(f"| {category} | {count} |")  # Add one measured category total.
        return lines

    def _top_document_lines(self, result: InventoryResult) -> list[str]:
        lines = [
            "",
            "## Top 50 priority documents",
            "",
            "| Rank | Priority | Title | Category | Pages | Parts |",
            "| -: | -: | - | - | -: | -: |",
        ]
        for index, group in enumerate(result.top_documents[:50], start=1):  # Include exactly the top 50 or fewer.
            safe_title = group.title.replace("|", "\\|")  # Escape table separators in source titles.
            lines.append(
                f"| {index} | {group.priority} | {safe_title} | {group.category} | {group.pages} | {group.part_count} |"
            )
        return lines


class InventoryBuilder:
    """Build the inventory database, work queue, and report."""

    def __init__(self, repo_root: Path, download_root: Path | None = None) -> None:
        self.repo_root = repo_root  # Store the worktree root that owns the factory database.
        self.download_root = download_root or Path.home() / "Downloads"  # Use the user download folder by default.
        self.roots = self._source_roots()  # Materialize the four locked source roots.
        self.metadata = HarvesterMetadataLoader(self.roots[0].path)  # Read metadata from juniper-harvest-md.
        self.scorer = PriorityScorer()  # Keep priority scoring separate and testable.

    def build(self) -> InventoryResult:
        logging.info("Building Juniper corpus inventory")  # Log the high-level build action.
        parts = CorpusScanner(self.roots, self.metadata).scan()  # Scan all physical Markdown roots.
        groups = PartSetGrouper().group(parts)  # Group split files before duplicate detection.
        decisions = DuplicateResolver().resolve(groups)  # Pick one conversion per logical document.
        self._score(decisions)  # Assign queue priority after duplicate resolution.
        InventoryDatabase(self.repo_root / "data" / "juniper_skills" / "factory.db").write(decisions)  # Persist state.
        result = self._result(parts, decisions)  # Build measured counts for reports and final output.
        InventoryReport(self.repo_root / "data" / "juniper_skills" / "inventory-report.md").write(
            result
        )  # Write report.
        logging.debug(
            "Inventory build finished with %s logical documents", result.logical_documents
        )  # Report final count.
        return result

    def _source_roots(self) -> list[SourceRoot]:
        archive = self.download_root / "juniper-doc-archives"  # Use the archive folder from the locked contract.
        return [
            SourceRoot("juniper-harvest-md", self.download_root / "juniper-harvest-md", 3),
            SourceRoot("archive-markdown", archive / "markdown", 1),
            SourceRoot("archive-markdown2", archive / "markdown2", 2),
            SourceRoot("juniper-corpus", self.repo_root / "data" / "juniper_corpus", 0),
        ]

    def _score(self, decisions: list[DuplicateDecision]) -> None:
        logging.info("Scoring %s logical documents", len(decisions))  # Log priority scoring start.
        for decision in decisions:  # Score only active winner records.
            decision.winner.priority = self.scorer.score(decision.winner)  # Store the tunable priority value.
        logging.debug("Scored %s logical documents", len(decisions))  # Report scored document count.

    def _result(self, parts: list[MarkdownPart], decisions: list[DuplicateDecision]) -> InventoryResult:
        winners = [decision.winner for decision in decisions]  # Use winners for logical document totals.
        category_totals = self._category_totals(winners)  # Count documents by selected category.
        top_documents = sorted(winners, key=lambda group: group.priority, reverse=True)[
            :50
        ]  # Rank top priority documents.
        part_sets = sum(1 for group in winners if group.part_count > 1)  # Count split sets after duplicate resolution.
        duplicate_losers = sum(len(decision.losers) for decision in decisions)  # Count loser conversions retained.
        part_set_details = [group for group in winners if group.part_count > 1]  # Keep part set details for the report.
        duplicate_details = [
            decision for decision in decisions if decision.losers
        ]  # Keep duplicate details for the report.
        return InventoryResult(
            len(self.roots),
            len(parts),
            len(winners),
            part_sets,
            duplicate_losers,
            category_totals,
            top_documents,
            part_set_details,
            duplicate_details,
        )

    def _category_totals(self, groups: list[DocumentGroup]) -> dict[str, int]:
        totals: dict[str, int] = defaultdict(int)  # Accumulate counts by selected category.
        for group in groups:  # Count each active logical document once.
            totals[group.category] += 1  # Increment the measured category total.
        return dict(totals)  # Return a plain dict for reporting and tests.
