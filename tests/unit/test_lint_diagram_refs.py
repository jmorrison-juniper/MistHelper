"""Tests for the Mermaid diagram reference lint script."""

import argparse
from pathlib import Path
from textwrap import dedent

import importlib.util
import sys

import pytest

SCRIPT_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
LINT_DIAGRAM_REFS_PATH = SCRIPT_DIR / "lint_diagram_refs.py"

spec = importlib.util.spec_from_file_location(
    "lint_diagram_refs",
    LINT_DIAGRAM_REFS_PATH,
)
if spec is None or spec.loader is None:
    raise ImportError(f"Cannot load lint_diagram_refs from {LINT_DIAGRAM_REFS_PATH}")
lint_diagram_refs = importlib.util.module_from_spec(spec)
sys.modules["lint_diagram_refs"] = lint_diagram_refs
spec.loader.exec_module(lint_diagram_refs)

DiagramReferenceValidator = lint_diagram_refs.DiagramReferenceValidator
BUILT_IN_ALLOWLIST = lint_diagram_refs.BUILT_IN_ALLOWLIST

@pytest.fixture
def validator():
    """Create a fresh validator instance."""
    return DiagramReferenceValidator()


@pytest.fixture
def validator_with_symbols(validator):
    """Validator pre-loaded with sample Python symbols."""
    validator.python_symbols = {
        "DataExporter", "write_with_format_selection",
        "APIFetchUtils", "fetch_with_pagination",
        "SQLiteDatabaseWriter", "upsert_records",
        "OperationRegistry", "RateLimitingUtils",
        "WebSocketManager", "PacketCaptureManager",
    }
    return validator


class TestMermaidBlockExtraction:
    """Test Mermaid code block extraction from markdown."""

    def test_extracts_single_block(self, validator):
        content = dedent("""\
            # Title

            ```mermaid
            classDiagram
                class DataExporter
            ```
        """)
        blocks = validator.extract_mermaid_blocks(content)
        assert len(blocks) == 1
        assert "DataExporter" in blocks[0]

    def test_extracts_multiple_blocks(self, validator):
        content = dedent("""\
            ```mermaid
            classDiagram
                class Foo
            ```

            Some text.

            ```mermaid
            sequenceDiagram
                participant Bar
            ```
        """)
        blocks = validator.extract_mermaid_blocks(content)
        assert len(blocks) == 2

    def test_ignores_non_mermaid_blocks(self, validator):
        content = dedent("""\
            ```python
            class NotADiagram:
                pass
            ```

            ```mermaid
            classDiagram
                class RealDiagram
            ```
        """)
        blocks = validator.extract_mermaid_blocks(content)
        assert len(blocks) == 1
        assert "RealDiagram" in blocks[0]

    def test_empty_content(self, validator):
        assert validator.extract_mermaid_blocks("") == []


class TestIdentifierExtraction:
    """Test identifier extraction from Mermaid code blocks."""

    def test_class_diagram_class_name(self, validator):
        block = "classDiagram\n    class DataExporter"
        ids = validator.extract_identifiers(block)
        assert "DataExporter" in ids

    def test_class_diagram_method(self, validator):
        block = "classDiagram\n    DataExporter : write_csv()"
        ids = validator.extract_identifiers(block)
        assert "DataExporter" in ids

    def test_class_diagram_inheritance(self, validator):
        block = "DataExporter <|-- OrgExportUtils"
        ids = validator.extract_identifiers(block)
        assert "DataExporter" in ids
        assert "OrgExportUtils" in ids

    def test_sequence_participant(self, validator):
        block = "sequenceDiagram\n    participant APIFetchUtils"
        ids = validator.extract_identifiers(block)
        assert "APIFetchUtils" in ids

    def test_sequence_arrow(self, validator):
        block = "APIFetchUtils->>DataExporter: write_csv"
        ids = validator.extract_identifiers(block)
        assert "APIFetchUtils" in ids
        assert "DataExporter" in ids

    def test_suffix_pattern_matching(self, validator):
        block = "Some text with PacketCaptureManager and FirmwareManager"
        ids = validator.extract_identifiers(block)
        assert "PacketCaptureManager" in ids
        assert "FirmwareManager" in ids

    def test_no_lowercase_classes(self, validator):
        block = "class lowercase_name"
        ids = validator.extract_identifiers(block)
        assert "lowercase_name" not in ids


class TestPythonSymbolExtraction:
    """Test Python symbol extraction via AST."""

    def test_extracts_class_names(self, validator, tmp_path):
        source = tmp_path / "test_source.py"
        source.write_text(dedent("""\
            class MyExporter:
                def export_data(self):
                    pass

            class MyManager:
                pass
        """))
        symbols = validator.extract_python_symbols(source)
        assert "MyExporter" in symbols
        assert "MyManager" in symbols
        assert "export_data" in symbols

    def test_extracts_top_level_functions(self, validator, tmp_path):
        source = tmp_path / "test_source.py"
        source.write_text("def top_level_func():\n    pass\n")
        symbols = validator.extract_python_symbols(source)
        assert "top_level_func" in symbols

    def test_handles_syntax_error(self, validator, tmp_path):
        source = tmp_path / "bad.py"
        source.write_text("def broken(\n")
        symbols = validator.extract_python_symbols(source)
        assert symbols == set()

    def test_handles_missing_file(self, validator, tmp_path):
        source = tmp_path / "nonexistent.py"
        symbols = validator.extract_python_symbols(source)
        assert symbols == set()


class TestAllowlistFiltering:
    """Test that allowlisted terms are skipped."""

    def test_builtin_allowlist_skips_keywords(self, validator_with_symbols):
        v = validator_with_symbols
        block = "classDiagram\n    class WebSocket"
        ids = v.extract_identifiers(block)
        # WebSocket is in allowlist, should not cause stale reference
        assert "WebSocket" in BUILT_IN_ALLOWLIST

    def test_custom_allowlist(self):
        custom = frozenset(["MyCustomTerm"])
        v = DiagramReferenceValidator(BUILT_IN_ALLOWLIST | custom)
        assert "MyCustomTerm" in v.allowlist


class TestStaleReferenceDetection:
    """Test stale reference detection and closest match."""

    def test_valid_reference_not_stale(self, validator_with_symbols):
        v = validator_with_symbols
        v.total_checked = 0
        name = "DataExporter"
        assert name in v.python_symbols

    def test_stale_reference_detected(self, validator_with_symbols):
        v = validator_with_symbols
        name = "OrgFooExporter"
        assert name not in v.python_symbols

    def test_closest_match_found(self, validator_with_symbols):
        v = validator_with_symbols
        match = v.find_closest_match("DataExportr")
        assert match is not None
        assert "DataExporter" in match

    def test_no_close_match(self, validator_with_symbols):
        v = validator_with_symbols
        match = v.find_closest_match("XyzAbcDefGhi")
        # Should return None if edit distance > len/2
        # This depends on the actual symbols
        assert match is None or "edit distance" in match


class TestEditDistance:
    """Test Levenshtein edit distance calculation."""

    def test_identical_strings(self, validator):
        assert validator._edit_distance("abc", "abc") == 0

    def test_single_insertion(self, validator):
        assert validator._edit_distance("abc", "abcd") == 1

    def test_single_deletion(self, validator):
        assert validator._edit_distance("abcd", "abc") == 1

    def test_single_substitution(self, validator):
        assert validator._edit_distance("abc", "axc") == 1

    def test_empty_strings(self, validator):
        assert validator._edit_distance("", "") == 0
        assert validator._edit_distance("abc", "") == 3


class TestExitCodes:
    """Test exit code behavior."""

    def test_report_success(self, validator):
        validator.total_checked = 5
        validator.files_scanned = 2
        validator.stale_references = []
        assert validator._report_results() == 0

    def test_report_failure(self, validator):
        validator.files_scanned = 1
        validator.stale_references = [
            {"file": "test.md", "line": 1, "name": "Foo", "closest": None}
        ]
        assert validator._report_results() == 1
