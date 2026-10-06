"""Ratchet guard for issue #3070 that stops new blind broad exception handlers.

A handler is broad when the `except` clause names `Exception` or `BaseException` directly, either
as a bare name or inside a tuple. A broad handler is blind when it binds no name, or when the
bound name never appears as a load anywhere in the handler body subtree. A reference inside a
nested function, a nested class, or a nested handler counts as a reference, because the bound
object still reaches the operator through that code. An attribute form such as
`builtins.Exception` stays out of scope.

The guard does not gate on the raw Ruff `BLE001` rule. A broad handler that binds and reports its
exception stays acceptable, and an unknown write outcome can require one. Pull request #3075
narrowed two upgrade-portal handlers and created a real regression that could have permitted a
duplicate firmware submission, so a raw `BLE001` gate is unsafe here.

The baseline file records the current handlers as accepted debt. The guard fails on growth only,
and it never raises the baseline on its own.
"""

from __future__ import annotations  # Keep annotations stable during pytest collection.

import ast  # Parse Python source so a comment or a string cannot create a false finding.
import json  # Read the accepted-debt baseline document.
import logging  # Record the measured counts for the guard proof audit.
import subprocess  # Ask git for the tracked file set instead of walking untracked output.
from dataclasses import dataclass  # Hold the measured counts in one immutable record.
from pathlib import Path, PurePosixPath  # Build repository paths without hardcoded separators.

import pytest  # Assert that each invalid input raises instead of reporting green.

logger = logging.getLogger(__name__)  # Share one module logger for guard diagnostics.
_REPO_ROOT = Path(__file__).resolve().parents[2]  # Locate the repository root from this guard file.


@dataclass(frozen=True)
class ScanReport:
    """Hold the measured counts and the findings of one blind-handler scan."""

    scanned_files: int  # Count every candidate file so a zero scope cannot pass silently.
    parsed_files: int  # Count every parsed file so a read failure cannot hide behind a green run.
    broad_handlers: int  # Count every broad handler to prove the scope of the rule.
    blind_counts: dict[str, int]  # Map each file to its blind handler count.
    parse_failures: tuple[str, ...]  # Record each read failure and each syntax failure.

    @property
    def blind_handlers(self) -> int:
        """Return the total blind handler count across every scanned file."""
        return sum(self.blind_counts.values())  # Sum the per-file counts for the proof line.


class BlindHandlerScanner:
    """Find broad exception handlers that never reference the caught exception."""

    BROAD_NAMES: frozenset[str] = frozenset({"Exception", "BaseException"})  # Name the broad builtins.
    EXCLUDED_PATH_COMPONENTS: tuple[str, ...] = ("tests",)  # Drop test trees from the measured scope.

    @classmethod
    def tracked_python_files(cls, root: Path) -> tuple[str, ...]:
        """Return the tracked non-test Python paths of one repository in POSIX form."""
        logger.info("Listing tracked Python files under %s", root)  # Log before the git call.
        listing = subprocess.run(  # Ask git so the scan skips .venv and other untracked output.
            ["git", "ls-files", "-z", "*.py"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
        entries = [entry for entry in listing.stdout.split("\0") if entry]  # Split the NUL-separated list.
        files = tuple(sorted(entry for entry in entries if not cls.is_excluded(entry)))  # Drop test paths.
        logger.debug("The blind-handler guard selected %d tracked file(s)", len(files))  # Record the count.
        return files  # Return the exact measured scope.

    @classmethod
    def is_excluded(cls, relative: str) -> bool:
        """Return true when a repository-relative path holds an excluded component."""
        parts = PurePosixPath(relative).parts  # Split the path so a partial name cannot match.
        return any(part in cls.EXCLUDED_PATH_COMPONENTS for part in parts)  # Match a whole component only.

    @classmethod
    def scan_paths(cls, root: Path, paths: tuple[str, ...]) -> ScanReport:
        """Return the scan report for the supplied repository-relative paths."""
        logger.info("Scanning %d tracked file(s) for blind broad handlers", len(paths))  # Log the scope.
        counts: dict[str, int] = {}  # Store the blind handler count of each affected file.
        failures: list[str] = []  # Store each read failure and each syntax failure.
        parsed = 0  # Count the files that produced a tree, so a silent read failure cannot pass.
        broad_total = 0  # Count every broad handler for the proof line.
        for relative in paths:  # Measure one file at a time to keep the failure list precise.
            tree = cls.parse_file(root / relative, relative, failures)  # Read and parse one file.
            if tree is None:  # A read failure or a syntax failure already entered the failure list.
                continue  # Move to the next file and keep the parsed count honest.
            parsed += 1  # Record one more measured file.
            broad, blind = cls.scan_tree(tree)  # Count the handlers of this one file.
            broad_total += broad  # Accumulate the broad handler count.
            if blind:  # Store only a positive count so the report holds no empty entry.
                counts[relative] = blind  # Record the blind handler count of this file.
        logger.debug("The blind-handler scan parsed %d file(s)", parsed)  # Record the parsed count.
        return ScanReport(len(paths), parsed, broad_total, counts, tuple(failures))  # Return the measurement.

    @staticmethod
    def parse_file(full_path: Path, relative: str, failures: list[str]) -> ast.Module | None:
        """Return one parsed module, or None after the guard records an input failure."""
        try:  # A read failure must become a visible finding, not a skipped file.
            source = full_path.read_text(encoding="utf-8")  # Read the source with the project encoding.
        except (OSError, UnicodeDecodeError) as read_error:  # Catch each read defect and report it.
            failures.append(f"{relative}: read failure: {read_error}")  # Name the file and the cause.
            return None  # Tell the caller that this file produced no tree.
        try:  # A syntax failure must also become a visible finding.
            return ast.parse(source, filename=relative)  # Parse the source into a module tree.
        except SyntaxError as syntax_error:  # Catch the parse defect and report it.
            failures.append(f"{relative}: syntax failure: {syntax_error}")  # Name the file and the cause.
            return None  # Tell the caller that this file produced no tree.

    @classmethod
    def scan_source(cls, source: str, relative: str) -> tuple[int, int]:
        """Return the broad handler count and the blind handler count of one source string."""
        logger.info("Parsing in-memory source for %s", relative)  # Log before the parse step.
        tree = ast.parse(source, filename=relative)  # Parse the supplied text without a temporary file.
        return cls.scan_tree(tree)  # Reuse the one decision path used by the repository scan.

    @classmethod
    def scan_tree(cls, tree: ast.AST) -> tuple[int, int]:
        """Return the broad handler count and the blind handler count of one parsed tree."""
        broad = 0  # Count every broad handler in this tree.
        blind = 0  # Count every broad handler that never references its bound exception.
        for node in ast.walk(tree):  # Walk the whole tree because a handler can sit at any depth.
            if not isinstance(node, ast.ExceptHandler) or not cls.catches_broad(node):  # Keep broad handlers.
                continue  # Ignore each narrow handler and each non-handler node.
            broad += 1  # Record one more broad handler.
            if not cls.references_bound_name(node):  # A handler that drops its exception is blind.
                blind += 1  # Record one more blind handler.
        logger.debug("One tree holds %d broad handler(s) and %d blind handler(s)", broad, blind)  # Log the result.
        return broad, blind  # Return both counts for the report.

    @classmethod
    def catches_broad(cls, handler: ast.ExceptHandler) -> bool:
        """Return true when one except clause names a broad builtin exception."""
        clause = handler.type  # Read the caught expression one time for clear branch checks.
        if clause is None:  # A bare `except:` clause stays outside this rule.
            return False  # Report the bare clause as not broad.
        items = clause.elts if isinstance(clause, ast.Tuple) else [clause]  # Expand a tuple clause.
        return any(isinstance(item, ast.Name) and item.id in cls.BROAD_NAMES for item in items)  # Match a name.

    @staticmethod
    def references_bound_name(handler: ast.ExceptHandler) -> bool:
        """Return true when the handler body references the bound exception name."""
        bound = handler.name  # Read the bound name, which is None when the handler binds nothing.
        if bound is None:  # A handler with no bound name cannot reference the exception.
            return False  # Report the unbound handler as blind.
        body = ast.Module(body=handler.body, type_ignores=[])  # Wrap the body so one walk covers it.
        return any(isinstance(node, ast.Name) and node.id == bound for node in ast.walk(body))  # Match a load.


class BaselineDocument:
    """Load and validate the accepted blind broad exception handler debt."""

    BASELINE_PATH: Path = _REPO_ROOT / ".github" / "blind-exception-handler-baseline.json"  # Name the file.
    EXPECTED_SCHEMA_VERSION: int = 1  # Reject a body that a later schema wrote.
    EXPECTED_RULE_ID: str = "blind_broad_exception_handler"  # Reject a body that belongs to another rule.
    EXPECTED_EXCLUSIONS: list[str] = ["tests"]  # Reject a body whose scope does not match this guard.

    def __init__(self, files: dict[str, int]) -> None:
        """Store the validated per-file accepted counts."""
        self.files = files  # Keep the accepted debt for the ratchet comparison.

    @classmethod
    def load(cls, path: Path) -> BaselineDocument:
        """Return the validated baseline that the supplied path holds."""
        logger.info("Reading the blind-handler baseline at %s", path)  # Log before the read.
        if not path.is_file():  # A missing baseline must fail, because the guard cannot measure growth.
            raise ValueError(f"blind-handler baseline is missing: {path}")  # Name the absent input.
        return cls.parse(path.read_text(encoding="utf-8"), path)  # Validate the body before use.

    @classmethod
    def parse(cls, body: str, source: Path) -> BaselineDocument:
        """Return the validated baseline that one JSON body holds."""
        try:  # A malformed body must fail, because the guard cannot trust an unreadable baseline.
            payload = json.loads(body, object_pairs_hook=cls.reject_duplicate_keys)  # Reject a repeated key.
        except ValueError as decode_error:  # JSONDecodeError and the duplicate-key error both land here.
            raise ValueError(f"blind-handler baseline is malformed: {source}: {decode_error}") from decode_error
        if not isinstance(payload, dict):  # The document root must be an object.
            raise ValueError(f"blind-handler baseline root is not an object: {source}")  # Name the defect.
        cls.check_header(payload, source)  # Reject a wrong schema, rule, or scope before the counts.
        return cls(cls.check_files(payload, source))  # Validate each entry and store the accepted debt.

    @staticmethod
    def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
        """Return one object body, or raise when the body repeats a key."""
        keys = [key for key, _ in pairs]  # Collect the keys in source order so a repeat stays visible.
        if len(keys) != len(set(keys)):  # The default parser hides a duplicate by keeping the last value.
            raise ValueError("the baseline body repeats a key")  # Fail instead of accepting hidden data.
        return dict(pairs)  # Return the object body for the standard parser.

    @classmethod
    def check_header(cls, payload: dict[str, object], source: Path) -> None:
        """Reject a baseline header that does not match this guard."""
        version = payload.get("schema_version")  # Read the version one time for the type check.
        if not cls.is_positive_integer(version) or version != cls.EXPECTED_SCHEMA_VERSION:  # Reject a boolean too.
            raise ValueError(f"blind-handler baseline has a wrong schema_version: {source}: {version!r}")
        if payload.get("rule_id") != cls.EXPECTED_RULE_ID:  # Reject a body that another rule owns.
            raise ValueError(f"blind-handler baseline has a wrong rule_id: {source}")  # Name the defect.
        scope = payload.get("scope")  # Read the scope object one time.
        if not isinstance(scope, dict) or scope.get("tracked_python_files") is not True:  # Require the git scope.
            raise ValueError(f"blind-handler baseline has a wrong scope: {source}")  # Name the defect.
        if scope.get("excluded_path_components") != cls.EXPECTED_EXCLUSIONS:  # Require the same exclusions.
            raise ValueError(f"blind-handler baseline has wrong exclusions: {source}")  # Name the defect.

    @classmethod
    def check_files(cls, payload: dict[str, object], source: Path) -> dict[str, int]:
        """Return the validated per-file counts that one baseline payload holds."""
        files = payload.get("files")  # Read the mapping one time for the type check.
        if not isinstance(files, dict):  # A missing or nonobject mapping must fail.
            raise ValueError(f"blind-handler baseline holds no files mapping: {source}")  # Name the defect.
        checked: dict[str, int] = {}  # Store each validated entry for the ratchet comparison.
        for path, count in files.items():  # Validate one entry at a time so the message names the entry.
            cls.check_entry(path, count, source)  # Reject an invalid path or an invalid count.
            checked[str(path)] = int(count)  # Store the entry with its exact declared types.
        logger.debug("The blind-handler baseline holds %d file entry(s)", len(checked))  # Record the count.
        return checked  # Return the accepted debt.

    @classmethod
    def check_entry(cls, path: object, count: object, source: Path) -> None:
        """Reject one baseline entry that is not a normalized path with a positive count."""
        if not isinstance(path, str) or not path.strip() or "\\" in path or path.startswith("/"):
            raise ValueError(f"blind-handler baseline holds an invalid path: {source}: {path!r}")
        if not cls.is_positive_integer(count):  # Reject a boolean, a float, a negative, and a zero.
            raise ValueError(f"blind-handler baseline holds an invalid count: {source}: {path}={count!r}")

    @staticmethod
    def is_positive_integer(value: object) -> bool:
        """Return true when a value is an integer above zero and not a boolean."""
        if isinstance(value, bool):  # Python treats a boolean as an integer, so reject it first.
            return False  # Report a boolean as an invalid count.
        return isinstance(value, int) and value > 0  # Require a stored count above zero.


class BlindHandlerRatchet:
    """Compare the measured blind handlers with the accepted baseline debt."""

    def __init__(self, report: ScanReport, baseline: BaselineDocument) -> None:
        """Store the measured report and the accepted baseline."""
        self.report = report  # Keep the measurement for the comparison and the proof line.
        self.baseline = baseline  # Keep the accepted debt for the comparison.

    def growth_violations(self) -> tuple[str, ...]:
        """Return one message for each file whose blind handler count is above its baseline."""
        violations: list[str] = []  # Collect every violation so one run gives the complete list.
        for path in sorted(self.report.blind_counts):  # Sort the paths to keep the output stable.
            accepted = self.baseline.files.get(path, 0)  # An unlisted file accepts zero blind handlers.
            current = self.report.blind_counts[path]  # Read the measured count of this file.
            if current > accepted:  # An equal count and a lower count both pass the ratchet.
                violations.append(f"{path}: {accepted} -> {current}")  # Name the file and the growth.
        logger.debug("The blind-handler ratchet found %d growth violation(s)", len(violations))  # Log the result.
        return tuple(violations)  # Return immutable findings for stable assertions.

    def proof_line(self) -> str:
        """Return the stable ASCII line that proves the measured scope of the guard."""
        report = self.report  # Read the report one time to keep each line inside the length limit.
        return (  # Build one line that a reader can compare between two runs.
            f"Scanned {report.scanned_files} tracked non-test Python files. "
            f"Parsed {report.parsed_files}. "
            f"Broad handlers {report.broad_handlers}. "
            f"Blind handlers {report.blind_handlers} in {len(report.blind_counts)} files. "
            f"Baseline files {len(self.baseline.files)}. "
            f"Growth violations {len(self.growth_violations())}. "
            f"Parse failures {len(report.parse_failures)}."
        )

    def check(self) -> str:
        """Return the proof line, or raise when the measurement or the ratchet fails."""
        if self.report.scanned_files == 0:  # A zero scope must fail instead of reporting green.
            raise ValueError("the blind-handler guard scanned 0 files")  # Name the empty scope.
        if self.report.parsed_files == 0:  # A scan that parsed nothing measured nothing.
            raise ValueError("the blind-handler guard parsed 0 files")  # Name the empty measurement.
        if self.report.parse_failures:  # A read failure or a syntax failure hides real findings.
            raise ValueError("blind-handler input failures: " + "; ".join(self.report.parse_failures))
        violations = self.growth_violations()  # Compare the measurement with the accepted debt.
        if violations:  # New blind handlers must fail the gate.
            raise ValueError("new blind broad exception handlers: " + "; ".join(violations))  # Name each file.
        return self.proof_line()  # Return the proof line for the caller to print.


class TestBlindHandlerScannerDecisions:
    """Direct decision tests for the blind broad exception handler rule."""

    @staticmethod
    def _report_for(source: str, relative: str) -> ScanReport:
        """Return a one-file scan report built from an in-memory source string."""
        broad, blind = BlindHandlerScanner.scan_source(source, relative)  # Measure the supplied source.
        counts = {relative: blind} if blind else {}  # Store a positive count only.
        return ScanReport(1, 1, broad, counts, ())  # Model a scan of exactly one readable file.

    def test_a_new_blind_handler_fails_against_an_empty_baseline(self) -> None:
        """A new blind handler must fail and the message must name the path and the growth."""
        source = "try:\n    run()\nexcept Exception:\n    pass\n"  # Model the defect that issue #3070 stops.
        report = self._report_for(source, "src/example.py")  # Measure the one-file scan.
        ratchet = BlindHandlerRatchet(report, BaselineDocument({}))  # Accept zero debt for this file.
        with pytest.raises(ValueError) as failure:  # The guard must raise instead of reporting green.
            ratchet.check()  # Run the same decision path that the repository test runs.
        assert report.blind_handlers == 1, f"the scanner found {report.blind_handlers} blind handler(s)"
        assert ratchet.growth_violations() == ("src/example.py: 0 -> 1",), "the violation text is not exact"
        assert "src/example.py: 0 -> 1" in str(failure.value), "the failure message does not name the growth"

    def test_a_reported_handler_passes_a_recorded_baseline(self) -> None:
        """A broad handler that reports its bound exception must leave the ratchet green."""
        source = (  # Model the accepted repair that keeps the broad catch and reports the cause.
            "try:\n"
            "    run()\n"
            "except Exception as exc:\n"
            "    logger.exception('the operation failed', exc_info=exc)\n"
        )
        report = self._report_for(source, "src/example.py")  # Measure the repaired source.
        ratchet = BlindHandlerRatchet(report, BaselineDocument({"src/example.py": 1}))  # Hold one accepted entry.
        assert report.broad_handlers == 1, f"the scanner found {report.broad_handlers} broad handler(s)"
        assert report.blind_handlers == 0, f"the scanner found {report.blind_handlers} blind handler(s)"
        assert ratchet.growth_violations() == (), "a repaired handler must create no violation"

    def test_a_tuple_handler_is_blind_only_when_the_bound_name_stays_unused(self) -> None:
        """A tuple clause that holds a broad name follows the same bound-name rule."""
        unused = "try:\n    run()\nexcept (Exception, ValueError) as error:\n    report()\n"  # Drop the exception.
        used = "try:\n    run()\nexcept (Exception, ValueError) as error:\n    report(error)\n"  # Report it.
        unused_broad, unused_blind = BlindHandlerScanner.scan_source(unused, "src/tuple_unused.py")  # Measure.
        used_broad, used_blind = BlindHandlerScanner.scan_source(used, "src/tuple_used.py")  # Measure.
        assert (unused_broad, unused_blind) == (1, 1), "an unused tuple binding must be a candidate"
        assert (used_broad, used_blind) == (1, 0), "a reported tuple binding must be accepted"

    def test_a_returning_handler_is_a_candidate_and_a_reporting_handler_is_accepted(self) -> None:
        """A handler that returns without reading the exception drops the failure cause."""
        returning = (  # Model the silent return, which needs a function scope to parse.
            "def op():\n" "    try:\n" "        run()\n" "    except Exception as error:\n" "        return\n"
        )
        reporting = "try:\n    run()\nexcept Exception as error:\n    report(error)\n"  # Model the repair.
        returning_counts = BlindHandlerScanner.scan_source(returning, "src/return.py")  # Measure the return.
        reporting_counts = BlindHandlerScanner.scan_source(reporting, "src/report.py")  # Measure the repair.
        assert returning_counts == (1, 1), f"the silent return measured {returning_counts}"
        assert reporting_counts == (1, 0), f"the reporting handler measured {reporting_counts}"

    def test_a_nested_body_reference_counts_as_a_reference(self) -> None:
        """A reference inside a nested body still delivers the exception to the operator."""
        source = (  # Model a reference that lives inside a nested function in the handler body.
            "try:\n"
            "    run()\n"
            "except Exception as error:\n"
            "    def describe():\n"
            "        return str(error)\n"
            "    schedule(describe)\n"
        )
        broad, blind = BlindHandlerScanner.scan_source(source, "src/nested.py")  # Measure the nested reference.
        assert broad == 1, f"the scanner found {broad} broad handler(s)"  # Prove the handler entered the scope.
        assert blind == 0, "a nested reference must count as a reference"  # State the documented rule.

    def test_a_narrow_handler_and_a_bare_handler_stay_outside_the_rule(self) -> None:
        """Only a direct broad builtin name enters the measured scope."""
        narrow = "try:\n    run()\nexcept ValueError:\n    pass\n"  # Model an acceptable narrow handler.
        bare = "try:\n    run()\nexcept:\n    pass\n"  # Model a bare clause that this rule does not own.
        narrow_counts = BlindHandlerScanner.scan_source(narrow, "src/narrow.py")  # Measure the narrow handler.
        bare_counts = BlindHandlerScanner.scan_source(bare, "src/bare.py")  # Measure the bare handler.
        assert narrow_counts == (0, 0), f"the narrow handler measured {narrow_counts}"
        assert bare_counts == (0, 0), f"the bare handler measured {bare_counts}"

    def test_test_directory_paths_leave_the_measured_scope(self) -> None:
        """The guard measures production code only, so a test path must drop out."""
        excluded = BlindHandlerScanner.is_excluded("tests/guardrails/test_example.py")  # A top-level test tree.
        nested = BlindHandlerScanner.is_excluded("src/package/tests/test_example.py")  # A nested test tree.
        kept = BlindHandlerScanner.is_excluded("src/package/testing_helpers.py")  # A partial name must stay.
        assert excluded is True, "a top-level test path must leave the scope"  # Prove the exclusion works.
        assert nested is True, "a nested test path must leave the scope"  # Prove whole-component matching.
        assert kept is False, "a partial name match must not leave the scope"  # Prove the match is exact.

    def test_a_zero_file_scan_fails_instead_of_reporting_green(self) -> None:
        """An empty scope proves nothing, so the guard must fail."""
        empty = BlindHandlerScanner.scan_paths(_REPO_ROOT, ())  # Drive the zero-input path directly.
        ratchet = BlindHandlerRatchet(empty, BaselineDocument({}))  # Build the ratchet over the empty scan.
        with pytest.raises(ValueError) as failure:  # The guard must raise on an empty measurement.
            ratchet.check()  # Run the same decision path that the repository test runs.
        assert empty.scanned_files == 0, "the zero-input proof did not report zero scanned files"
        assert "scanned 0 files" in str(failure.value), "the failure message does not name the empty scope"

    def test_an_input_failure_fails_instead_of_reporting_green(self) -> None:
        """A read failure or a syntax failure must stop the guard, not shrink the scope."""
        failures: list[str] = []  # Collect the recorded input failures.
        missing = BlindHandlerScanner.parse_file(_REPO_ROOT / "no_such_file.py", "no_such_file.py", failures)
        report = ScanReport(1, 1, 0, {}, tuple(failures))  # Model a scan that recorded one input failure.
        with pytest.raises(ValueError) as failure:  # The guard must raise on a recorded input failure.
            BlindHandlerRatchet(report, BaselineDocument({})).check()  # Run the decision path.
        assert missing is None, "a missing file must produce no tree"  # Prove the read path returned nothing.
        assert len(failures) == 1, f"the scanner recorded {len(failures)} input failure(s)"
        assert "read failure" in str(failure.value), "the failure message does not name the input defect"


class TestBaselineDocumentDecisions:
    """Direct decision tests for the accepted-debt baseline document."""

    def test_a_missing_baseline_fails(self) -> None:
        """The guard cannot measure growth without a baseline, so it must fail."""
        with pytest.raises(ValueError) as failure:  # The load path must raise on an absent file.
            BaselineDocument.load(_REPO_ROOT / "no_such_baseline.json")  # Drive the missing-input path.
        assert "is missing" in str(failure.value), "the failure message does not name the absent baseline"

    def test_a_malformed_baseline_body_fails(self) -> None:
        """A body that does not parse must fail instead of reporting an empty baseline."""
        with pytest.raises(ValueError) as failure:  # The parse path must raise on damaged text.
            BaselineDocument.parse("{not valid JSON", Path("baseline.json"))  # Drive the malformed path.
        assert "is malformed" in str(failure.value), "the failure message does not name the malformed body"

    def test_a_duplicate_key_fails(self) -> None:
        """The default parser hides a duplicate key, so the guard must reject one."""
        body = '{"files": {"src/a.py": 1, "src/a.py": 2}}'  # Model a body that repeats one file key.
        with pytest.raises(ValueError) as failure:  # The parse path must raise on the repeated key.
            BaselineDocument.parse(body, Path("baseline.json"))  # Drive the duplicate-key path.
        assert "is malformed" in str(failure.value), "the failure message does not name the duplicate key"

    def test_each_invalid_count_fails(self) -> None:
        """An empty, negative, boolean, or noninteger count must fail."""
        invalid: list[object] = [0, -1, True, 1.5, "1", None]  # Model each rejected count value.
        accepted = [value for value in invalid if BaselineDocument.is_positive_integer(value)]  # Measure them.
        with pytest.raises(ValueError) as failure:  # One entry check must raise on a boolean count.
            BaselineDocument.check_entry("src/a.py", True, Path("baseline.json"))  # Drive the entry path.
        assert accepted == [], f"the baseline accepted {accepted} as a positive count"
        assert "invalid count" in str(failure.value), "the failure message does not name the invalid count"

    def test_each_invalid_path_fails(self) -> None:
        """A blank, absolute, Windows, or nonstring path must fail."""
        invalid: list[object] = ["", "   ", "/src/a.py", "src\\a.py", 5, None]  # Model each rejected path.
        rejected = 0  # Count the entries that the guard refused.
        for candidate in invalid:  # Check one candidate at a time so the count stays exact.
            with pytest.raises(ValueError):  # Each candidate must raise inside the entry check.
                BaselineDocument.check_entry(candidate, 1, Path("baseline.json"))  # Drive the entry path.
            rejected += 1  # Record one more refused entry.
        assert rejected == len(invalid), f"the baseline refused {rejected} of {len(invalid)} invalid path(s)"

    def test_a_wrong_header_fails(self) -> None:
        """A wrong schema version, rule, or scope must fail."""
        bodies = [  # Model one body for each rejected header defect.
            '{"schema_version": 2, "rule_id": "blind_broad_exception_handler", "files": {}}',
            '{"schema_version": true, "rule_id": "blind_broad_exception_handler", "files": {}}',
            '{"schema_version": 1, "rule_id": "other_rule", "files": {}}',
            '{"schema_version": 1, "rule_id": "blind_broad_exception_handler", "files": {}}',
        ]
        rejected = 0  # Count the bodies that the guard refused.
        for body in bodies:  # Check one body at a time so the count stays exact.
            with pytest.raises(ValueError):  # Each body must raise inside the header check.
                BaselineDocument.parse(body, Path("baseline.json"))  # Drive the header path.
            rejected += 1  # Record one more refused body.
        assert rejected == len(bodies), f"the baseline refused {rejected} of {len(bodies)} invalid header(s)"

    def test_the_stored_baseline_holds_the_accepted_debt(self) -> None:
        """The stored baseline must validate and hold only positive counts."""
        baseline = BaselineDocument.load(BaselineDocument.BASELINE_PATH)  # Validate the real stored file.
        lowest = min(baseline.files.values())  # Read the smallest stored count for the positive check.
        assert len(baseline.files) > 0, "the stored baseline holds no file entry"  # Prove it measured input.
        assert lowest > 0, f"the stored baseline holds a count of {lowest}"  # Prove each count is positive.


class TestRepositoryBlindHandlerRatchet:
    """Repository check that stops new blind broad exception handlers."""

    def test_the_repository_adds_no_blind_broad_exception_handler(self) -> None:
        """The measured repository must hold no blind handler above its accepted baseline."""
        files = BlindHandlerScanner.tracked_python_files(_REPO_ROOT)  # Build the measured scope from git.
        report = BlindHandlerScanner.scan_paths(_REPO_ROOT, files)  # Measure every tracked non-test file.
        baseline = BaselineDocument.load(BaselineDocument.BASELINE_PATH)  # Load the accepted debt.
        ratchet = BlindHandlerRatchet(report, baseline)  # Compare the measurement with the accepted debt.
        proof = ratchet.check()  # Raise on an empty scope, an input failure, or new growth.
        print(proof)  # Print the stable proof line so a reader can compare two runs.
        assert report.scanned_files > 0, "the blind-handler guard scanned 0 files"  # Prove the scope.
        assert report.parsed_files == report.scanned_files, f"the guard parsed {report.parsed_files} files"
        assert report.blind_handlers <= sum(baseline.files.values()), "the blind handler total grew"
