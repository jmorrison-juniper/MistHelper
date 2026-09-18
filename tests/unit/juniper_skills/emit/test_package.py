"""Unit tests for Juniper domain skill package assembly."""

from __future__ import annotations

import shutil
from pathlib import Path

from src.juniper_skills.emit.package import (
    CitationKeyAllocator,
    DocumentPackageInput,
    IndexRenderer,
    RouteTableBuilder,
    SkillPackageAssembler,
    SkillPackageValidator,
    TopicRoute,
)


class EmitTestWorkspace:
    """Create project-local test workspaces without using a system temp path."""

    root = Path("data") / "juniper_skills" / "emit-tests"

    def reset(self, name: str) -> Path:
        path = self.root / name  # Keep test files under the repository data tree.
        if path.exists():  # Remove old data so each test starts with a known state.
            shutil.rmtree(path)  # Delete only the named test directory.
        path.mkdir(parents=True, exist_ok=True)  # Create the directory for this test.
        return path  # Return the workspace path to the test.

    def document(self, root: Path, slug: str, title: str, lifecycle: str = "day1") -> DocumentPackageInput:
        document_dir = root / "out" / "juniper-junos-fundamentals" / "documents" / slug  # Use a real package tree.
        document_dir.mkdir(parents=True, exist_ok=True)  # Create the source document tree.
        self._topic(document_dir, "00-overview.md", title, lifecycle)  # Add the required overview topic.
        self._index(document_dir, title, lifecycle)  # Add the level 2 index that the assembler must read.
        markdown = Path("guides") / f"{slug}.md"  # Store a relative harvest path for sources.md.
        pdf = Path("pdf") / f"{slug}.pdf"  # Store a relative PDF path for sources.md.
        return DocumentPackageInput(slug, title, "guides", 10, document_dir, (markdown,), pdf, "https://example.test")

    def _topic(self, document_dir: Path, name: str, title: str, lifecycle: str) -> None:
        text = (
            f"---\ntopic: {title}\ndomain: junos-fundamentals\ndocument: {document_dir.name}\n"
            f"lifecycle: [{lifecycle}]\nsources: [DOC p.1-2]\n---\n\n"
            f"# {title}\n\n- INFO: Read about {title}. [DOC p.1-2]\n"
        )  # Build one contract-shaped source topic.
        (document_dir / name).write_text(text, encoding="utf-8")  # Write the source topic for the assembler.

    def _index(self, document_dir: Path, title: str, lifecycle: str) -> None:
        text = (
            f"# {title} index\n\n| Topic | Pages | Life cycle | Subject |\n| - | - | - | - |\n"
            f"| {title} | p.1-2 | {lifecycle} | Use {title} for a real operator question. |\n"
        )  # Build the segmenter subject table that the assembler must read.
        (document_dir / "INDEX.md").write_text(text, encoding="utf-8")  # Write the existing level 2 index.


class TestSkillPackageEmitter:
    """Verify the assembler, key allocator, coverage report, and validator."""

    def test_index_degrades_when_topic_rows_exceed_hard_limit(self) -> None:
        workspace = EmitTestWorkspace().reset("degrade")  # Create isolated project-local test data.
        document = EmitTestWorkspace().document(workspace, "doc-one", "Large Route Guide")  # Build one source.
        routes = self._many_routes(900)  # Create enough rows to exceed the level 1 hard limit.
        coverage = {"day0": 1, "day1": 900, "day2": 0, "day2plus": 0}  # Provide measured coverage counts.
        text = IndexRenderer("junos-fundamentals", (document,), routes, coverage).render()  # Render the index.
        assert len(text.encode("utf-8")) <= 40_960  # The renderer must stay below the hard limit.
        assert "Detail lives in the document index." in text  # The renderer must state the degradation method.

    def test_allocator_persists_collision_free_keys(self) -> None:
        workspace = EmitTestWorkspace().reset("keys")  # Create isolated project-local test data.
        allocator = CitationKeyAllocator(workspace / "factory.db")  # Use a local SQLite allocation store.
        first = allocator.allocate("junos-fundamentals", "doc-one", "Day One Junos Guide")  # Allocate key one.
        second = allocator.allocate("junos-fundamentals", "doc-two", "Day One Junos Guide")  # Allocate key two.
        again = allocator.allocate("junos-fundamentals", "doc-one", "Changed Title")  # Verify stable reuse.
        assert first != second  # A collision must receive a distinct key.
        assert first == again  # A persisted allocation must not change when the title changes.

    def test_skill_route_rows_keep_concrete_destinations(self) -> None:
        workspace = EmitTestWorkspace().reset("routes")  # Create isolated project-local test data.
        document = EmitTestWorkspace().document(workspace, "doc-one", "Routing Guide")  # Build one source.
        rows = RouteTableBuilder((document,), self._many_routes(2)).rows(10_000)  # Build a small route table.
        assert "`documents/doc-one/INDEX.md`" in rows  # A grouped route must point at the document index.
        assert rows.count("`INDEX.md`") == 0  # A topic-sized route table must not redirect every row.

    def test_skill_route_rows_use_user_vocabulary_clusters(self) -> None:
        workspace = EmitTestWorkspace().reset("cluster")  # Create isolated project-local test data.
        document = EmitTestWorkspace().document(workspace, "doc-one", "Cluster Guide")  # Build one source.
        routes = self._cluster_routes()  # Build routes that model the pilot document subjects.
        rows = RouteTableBuilder((document,), routes).rows(10_000)  # Build the SKILL.md route table.
        assert "Filtering or searching command output" in rows  # The route must name user question terms.
        assert "`documents/doc-one/08-filtering-output.md`" in rows  # The route must point at the topic file.
        assert "Read about Filtering Output" not in rows  # The route must not restate the file name.
        assert rows.count("\n|") <= 20  # The route table must be a cluster list, not a directory listing.

    def test_sources_read_converted_frontmatter_fields(self) -> None:
        workspace = EmitTestWorkspace().reset("sources")  # Create isolated project-local test data.
        source = workspace / "harvest" / "guides" / "source.md"  # Create a source file with converter metadata.
        source.parent.mkdir(parents=True, exist_ok=True)  # Create the harvest-like directory.
        source.write_text(self._source_frontmatter(), encoding="utf-8")  # Write the source metadata.
        document = DocumentPackageInput(  # Build an input that lets sources.md read the real metadata.
            "doc-one",
            "Fallback Title",
            "guides",
            1,
            EmitTestWorkspace().document(workspace, "doc-one", "Topic Guide").document_dir,
            (source,),
            Path("guides") / "source.pdf",
            "https://example.test/source",
        )
        result = SkillPackageAssembler(workspace / "factory.db").assemble(
            "junos-fundamentals", workspace / "out", (document,), self._taxonomy(workspace)
        )  # Assemble sources.md from the metadata-bearing source.
        sources = (result.package_dir / "sources.md").read_text(encoding="utf-8")  # Read the attribution table.
        assert "Source Title" in sources  # The source title must come from the source frontmatter.
        assert "Source Author" in sources  # The author must come from the source frontmatter.
        assert "| 77 |" in sources  # The page count must come from the source frontmatter.

    def test_assembler_does_not_write_topic_files(self) -> None:
        workspace = EmitTestWorkspace().reset("preserve")  # Create isolated project-local test data.
        document = EmitTestWorkspace().document(workspace, "doc-one", "Preserve Guide", "day2")  # Build source.
        topic_path = document.document_dir / "00-overview.md"  # Select the topic that must remain unchanged.
        before = topic_path.read_text(encoding="utf-8")  # Capture the exact topic content before assembly.
        SkillPackageAssembler(workspace / "factory.db").assemble(
            "junos-fundamentals", workspace / "out", (document,), self._taxonomy(workspace)
        )  # Assemble level 1 files only.
        after = topic_path.read_text(encoding="utf-8")  # Capture the exact topic content after assembly.
        assert after == before  # The assembler must never replace real topic content with a stub.

    def test_coverage_gap_is_written_to_level_one_index(self) -> None:
        workspace = EmitTestWorkspace().reset("coverage")  # Create isolated project-local test data.
        document = EmitTestWorkspace().document(workspace, "doc-one", "Coverage Guide", "day1")  # Build source.
        taxonomy = self._taxonomy(workspace)  # Write the taxonomy row that feeds the SKILL description.
        assembler = SkillPackageAssembler(workspace / "factory.db")  # Use a local allocation store.
        result = assembler.assemble("junos-fundamentals", workspace / "out", (document,), taxonomy)  # Assemble.
        index_text = (result.package_dir / "INDEX.md").read_text(encoding="utf-8")  # Read the generated index.
        assert "| day2plus | 0 | gap |" in index_text  # The coverage table must show the missing stage.
        assert "- day2plus has no topic." in index_text  # The gap section must name the missing stage.

    def test_validator_reports_missing_life_cycle_tag(self) -> None:
        workspace = EmitTestWorkspace().reset("validator")  # Create isolated project-local test data.
        document = EmitTestWorkspace().document(workspace, "doc-one", "Broken Guide", "day1")  # Build source.
        taxonomy = self._taxonomy(workspace)  # Write the taxonomy row that feeds the SKILL description.
        result = SkillPackageAssembler(workspace / "factory.db").assemble(
            "junos-fundamentals", workspace / "out", (document,), taxonomy
        )  # Assemble a valid package before introducing one real violation.
        topic_path = result.package_dir / "documents" / "doc-one" / "00-overview.md"  # Select the topic file.
        topic_text = topic_path.read_text(encoding="utf-8")  # Read the generated topic text.
        topic_path.write_text(topic_text.replace("lifecycle: [day1]", "lifecycle: []"), "utf-8")  # Break it.
        validation = SkillPackageValidator().validate(result.package_dir)  # Run the validator on the package.
        messages = [finding.message for finding in validation.errors]  # Collect messages for a precise assertion.
        assert "topic has no life cycle tag" in messages  # The validator must catch the real violation.

    def _many_routes(self, count: int) -> list[TopicRoute]:
        return [
            TopicRoute(
                f"Topic {index}",
                f"Read about detailed Junos configuration route subject number {index} with many routing words.",
                ("day1",),
                "JUNOS p.1-2",
                "p.1-2",
                Path("documents") / "doc-one" / f"{index:02d}-topic.md",
            )
            for index in range(count)
        ]  # Return route rows that make the level 1 index exceed the hard limit.

    def _cluster_routes(self) -> list[TopicRoute]:
        return [
            TopicRoute(
                "Filtering Output",
                "Use match, count, and except pipe filters to read operational command output.",
                ("day2",),
                "JUNOS p.64-70",
                "p.64-70",
                Path("documents") / "doc-one" / "08-filtering-output.md",
            ),
            TopicRoute(
                "CLI Help",
                "Shows help commands that find syntax, topics, and command options.",
                ("day1", "day2"),
                "JUNOS p.70-77",
                "p.70-77",
                Path("documents") / "doc-one" / "09-cli-help.md",
            ),
        ]  # Return pilot-like topics that must become user-language clusters.

    def _source_frontmatter(self) -> str:
        return (
            "---\ntitle: Source Title\nauthor: Source Author\npages: 77\n"
            "creationDate: D:20200101000000-07'00'\nmodDate: D:20210101000000-07'00'\n---\n\nBody.\n"
        )  # Return source metadata that the attribution table must publish.

    def _taxonomy(self, workspace: Path) -> Path:
        taxonomy = workspace / "domain-taxonomy.md"  # Create a local contract fragment for this test.
        taxonomy.write_text(
            "| Priority | Skill | Routing keywords | Assignment rule |\n"
            "| -: | - | - | - |\n"
            "| 15 | `juniper-junos-fundamentals` | Junos, commit, rollback, interfaces. | Match Junos. |\n",
            encoding="utf-8",
        )  # Write only the row needed by the assembler.
        return taxonomy  # Return the taxonomy path to the test.
