"""Static proof that every logging call in the capture portal obeys the rules.

Why:
    A log line is the only record an operator reads after a failed upgrade. Five
    rules keep that record safe and readable. A static scan is the only way to
    prove the first four at once. A runtime test would prove one branch and
    would leave every unvisited branch unchecked.

    The fifth rule names two fields of the record instead of the message, so the
    last two tests read the format string and render one real record.

    The five rules:

    1. A message is a plain string with `%s` placeholders. The logging library
       then builds the text only when a handler accepts the record, and a broken
       argument raises inside logging instead of at the call site.
    2. A message holds ASCII characters only. See `quickstart.md` section 11.
    3. No call passes an email address, a password, an API token, or a lock
       token as a plain value. `runtime/identity.py` states that the digest from
       `email_digest` is the only form of an address that a log record may hold.
    4. The placeholder count matches the argument count, so no argument is
       dropped from the record without a reader ever noticing.
    5. Every record carries a run identifier and a site identifier, so a reader
       follows one upgrade through the lines of ten operators. The format string
       names both fields, and a filter supplies a value for a record that names
       neither.

    Scope: `src/upgrade_portal/` only. `src/auth/interactive/login_orchestrator.py`
    logs a plain email address at its lines 82, 121, and 221. That file sits
    outside this package, so this module never reads it and never reports it.
    A separate task owns that repair.

    Every failure message below names the file and the line, because a bare
    failure teaches a future reader nothing.
"""

from __future__ import annotations

import ast
import logging
import re
from pathlib import Path
from typing import NamedTuple

import pytest

from src.upgrade_portal.app import factory  # The module that owns the log format and the log handler.

# WHY: The test file sits three levels below the repository root, so the scan
# needs no working directory and no import of the package under test.
REPO_ROOT = Path(__file__).resolve().parents[3]
PACKAGE_ROOT = REPO_ROOT / "src" / "upgrade_portal"

# WHY: The scan reads this package and nothing else. A path outside it belongs
# to another owner and to another task.
PACKAGE_PREFIX = "src/upgrade_portal/"

# WHY: Every method the logging library publishes for writing a record. A survey
# of the package found three receivers only: `logger`, `_LOGGER`, and `logging`.
LOGGING_METHODS = frozenset({"debug", "info", "warning", "warn", "error", "exception", "critical", "fatal", "log"})

# WHY: `Logger.log` takes the level first, so the message is the second value.
LEVEL_FIRST_METHODS = frozenset({"log"})

# WHY: A receiver whose name holds this text is a logger. The rule keeps an
# unrelated `report.error(...)` call out of the scan.
RECEIVER_MARK = "log"

# WHY: The credential field names from `runtime/identity.py`, plus the word for
# a personal address. A value under any of these names must never reach a log.
CREDENTIAL_WORDS = (
    "email",
    "password",
    "passwd",
    "secret",
    "token",
    "apikey",
    "api_key",
    "authorization",
    "credential",
    "otp",
)

# WHY: A name that ends this way carries a safe form. `email_digest` holds the
# one-way digest, and `SECRET_KEY_VARIABLE` holds the name of a variable, never
# its value. The portal names the variable and never the value.
SAFE_SUFFIXES = ("_digest", "_variable", "_name", "_names", "_field", "_fields", "_present", "_count")

# WHY: A call to a function whose name ends this way returns the safe form, so
# the argument it reads is already sanitized.
SANITIZER_SUFFIX = "_digest"

# WHY: The `%`-style conversion specifiers that the logging library expands. The
# scan counts them against the arguments, and `%%` is an escape, never a slot.
PLACEHOLDER_PATTERN = re.compile(r"%(?:%|[-+ #0]*[0-9*]*(?:\.[0-9*]+)?[hlL]?[diouxXeEfFgGcrsab])")
ESCAPED_PERCENT = "%%"

# WHY: An address shape, not an address validator. The scan only needs to catch
# a literal address that a developer pasted into a message.
EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")

# WHY: A floor, never the exact count. The package holds well over two hundred
# calls today. A scan that suddenly finds almost none is broken, and every other
# test here would then pass while proving nothing.
MINIMUM_CALLS = 50

# WHY: The two context fields that every portal record carries. The names are
# written out here, so a rename of a constant inside the package cannot make the
# test agree with itself.
CONTEXT_FIELDS = ("run_id", "site_id")

# WHY: A plain message with no slot, no personal value, and no credential. The
# record below carries neither context field, which is the common shape.
PLAIN_MESSAGE = "portal: a probe record for the log format"

# WHY: The logger name plays no part in the two context fields. A fixed name
# keeps a failure message readable.
PROBE_LOGGER = "upgrade_portal.probe"


class LogCall(NamedTuple):
    """One logging call and the file it came from.

    Why:
        A failure message must name the file and the line. The syntax node
        carries the line, and the tree carries no file name, so the record
        pairs the two.
    """

    path: str
    node: ast.Call


def where(call: LogCall) -> str:
    """Name the file and the line of one logging call.

    Args:
        call: The recorded call.

    Returns:
        The path and the line number, joined by a colon.
    """
    return f"{call.path}:{call.node.lineno}"  # The shape an editor opens directly.


def parse_module(path: Path) -> ast.Module:
    """Parse one source file into a syntax tree.

    Args:
        path: The file to read.

    Returns:
        The parsed tree.

    Raises:
        AssertionError: When the file does not parse.
    """
    try:  # A source file that another task is writing may be incomplete.
        return ast.parse(path.read_text(encoding="utf-8"))  # The scan reads the tree, never the text.
    except SyntaxError as fault:  # Report the place, because a bare fault names no line.
        raise AssertionError(f"{path.as_posix()}:{fault.lineno} does not parse: {fault.msg}") from fault


def attribute_name(node: ast.Call) -> str:
    """Return the method name of one call.

    Args:
        node: The call node.

    Returns:
        The attribute name, or an empty string for a plain function call.
    """
    return node.func.attr if isinstance(node.func, ast.Attribute) else ""  # `logger.info` gives `info`.


def is_logging_call(node: ast.AST) -> bool:
    """Report whether one node is a call that writes a log record.

    Args:
        node: Any syntax node.

    Returns:
        True for a call such as `logger.info(...)` or `logging.warning(...)`.
    """
    if not isinstance(node, ast.Call) or attribute_name(node) not in LOGGING_METHODS:  # Wrong shape.
        return False
    receiver = ast.unparse(node.func.value) if isinstance(node.func, ast.Attribute) else ""  # The object.
    return RECEIVER_MARK in receiver.lower()  # Keeps an unrelated `report.error(...)` out of the scan.


def collect_log_calls() -> list[LogCall]:
    """Read every module of the package and record every logging call.

    Why:
        One pass builds the record set that every test below reads. A per-test
        pass would parse the whole package once for each rule.

    Returns:
        Every logging call, with the file it came from.
    """
    found: list[LogCall] = []  # One flat list keeps each test simple.
    for path in sorted(PACKAGE_ROOT.rglob("*.py")):  # A stable order gives a stable failure message.
        relative = path.relative_to(REPO_ROOT).as_posix()  # A short path reads better in a message.
        nodes = [node for node in ast.walk(parse_module(path)) if is_logging_call(node)]  # One file.
        found.extend(LogCall(relative, node) for node in nodes if isinstance(node, ast.Call))  # Narrow.
    return found  # The fixture holds this list for the whole module.


def positional_values(node: ast.Call) -> list[ast.expr]:
    """Return the positional arguments that follow the message.

    Args:
        node: The logging call.

    Returns:
        Every positional argument after the message.
    """
    given = list(node.args)  # A copy, because the level removal below edits the list.
    if attribute_name(node) in LEVEL_FIRST_METHODS:  # `Logger.log` takes the level first.
        given = given[1:]  # Drop the level, so the message sits first again.
    return given[1:]  # Drop the message and keep the values it formats.


def checked_values(node: ast.Call) -> list[ast.expr]:
    """Return every argument expression that the credential scan must read.

    Args:
        node: The logging call.

    Returns:
        The positional values after the message, plus every keyword value.
    """
    return positional_values(node) + [keyword.value for keyword in node.keywords]  # `extra=` counts too.


def message_argument(node: ast.Call) -> ast.expr | None:
    """Return the argument that carries the message of one call.

    Args:
        node: The logging call.

    Returns:
        The message expression, or None when the call passes no message.
    """
    given = list(node.args)  # The message sits among the positional arguments.
    if attribute_name(node) in LEVEL_FIRST_METHODS:  # `Logger.log` takes the level first.
        given = given[1:]  # Drop the level, so the message sits first again.
    return given[0] if given else None  # A call with no message has its own report.


def constant_message(node: ast.Call) -> str | None:
    """Return the message of one call when the message is a plain string.

    Args:
        node: The logging call.

    Returns:
        The message text, or None when the message is absent or built at runtime.
    """
    message = message_argument(node)  # One shared reader for every message rule.
    if not isinstance(message, ast.Constant) or not isinstance(message.value, str):  # Built, or absent.
        return None  # One test reports this shape, and the others skip the call.
    return message.value  # A plain string, ready for the ASCII and slot rules.


def message_shape(node: ast.Call) -> str:
    """Name the syntax shape of the message of one call.

    Args:
        node: The logging call.

    Returns:
        The node class name, or the word `missing`.
    """
    message = message_argument(node)  # The shape names the rule the call broke.
    return "missing" if message is None else type(message).__name__  # `JoinedStr` names an f-string.


def leaf_identifier(node: ast.expr) -> str:
    """Return the final name of one expression.

    Args:
        node: The expression to read.

    Returns:
        The attribute name, the plain name, or an empty string.
    """
    if isinstance(node, ast.Attribute):  # `owner.email_digest` gives `email_digest`.
        return node.attr  # The final part carries the meaning.
    if isinstance(node, ast.Name):  # `actor_email` gives itself.
        return node.id  # The whole name.
    return ""  # Every other shape carries no name of its own.


def names_a_credential(name: str) -> bool:
    """Report whether one name holds a value that must never reach a log.

    Args:
        name: The identifier to judge.

    Returns:
        True when the name promises a credential or a personal address.
    """
    lowered = name.lower()  # The package mixes upper case constants and lower case names.
    if lowered.endswith(SAFE_SUFFIXES):  # A digest, or the name of a variable.
        return False  # The safe form is the required form, never a violation.
    return any(word in lowered for word in CREDENTIAL_WORDS)  # A substring is enough to refuse.


def is_sanitizer(func: ast.expr) -> bool:
    """Report whether one callee returns a safe form of a personal value.

    Args:
        func: The callee expression of a call.

    Returns:
        True for a call such as `email_digest(...)`.
    """
    return leaf_identifier(func).lower().endswith(SANITIZER_SUFFIX)  # The digest sanitizes its argument.


def child_leaks(node: ast.expr) -> list[str]:
    """Check every child expression of one node.

    Args:
        node: The expression to walk into.

    Returns:
        Every name that promises a credential.
    """
    found: list[str] = []  # One list for every branch of the node.
    for child in ast.iter_child_nodes(node):  # A dictionary, a tuple, and a call all reach here.
        if isinstance(child, ast.expr):  # A slice or an operator carries no value of its own.
            found.extend(find_leaks(child))  # The same rules apply one level down.
    return found  # The caller joins these into one message.


def find_leaks(node: ast.expr) -> list[str]:
    """Find every credential value inside one argument expression.

    Why:
        A digest call is the approved form, so the scan stops at it and never
        reports the plain address that the digest reads. Every other shape is
        walked to its leaves, so a value hidden inside a tuple is still found.

    Args:
        node: The argument expression.

    Returns:
        Every name or literal that promises a credential.
    """
    if isinstance(node, ast.Call):  # A call either sanitizes its argument or hides one.
        return [] if is_sanitizer(node.func) else child_leaks(node)  # The digest ends the walk.
    if isinstance(node, ast.Name | ast.Attribute):  # A plain read of a value.
        name = leaf_identifier(node)  # The final part of the expression.
        return [name] if names_a_credential(name) else []  # The name is the whole evidence.
    if isinstance(node, ast.Constant):  # A literal address pasted into the call.
        return [node.value] if isinstance(node.value, str) and EMAIL_PATTERN.search(node.value) else []
    return child_leaks(node)  # A tuple, a dictionary, or an operator.


@pytest.fixture(scope="module")
def log_calls() -> list[LogCall]:
    """Return every logging call in the capture portal package.

    Why:
        The scan parses every module of the package. Module scope runs that
        work once for the whole file instead of once for each test.

    Returns:
        Every recorded logging call.
    """
    return collect_log_calls()  # One pass over the package.


def test_the_package_directory_exists() -> None:
    """The scan reads a real directory, so no other test can pass vacuously."""
    assert PACKAGE_ROOT.is_dir(), f"The scan found no package at {PACKAGE_ROOT.as_posix()}."


def test_the_scan_found_the_expected_call_volume(log_calls: list[LogCall]) -> None:
    """The scan finds many calls, so a broken scan cannot pass every rule.

    Args:
        log_calls: Every recorded logging call.
    """
    assert len(log_calls) >= MINIMUM_CALLS, (
        f"The scan found only {len(log_calls)} logging calls under {PACKAGE_PREFIX}. "
        f"A working scan finds at least {MINIMUM_CALLS}, so the scan itself is broken."
    )


def test_the_scan_reads_the_portal_package_only(log_calls: list[LogCall]) -> None:
    """No scanned file lies outside the capture portal package.

    Why:
        `src/auth/interactive/login_orchestrator.py` logs a plain email address.
        That file belongs to another owner, so this test states the boundary
        instead of reporting a defect the module may not repair.

    Args:
        log_calls: Every recorded logging call.
    """
    outside = sorted({call.path for call in log_calls if not call.path.startswith(PACKAGE_PREFIX)})
    assert not outside, f"The scan read a file outside {PACKAGE_PREFIX}: {outside}."


def test_every_message_is_a_plain_string(log_calls: list[LogCall]) -> None:
    """No message uses an f-string, a format call, or a concatenation.

    Args:
        log_calls: Every recorded logging call.
    """
    broken = [
        f"{where(call)} builds the message as {message_shape(call.node)}"
        for call in log_calls
        if constant_message(call.node) is None
    ]
    assert not broken, "A log message must be a plain string with %s placeholders:\n" + "\n".join(broken)


def test_every_message_is_ascii(log_calls: list[LogCall]) -> None:
    """No message holds a character above the ASCII range.

    Args:
        log_calls: Every recorded logging call.
    """
    broken = [
        f"{where(call)} holds {constant_message(call.node)!r}"
        for call in log_calls
        if not (constant_message(call.node) or "").isascii()
    ]
    assert not broken, "A log message must hold ASCII characters only:\n" + "\n".join(broken)


def test_no_call_passes_a_credential_value(log_calls: list[LogCall]) -> None:
    """No call passes an email address, a password, or a token as a plain value.

    Why:
        `runtime/identity.py` states that the digest from `email_digest` is the
        only form of an address that a log record may hold. The same rule covers
        a password, an API token, and a lock token.

    Args:
        log_calls: Every recorded logging call.
    """
    broken = [
        f"{where(call)} passes {leak}"
        for call in log_calls
        for value in checked_values(call.node)
        for leak in find_leaks(value)
    ]
    assert not broken, "A log call must pass a digest or a variable name, never a value:\n" + "\n".join(broken)


def test_no_message_holds_a_literal_email_address(log_calls: list[LogCall]) -> None:
    """No message text carries an address that a developer pasted in.

    Args:
        log_calls: Every recorded logging call.
    """
    broken = [
        f"{where(call)} holds {constant_message(call.node)!r}"
        for call in log_calls
        if EMAIL_PATTERN.search(constant_message(call.node) or "")
    ]
    assert not broken, "A log message must hold no address:\n" + "\n".join(broken)


def count_placeholders(message: str) -> int:
    """Count the `%`-style slots in one message.

    Args:
        message: The message text.

    Returns:
        The number of slots, with every `%%` escape left out.
    """
    found = PLACEHOLDER_PATTERN.findall(message)  # Every specifier, including the escape.
    return len([item for item in found if item != ESCAPED_PERCENT])  # An escape fills no slot.


def counts_disagree(node: ast.Call) -> bool:
    """Report whether the slot count and the argument count differ.

    Args:
        node: The logging call.

    Returns:
        True when the two counts differ and a static reader can compare them.
    """
    message = constant_message(node)  # A built message has its own test.
    values = positional_values(node)  # The keyword arguments fill no slot.
    if message is None or any(isinstance(value, ast.Starred) for value in values):  # Not comparable.
        return False  # A star unpack hides the count from a static reader.
    return count_placeholders(message) != len(values)  # A dropped value never reaches the record.


def test_placeholder_count_matches_the_argument_count(log_calls: list[LogCall]) -> None:
    """Every message holds one slot for each value the call passes.

    Why:
        A message with too few slots drops a value from the record with no
        warning. A message with too many raises inside the logging library at
        the moment an operator most needs the line.

    Args:
        log_calls: Every recorded logging call.
    """
    broken = [
        f"{where(call)} holds {count_placeholders(constant_message(call.node) or '')} slots "
        f"for {len(positional_values(call.node))} values"
        for call in log_calls
        if counts_disagree(call.node)
    ]
    assert not broken, "A log message must hold one slot for each value:\n" + "\n".join(broken)


def plain_log_record() -> logging.LogRecord:
    """Build one record that names neither the run nor the site.

    Why:
        Most portal modules call `logger.info` with no extra field, so this is
        the common shape of a record. The record holds a plain message, no
        personal value, and no credential.

    Returns:
        A record ready for the portal handler.
    """
    return logging.LogRecord(PROBE_LOGGER, logging.INFO, __file__, 1, PLAIN_MESSAGE, None, None)


def rendered_by_the_portal_handler(record: logging.LogRecord) -> str:
    """Pass one record through the portal handler and return the text.

    Why:
        The handler holds the formatter and the filter together, so one reader
        proves both parts. The logging library raises a `ValueError` when the
        format string names a field that the record does not carry.

    Args:
        record: The record to render.

    Returns:
        The rendered line.
    """
    handler = factory.build_log_handler()  # The formatter and the filter, joined as the portal joins them.
    handler.filter(record)  # The filter supplies a value for each field that the record does not carry.
    return handler.format(record)  # Raises when a named field is still absent.


def test_the_log_format_names_the_run_and_the_site() -> None:
    """The portal log format holds one slot for the run and one for the site.

    Why:
        Ten operators share one log file. A reader follows one upgrade only
        while every line carries the run identifier and the site identifier.
    """
    absent = [name for name in CONTEXT_FIELDS if f"%({name})s" not in factory.LOG_FORMAT]
    assert not absent, f"The portal log format names no slot for {absent}."


def test_a_record_that_names_no_run_still_formats() -> None:
    """The portal handler renders a record that carries neither context field.

    Why:
        The format string names both context fields, so the logging library
        raises on a record that carries neither. A filter supplies a placeholder
        for each absent field. A test that read the format string alone would
        still pass after a delete of that filter, and every portal log line
        would then fail to render.
    """
    record = plain_log_record()  # The common shape, which names neither field.
    rendered = rendered_by_the_portal_handler(record)  # Raises when the filter supplies nothing.
    assert PLAIN_MESSAGE in rendered, f"The portal handler dropped the message from {rendered!r}."
