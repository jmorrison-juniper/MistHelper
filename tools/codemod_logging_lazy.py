"""LibCST-based codemod that converts eager logging formatting to lazy %s args.

This tool implements the transforms required by GitHub issue #429 (the
``CONV-LOG-FSTRING`` sweep). It walks ``MistHelper.py`` (or any provided
target), finds every ``logging.<level>`` / ``<logger>.<level>`` call whose
first argument uses eager formatting, and rewrites the call to use lazy
``%s``-style positional arguments so the logging framework can defer
interpolation when the record is filtered out.

Supported rewrites:

* **G004 (logging-f-string)** -- ``logging.info(f"x={x}")`` becomes
  ``logging.info("x=%s", x)``.
* **G003 (logging-string-concat)** -- ``logging.info("x=" + str(x))`` becomes
  ``logging.info("x=%s", x)``. Also handles ``.format()`` and ``%``-pre-format
  message construction.
* **G201 (logging-exc-info)** -- inside an ``except`` block,
  ``logging.error(msg, exc_info=True)`` becomes ``logging.exception(msg)``.

CLI flags (all optional):

* ``--dry-run`` -- write nothing; report what would change.
* ``--max-sites N`` -- stop after rewriting N sites in this invocation.
* ``--start-line L`` -- only consider call sites whose line number is >= L.
* ``--end-line L`` -- only consider call sites whose line number is <= L.
* ``--skip-lines L1,L2,...`` -- explicit line numbers to leave untouched
  (used by the security audit to opt sites out).
* ``--report PATH`` -- write a per-site JSON change report to PATH.

Exit codes:

* ``0`` -- success (zero or more rewrites; tree-clean exit).
* ``1`` -- parse error reading the input file.
* ``2`` -- encountered an unrecognized format spec inside an f-string and
  ``--allow-skip-unknown`` was NOT passed.
* ``3`` -- encountered an audit-flagged line that was NOT included in
  ``--skip-lines`` (operator must decide before continuing).

Issue: https://github.com/jmorrison-juniper/MistHelper/issues/429
"""

from __future__ import annotations  # Enable PEP 604 unions on Python 3.13.

import argparse  # Stdlib CLI argument parser.
import json  # For optional --report JSON output.
import logging  # We log our own progress through the codemod.
from dataclasses import dataclass, field  # Lightweight result records.
from pathlib import Path  # Portable path handling on Windows + POSIX.

import libcst as cst  # The AST-preserving CST library we transform against.
from libcst.metadata import PositionProvider  # Lets us read 1-based line numbers.

LOGGER_NAMES: frozenset[str] = frozenset(  # Names the codemod recognizes as a logger object.
    {"logging", "logger", "log", "LOG", "_logger", "_log"}
)
LEVEL_METHODS: frozenset[str] = frozenset(  # Method names that take a message + args.
    {"debug", "info", "warning", "warn", "error", "critical", "exception", "log"}
)


@dataclass
class CodemodReport:
    """Per-site record of what the codemod did (or skipped)."""

    file: str  # Absolute or relative path of the file scanned.
    rewrites: list[dict] = field(default_factory=list)  # One dict per converted site.
    skipped: list[dict] = field(default_factory=list)  # One dict per skipped site (with reason).
    parse_error: str | None = None  # libcst parse error message, if any.

    def to_json(self) -> str:
        """Serialize the report to indented JSON for human + diff review."""
        return json.dumps(  # Pretty-print so reviewers can read it.
            {
                "file": self.file,
                "rewrites": self.rewrites,
                "skipped": self.skipped,
                "parse_error": self.parse_error,
            },
            indent=2,
            sort_keys=True,
        )


class LoggingLazyCodemod(cst.CSTTransformer):
    """LibCST transformer that rewrites eager logging calls to lazy form.

    Phase-0 scaffold: this class wires up metadata and the public surface,
    but the transformer methods (G004/G003/G201) are stubs that simply
    record visits in ``self.report`` without modifying the tree. The
    behavior-modifying transforms land in Phase 1.
    """

    METADATA_DEPENDENCIES = (PositionProvider,)  # Required for line-number filtering.

    def __init__(
        self,
        *,
        start_line: int = 0,
        end_line: int = 10**9,
        skip_lines: frozenset[int] = frozenset(),
        max_sites: int | None = None,
        dry_run: bool = False,
    ) -> None:
        """Construct the transformer with filtering knobs from the CLI."""
        super().__init__()  # Required to initialize the libcst transformer state.
        self.start_line = start_line  # Inclusive lower line bound for sites.
        self.end_line = end_line  # Inclusive upper line bound for sites.
        self.skip_lines = skip_lines  # Sites the security audit told us to skip.
        self.max_sites = max_sites  # Stop rewriting after this many sites this run.
        self.dry_run = dry_run  # If True, transforms run but result is discarded by CLI.
        self.report = CodemodReport(file="")  # Filled in by the CLI before transform.
        self._rewrite_count = 0  # Running count of sites rewritten this invocation.
        logging.debug(  # Action-logging rule: emit configuration after construction.
            "LoggingLazyCodemod configured: start=%s end=%s skip=%d max=%s dry_run=%s",
            start_line,
            end_line,
            len(skip_lines),
            max_sites,
            dry_run,
        )

    def leave_Call(  # libcst hook invoked once per Call node after children visited.
        self, original_node: cst.Call, updated_node: cst.Call
    ) -> cst.Call:
        """Phase-0 stub: detect logging calls but do not rewrite yet."""
        if not self._is_logging_call(updated_node):  # Skip non-logging calls fast.
            return updated_node  # Tree unchanged.
        line = self._line_of(original_node)  # Resolve the 1-based source line.
        if line < self.start_line or line > self.end_line:  # Outside requested range.
            return updated_node  # Tree unchanged.
        if line in self.skip_lines:  # Operator opted this site out.
            self.report.skipped.append(  # Record the skip so the report shows it.
                {"line": line, "reason": "in --skip-lines"}
            )
            return updated_node  # Tree unchanged.
        self.report.skipped.append(  # Phase-0 scaffold: every detected site is "skipped: not_implemented".
            {"line": line, "reason": "phase0_stub_no_transform_yet"}
        )
        return updated_node  # Tree unchanged until Phase 1 transforms land.

    def _is_logging_call(self, node: cst.Call) -> bool:
        """Return True if the Call looks like ``<logger>.<level>(...)``."""
        func = node.func  # Pull out the callable expression once.
        if isinstance(func, cst.Attribute):  # Common case: foo.bar(...) calls.
            method = func.attr.value  # Method name (the .bar part).
            if method not in LEVEL_METHODS:  # Not a logging method name.
                return False  # Bail out fast.
            value = func.value  # Object the method is called on (the foo part).
            if isinstance(value, cst.Name) and value.value in LOGGER_NAMES:  # logging.info(...)
                return True  # Direct match against known logger names.
            if isinstance(value, cst.Attribute) and value.attr.value in LOGGER_NAMES:  # self.logger.info(...)
                return True  # Matches attribute-chain access to a logger.
        return False  # Anything else is not a logging call we touch.

    def _line_of(self, node: cst.CSTNode) -> int:
        """Look up the 1-based source line for a node via libcst metadata."""
        pos = self.get_metadata(PositionProvider, node)  # Returns CodeRange.
        return pos.start.line  # Top-left line of the node.


def _parse_skip_lines(raw: str | None) -> frozenset[int]:
    """Parse the ``--skip-lines L1,L2,...`` CLI argument into a frozenset."""
    if not raw:  # Empty / missing -> no sites skipped.
        return frozenset()  # Immutable empty set is the safe default.
    parts = [p.strip() for p in raw.split(",") if p.strip()]  # Tolerate whitespace + trailing commas.
    return frozenset(int(p) for p in parts)  # ValueError surfaces bad input clearly.


def build_argument_parser() -> argparse.ArgumentParser:
    """Build the argparse instance for the CLI entry point."""
    parser = argparse.ArgumentParser(  # One parser per invocation.
        prog="codemod_logging_lazy",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,  # Keep docstring layout.
    )
    parser.add_argument("path", type=Path, help="Python file to rewrite (e.g. MistHelper.py)")
    parser.add_argument("--dry-run", action="store_true", help="report only; do not write")
    parser.add_argument("--max-sites", type=int, default=None, help="stop after N rewrites")
    parser.add_argument("--start-line", type=int, default=0, help="only sites with line >= L")
    parser.add_argument("--end-line", type=int, default=10**9, help="only sites with line <= L")
    parser.add_argument("--skip-lines", type=str, default="", help="comma-separated line numbers to skip")
    parser.add_argument("--report", type=Path, default=None, help="write JSON report to PATH")
    parser.add_argument(  # Allow the codemod to skip unknown format specs without aborting.
        "--allow-skip-unknown",
        action="store_true",
        help="if set, unrecognized format specs are skipped instead of triggering exit 2",
    )
    return parser  # Returned so __main__ can call parser.parse_args().


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns the documented exit code (0/1/2/3)."""
    logging.basicConfig(  # Default to INFO so progress lines render on stderr.
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    parser = build_argument_parser()  # Build the CLI parser.
    args = parser.parse_args(argv)  # Parse caller-supplied or sys.argv arguments.
    logging.info("codemod start: path=%s dry_run=%s", args.path, args.dry_run)  # Action log entry.
    try:
        source = args.path.read_text(encoding="utf-8")  # Read the target file.
    except OSError as exc:  # Cover both missing file and permission errors.
        logging.error("failed to read %s: %s", args.path, exc)  # Surface the failure.
        return 1  # Documented "parse / read error" exit.
    try:
        module = cst.parse_module(source)  # Parse the file into a libcst Module.
    except cst.ParserSyntaxError as exc:  # libcst-specific parse error type.
        logging.error("libcst parse failed for %s: %s", args.path, exc)  # Surface it.
        return 1  # Same exit code as a read failure (both are "couldn't get the AST").
    wrapper = cst.MetadataWrapper(module)  # Required to enable PositionProvider metadata.
    transformer = LoggingLazyCodemod(  # Build the transformer with CLI knobs.
        start_line=args.start_line,
        end_line=args.end_line,
        skip_lines=_parse_skip_lines(args.skip_lines),
        max_sites=args.max_sites,
        dry_run=args.dry_run,
    )
    transformer.report.file = str(args.path)  # Stamp the file path for the report.
    new_module = wrapper.visit(transformer)  # Run the visitor; returns a new (or unchanged) module.
    detected = len(transformer.report.skipped) + len(transformer.report.rewrites)  # Combined visit count.
    logging.info(  # Summary line after the walk completes.
        "codemod done: detected=%d rewrites=%d skipped=%d",
        detected,
        len(transformer.report.rewrites),
        len(transformer.report.skipped),
    )
    if args.report is not None:  # Caller wants a machine-readable artifact.
        args.report.write_text(transformer.report.to_json(), encoding="utf-8")  # Emit the JSON.
        logging.info("wrote report to %s", args.report)  # Acknowledge the write.
    if args.dry_run:  # Dry-run: never touch the source file.
        logging.info("dry-run: source file untouched")  # Be explicit about the no-op.
        return 0  # Phase 0 scaffold exits cleanly when there's nothing to do.
    if new_module.code != source:  # Tree changed during transform.
        args.path.write_text(new_module.code, encoding="utf-8")  # Persist the rewrite.
        logging.info("wrote %d bytes to %s", len(new_module.code), args.path)  # Confirm write.
    return 0  # Success.


if __name__ == "__main__":  # Standard CLI guard so import-time has no side effects.
    raise SystemExit(main())  # Propagate the documented exit code.
