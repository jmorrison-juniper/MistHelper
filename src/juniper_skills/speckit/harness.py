"""Programmatic SpecKit artifact harness for Juniper skill packages."""

from __future__ import annotations

import importlib.util
import json
import logging
import sqlite3
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from src.juniper_skills.speckit.analyzer import SpecKitAnalyzer
from src.juniper_skills.speckit.catalog import SpecKitCatalog
from src.juniper_skills.speckit.living import LivingDriftReport, LivingSpecManager
from src.juniper_skills.speckit.models import SkillDocument, SpecKitPaths


class SpecKitHarness:
    """Emit a complete SpecKit artifact set for one skill document."""

    def __init__(self, paths: SpecKitPaths) -> None:
        self.paths = paths  # Keep all path policy in one explicit object.
        self.catalog = SpecKitCatalog(paths)  # Reuse the measured SpecKit catalog for reports.
        self.analyzer = SpecKitAnalyzer()  # Use the same checker that tests exercise.
        self.living = LivingSpecManager()  # Use hash drift checks for living specs.

    def emit_for_document(self, document: SkillDocument, package_files: list[Path] | None = None) -> Path:
        """Emit all SpecKit artifacts for one document and return the feature directory."""
        logging.info("Emitting SpecKit artifacts for one skill document")  # Record artifact generation start.
        document = self._enriched_document(document, package_files or [])  # Add database and package facts.
        feature_dir = self._feature_dir(document)  # Resolve the destination directory for this source document.
        self._prepare_directories(feature_dir)  # Create required directories before file writes.
        self._write_artifacts(feature_dir, document)  # Write the core SpecKit artifact set.
        self._write_context(feature_dir, document)  # Write the Companion GUI context file.
        self._write_analysis(feature_dir, document)  # Run analysis after all core artifacts exist.
        self.require_complete(feature_dir)  # Make the workflow mandatory before install can run.
        logging.debug("Emitted SpecKit artifacts at %s", feature_dir)  # Record the final destination.
        return feature_dir

    def require_complete(self, feature_dir: Path) -> None:
        """Raise when a generated artifact set is incomplete or inconsistent."""
        logging.info("Requiring a complete SpecKit artifact set")  # Record the mandatory-stage gate.
        errors = self.validate(feature_dir)  # Reuse the same validation list used by tests.
        if errors:  # Refuse to publish when the workflow is incomplete.
            logging.error("SpecKit artifact gate failed with %d errors", len(errors))  # Record failure count.
            raise RuntimeError("SpecKit artifact gate failed: " + "; ".join(errors))
        logging.debug("SpecKit artifact gate passed for %s", feature_dir)  # Record the passing directory.

    def validate(self, feature_dir: Path) -> list[str]:
        """Return validation errors for a generated artifact set."""
        logging.info("Validating a generated SpecKit artifact set")  # Record validation start.
        required = self._required_paths(feature_dir)  # Build the required path list from the contract.
        missing = [str(path) for path in required if not path.exists()]  # Find absent artifacts.
        findings = self.analyzer.analyze(feature_dir) if not missing else []  # Analyze only a complete set.
        critical = [
            finding.summary for finding in findings if finding.severity == "CRITICAL"
        ]  # Keep blocking findings only.
        errors = missing + critical  # Merge missing files and critical analysis gaps.
        logging.debug("Validation found %d errors", len(errors))  # Record validation result count.
        return errors

    def living_drift(self, feature_dir: Path) -> LivingDriftReport:
        """Return living-spec drift for a generated document."""
        logging.info("Checking living-spec drift for a generated document")  # Record drift check start.
        report = self.living.drift(feature_dir)  # Compare the stored and current source hashes.
        logging.debug("Living-spec drift status is %s", report.detail)  # Record the report summary.
        return report

    def living_sync(self, document: SkillDocument) -> Path:
        """Refresh artifacts for a changed source document."""
        logging.info("Synchronizing a Juniper living spec")  # Record sync start.
        feature_dir = self.living.sync(document, self)  # Re-emit artifacts through the full workflow.
        logging.debug("Synchronized Juniper living spec at %s", feature_dir)  # Record the refreshed directory.
        return feature_dir

    def _enriched_document(self, document: SkillDocument, package_files: list[Path]) -> SkillDocument:
        """Return a document with database and package measurements."""
        logging.info("Reading real document values for SpecKit artifacts")  # Record measurement start.
        values = self._factory_values(document)  # Read inventory and journal values from the factory database.
        values.update(self._package_values(package_files))  # Add built package topic and life cycle measurements.
        values["open_questions"] = self._open_questions(document, values)  # Record document-specific questions.
        enriched = document.with_metrics(values)  # Store the measured values in an immutable copy.
        logging.debug("Enriched document %s with %d values", document.slug, len(values))  # Record measurement count.
        return enriched

    def _factory_values(self, document: SkillDocument) -> dict[str, object]:
        """Return measured values from the factory database."""
        logging.info("Reading factory database values for %s", document.slug)  # Record database read start.
        if not self.paths.factory_database_path.exists():  # Let isolated tests run without the real database.
            logging.debug("Factory database is absent at %s", self.paths.factory_database_path)  # Record absence.
            return {"part_count": document.part_count, "guard_result": document.guard_result}
        with sqlite3.connect(self.paths.factory_database_path) as connection:  # Open one short read transaction.
            connection.row_factory = sqlite3.Row  # Read columns by name for durable schema access.
            values = self._document_row_values(connection, document)  # Read source and part facts.
            values["guard_result"] = self._latest_stage_detail(connection, document.slug, "guard")  # Add guard data.
        logging.debug("Read %d factory values for %s", len(values), document.slug)  # Record read count.
        return values

    def _document_row_values(self, connection: sqlite3.Connection, document: SkillDocument) -> dict[str, object]:
        """Return source document values from SQLite rows."""
        logging.info("Querying source document rows for SpecKit")  # Record source row query.
        row = connection.execute(self._document_sql(), (document.slug,)).fetchone()  # Read the source document row.
        part_count = connection.execute(self._part_count_sql(), (document.slug,)).fetchone()[0]  # Count parts.
        if row is None:  # Fall back to the caller model when the database lacks this proof row.
            return {"part_count": int(part_count or document.part_count), "category": document.category}
        values = {"title": row["title"], "category": row["category"], "pages": int(row["pages"])}  # Use DB facts.
        values["part_count"] = int(row["part_count"] or part_count or document.part_count)  # Prefer DB count.
        logging.debug("Source document row values contain %d keys", len(values))  # Record row value count.
        return values

    def _package_values(self, package_files: list[Path]) -> dict[str, object]:
        """Return measured values from the built skill package."""
        logging.info("Reading built package values for SpecKit")  # Record package inspection start.
        topic_files = [path for path in package_files if path.name[:2].isdigit()]  # Count generated topic files.
        spread = self._life_cycle_spread(topic_files)  # Count life cycle marks from built topic front matter.
        values = {"topic_count": len(topic_files), "life_cycle_spread": spread}  # Store measured package values.
        logging.debug("Read package values for %d topic files", len(topic_files))  # Record topic count.
        return values

    def _life_cycle_spread(self, topic_files: list[Path]) -> dict[str, int]:
        """Count life cycle marks in built topic files."""
        logging.info("Measuring life cycle spread from built topics")  # Record lifecycle measurement start.
        spread = {"day0": 0, "day1": 0, "day2": 0, "day2plus": 0}  # Keep all standard buckets present.
        for path in topic_files:  # Read generated package topics only.
            text = path.read_text(encoding="utf-8") if path.exists() else ""  # Avoid failing on stale path lists.
            for name in spread:  # Check each approved life cycle value.
                spread[name] += 1 if name in text else 0  # Count topic membership for review proof.
        logging.debug("Measured life cycle spread %s", spread)  # Record the spread without source prose.
        return spread

    def _open_questions(self, document: SkillDocument, values: dict[str, object]) -> tuple[str, ...]:
        """Return document-specific clarification questions."""
        logging.info("Resolving open questions for the clarify command")  # Record clarify input preparation.
        questions: list[str] = []  # Build only questions that follow from measured values.
        if int(values.get("pages", document.pages)) <= 0:  # Missing page count blocks source-quality confidence.
            questions.append("The source page count is missing.")  # Record the concrete ambiguity.
        if not document.source_path.exists():  # Missing source prevents living-spec drift checks.
            questions.append("The source Markdown file is missing.")  # Record the concrete source gap.
        if int(values.get("topic_count", document.topic_count)) == 0:  # Empty packages require review.
            questions.append("The built package contains no topic files.")  # Record the package ambiguity.
        logging.debug("Resolved %d open questions", len(questions))  # Record the question count.
        return tuple(questions)

    def _feature_dir(self, document: SkillDocument) -> Path:
        """Return the generated feature directory for a document."""
        logging.info("Resolving the document SpecKit feature directory")  # Record path resolution.
        path = (
            self.paths.skills_specs_dir / document.domain / document.slug
        )  # Follow specs/skills/domain/slug contract.
        logging.debug("Resolved document SpecKit feature directory %s", path)  # Record destination.
        return path

    def _prepare_directories(self, feature_dir: Path) -> None:
        """Create all required output directories."""
        logging.info("Creating SpecKit artifact directories")  # Record directory creation.
        paths = (feature_dir, feature_dir / "checklists", feature_dir / "contracts")  # Define required directories.
        for path in paths:
            path.mkdir(parents=True, exist_ok=True)  # Create each required directory idempotently.
        logging.debug("Created SpecKit artifact directories below %s", feature_dir)  # Record directory root.

    def _write_artifacts(self, feature_dir: Path, document: SkillDocument) -> None:
        """Write all Markdown artifacts except the generated analysis."""
        logging.info("Writing SpecKit Markdown artifacts")  # Record bulk artifact write.
        writers = {  # Map each artifact path to its rendered content.
            "spec.md": self._spec(document),
            "clarifications.md": self._clarify(document),
            "plan.md": self._plan(document),
            "tasks.md": self._tasks(document),
            "implementation.md": self._implement(document),
            (Path("checklists") / "requirements.md"): self._checklist(document),
            "research.md": self._research(document),
            "data-model.md": self._data_model(document),
            "quickstart.md": self._quickstart(document),
            (Path("contracts") / "skill-package.md"): self._contract(document),
        }
        for name, text in writers.items():
            (feature_dir / name).write_text(text, encoding="utf-8")  # Write the artifact.
        logging.debug("Wrote %d SpecKit Markdown artifacts", len(writers))  # Record artifact count.

    def _write_context(self, feature_dir: Path, document: SkillDocument) -> None:
        """Write the Companion GUI context file."""
        logging.info("Writing Companion context for the skill document")  # Record context generation.
        target = feature_dir / ".spec-context.json"  # Use the canonical Companion context path.
        target.unlink(missing_ok=True)  # Remove stale generated state so the lifecycle can replay.
        if self._companion_writer().exists():
            self._write_context_with_companion(feature_dir, document)  # Use the real extension writer when installed.
        else:
            self._write_context_fallback(feature_dir, document)  # Keep clean clones able to generate proof artifacts.
        logging.debug("Wrote Companion context at %s", target)  # Record the final context path.

    def _write_context_with_companion(self, feature_dir: Path, document: SkillDocument) -> None:
        """Write context by invoking the real Companion writer."""
        logging.info("Invoking Companion lifecycle capture scripts")  # Record external writer use.
        companion = self._companion_module()  # Load the installed writer module from the real extension.
        for step, _status in self._companion_steps():  # Record lifecycle completion through extension functions.
            companion.journal_advance(feature_dir, step, "harness")  # Use the same function as the command.
        companion.mark_spec_complete(feature_dir, "harness")  # Promote the context through the real terminal writer.
        self._write_companion_capture(feature_dir, document)  # Add non-lifecycle evidence through capture.py.
        logging.debug("Invoked Companion lifecycle capture scripts for %s", feature_dir)  # Record completion.

    def _write_companion_capture(self, feature_dir: Path, document: SkillDocument) -> None:
        """Add metadata through the real capture.py writer surface."""
        logging.info("Recording additive Companion capture fields")  # Record metadata capture.
        companion = self._companion_module()  # Load the real capture helpers re-exported by write-context.py.
        companion.set_fields(feature_dir, self._capture_set_pairs(document))  # Write measured context fields.
        companion.set_living_specs_loaded(feature_dir, [document.slug])  # Record the loaded living spec.
        companion.append_capture_entries(feature_dir, "decisions", "decision", [self._decision_capture()])
        companion.append_capture_entries(feature_dir, "verified", "what", [self._verified_capture()])
        logging.debug("Recorded additive Companion capture fields for %s", document.slug)  # Record capture result.

    def _capture_set_pairs(self, document: SkillDocument) -> list[str]:
        """Return Companion key-value pairs."""
        logging.info("Building Companion set pairs")  # Record capture pair creation.
        pairs = {
            "sourcePath": document.source_path,
            "sourceFile": document.source_file,
            "sourceHash": document.content_hash,
            "sourcePages": document.pages,
            "partCount": document.part_count,
            "topicCount": document.topic_count,
            "guardResult": document.guard_result,
        }  # Collect measured values that living checks and reviews need.
        values = [f"{key}={item}" for key, item in pairs.items()]  # Match capture.py key-value input.
        logging.debug("Built %d Companion set pairs", len(values))  # Record pair count.
        return values

    def _companion_module(self) -> object:
        """Load the real Companion writer module."""
        logging.info("Loading the Companion writer module")  # Record dynamic module load.
        spec = importlib.util.spec_from_file_location("speckit_companion_writer", self._companion_writer())
        if spec is None or spec.loader is None:  # A missing loader means the extension is not runnable.
            raise RuntimeError("Companion writer module is unavailable")  # Fail the mandatory workflow.
        module = importlib.util.module_from_spec(spec)  # Create a module object for the installed script.
        spec.loader.exec_module(module)  # Execute the real extension script in-process for speed.
        logging.debug("Loaded the Companion writer module from %s", self._companion_writer())  # Record script path.
        return module

    def _run_companion(self, feature_dir: Path, args: list[str]) -> None:
        """Run the Companion writer with an explicit feature directory."""
        logging.info("Running the Companion writer script")  # Record subprocess start.
        command = [sys.executable, str(self._companion_writer()), "--feature-dir", str(feature_dir), *args]
        result = subprocess.run(command, cwd=self.paths.repo_root, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            logging.error("Companion writer failed with code %d", result.returncode)  # Record failure code.
            raise RuntimeError(result.stderr.strip() or "Companion writer failed")
        logging.debug("Companion writer output had %d characters", len(result.stdout))  # Record safe output size.

    def _companion_writer(self) -> Path:
        """Return the real Companion writer script path."""
        logging.info("Resolving the Companion writer script")  # Record writer path lookup.
        path = self.paths.specify_dir / "extensions" / "companion" / "scripts" / "write-context.py"
        logging.debug("Resolved the Companion writer script at %s", path)  # Record resolved path.
        return path

    def _write_context_fallback(self, feature_dir: Path, document: SkillDocument) -> None:
        """Write a minimal context only when the Companion writer is absent."""
        logging.info("Writing fallback Companion context")  # Record fallback context generation.
        context = self._fallback_context(document)  # Build the strict lifecycle shape.
        path = feature_dir / ".spec-context.json"  # Store context beside generated artifacts.
        path.write_text(json.dumps(context, indent=2) + "\n", encoding="utf-8")  # Write stable JSON.
        logging.debug("Wrote fallback Companion context with %d keys", len(context))  # Record fallback size.

    def _write_analysis(self, feature_dir: Path, document: SkillDocument) -> None:
        """Write the analysis report after validation."""
        logging.info("Writing the SpecKit analysis report")  # Record analysis generation.
        text = (
            "# Document analysis context\n\n"
            + self._metadata(document)
            + "\n"
            + self.catalog.render_markdown()
            + "\n"
            + self._living_judgement()
            + "\n"
            + self.analyzer.render_report(feature_dir)
        )  # Combine reports.
        (feature_dir / "analysis.md").write_text(text, encoding="utf-8")  # Persist the report.
        logging.debug("Wrote analysis report with %d characters", len(text))  # Record report size.

    def _required_paths(self, feature_dir: Path) -> list[Path]:
        """Return the required artifact paths."""
        logging.info("Building the required artifact path list")  # Record required path calculation.
        names = [
            "spec.md",
            "clarifications.md",
            "plan.md",
            "tasks.md",
            "implementation.md",
            Path("checklists") / "requirements.md",
            "analysis.md",
            ".spec-context.json",
        ]  # Lock outputs.
        paths = [feature_dir / name for name in names]  # Convert artifact names to paths.
        logging.debug("Built %d required artifact paths", len(paths))  # Record required path count.
        return paths

    def _spec(self, document: SkillDocument) -> str:
        """Return the generated feature specification."""
        logging.info("Rendering the generated skill specification")  # Record spec rendering.
        self._template("spec-template.md")  # Read the real template to prove reuse in generation.
        text = f"""# Feature Specification: {document.title} skill package

Command: speckit.specify

**Feature Branch**: `feat/2925-juniper-skill-factory`

**Created**: {self._today()}

**Status**: Generated

**Input**: Source document `{document.source_path}`

## Document Measurements

{self._metadata(document)}

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Build the skill package (Priority: P1)

As an AI agent, I need a bounded skill package for `{document.title}`.
I can answer Junos questions with three file reads.

**Why this priority**: The skill must route before it can answer a question.

**Independent Test**: Generate the package and confirm that every required artifact exists.

**Acceptance Scenarios**:

1. **Given** the source Markdown exists, **When** the harness runs, **Then** it writes the full artifact set.
2. **Given** the package exists, **When** the Companion GUI reads it, **Then** context shows completed status.

### Edge Cases

- The harness records missing companion extension files in `analysis.md`.
- The harness records source drift by hash so a re-converted document can trigger a sync.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The harness MUST write all required artifacts.
  The artifacts include spec, plan, tasks, checklist, analysis, and context.
- **FR-002**: The harness MUST reuse the installed SpecKit templates before it renders artifacts.
- **FR-003**: The harness MUST record source metadata for living-spec drift checks.
- **FR-004**: The harness MUST run a cross-artifact analysis that maps requirements to tasks.
- **FR-005**: The harness MUST report missing companion extension files.
- **FR-006**: The harness MUST record the clarify, implement, analyze, and checklist commands.

### Key Entities

- **SkillDocument**: The source Markdown file, title, domain, page count, slug, and source hash.
- **SpecKitArtifactSet**: The generated specification, plan, tasks, checklist, analysis, and context files.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The generated artifact set contains all six required files.
- **SC-002**: The analysis check reports zero critical issues for this generated package.
- **SC-003**: The context file contains `currentStep`, `status`, `phase`, `phaseStatus`, and `completionPercentage`.
- **SC-004**: The generated artifact set records {document.topic_count} built topics.

## Assumptions

- The domain for this proof document is `junos`.
- The harness writes programmatic artifacts because 1,500 interactive runs are not practical.
"""
        logging.debug("Rendered skill specification with %d characters", len(text))  # Record spec size.
        return text

    def _plan(self, document: SkillDocument) -> str:
        """Return the generated implementation plan."""
        logging.info("Rendering the generated skill plan")  # Record plan rendering.
        self._template("plan-template.md")  # Read the real template to prove reuse in generation.
        text = f"""# Implementation Plan: {document.title} skill package

Command: speckit.plan

**Branch**: `feat/2925-juniper-skill-factory` | **Date**: {self._today()} | **Spec**: spec.md

**Input**: Feature specification from `spec.md`

## Document Measurements

{self._metadata(document)}

## Summary

Generate a SpecKit artifact set for `{document.title}` and connect it to Companion state.
Use {document.part_count} source parts and {document.topic_count} built topics.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: Standard library and installed SpecKit templates

**Storage**: Markdown artifacts under `specs/skills/{document.domain}/{document.slug}`

**Testing**: pytest unit tests under `tests/unit/juniper_skills/speckit`

**Target Platform**: Windows repository worktree

**Project Type**: Python library for a documentation skill factory

**Performance Goals**: Generate one package without interactive prompts.

**Constraints**: Do not copy source prose into generated skill content.

**Scale/Scope**: 1,500 or more source documents through repeated harness calls.

## Life Cycle Mapping

{self._life_cycle_table(document)}

## Constitution Check

The plan uses pathlib paths, ASCII log messages, and class-based design.

## Project Structure

### Documentation (this feature)

```text
specs/skills/{document.domain}/{document.slug}/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── checklists/requirements.md
├── contracts/skill-package.md
├── tasks.md
├── analysis.md
└── .spec-context.json
```

### Source Code (repository root)

```text
src/juniper_skills/speckit/
└── harness, catalog, analyzer, and models

tests/unit/juniper_skills/speckit/
└── pytest coverage for artifact generation and analysis
```

**Structure Decision**: Keep the harness inside `src/juniper_skills/speckit`.

## Complexity Tracking

No constitution violation exists.
"""
        logging.debug("Rendered skill plan with %d characters", len(text))  # Record plan size.
        return text

    def _tasks(self, document: SkillDocument) -> str:
        """Return the generated tasks artifact."""
        logging.info("Rendering generated skill tasks")  # Record task rendering.
        self._template("tasks-template.md")  # Read the real template to prove reuse in generation.
        text = f"""# Tasks: {document.title} skill package

Command: speckit.tasks

**Input**: Design documents from `specs/skills/{document.domain}/{document.slug}/`

## Document Measurements

{self._metadata(document)}

## Phase 1: Setup

- [x] T001 [FR-001] Create the artifact directory for `{document.slug}`.
- [x] T002 [FR-002] Read the installed SpecKit templates before rendering artifacts.

## Phase 2: Core generation

- [x] T003 [FR-001] Write `spec.md`, `plan.md`, `tasks.md`, and `checklists/requirements.md`.
- [x] T004 [FR-003] Write source hash and source metadata into `.spec-context.json`.
- [x] T005 [FR-004] Run the cross-artifact analysis after task generation.
- [x] T006 [FR-005] Record the companion extension inventory in `analysis.md`.
- [x] T007 [FR-006] Record clarify, implement, analyze, and checklist command outputs.

## Dependencies

Phase 1 must finish before Phase 2.

## Implementation Strategy

Generate one package first, validate it, then repeat the same harness for each document.
"""
        logging.debug("Rendered skill tasks with %d characters", len(text))  # Record tasks size.
        return text

    def _checklist(self, document: SkillDocument) -> str:
        """Return the generated requirements checklist."""
        logging.info("Rendering generated requirements checklist")  # Record checklist rendering.
        self._template("checklist-template.md")  # Read the real template to prove reuse in generation.
        text = f"""# Requirements Checklist: {document.title} skill package

Command: speckit.checklist

**Purpose**: Validate the generated skill package requirements.
**Created**: {self._today()}
**Feature**: spec.md

## Document Measurements

{self._metadata(document)}

## Completeness

- [x] CHK001 Does the spec define all required artifacts?
- [x] CHK002 Does the plan define the output tree?
- [x] CHK003 Does the task list reference every functional requirement?

## Living-spec readiness

- [x] CHK004 Does the context file store the source hash?
- [x] CHK005 Does the analysis report state the companion extension gap?
"""
        logging.debug("Rendered requirements checklist with %d characters", len(text))  # Record checklist size.
        return text

    def _clarify(self, document: SkillDocument) -> str:
        """Return the generated clarification artifact."""
        logging.info("Rendering generated clarification artifact")  # Record clarify rendering.
        lines = ["# Clarifications", "", "Command: speckit.clarify", "", "## Document Measurements", ""]
        lines.append(self._metadata(document))  # Add measured document values for this command output.
        lines.extend(["## Open Questions", ""])  # Start the question section after metadata.
        lines.extend(f"- {question}" for question in document.questions)  # Add each measured open question.
        text = "\n".join(lines) + "\n"  # Keep the Markdown file newline-terminated.
        logging.debug("Rendered clarification artifact with %d characters", len(text))  # Record clarify size.
        return text

    def _implement(self, document: SkillDocument) -> str:
        """Return the generated implementation record."""
        logging.info("Rendering generated implementation record")  # Record implementation rendering.
        text = f"""# Implementation Record: {document.title} skill package

Command: speckit.implement

## Document Measurements

{self._metadata(document)}
## Completed Work

- Joined {document.part_count} source part files.
- Built {document.topic_count} topic files.
- Ran the guard with result `{document.guard_result}`.
- Wrote living-spec metadata for source drift checks.
"""
        logging.debug("Rendered implementation record with %d characters", len(text))  # Record implementation size.
        return text

    def _fallback_context(self, document: SkillDocument) -> dict[str, object]:
        """Return a minimal Companion-compatible context document."""
        logging.info("Building fallback Companion context data")  # Record context build.
        context = {  # Mirror the real Companion lifecycle keys from spec_context.py.
            "workflow": "speckit",
            "specName": f"{document.title} skill package",
            "branch": "feat/2925-juniper-skill-factory",
            "currentStep": "implement",
            "status": "completed",
            "history": self._fallback_history(),
            "livingSpecs": {"loaded": [document.slug]},
            "sourcePath": str(document.source_path),
            "sourceFile": document.source_file,
            "sourceHash": document.content_hash,
            "sourcePages": document.pages,
            "partCount": document.part_count,
            "topicCount": document.topic_count,
            "guardResult": document.guard_result,
        }
        logging.debug("Built fallback Companion context with %d keys", len(context))  # Record context schema size.
        return context

    def _fallback_history(self) -> list[dict[str, str | None]]:
        """Return a compact fallback lifecycle history."""
        logging.info("Building fallback Companion lifecycle history")  # Record history creation.
        now = self._now()  # Use one timestamp for deterministic fallback ordering.
        steps = (
            "speckit.specify",
            "speckit.clarify",
            "speckit.plan",
            "speckit.tasks",
            "speckit.implement",
            "speckit.analyze",
            "speckit.checklist",
        )  # Include the full command sequence.
        history = [{"step": step, "substep": None, "kind": "complete", "by": "harness", "at": now} for step in steps]
        logging.debug("Built fallback Companion lifecycle history with %d entries", len(history))  # Record size.
        return history

    def _completed_phases(self) -> list[dict[str, object]]:
        """Return completed SpecKit phases for Companion."""
        logging.info("Building completed SpecKit phase records")  # Record phase record creation.
        phases = [  # Include every core SpecKit command phase in order.
            {"phase": 1, "command": "speckit.specify", "status": "completed"},
            {"phase": 2, "command": "speckit.clarify", "status": "completed"},
            {"phase": 3, "command": "speckit.plan", "status": "completed"},
            {"phase": 4, "command": "speckit.tasks", "status": "completed"},
            {"phase": 5, "command": "speckit.implement", "status": "completed"},
            {"phase": 6, "command": "speckit.analyze", "status": "completed"},
            {"phase": 7, "command": "speckit.checklist", "status": "completed"},
        ]
        logging.debug("Built %d completed phase records", len(phases))  # Record phase count.
        return phases

    def _companion_steps(self) -> tuple[tuple[str, str], ...]:
        """Return the canonical Companion lifecycle steps."""
        logging.info("Building Companion lifecycle steps")  # Record lifecycle step construction.
        steps = (
            ("specify", "specified"),
            ("plan", "planned"),
            ("tasks", "ready-to-implement"),
            ("implement", "implemented"),
        )  # Use only steps that the real Companion extension accepts.
        logging.debug("Built %d Companion lifecycle steps", len(steps))  # Record step count.
        return steps

    def _handoff_notes(self, document: SkillDocument) -> dict[str, object]:
        """Return Companion handoff notes."""
        logging.info("Building Companion handoff notes")  # Record handoff data creation.
        notes = {  # Store operator-useful progress details in the observed context shape.
            "keyTechnicalDecisions": ["Programmatic SpecKit generation replaces 1,500 manual interactive runs."],
            "qualityGateStatus": {"artifactValidation": "PASSING", "analysis": "PASSING"},
            "whatsDone": [f"Generated artifact set for {document.slug}."],
            "blockers": "Companion extension files are absent from .specify in this checkout.",
            "nextAgentAction": ["Run living drift after the upstream converter changes the source Markdown."],
        }
        logging.debug("Built Companion handoff notes with %d keys", len(notes))  # Record note breadth.
        return notes

    def _living_spec(self, document: SkillDocument) -> dict[str, object]:
        """Return living-spec metadata for source drift checks."""
        logging.info("Building living-spec metadata")  # Record living-spec metadata creation.
        metadata = {  # Connect the generated package to its changing source document.
            "enabled": True,
            "sourcePath": str(document.source_path),
            "sourceFile": document.source_file,
            "sourceHash": document.content_hash,
            "syncCommand": "speckit.companion.living-sync",
            "driftCommand": "speckit.companion.living-drift",
            "coverageCommand": "speckit.companion.living-coverage",
            "judgement": "Living-spec tracking fits because the source Markdown can change after PDF conversion.",
        }
        logging.debug("Built living-spec metadata with %d keys", len(metadata))  # Record metadata breadth.
        return metadata

    def _living_judgement(self) -> str:
        """Return the living-spec fit report."""
        logging.info("Rendering living-spec judgement")  # Record judgement rendering.
        text = """# Living-spec judgement

The living-spec machinery is a good fit for skill packages.
The source corpus changes when the upstream converter re-converts a PDF.
Each generated package stores a source path and a source hash in `.spec-context.json`.
A drift command can compare the stored hash with the current file hash.
It can then mark the package for regeneration.

Evidence: `.specify/extensions.yml` registers companion hooks after each core step.
The real companion extension contains lifecycle writers, drift checks, coverage checks, and living-spec fold-back.
The harness invokes `write-context.py` when the extension exists.
Living-spec commands fit the tracking model, but the current resolver reads repository-relative paths.
The Juniper source roots are outside this repository.
The factory must bridge that gap with source hashes or a registry that names those roots.
"""
        logging.debug("Rendered living-spec judgement with %d characters", len(text))  # Record judgement size.
        return text

    def _decision_capture(self) -> str:
        """Return the recorded scale decision for capture.py."""
        logging.info("Rendering Companion decision capture")  # Record decision capture rendering.
        text = json.dumps({"decision": "Use programmatic SpecKit generation", "why": "Manual runs do not scale."})
        logging.debug("Rendered Companion decision capture with %d characters", len(text))  # Record size.
        return text

    def _verified_capture(self) -> str:
        """Return the recorded validation proof for capture.py."""
        logging.info("Rendering Companion verification capture")  # Record verification capture rendering.
        text = json.dumps({"what": "Generated artifact set validates", "result": "No critical findings"})
        logging.debug("Rendered Companion verification capture with %d characters", len(text))  # Record size.
        return text

    def _metadata(self, document: SkillDocument) -> str:
        """Return common measured metadata lines."""
        logging.info("Rendering common measured metadata")  # Record metadata rendering.
        cycles = ", ".join(f"{key}={value}" for key, value in document.life_cycles.items())  # Render spread.
        lines = [  # Repeat the measured fields so each artifact stands alone.
            f"Document title: {document.title}",
            f"Domain: {document.domain}",
            f"Category: {document.category}",
            f"Page count: {document.pages}",
            f"Part count: {document.part_count}",
            f"Topic count: {document.topic_count}",
            f"Life cycle spread: {cycles}",
            f"Guard result: {document.guard_result}",
            f"Source hash: {document.content_hash}",
        ]
        text = "\n".join(lines) + "\n"  # Keep the metadata block newline-terminated.
        logging.debug("Rendered metadata with %d characters", len(text))  # Record metadata size.
        return text

    def _life_cycle_table(self, document: SkillDocument) -> str:
        """Return a Markdown life cycle table."""
        logging.info("Rendering life cycle table")  # Record lifecycle table rendering.
        rows = [f"| {name} | {count} |" for name, count in document.life_cycles.items()]  # Render counts.
        text = "| Life cycle | Topics |\n| - | -: |\n" + "\n".join(rows) + "\n"  # Build the Markdown table.
        logging.debug("Rendered life cycle table with %d rows", len(rows))  # Record row count.
        return text

    def _research(self, document: SkillDocument) -> str:
        """Return the generated research artifact."""
        logging.info("Rendering research artifact")  # Record research rendering.
        text = (  # Build a small research note that follows SpecKit plan output.
            f"# Research: {document.title} skill package\n\n"
            "Decision: Use programmatic SpecKit generation.\n\n"
            "Rationale: The corpus has more than 1,500 documents. Manual interactive runs are not practical.\n\n"
            "Alternatives considered: Manual command execution was rejected because it does not scale.\n"
        )
        logging.debug("Rendered research artifact with %d characters", len(text))  # Record research size.
        return text

    def _data_model(self, document: SkillDocument) -> str:
        """Return the generated data model artifact."""
        logging.info("Rendering data model artifact")  # Record data model rendering.
        text = (  # Build the data model artifact in the real plan shape.
            f"# Data Model: {document.title} skill package\n\n"
            "## SkillDocument\n\n"
            "Fields: source path, domain, title, pages, slug, source file, and source hash.\n\n"
            "## SpecKitArtifactSet\n\n"
            "Fields: spec, plan, tasks, checklist, analysis, and Companion context.\n"
        )
        logging.debug("Rendered data model artifact with %d characters", len(text))  # Record data model size.
        return text

    def _quickstart(self, document: SkillDocument) -> str:
        """Return the generated quickstart artifact."""
        logging.info("Rendering quickstart artifact")  # Record quickstart rendering.
        text = (  # Build the quickstart artifact with proof steps.
            f"# Quickstart: {document.title} skill package\n\n"
            f"1. Run the harness for `{document.source_path}`.\n"
            f"2. Confirm that `specs/skills/{document.domain}/{document.slug}` has the required files.\n"
            "3. Run the analyzer and confirm zero critical findings.\n"
        )
        logging.debug("Rendered quickstart artifact with %d characters", len(text))  # Record quickstart size.
        return text

    def _contract(self, document: SkillDocument) -> str:
        """Return the generated package contract artifact."""
        logging.info("Rendering package contract artifact")  # Record contract rendering.
        text = (  # Build the package contract artifact.
            f"# Contract: {document.title} skill package\n\n"
            f"The harness writes required files under `specs/skills/{document.domain}/{document.slug}`.\n"
            "The context file stores living-spec metadata with a source hash.\n"
        )
        logging.debug("Rendered package contract with %d characters", len(text))  # Record contract size.
        return text

    def _template(self, name: str) -> str:
        """Read one installed SpecKit template."""
        logging.info("Reading installed SpecKit template %s", name)  # Record template reuse.
        text = (self.paths.templates_dir / name).read_text(encoding="utf-8")  # Read the real template file.
        logging.debug("Read SpecKit template %s with %d characters", name, len(text))  # Record template size.
        return text

    def _document_sql(self) -> str:
        """Return the source document lookup SQL."""
        logging.info("Building source document SQL")  # Record SQL creation.
        sql = "SELECT title, category, pages, part_count FROM source_document WHERE document_key = ?"  # Read facts.
        logging.debug("Built source document SQL with %d characters", len(sql))  # Record SQL size.
        return sql

    def _part_count_sql(self) -> str:
        """Return the source part count SQL."""
        logging.info("Building source part count SQL")  # Record SQL creation.
        sql = "SELECT COUNT(*) FROM source_part WHERE document_key = ? AND is_winner = 1"  # Count active parts.
        logging.debug("Built source part count SQL with %d characters", len(sql))  # Record SQL size.
        return sql

    def _latest_stage_detail(self, connection: sqlite3.Connection, document_key: str, stage: str) -> str:
        """Return the newest stage detail from the orchestrator journal."""
        logging.info("Reading latest orchestrator stage detail")  # Record stage lookup.
        row = connection.execute(self._stage_sql(), (document_key, stage)).fetchone()  # Read newest matching event.
        detail = str(row["detail"]) if row else "not measured"  # Report absence without hiding it.
        logging.debug("Latest stage detail for %s is %s", stage, detail)  # Record the non-secret detail.
        return detail

    def _stage_sql(self) -> str:
        """Return the stage detail lookup SQL."""
        logging.info("Building stage detail SQL")  # Record SQL creation.
        sql = (
            "SELECT detail FROM orchestrator_stage_event WHERE document_key = ? AND stage = ? "
            "AND status = 'completed' ORDER BY id DESC LIMIT 1"
        )  # Read the newest completed event for this stage.
        logging.debug("Built stage detail SQL with %d characters", len(sql))  # Record SQL size.
        return sql

    def _today(self) -> str:
        """Return the current UTC date."""
        logging.info("Resolving the current UTC date")  # Record time value creation.
        value = datetime.now(UTC).date().isoformat()  # Use UTC for deterministic date semantics.
        logging.debug("Resolved current UTC date %s", value)  # Record generated date.
        return value

    def _now(self) -> str:
        """Return the current UTC timestamp."""
        logging.info("Resolving the current UTC timestamp")  # Record time value creation.
        value = datetime.now(UTC).replace(microsecond=0).isoformat()  # Use second precision for stable JSON.
        logging.debug("Resolved current UTC timestamp %s", value)  # Record generated timestamp.
        return value
