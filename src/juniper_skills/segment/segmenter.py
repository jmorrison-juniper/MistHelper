"""Build contract-sized topic units from one joined Markdown document."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path

from src.juniper_skills.segment.commands import CommandBlockDetector
from src.juniper_skills.segment.repair import DefectRepairResult, DocumentDefectRepairer


@dataclass(frozen=True)
class TopicSegment:
    """One bounded source topic for the rewrite stage."""

    index: int  # Store the stable topic order inside one document.
    title: str  # Store the heading or generated topic title.
    text: str  # Store repaired source text for the rewriter.
    page_start: int  # Store the first cited page in this topic.
    page_end: int  # Store the last cited page in this topic.
    size_bytes: int  # Store the UTF-8 size for contract proof.

    def source_key(self, document_code: str) -> str:
        return f"{document_code} p.{self.page_start}-{self.page_end}"  # Build the contract citation key.


@dataclass(frozen=True)
class SegmenterResult:
    """The segmentation result and its measured proof values."""

    segments: list[TopicSegment]  # Store all bounded topic units.
    repair: DefectRepairResult  # Store converter defect repair counts.
    command_blocks: int  # Store the number of new command fences.
    command_lines: int  # Store the number of command or output lines fenced.
    hard_limit_breaks: list[TopicSegment]  # Store any topic that still violates the hard limit.


@dataclass(frozen=True)
class _Chunk:
    """Internal chunk built from one heading range or one oversize slice."""

    title: str  # Store a readable title for merged topics.
    text: str  # Store the chunk source text.
    page_start: int  # Store the first page marker in the chunk.
    page_end: int  # Store the last page marker in the chunk.


class PageTracker:
    """Attach page numbers to Markdown lines from converter markers."""

    PAGE_PATTERN = re.compile(r"<!--\s*page\s+(\d+)\s*-->", re.IGNORECASE)  # Match universal page markers.

    def annotate(self, lines: list[str]) -> list[tuple[str, int]]:
        logging.info("Annotating %s lines with page markers", len(lines))  # Log before citation mapping.
        page = 0  # Use zero until the first marker appears.
        annotated: list[tuple[str, int]] = []  # Accumulate each source line with its active page.
        for line in lines:  # Walk the document in source order.
            match = self.PAGE_PATTERN.search(line)  # Detect whether this line changes the active page.
            page = int(match.group(1)) if match else page  # Update the page after a marker appears.
            annotated.append((line, page))  # Attach the current page to the line.
        logging.debug("Annotated %s lines through page %s", len(annotated), page)  # Report mapping size and last page.
        return annotated


class DocumentSegmenter:
    """Segment repaired Markdown on heading hierarchy with contract size limits."""

    HEADING_PATTERN = re.compile(r"^(#{2,6})\s+(.+?)\s*$")  # Use level-2 headings as the top source level.

    def __init__(self, soft_limit: int = 12_288, hard_limit: int = 20_480, tiny_limit: int = 2_048) -> None:
        self.soft_limit = soft_limit  # Store the topic size target from the locked contract.
        self.hard_limit = hard_limit  # Store the maximum topic size from the locked contract.
        self.tiny_limit = tiny_limit  # Store the merge threshold for one-paragraph sections.
        self.repairer = DocumentDefectRepairer()  # Repair converter defects before heading segmentation.
        self.detector = CommandBlockDetector()  # Re-fence Junos command blocks before topic splitting.
        self.page_tracker = PageTracker()  # Preserve page citation ranges for every topic.

    def segment_text(self, text: str, document_slug: str = "document") -> SegmenterResult:
        logging.info("Segmenting document %s", document_slug)  # Log before any document transformation.
        body = self._strip_front_matter(text)  # Remove converter front matter from topic content.
        repair = self.repairer.repair(body)  # Repair measured converter defects first.
        command_result = self.detector.refence_text(repair.text)  # Fence commands while preserving exact command text.
        chunks = self._initial_chunks(command_result.text)  # Split on the observed heading hierarchy.
        bounded = self._bound_chunks(chunks)  # Split oversize chunks before topic merge.
        segments = self._merge_chunks(bounded)  # Merge tiny adjacent chunks without breaking the hard limit.
        breaks = [segment for segment in segments if segment.size_bytes > self.hard_limit]  # Report failed topics.
        logging.debug(
            "Document %s produced %s topics with %s hard breaks", document_slug, len(segments), len(breaks)
        )  # Report.
        return SegmenterResult(
            segments, repair, command_result.fenced_blocks, command_result.command_lines, breaks
        )  # Return.

    def _strip_front_matter(self, text: str) -> str:
        if not text.startswith("---\n"):  # Keep text unchanged when no front matter exists.
            return text
        end = text.find("\n---", 4)  # Find the closing front matter marker.
        return text[end + 4 :].lstrip("\n") if end != -1 else text  # Remove only valid front matter.

    def _initial_chunks(self, text: str) -> list[_Chunk]:
        logging.info("Splitting document on Markdown heading hierarchy")  # Log before structural segmentation.
        annotated = self.page_tracker.annotate(text.splitlines())  # Attach citation pages to every source line.
        heading_indexes = [index for index, row in enumerate(annotated) if self.HEADING_PATTERN.match(row[0])]  # Find.
        chunks = (
            self._chunks_from_headings(annotated, heading_indexes) if heading_indexes else [self._make_chunk(annotated)]
        )  # Build.
        logging.debug("Heading split produced %s chunks", len(chunks))  # Report initial structural count.
        return chunks

    def _chunks_from_headings(self, rows: list[tuple[str, int]], indexes: list[int]) -> list[_Chunk]:
        starts = [0] if indexes[0] != 0 else []  # Keep preface text as the overview chunk.
        starts.extend(indexes)  # Add every heading as a possible topic boundary.
        stops = [*starts[1:], len(rows)]  # End each chunk at the next boundary.
        chunks: list[_Chunk] = []  # Accumulate heading chunks without a long comprehension.
        for start, stop in zip(starts, stops, strict=False):  # Pair each boundary with the next boundary.
            if rows[start:stop]:  # Skip empty ranges that can appear at a document edge.
                chunks.append(self._make_chunk(rows[start:stop]))  # Build one source chunk for this range.
        return chunks  # Return heading chunks in source order.

    def _make_chunk(self, rows: list[tuple[str, int]]) -> _Chunk:
        text = "\n".join(line for line, _page in rows).strip()  # Keep source lines verbatim inside this chunk.
        title = self._title_for(rows, "overview")  # Use the first heading when one exists.
        pages = [page for _line, page in rows if page > 0]  # Ignore zero before the first page marker.
        page_start = min(pages) if pages else 0  # Record the first cited page.
        page_end = max(pages) if pages else page_start  # Record the last cited page.
        return _Chunk(title, text, page_start, page_end)  # Return the internal chunk.

    def _title_for(self, rows: list[tuple[str, int]], fallback: str) -> str:
        for line, _page in rows:  # Search the chunk for its first heading.
            match = self.HEADING_PATTERN.match(line)  # Parse the heading line when present.
            if match:  # Use the heading text as the topic title.
                return match.group(2).strip()
        return fallback  # Use overview for preface chunks.

    def _bound_chunks(self, chunks: list[_Chunk]) -> list[_Chunk]:
        logging.info("Applying topic hard size limit to %s chunks", len(chunks))  # Log before oversize handling.
        bounded: list[_Chunk] = []  # Accumulate chunks that obey the hard limit.
        for chunk in chunks:  # Check each heading chunk independently.
            if self._size(chunk.text) <= self.hard_limit:  # Keep contract-sized chunks unchanged.
                bounded.append(chunk)  # Add the safe chunk to the output list.
                continue
            bounded.extend(self._split_large_chunk(chunk))  # Split oversize chunks at paragraph boundaries.
        logging.debug("Hard limit split produced %s chunks", len(bounded))  # Report bounded chunk count.
        return bounded

    def _split_large_chunk(self, chunk: _Chunk) -> list[_Chunk]:
        rows = self.page_tracker.annotate(chunk.text.splitlines())  # Reattach pages for paragraph splitting.
        rows = [(line, page or chunk.page_start) for line, page in rows]  # Inherit pages when a marker was earlier.
        groups = self._paragraph_groups(rows)  # Use blank lines as lower-level boundaries.
        parts = self._pack_groups(chunk.title, groups)  # Pack paragraphs into hard-limit chunks.
        return parts  # Return the lower-level chunks.

    def _paragraph_groups(self, rows: list[tuple[str, int]]) -> list[list[tuple[str, int]]]:
        groups: list[list[tuple[str, int]]] = []  # Accumulate paragraph groups.
        current: list[tuple[str, int]] = []  # Store the current paragraph lines.
        for row in rows:  # Split on blank lines while preserving source line text.
            if row[0].strip():  # Nonblank lines belong to the current paragraph.
                current.append(row)  # Keep the source row in its paragraph.
            elif current:  # A blank closes the current paragraph group.
                groups.append(current)  # Store the completed paragraph.
                current = []  # Start a new paragraph after the blank.
        return [*groups, current] if current else groups  # Include the final paragraph when present.

    def _pack_groups(self, title: str, groups: list[list[tuple[str, int]]]) -> list[_Chunk]:
        chunks: list[_Chunk] = []  # Accumulate packed paragraph chunks.
        current: list[tuple[str, int]] = []  # Store rows for the current packed chunk.
        for group in groups:  # Add groups until the next one would break the hard limit.
            for unit in self._split_large_group(group):  # Reduce an oversize paragraph before packing.
                candidate = [*current, *unit]  # Build a trial chunk for size checking.
                if current and self._size_rows(candidate) > self.hard_limit:  # Close the chunk before overflow.
                    chunks.append(self._make_chunk(current))  # Store the current hard-limit chunk.
                    current = unit  # Start the next chunk with the unit that did not fit.
                else:  # The paragraph unit fits in the current chunk.
                    current = candidate  # Keep growing the current chunk.
        return [*chunks, self._make_chunk(current)] if current else chunks  # Return all packed chunks.

    def _split_large_group(self, group: list[tuple[str, int]]) -> list[list[tuple[str, int]]]:
        if self._size_rows(group) <= self.hard_limit:  # Keep normal paragraphs intact.
            return [group]
        units: list[list[tuple[str, int]]] = []  # Accumulate word-bounded paragraph slices.
        current: list[tuple[str, int]] = []  # Store rows for the current slice.
        for line, page in group:  # Split each oversize prose row without changing word order.
            for unit_line in self._split_large_line(line):  # Break a long row at word boundaries.
                candidate = [*current, (unit_line, page)]  # Test whether the line fits in the current slice.
                if current and self._size_rows(candidate) > self.hard_limit:  # Flush before the slice overflows.
                    units.append(current)  # Store the completed paragraph slice.
                    current = [(unit_line, page)]  # Start a new slice with the current line.
                else:  # The line fits in the current slice.
                    current = candidate  # Keep growing the current slice.
        return [*units, current] if current else units  # Return all slices for packing.

    def _split_large_line(self, line: str) -> list[str]:
        if self._size(line) <= self.hard_limit:  # Keep normal source lines unchanged.
            return [line]
        words = line.split(" ")  # Split only on spaces so words and numbers stay unchanged.
        lines: list[str] = []  # Accumulate safe line slices.
        current = ""  # Store the current line slice.
        for word in words:  # Pack words until the hard limit would be exceeded.
            candidate = f"{current} {word}".strip()  # Build a trial line slice.
            if current and self._size(candidate) > self.hard_limit:  # Flush before overflow.
                lines.append(current)  # Store the completed line slice.
                current = word  # Start the next line slice.
            else:  # The word fits in the current line slice.
                current = candidate  # Keep the word in the current line slice.
        return [*lines, current] if current else lines  # Return all safe line slices.

    def _merge_chunks(self, chunks: list[_Chunk]) -> list[TopicSegment]:
        logging.info("Merging tiny sections into bounded topics")  # Log before small-section merge.
        segments: list[TopicSegment] = []  # Store final topic segments.
        current: list[_Chunk] = []  # Store chunks for the current topic.
        for chunk in chunks:  # Pack chunks until the soft target or hard limit is reached.
            current = self._merge_one_chunk(segments, current, chunk)  # Add or flush one chunk.
        if current:  # Flush the final topic after the loop.
            self._append_segment(segments, current)  # Convert the final chunks into one topic segment.
        logging.debug("Merged chunks into %s topic segments", len(segments))  # Report final topic count.
        return segments

    def _merge_one_chunk(self, segments: list[TopicSegment], current: list[_Chunk], chunk: _Chunk) -> list[_Chunk]:
        candidate = [*current, chunk]  # Build a trial topic for size checking.
        candidate_size = self._size("\n\n".join(item.text for item in candidate))  # Measure the trial topic.
        if current and candidate_size > self.hard_limit:  # Flush before adding a chunk that would break the contract.
            self._append_segment(segments, current)  # Store the current topic.
            return [chunk]  # Start the next topic with the chunk that did not fit.
        if candidate_size >= self.soft_limit and self._size(chunk.text) >= self.tiny_limit:  # Avoid over-merging.
            self._append_segment(segments, candidate)  # Store the topic once it reaches the soft target.
            return []  # Start a new empty topic.
        return candidate  # Continue merging tiny sections.

    def _append_segment(self, segments: list[TopicSegment], chunks: list[_Chunk]) -> None:
        text = "\n\n".join(
            chunk.text for chunk in chunks if chunk.text
        ).strip()  # Combine source chunks with separators.
        pages = [page for chunk in chunks for page in [chunk.page_start, chunk.page_end] if page > 0]  # Collect pages.
        title = chunks[0].title if chunks else "overview"  # Keep a stable topic title from the first chunk.
        segment = TopicSegment(
            len(segments), title, text, min(pages) if pages else 0, max(pages) if pages else 0, self._size(text)
        )  # Build topic.
        segments.append(segment)  # Store the final topic in source order.

    def _size_rows(self, rows: list[tuple[str, int]]) -> int:
        return self._size("\n".join(line for line, _page in rows))  # Measure rows as UTF-8 bytes.

    def _size(self, text: str) -> int:
        return len(text.encode("utf-8"))  # Measure the contract limit in bytes.

    def write_topic_tree(self, result: SegmenterResult, output_dir: Path, document_code: str) -> None:
        logging.info("Writing %s segment topic files to %s", len(result.segments), output_dir)  # Log before writes.
        output_dir.mkdir(parents=True, exist_ok=True)  # Create the destination tree for generated topics.
        for segment in result.segments:  # Write each topic segment with citation metadata.
            self._write_segment(segment, output_dir, document_code)  # Write one segment file.
        logging.debug("Wrote %s segment topic files", len(result.segments))  # Report write completion.

    def _write_segment(self, segment: TopicSegment, output_dir: Path, document_code: str) -> None:
        filename = f"{segment.index:02d}-{self._slug(segment.title)}.md"  # Build a stable topic file name.
        content = self._topic_content(segment, document_code)  # Build the source topic file with front matter.
        (output_dir / filename).write_text(content, encoding="utf-8")  # Write the topic content for downstream use.

    def _topic_content(self, segment: TopicSegment, document_code: str) -> str:
        source_key = segment.source_key(document_code)  # Build the exact citation key for this source topic.
        return f"---\ntopic: {segment.title}\nsources: [{source_key}]\n---\n\n{segment.text}\n"  # Return content.

    def _slug(self, value: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")  # Make a file-safe slug from the topic title.
        return slug[:60] or "overview"  # Keep file names bounded and nonempty.
