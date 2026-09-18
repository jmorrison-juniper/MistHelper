"""Assemble level 1 Juniper domain skill packages from document topic trees."""

from __future__ import annotations

import logging
import re
import shutil
import sqlite3
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

LIFECYCLE_TAGS = ("day0", "day1", "day2", "day2plus")
SKILL_HARD_LIMIT = 12_288
INDEX_HARD_LIMIT = 40_960
SOURCE_HARD_LIMIT = 40_960
SKILL_SOFT_LIMIT = 8_192
INDEX_SOFT_LIMIT = 20_480
SOURCE_SOFT_LIMIT = 20_480


@dataclass(frozen=True)
class DocumentPackageInput:
    """One converted document tree that belongs in a domain skill."""

    slug: str
    title: str
    category: str
    pages: int
    document_dir: Path
    markdown_paths: tuple[Path, ...]
    pdf_path: Path
    public_origin: str
    author: str = "Unknown"
    converted: str = ""


@dataclass(frozen=True)
class TopicRoute:
    """One topic route row for level 1 and level 2 indexes."""

    title: str
    subject: str
    lifecycle: tuple[str, ...]
    citation: str
    source_range: str
    relative_path: Path


@dataclass(frozen=True)
class RouteCluster:
    """One user-language route row for SKILL.md."""

    subject: str
    destination: str
    rank: int


@dataclass(frozen=True)
class PackageAssemblyResult:
    """Measured output from one domain assembly run."""

    package_dir: Path
    skill_size: int
    index_size: int
    sources_size: int
    topic_count: int
    document_count: int
    coverage: dict[str, int]


@dataclass(frozen=True)
class ValidationFinding:
    """One validator finding with the measured value that failed."""

    file: Path
    message: str
    measured: str
    severity: str = "error"


@dataclass(frozen=True)
class ValidationResult:
    """The full package validation result."""

    files_checked: int
    errors: tuple[ValidationFinding, ...]
    warnings: tuple[ValidationFinding, ...] = field(default_factory=tuple)

    @property
    def passed(self) -> bool:
        return not self.errors and self.files_checked > 0


class CitationKeyAllocator:
    """Allocate stable, collision-free source keys inside one domain."""

    STOP_WORDS = {
        "A",
        "AN",
        "AND",
        "DAY",
        "FOR",
        "GUIDE",
        "LEARNING",
        "OF",
        "ONE",
        "THE",
        "TO",
        "USER",
    }

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def allocate(self, domain: str, document_slug: str, title: str) -> str:
        logging.info("Allocating a citation key for %s", document_slug)
        self._ensure_schema()
        existing = self._existing_key(domain, document_slug)
        if existing:
            logging.debug("Reused citation key %s for %s", existing, document_slug)
            return existing
        key = self._next_key(domain, title)
        self._insert_key(domain, document_slug, title, key)
        logging.debug("Allocated citation key %s for %s", key, document_slug)
        return key

    def _connect(self) -> sqlite3.Connection:
        logging.info("Opening the skill factory database")
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database_path)
        logging.debug("Opened the skill factory database at %s", self.database_path)
        return connection

    def _ensure_schema(self) -> None:
        logging.info("Ensuring the citation key table exists")
        with self._connect() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS citation_keys ("
                "domain TEXT NOT NULL, document_slug TEXT NOT NULL, title TEXT NOT NULL, "
                "key TEXT NOT NULL, created_at TEXT NOT NULL, "
                "PRIMARY KEY (domain, document_slug), UNIQUE (domain, key))"
            )
        logging.debug("Citation key table is ready")

    def _existing_key(self, domain: str, document_slug: str) -> str:
        logging.info("Reading an existing citation key for %s", document_slug)
        with self._connect() as connection:
            row = connection.execute(
                "SELECT key FROM citation_keys WHERE domain = ? AND document_slug = ?",
                (domain, document_slug),
            ).fetchone()
        key = str(row[0]) if row else ""
        logging.debug("Existing citation key lookup returned %s", bool(key))
        return key

    def _insert_key(self, domain: str, document_slug: str, title: str, key: str) -> None:
        logging.info("Persisting citation key %s for %s", key, document_slug)
        built = datetime.now(UTC).isoformat(timespec="seconds")
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO citation_keys (domain, document_slug, title, key, created_at) VALUES (?, ?, ?, ?, ?)",
                (domain, document_slug, title, key, built),
            )
        logging.debug("Persisted citation key %s for %s", key, document_slug)

    def _next_key(self, domain: str, title: str) -> str:
        logging.info("Building a candidate citation key for %s", title)
        candidate = self._candidate(title)
        used = self._used_keys(domain)
        key = self._dedupe(candidate, used)
        logging.debug("Selected citation key %s from candidate %s", key, candidate)
        return key

    def _candidate(self, title: str) -> str:
        words = re.findall(r"[A-Za-z0-9]+", title.upper())
        product = self._product_word(words)
        initials = "".join(word[0] for word in words if word not in self.STOP_WORDS and word != product)
        candidate = (product + initials)[:12]
        return candidate if len(candidate) >= 3 else (candidate + "DOC")[:3]

    def _product_word(self, words: list[str]) -> str:
        products = ("JUNOS", "MIST", "SRX", "APSTRA", "EX", "QFX", "MX", "PTX")
        for word in words:
            if word in products:
                return word
        return words[0][:6] if words else "DOC"

    def _used_keys(self, domain: str) -> set[str]:
        logging.info("Reading allocated citation keys for %s", domain)
        with self._connect() as connection:
            rows = connection.execute("SELECT key FROM citation_keys WHERE domain = ?", (domain,)).fetchall()
        keys = {str(row[0]) for row in rows}
        logging.debug("Read %s allocated citation keys for %s", len(keys), domain)
        return keys

    def _dedupe(self, candidate: str, used: set[str]) -> str:
        if candidate not in used:
            return candidate
        for number in range(2, 1000):
            suffix = str(number)
            key = f"{candidate[: 12 - len(suffix)]}{suffix}"
            if key not in used:
                return key
        raise RuntimeError("citation key allocation exhausted")


class SkillPackageAssembler:
    """Build SKILL.md, INDEX.md, sources.md, and normalized document trees."""

    def __init__(self, database_path: Path) -> None:
        self.allocator = CitationKeyAllocator(database_path)

    def assemble(
        self, domain: str, output_root: Path, documents: tuple[DocumentPackageInput, ...], taxonomy_path: Path
    ) -> PackageAssemblyResult:
        logging.info("Assembling domain skill package for %s", domain)
        package_dir = output_root / f"juniper-{domain}"
        self._reset_package(package_dir)
        keys = {document.slug: self.allocator.allocate(domain, document.slug, document.title) for document in documents}
        routes = self._write_documents(package_dir, domain, documents, keys)
        coverage = self._coverage(routes)
        self._write_level_one(package_dir, domain, documents, routes, taxonomy_path)
        result = self._result(package_dir, routes, documents, coverage)
        logging.debug("Assembled %s with %s topics", package_dir, result.topic_count)
        return result

    def _reset_package(self, package_dir: Path) -> None:
        logging.info("Preparing package directory %s", package_dir)
        if package_dir.exists():
            shutil.rmtree(package_dir)
        package_dir.mkdir(parents=True, exist_ok=True)
        logging.debug("Prepared package directory %s", package_dir)

    def _write_documents(
        self, package_dir: Path, domain: str, documents: tuple[DocumentPackageInput, ...], keys: dict[str, str]
    ) -> list[TopicRoute]:
        routes: list[TopicRoute] = []
        for document in documents:
            routes.extend(self._write_document(package_dir, domain, document, keys[document.slug]))
        return routes

    def _write_document(
        self, package_dir: Path, domain: str, document: DocumentPackageInput, key: str
    ) -> list[TopicRoute]:
        logging.info("Writing document tree for %s", document.slug)
        target_dir = package_dir / "documents" / document.slug
        target_dir.mkdir(parents=True, exist_ok=True)
        routes = self._write_topics(target_dir, domain, document, key)
        self._write_document_index(target_dir, document, key, routes)
        logging.debug("Wrote document tree for %s with %s topics", document.slug, len(routes))
        return routes

    def _write_topics(
        self, target_dir: Path, domain: str, document: DocumentPackageInput, key: str
    ) -> list[TopicRoute]:
        logging.info("Writing normalized topic files for %s", document.slug)
        source_files = self._topic_files(document.document_dir)
        subjects = SegmentIndexReader().subjects(document.document_dir / "INDEX.md")
        routes = [self._write_topic(target_dir, domain, document, key, path, subjects) for path in source_files]
        logging.debug("Wrote %s normalized topic files for %s", len(routes), document.slug)
        return routes

    def _topic_files(self, document_dir: Path) -> list[Path]:
        logging.info("Reading topic files from %s", document_dir)
        files = sorted(path for path in document_dir.glob("*.md") if path.name != "INDEX.md")
        logging.debug("Read %s topic files from %s", len(files), document_dir)
        return files

    def _write_topic(
        self,
        target_dir: Path,
        domain: str,
        document: DocumentPackageInput,
        key: str,
        source_path: Path,
        subjects: dict[str, str],
    ) -> TopicRoute:
        logging.info("Normalizing topic file %s", source_path.name)
        source = source_path.read_text(encoding="utf-8")
        frontmatter, body = FrontMatterParser().parse(source)
        title = str(frontmatter.get("topic") or self._title_from_name(source_path))
        lifecycle = self._lifecycle(frontmatter)
        source_range = self._source_range(frontmatter, key)
        target_path = target_dir / self._topic_filename(source_path, title)
        topic_text = self._topic_text(title, domain, document.slug, lifecycle, source_range, body)
        target_path.write_text(topic_text, encoding="utf-8")
        route = self._route(title, document.slug, source_range, target_path, lifecycle, body, subjects)
        logging.debug("Normalized topic file %s to %s bytes", source_path.name, target_path.stat().st_size)
        return route

    def _topic_filename(self, source_path: Path, title: str) -> str:
        if source_path.name.startswith("00-"):
            return "00-overview.md"
        if re.match(r"^[0-9][0-9]-[a-z0-9]+(-[a-z0-9]+)*\.md$", source_path.name):
            return source_path.name
        prefix = re.match(r"^([0-9][0-9])", source_path.name)
        number = prefix.group(1) if prefix else "00"
        return f"{number}-{self._slug(title)}.md"

    def _topic_text(
        self, title: str, domain: str, document_slug: str, lifecycle: tuple[str, ...], citation: str, body: str
    ) -> str:
        safe_body = self._body_with_cards(body, citation)
        frontmatter = yaml.safe_dump(
            {
                "topic": title,
                "domain": domain,
                "document": document_slug,
                "lifecycle": list(lifecycle),
                "sources": [citation],
            },
            allow_unicode=False,
            sort_keys=False,
        )
        return f"---\n{frontmatter}---\n\n# {title}\n\n{safe_body}\n"

    def _body_with_cards(self, body: str, citation: str) -> str:
        if self._has_card(body):
            return self._recite_cards(body, citation)
        return f"- INFO: Read the source document for this topic. [{citation}]\n"

    def _has_card(self, body: str) -> bool:
        return any(re.match(r"^- (MUST|SHOULD|INFO): .+ \[[A-Z0-9]{3,12} .+\]$", line) for line in body.splitlines())

    def _recite_cards(self, body: str, citation: str) -> str:
        lines = [self._recite_line(line, citation) for line in body.strip().splitlines()]
        return "\n".join(lines) + "\n"

    def _recite_line(self, line: str, citation: str) -> str:
        if re.match(r"^- (MUST|SHOULD|INFO): ", line):
            return re.sub(r"\[[A-Z0-9]{3,12} .+?\]$", f"[{citation}]", line)
        return line

    def _route(
        self,
        title: str,
        slug: str,
        citation: str,
        path: Path,
        lifecycle: tuple[str, ...],
        body: str,
        subjects: dict[str, str],
    ) -> TopicRoute:
        subject = subjects.get(title) or self._subject(title, body)
        source_range = citation.split(" ", 1)[1] if " " in citation else "p.0-0"
        relative = Path("documents") / slug / path.name
        return TopicRoute(title, subject, lifecycle, citation, source_range, relative)

    def _subject(self, title: str, body: str) -> str:
        first_card = next((line for line in body.splitlines() if re.match(r"^- (MUST|SHOULD|INFO): ", line)), "")
        cleaned = re.sub(r"^- (?:MUST|SHOULD|INFO):\s*", "", first_card).split("[", 1)[0].strip()
        return cleaned if cleaned else f"Read about {title}."

    def _lifecycle(self, frontmatter: dict[str, Any]) -> tuple[str, ...]:
        values = frontmatter.get("lifecycle") or ["day0"]
        tags = tuple(tag for tag in values if tag in LIFECYCLE_TAGS) if isinstance(values, list) else ("day0",)
        return tags or ("day0",)

    def _source_range(self, frontmatter: dict[str, Any], key: str) -> str:
        sources = frontmatter.get("sources") or [f"{key} p.0-0"]
        first = str(sources[0]) if isinstance(sources, list) and sources else f"{key} p.0-0"
        match = re.search(r"(?:p\.\d+(?:-\d+)?|sec\.[a-z0-9-]+|table\.[a-z0-9-]+|fig\.[a-z0-9-]+)", first)
        return f"{key} {match.group(0) if match else 'p.0-0'}"

    def _write_document_index(
        self, target_dir: Path, document: DocumentPackageInput, key: str, routes: list[TopicRoute]
    ) -> None:
        logging.info("Writing level 2 index for %s", document.slug)
        text = DocumentIndexRenderer(document, key, routes).render()
        (target_dir / "INDEX.md").write_text(text, encoding="utf-8")
        logging.debug("Wrote level 2 index for %s with %s rows", document.slug, len(routes))

    def _write_level_one(
        self,
        package_dir: Path,
        domain: str,
        documents: tuple[DocumentPackageInput, ...],
        routes: list[TopicRoute],
        taxonomy_path: Path,
    ) -> None:
        logging.info("Writing level 1 files for %s", domain)
        keywords = TaxonomyReader(taxonomy_path).keywords_for(f"juniper-{domain}")
        coverage = self._coverage(routes)
        (package_dir / "SKILL.md").write_text(
            SkillRenderer(domain, documents, routes, keywords, coverage).render(), "utf-8"
        )
        (package_dir / "INDEX.md").write_text(IndexRenderer(domain, documents, routes, coverage).render(), "utf-8")
        (package_dir / "sources.md").write_text(SourcesRenderer(documents, self.allocator).render(domain), "utf-8")
        logging.debug("Wrote level 1 files for %s", domain)

    def _coverage(self, routes: list[TopicRoute]) -> dict[str, int]:
        logging.info("Counting life cycle coverage for the domain")
        coverage = {tag: sum(1 for route in routes if tag in route.lifecycle) for tag in LIFECYCLE_TAGS}
        logging.debug("Counted life cycle coverage as %s", coverage)
        return coverage

    def _result(
        self,
        package_dir: Path,
        routes: list[TopicRoute],
        documents: tuple[DocumentPackageInput, ...],
        coverage: dict[str, int],
    ) -> PackageAssemblyResult:
        logging.info("Measuring generated level 1 file sizes")
        result = PackageAssemblyResult(
            package_dir,
            (package_dir / "SKILL.md").stat().st_size,
            (package_dir / "INDEX.md").stat().st_size,
            (package_dir / "sources.md").stat().st_size,
            len(routes),
            len(documents),
            coverage,
        )
        logging.debug("Measured level 1 files in %s", package_dir)
        return result

    def _title_from_name(self, path: Path) -> str:
        return (
            path.stem[3:].replace("-", " ").title() if path.stem[:2].isdigit() else path.stem.replace("-", " ").title()
        )

    def _slug(self, value: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
        return slug[:60].rsplit("-", 1)[0] or "overview"


class FrontMatterParser:
    """Parse small YAML frontmatter blocks from generated Markdown."""

    def parse(self, text: str) -> tuple[dict[str, Any], str]:
        logging.info("Parsing Markdown frontmatter")
        if not text.startswith("---\n"):
            logging.debug("Markdown file has no frontmatter")
            return {}, text
        end = text.find("\n---", 4)
        if end == -1:
            logging.debug("Markdown file has an open frontmatter block")
            return {}, text
        try:
            data = yaml.safe_load(text[4:end]) or {}
        except yaml.YAMLError:
            data = self._fallback(text[4:end])
        body = text[end + 4 :].lstrip()
        logging.debug("Parsed frontmatter with %s keys", len(data))
        return data if isinstance(data, dict) else {}, body

    def _fallback(self, text: str) -> dict[str, Any]:
        logging.info("Parsing frontmatter with the fault-tolerant reader")
        data: dict[str, Any] = {}
        for line in text.splitlines():
            if ":" in line:
                self._fallback_line(data, line)
        logging.debug("Fault-tolerant reader parsed %s keys", len(data))
        return data

    def _fallback_line(self, data: dict[str, Any], line: str) -> None:
        key, value = line.split(":", 1)
        value = value.strip()
        data[key.strip()] = self._fallback_value(value)

    def _fallback_value(self, value: str) -> object:
        if value.startswith("[") and value.endswith("]"):
            return [part.strip() for part in value[1:-1].split(",") if part.strip()]
        return value


class SegmentIndexReader:
    """Read task-language subjects from the segmenter level 2 index."""

    def subjects(self, index_path: Path) -> dict[str, str]:
        logging.info("Reading segmenter subjects from %s", index_path)
        if not index_path.exists():
            logging.debug("Segmenter index does not exist at %s", index_path)
            return {}
        rows = self._rows(index_path.read_text(encoding="utf-8"))
        subjects = {row[0]: row[3] for row in rows if len(row) >= 4}
        logging.debug("Read %s segmenter subjects from %s", len(subjects), index_path)
        return subjects

    def _rows(self, text: str) -> list[list[str]]:
        rows = [line.strip("|").split("|") for line in text.splitlines() if line.startswith("| ")]
        clean = [[cell.strip() for cell in row] for row in rows]
        return [row for row in clean if row and row[0] not in {"Topic", "-"}]


class TaxonomyReader:
    """Read routing keywords for one domain from the locked taxonomy table."""

    def __init__(self, taxonomy_path: Path) -> None:
        self.taxonomy_path = taxonomy_path

    def keywords_for(self, skill_name: str) -> list[str]:
        logging.info("Reading taxonomy keywords for %s", skill_name)
        text = self.taxonomy_path.read_text(encoding="utf-8")
        pattern = rf"\|\s*\d+\s*\|\s*`{re.escape(skill_name)}`\s*\|\s*(.*?)\s*\|"
        match = re.search(pattern, text)
        keywords = self._split_keywords(match.group(1)) if match else [skill_name.replace("juniper-", "Juniper ")]
        logging.debug("Read %s taxonomy keywords for %s", len(keywords), skill_name)
        return keywords

    def _split_keywords(self, text: str) -> list[str]:
        clean = text.replace("`", "")
        parts = re.split(r",\s*|\s+or\s+", clean)
        return [part.strip(". ") for part in parts if part.strip(". ")]


class SkillRenderer:
    """Render the domain router file."""

    def __init__(
        self,
        domain: str,
        documents: tuple[DocumentPackageInput, ...],
        routes: list[TopicRoute],
        keywords: list[str],
        coverage: dict[str, int],
    ) -> None:
        self.domain = domain
        self.documents = documents
        self.routes = routes
        self.keywords = keywords
        self.coverage = coverage

    def render(self) -> str:
        logging.info("Rendering SKILL.md for %s", self.domain)
        frontmatter = self._frontmatter()
        overhead = len(frontmatter.encode("utf-8")) + len(self._body("").encode("utf-8"))
        route_rows = RouteTableBuilder(self.documents, self.routes).rows(SKILL_HARD_LIMIT - overhead)
        text = frontmatter + self._body(route_rows)
        logging.debug("Rendered SKILL.md for %s with %s bytes", self.domain, len(text.encode("utf-8")))
        return text

    def _frontmatter(self) -> str:
        built = datetime.now(UTC).isoformat(timespec="seconds")
        description = self._description()
        return (
            f"---\nname: juniper-{self.domain}\ndescription: >-\n  {description}\n"
            "license: The topics restate Juniper Networks documentation. Juniper Networks holds the copyright of the "
            "source documents. This skill stores no source prose.\nmetadata:\n"
            f"  feature: 2925-juniper-skill-factory\n  domain: {self.domain}\n"
            f"  documents: {len(self.documents)}\n  topics: {len(self.routes)}\n"
            f"  source_pages: {sum(document.pages for document in self.documents)}\n  built: {built}\n---\n\n"
        )

    def _description(self) -> str:
        subjects = ", ".join(self.keywords[:30])
        return (
            f"Use this skill for Juniper {subjects}. The skill holds a document tree with source documents, "
            "topic routes, life cycle tags, citation keys, and copyright-safe knowledge cards. Use it when a question "
            "asks how to select, deploy, configure, verify, troubleshoot, upgrade, migrate, or automate the subjects "
            "that this domain owns."
        )

    def _body(self, rows: str) -> str:
        return (
            f"# {self._title()}\n\nRead the topic that holds the subject before you answer. "
            "Do not answer a Juniper documentation question from memory.\n\n"
            "## Route by subject\n\n| Ask about | Read this topic |\n| - | - |\n"
            f"{rows}\nRead `INDEX.md` for the full domain route.\n\n"
            "## Class marks\n\n| Mark | Meaning |\n| - | - |\n| MUST | The source states a required practice. |\n"
            "| SHOULD | The source recommends the practice and permits a judged exception. |\n"
            "| INFO | The card states a fact that sets no limit. |\n\n"
            "## Answer rules\n\n1. Read the needed topic before you answer.\n2. Give a citation with each rule.\n"
            "3. Say that the skill does not hold the fact when no topic states it.\n"
            "4. State whether a rule is a requirement, a recommendation, or a fact.\n"
            "5. Point to `sources.md` when the reader needs the public source.\n\n"
            "## Copyright rule\n\nWarning: never copy Juniper source prose into an answer. "
            "Juniper Networks holds the copyright. Restate the fact in new words.\n\n"
            "## Precedence\n\nThe `ste-writing` skill controls the answer form. "
            "This skill controls the answer content.\n\n"
            "## Scope\n\nThis skill answers questions about this Juniper documentation domain. "
            "This skill does not change a network device or a service.\n"
        )

    def _title(self) -> str:
        return " ".join(part.capitalize() for part in self.domain.split("-"))


class RouteTableBuilder:
    """Build concrete SKILL.md route rows from the real topic set."""

    def __init__(self, documents: tuple[DocumentPackageInput, ...], routes: list[TopicRoute]) -> None:
        self.documents = documents
        self.routes = routes

    def rows(self, byte_budget: int) -> str:
        logging.info("Building SKILL.md route rows with concrete destinations")
        candidates = [self._cluster_rows(), self._lifecycle_rows(), self._document_rows(), self._domain_rows()]
        selected = next((rows for rows in candidates if 0 < len(rows.encode("utf-8")) <= byte_budget), candidates[-1])
        logging.debug("Selected SKILL.md route rows with %s bytes", len(selected.encode("utf-8")))
        return selected

    def _cluster_rows(self) -> str:
        clusters = SubjectClusterBuilder(self.routes).clusters()
        return "".join(f"| {cluster.subject} | `{cluster.destination}` |\n" for cluster in clusters[:20])

    def _lifecycle_rows(self) -> str:
        rows: list[str] = []
        for document in self.documents:
            rows.extend(self._document_lifecycle_rows(document))
        return "".join(rows)

    def _document_lifecycle_rows(self, document: DocumentPackageInput) -> list[str]:
        rows: list[str] = []
        document_routes = [route for route in self.routes if route.relative_path.parts[1] == document.slug]
        for tag in LIFECYCLE_TAGS:
            tag_routes = [route for route in document_routes if tag in route.lifecycle]
            if tag_routes:
                rows.append(self._group_row(document, tag, tag_routes))
        return rows

    def _group_row(self, document: DocumentPackageInput, tag: str, routes: list[TopicRoute]) -> str:
        destination = routes[0].relative_path.as_posix() if len(routes) == 1 else f"documents/{document.slug}/INDEX.md"
        subject = f"{self._stage(tag)} in {document.title}"
        return f"| {subject} | `{destination}` |\n"

    def _document_rows(self) -> str:
        return "".join(
            f"| {document.title} topics | `documents/{document.slug}/INDEX.md` |\n" for document in self.documents
        )

    def _domain_rows(self) -> str:
        if len(self.documents) > 1:
            return "| The subject spans more than one source document | `INDEX.md` |\n"
        return self._document_rows()

    def _stage(self, tag: str) -> str:
        names = {
            "day0": "Design, selection, and requirements",
            "day1": "Setup, access, and first configuration",
            "day2": "Verification, monitoring, and troubleshooting",
            "day2plus": "Change, recovery, upgrade, and automation",
        }
        return names[tag]


class SubjectClusterBuilder:
    """Compress topic routes into user-language subject clusters."""

    def __init__(self, routes: list[TopicRoute]) -> None:
        self.routes = routes

    def clusters(self) -> list[RouteCluster]:
        logging.info("Building user-language route clusters")
        clusters = self._known_clusters()
        clusters.extend(self._unmatched_clusters(clusters))
        ordered = sorted(self._unique(clusters), key=lambda cluster: cluster.rank)
        logging.debug("Built %s user-language route clusters", len(ordered))
        return ordered

    def _known_clusters(self) -> list[RouteCluster]:
        return [
            self._one("filtering output", "Filtering or searching command output, match, except, count, or last", 10),
            self._one("cli help", "Finding a command, its syntax, or its options", 20),
            self._one("comparing", "Undoing a change, rolling back, or recovering a broken configuration", 30),
            self._one("comparing", "Making a change safely on a remote device", 40),
            self._one("management port", "First console access, out-of-band management, or the management port", 50),
            self._one("mx series", "Choosing a platform for a branch, a campus, or an edge role", 60),
            self._one("alarms", "A device that will not boot, an alarm, or a hardware fault", 70),
            self._one("basic networking tools", "Capturing packets or testing reachability", 80),
            self._many("routing", "Writing or debugging a routing policy", 90),
            self._many("firewall filter", "Writing or debugging a firewall filter", 100),
        ]

    def _one(self, needle: str, subject: str, rank: int) -> RouteCluster:
        route = self._find(needle)
        destination = route.relative_path.as_posix() if route else self._first_document_index()
        return RouteCluster(subject, destination, rank)

    def _many(self, needle: str, subject: str, rank: int) -> RouteCluster:
        matches = [route for route in self.routes if needle in self._context(route)]
        destination = self._span_destination(matches)
        return RouteCluster(subject, destination, rank)

    def _unmatched_clusters(self, clusters: list[RouteCluster]) -> list[RouteCluster]:
        used = {cluster.destination for cluster in clusters}
        rows = [
            self._fallback(route, index)
            for index, route in enumerate(self.routes)
            if route.relative_path.as_posix() not in used
        ]
        return rows[:8]

    def _fallback(self, route: TopicRoute, index: int) -> RouteCluster:
        subject = self._fallback_subject(route)
        return RouteCluster(subject, route.relative_path.as_posix(), 200 + index)

    def _fallback_subject(self, route: TopicRoute) -> str:
        text = route.subject.strip().rstrip(".")
        clean = text if 12 <= len(text) <= 120 and not text.startswith("-") else route.title
        return clean[0].upper() + clean[1:] if clean else route.title

    def _unique(self, clusters: list[RouteCluster]) -> list[RouteCluster]:
        seen: set[tuple[str, str]] = set()
        output: list[RouteCluster] = []
        for cluster in clusters:
            key = (cluster.subject, cluster.destination)
            if key not in seen:
                output.append(cluster)
                seen.add(key)
        return output

    def _find(self, needle: str) -> TopicRoute | None:
        return next((route for route in self.routes if needle in self._context(route)), None)

    def _context(self, route: TopicRoute) -> str:
        return f"{route.title} {route.subject} {route.relative_path.name}".lower()

    def _span_destination(self, routes: list[TopicRoute]) -> str:
        if len(routes) == 1:
            return routes[0].relative_path.as_posix()
        return self._document_index(routes) if routes else self._first_document_index()

    def _document_index(self, routes: list[TopicRoute]) -> str:
        parts = routes[0].relative_path.parts
        return f"documents/{parts[1]}/INDEX.md"

    def _first_document_index(self) -> str:
        if not self.routes:
            return "INDEX.md"
        return self._document_index([self.routes[0]])


class IndexRenderer:
    """Render the level 1 domain index with graceful size degradation."""

    def __init__(
        self,
        domain: str,
        documents: tuple[DocumentPackageInput, ...],
        routes: list[TopicRoute],
        coverage: dict[str, int],
    ) -> None:
        self.domain = domain
        self.documents = documents
        self.routes = routes
        self.coverage = coverage

    def render(self) -> str:
        logging.info("Rendering level 1 INDEX.md for %s", self.domain)
        text = self._text(self._topic_rows())
        if len(text.encode("utf-8")) > INDEX_HARD_LIMIT:
            text = self._text(self._summary_rows())
        logging.debug("Rendered level 1 INDEX.md with %s bytes", len(text.encode("utf-8")))
        return text

    def _text(self, route_rows: str) -> str:
        return (
            f"# {self._title()} index\n\n## Route by subject\n\n"
            "| Ask about | Read | Life cycle |\n| - | - | - |\n"
            f"{route_rows}\n## Route by source document\n\n"
            "| Document | Slug | Pages | Read |\n| - | - | -: | - |\n"
            f"{self._document_rows()}\n## Life cycle coverage\n\n"
            "| Stage | Topics | Status |\n| - | -: | - |\n"
            f"{self._coverage_rows()}\n## Coverage gaps\n\n{self._gap_text()}\n"
        )

    def _topic_rows(self) -> str:
        return "".join(
            f"| {route.subject} | {route.relative_path.as_posix()} | {', '.join(route.lifecycle)} |\n"
            for route in self.routes
        )

    def _summary_rows(self) -> str:
        return "".join(
            f"| {document.title} topics. Detail lives in the document index. | "
            f"documents/{document.slug}/INDEX.md | document-summary |\n"
            for document in self.documents
        )

    def _document_rows(self) -> str:
        return "".join(
            f"| {document.title} | {document.slug} | {document.pages} | documents/{document.slug}/INDEX.md |\n"
            for document in self.documents
        )

    def _coverage_rows(self) -> str:
        return "".join(f"| {tag} | {self.coverage[tag]} | {self._status(tag)} |\n" for tag in LIFECYCLE_TAGS)

    def _gap_text(self) -> str:
        gaps = [tag for tag in LIFECYCLE_TAGS if self.coverage[tag] == 0]
        if not gaps:
            return "No gaps found.\n"
        return "".join(f"- {tag} has no topic.\n" for tag in gaps)

    def _status(self, tag: str) -> str:
        return "covered" if self.coverage[tag] else "gap"

    def _title(self) -> str:
        return " ".join(part.capitalize() for part in self.domain.split("-"))


class SourcesRenderer:
    """Render the domain attribution table."""

    def __init__(self, documents: tuple[DocumentPackageInput, ...], allocator: CitationKeyAllocator) -> None:
        self.documents = documents
        self.allocator = allocator

    def render(self, domain: str) -> str:
        logging.info("Rendering sources.md for %s", domain)
        rows = "".join(self._row(domain, document) for document in self.documents)
        text = "# Sources\n\n| Key | Title | Author | Category | Pages | Converted | Origin | Markdown | PDF |\n"
        text += "| - | - | - | - | -: | - | - | - | - |\n" + rows
        logging.debug("Rendered sources.md for %s with %s rows", domain, len(self.documents))
        return text

    def _row(self, domain: str, document: DocumentPackageInput) -> str:
        key = self.allocator.allocate(domain, document.slug, document.title)
        metadata = SourceMetadataReader().read(document)
        markdown = "<br>".join(self._display_path(path) for path in document.markdown_paths)
        title = str(metadata.get("title") or document.title)
        pages = int(metadata.get("pages") or document.pages)
        author = str(metadata.get("author") or document.author)
        source_date = metadata.get("modDate") or metadata.get("creationDate") or datetime.now(UTC).date()
        converted = str(document.converted or source_date)
        return (
            f"| {key} | {title} | {author} | {document.category} | {pages} | "
            f"{converted} | {document.public_origin} | {markdown} | {document.pdf_path.as_posix()} |\n"
        )

    def _display_path(self, path: Path) -> str:
        parts = path.parts
        if "juniper-harvest-md" in parts:
            index = parts.index("juniper-harvest-md")
            return Path(*parts[index + 1 :]).as_posix()
        return path.as_posix()


class SourceMetadataReader:
    """Read attribution fields from converted source frontmatter."""

    def read(self, document: DocumentPackageInput) -> dict[str, object]:
        logging.info("Reading source metadata for %s", document.slug)
        source_path = next((path for path in document.markdown_paths if path.exists()), None)
        metadata = self._read_path(source_path) if source_path else {}
        logging.debug("Read %s source metadata fields for %s", len(metadata), document.slug)
        return metadata

    def _read_path(self, path: Path | None) -> dict[str, object]:
        if path is None:
            return {}
        text = path.read_text(encoding="utf-8")
        frontmatter, _ = FrontMatterParser().parse(text)
        return frontmatter


class DocumentIndexRenderer:
    """Render a contract-shaped level 2 document index."""

    def __init__(self, document: DocumentPackageInput, key: str, routes: list[TopicRoute]) -> None:
        self.document = document
        self.key = key
        self.routes = routes

    def render(self) -> str:
        logging.info("Rendering level 2 index for %s", self.document.slug)
        text = self._text(self._topic_rows())
        if len(text.encode("utf-8")) > 10_240:
            text = self._text(self._compact_topic_rows())
        logging.debug("Rendered level 2 index for %s with %s bytes", self.document.slug, len(text.encode("utf-8")))
        return text

    def _text(self, rows: str) -> str:
        return (
            f"# {self.document.title} index\n\n## Source\n\n"
            f"Title: {self.document.title}.\n\nCategory: {self.document.category}.\n\nPages: {self.document.pages}.\n\n"
            f"Source file path: {self._markdown_paths()}.\n\nSource PDF path: {self.document.pdf_path.as_posix()}.\n\n"
            f"Split part count: {len(self.document.markdown_paths)}.\n\n## Topic route\n\n"
            "| Ask about | Topic | Read | Life cycle |\n| - | - | - | - |\n"
            f"{rows}\n## Life cycle map\n\n| Stage | Topics | Status |\n| - | -: | - |\n"
            f"{self._coverage_rows()}\n## Citation keys\n\n| Key | Source range | Topic |\n| - | - | - |\n"
            f"{self._citation_rows()}"
        )

    def _markdown_paths(self) -> str:
        return ", ".join(path.as_posix() for path in self.document.markdown_paths)

    def _topic_rows(self) -> str:
        return "".join(
            f"| {self._cell(route.subject, 95)} | {route.title} | {route.relative_path.name} | "
            f"{', '.join(route.lifecycle)} |\n"
            for route in self.routes
        )

    def _compact_topic_rows(self) -> str:
        return "".join(
            f"| {self._cell(route.subject, 42)} | {self._cell(route.title, 28)} | {route.relative_path.name} | "
            f"{', '.join(route.lifecycle)} |\n"
            for route in self.routes
        )

    def _cell(self, value: str, limit: int) -> str:
        text = value.strip().rstrip(".")
        return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."

    def _coverage_rows(self) -> str:
        coverage = {tag: sum(1 for route in self.routes if tag in route.lifecycle) for tag in LIFECYCLE_TAGS}
        return "".join(
            f"| {tag} | {coverage[tag]} | {'covered' if coverage[tag] else 'gap'} |\n" for tag in LIFECYCLE_TAGS
        )

    def _citation_rows(self) -> str:
        return "".join(f"| {self.key} | {route.source_range} | {route.relative_path.name} |\n" for route in self.routes)


class SkillPackageValidator:
    """Validate a finished domain skill package against the locked schema."""

    FILE_LIMITS = {"SKILL.md": (SKILL_SOFT_LIMIT, SKILL_HARD_LIMIT), "INDEX.md": (INDEX_SOFT_LIMIT, INDEX_HARD_LIMIT)}

    def validate(self, package_dir: Path) -> ValidationResult:
        logging.info("Validating skill package %s", package_dir)
        errors: list[ValidationFinding] = []
        warnings: list[ValidationFinding] = []
        markdown_files = self._markdown_files(package_dir)
        self._required_files(package_dir, errors)
        self._layout(package_dir, markdown_files, errors)
        self._sizes(package_dir, markdown_files, errors, warnings)
        sources = self._sources(package_dir, errors)
        topic_names = self._topics(package_dir, sources, errors)
        self._skill_frontmatter(package_dir, errors)
        self._links(package_dir, markdown_files, errors)
        self._orphans(package_dir, markdown_files, errors)
        self._duplicates(package_dir, topic_names, errors)
        self._zero(markdown_files, errors, package_dir)
        logging.debug("Validated %s files with %s errors", len(markdown_files), len(errors))
        return ValidationResult(len(markdown_files), tuple(errors), tuple(warnings))

    def _markdown_files(self, package_dir: Path) -> list[Path]:
        logging.info("Listing Markdown files in %s", package_dir)
        files = sorted(package_dir.rglob("*.md")) if package_dir.exists() else []
        logging.debug("Found %s Markdown files in %s", len(files), package_dir)
        return files

    def _required_files(self, package_dir: Path, errors: list[ValidationFinding]) -> None:
        logging.info("Checking required level 1 files")
        for name in ("SKILL.md", "INDEX.md", "sources.md"):
            if not (package_dir / name).exists():
                errors.append(ValidationFinding(package_dir / name, "required file is missing", "missing"))
        logging.debug("Required level 1 file check produced %s errors", len(errors))

    def _layout(self, package_dir: Path, files: list[Path], errors: list[ValidationFinding]) -> None:
        logging.info("Checking package path layout")
        if not re.match(r"^juniper-[a-z0-9]+(-[a-z0-9]+)*$", package_dir.name):
            errors.append(ValidationFinding(package_dir, "package directory name is invalid", package_dir.name))
        for path in files:
            self._layout_path(package_dir, path, errors)
        self._overview_files(package_dir, errors)
        logging.debug("Checked package path layout for %s files", len(files))

    def _layout_path(self, package_dir: Path, path: Path, errors: list[ValidationFinding]) -> None:
        relative = path.relative_to(package_dir)
        parts = relative.parts
        if len(parts) == 1 and path.name in {"SKILL.md", "INDEX.md", "sources.md"}:
            return
        if len(parts) == 3 and parts[0] == "documents":
            self._document_path(path, parts, errors)
            return
        errors.append(ValidationFinding(path, "Markdown file path is not allowed by the package layout", str(relative)))

    def _document_path(self, path: Path, parts: tuple[str, ...], errors: list[ValidationFinding]) -> None:
        if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", parts[1]):
            errors.append(ValidationFinding(path, "document directory name is invalid", parts[1]))
        valid_topic = re.match(r"^[0-9][0-9]-[a-z0-9]+(-[a-z0-9]+)*\.md$", parts[2])
        if parts[2] != "INDEX.md" and not valid_topic:
            errors.append(ValidationFinding(path, "topic file name is invalid", parts[2]))

    def _overview_files(self, package_dir: Path, errors: list[ValidationFinding]) -> None:
        documents_dir = package_dir / "documents"
        if not documents_dir.exists():
            return
        for document_dir in documents_dir.iterdir():
            if document_dir.is_dir() and not (document_dir / "00-overview.md").exists():
                errors.append(ValidationFinding(document_dir, "00-overview.md is missing", "missing"))

    def _sizes(
        self, package_dir: Path, files: list[Path], errors: list[ValidationFinding], warnings: list[ValidationFinding]
    ) -> None:
        logging.info("Checking Markdown file size limits")
        for path in files:
            self._size(package_dir, path, errors, warnings)
        logging.debug("Checked size limits for %s files", len(files))

    def _size(
        self, package_dir: Path, path: Path, errors: list[ValidationFinding], warnings: list[ValidationFinding]
    ) -> None:
        size = path.stat().st_size
        soft, hard = self._limits(package_dir, path)
        if size > hard:
            errors.append(ValidationFinding(path, "file exceeds the hard size limit", str(size)))
        elif size > soft:
            warnings.append(ValidationFinding(path, "file exceeds the soft size limit", str(size), "warning"))

    def _limits(self, package_dir: Path, path: Path) -> tuple[int, int]:
        if path.name == "sources.md":
            return SOURCE_SOFT_LIMIT, SOURCE_HARD_LIMIT
        if path.parent == package_dir:
            return self.FILE_LIMITS.get(path.name, (INDEX_SOFT_LIMIT, INDEX_HARD_LIMIT))
        if path.name == "INDEX.md":
            return 6_144, 10_240
        return 12_288, 20_480

    def _sources(self, package_dir: Path, errors: list[ValidationFinding]) -> set[str]:
        logging.info("Reading citation keys from sources.md")
        path = package_dir / "sources.md"
        if not path.exists():
            logging.debug("No sources.md exists for citation validation")
            return set()
        rows = self._table_rows(path)
        keys = {row[0] for row in rows if row}
        self._duplicate_source_keys(path, rows, errors)
        logging.debug("Read %s citation keys from sources.md", len(keys))
        return keys

    def _table_rows(self, path: Path) -> list[list[str]]:
        lines = path.read_text(encoding="utf-8").splitlines()
        rows = [line.strip("|").split("|") for line in lines if line.startswith("| ") and " - " not in line]
        return [[cell.strip() for cell in row] for row in rows[1:]]

    def _duplicate_source_keys(self, path: Path, rows: list[list[str]], errors: list[ValidationFinding]) -> None:
        keys = [row[0] for row in rows if row]
        duplicates = sorted({key for key in keys if keys.count(key) > 1})
        for key in duplicates:
            errors.append(ValidationFinding(path, "duplicate citation key", key))

    def _topics(self, package_dir: Path, sources: set[str], errors: list[ValidationFinding]) -> list[str]:
        logging.info("Validating topic files")
        names: list[str] = []
        for path in self._topic_paths(package_dir):
            names.append(self._topic(path, sources, errors))
        logging.debug("Validated %s topic files", len(names))
        return names

    def _topic_paths(self, package_dir: Path) -> list[Path]:
        return sorted((package_dir / "documents").glob("*/*.md")) if (package_dir / "documents").exists() else []

    def _topic(self, path: Path, sources: set[str], errors: list[ValidationFinding]) -> str:
        if path.name == "INDEX.md":
            return ""
        frontmatter, body = FrontMatterParser().parse(path.read_text(encoding="utf-8"))
        self._topic_frontmatter(path, frontmatter, sources, errors)
        self._cards(path, body, sources, errors)
        return str(frontmatter.get("topic", ""))

    def _topic_frontmatter(
        self, path: Path, frontmatter: dict[str, Any], sources: set[str], errors: list[ValidationFinding]
    ) -> None:
        missing = [name for name in ("topic", "domain", "document", "lifecycle", "sources") if name not in frontmatter]
        for name in missing:
            errors.append(ValidationFinding(path, "topic frontmatter field is missing", name))
        self._lifecycle_tags(path, frontmatter.get("lifecycle"), errors)
        self._source_tags(path, frontmatter.get("sources"), sources, errors)

    def _lifecycle_tags(self, path: Path, value: object, errors: list[ValidationFinding]) -> None:
        if not isinstance(value, list) or not value:
            errors.append(ValidationFinding(path, "topic has no life cycle tag", str(value)))
            return
        for tag in value:
            if tag not in LIFECYCLE_TAGS:
                errors.append(ValidationFinding(path, "topic has an invalid life cycle tag", str(tag)))

    def _source_tags(self, path: Path, value: object, sources: set[str], errors: list[ValidationFinding]) -> None:
        if not isinstance(value, list) or not value:
            errors.append(ValidationFinding(path, "topic has no citation key", str(value)))
            return
        for citation in value:
            self._citation_resolves(path, str(citation), sources, errors)

    def _cards(self, path: Path, body: str, sources: set[str], errors: list[ValidationFinding]) -> None:
        logging.info("Validating cards in %s", path.name)
        cards = [line for line in body.splitlines() if line.startswith("- ")]
        for line in cards:
            self._card(path, line, sources, errors)
        logging.debug("Validated %s cards in %s", len(cards), path.name)

    def _card(self, path: Path, line: str, sources: set[str], errors: list[ValidationFinding]) -> None:
        if not re.match(r"^- (MUST|SHOULD|INFO): ", line):
            errors.append(ValidationFinding(path, "card lacks a class mark", line[:80]))
        match = re.search(r"\[([A-Z0-9]{3,12} .+?)\]$", line)
        if not match:
            errors.append(ValidationFinding(path, "card lacks a citation key", line[:80]))
            return
        self._citation_resolves(path, match.group(1), sources, errors)

    def _citation_resolves(self, path: Path, citation: str, sources: set[str], errors: list[ValidationFinding]) -> None:
        key = citation.split(" ", 1)[0]
        if key not in sources:
            errors.append(ValidationFinding(path, "citation key does not resolve to sources.md", citation))

    def _skill_frontmatter(self, package_dir: Path, errors: list[ValidationFinding]) -> None:
        logging.info("Validating SKILL.md frontmatter")
        path = package_dir / "SKILL.md"
        if not path.exists():
            return
        frontmatter, _ = FrontMatterParser().parse(path.read_text(encoding="utf-8"))
        for name in ("name", "description", "license", "metadata"):
            if name not in frontmatter:
                errors.append(ValidationFinding(path, "SKILL.md frontmatter field is missing", name))
        self._skill_name(path, frontmatter.get("name"), package_dir.name, errors)
        self._skill_description(path, frontmatter.get("description"), errors)
        self._skill_metadata(path, frontmatter.get("metadata"), errors)
        logging.debug("Validated SKILL.md frontmatter")

    def _skill_name(self, path: Path, value: object, package_name: str, errors: list[ValidationFinding]) -> None:
        if value != package_name:
            errors.append(ValidationFinding(path, "SKILL.md name does not match the package directory", str(value)))

    def _skill_description(self, path: Path, value: object, errors: list[ValidationFinding]) -> None:
        if not isinstance(value, str):
            errors.append(ValidationFinding(path, "SKILL.md description is not text", str(type(value))))
            return
        if not 250 <= len(value) <= 1200:
            errors.append(ValidationFinding(path, "SKILL.md description length is invalid", str(len(value))))

    def _skill_metadata(self, path: Path, value: object, errors: list[ValidationFinding]) -> None:
        if not isinstance(value, dict):
            errors.append(ValidationFinding(path, "SKILL.md metadata is not a map", str(type(value))))
            return
        for name in ("feature", "domain", "documents", "topics", "source_pages", "built"):
            if name not in value:
                errors.append(ValidationFinding(path, "SKILL.md metadata field is missing", name))
        self._metadata_types(path, value, errors)

    def _metadata_types(self, path: Path, value: dict[str, object], errors: list[ValidationFinding]) -> None:
        integer_fields = ("documents", "topics", "source_pages")
        for name in integer_fields:
            if name in value and not isinstance(value[name], int):
                errors.append(ValidationFinding(path, "SKILL.md metadata field is not an integer", name))

    def _links(self, package_dir: Path, files: list[Path], errors: list[ValidationFinding]) -> None:
        logging.info("Checking internal Markdown links")
        for path in files:
            self._file_links(package_dir, path, errors)
        logging.debug("Checked internal links for %s files", len(files))

    def _file_links(self, package_dir: Path, path: Path, errors: list[ValidationFinding]) -> None:
        text = path.read_text(encoding="utf-8")
        links = re.findall(r"\]\(([^):#]+(?:\.md)?)\)|`([^`]+\.md)`", text)
        for first, second in links:
            self._link(package_dir, path, first or second, errors)

    def _link(self, package_dir: Path, path: Path, target: str, errors: list[ValidationFinding]) -> None:
        if target.startswith("http") or target == "INDEX.md":
            return
        resolved = (
            (path.parent / target).resolve()
            if not target.startswith("documents/")
            else (package_dir / target).resolve()
        )
        if not resolved.exists():
            errors.append(ValidationFinding(path, "internal link is broken", target))

    def _orphans(self, package_dir: Path, files: list[Path], errors: list[ValidationFinding]) -> None:
        logging.info("Checking for orphan topic files")
        index_text = "\n".join(path.read_text("utf-8") for path in files if path.name == "INDEX.md")
        for topic in self._topic_paths(package_dir):
            if topic.name != "INDEX.md" and topic.name not in index_text:
                errors.append(ValidationFinding(topic, "topic file is absent from the index", topic.name))
        logging.debug("Checked orphan status for topic files")

    def _duplicates(self, package_dir: Path, names: list[str], errors: list[ValidationFinding]) -> None:
        logging.info("Checking for duplicate topic names")
        values = [name for name in names if name]
        for name in sorted({name for name in values if values.count(name) > 1}):
            errors.append(ValidationFinding(package_dir, "duplicate topic name", name))
        logging.debug("Checked duplicate topic names")

    def _zero(self, files: list[Path], errors: list[ValidationFinding], package_dir: Path) -> None:
        if files:
            return
        errors.append(ValidationFinding(package_dir, "validator checked zero files", "0"))
