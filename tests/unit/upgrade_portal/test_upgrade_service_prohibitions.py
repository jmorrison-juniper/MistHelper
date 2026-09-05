"""Guard tests that prove the upgrade seam breaks no prohibition.

Why:
    Section 3 of ``specs/1823-upgrade-capture-portal/contracts/upgrade-service.md``
    lists six prohibitions. A prohibition that no test checks returns the first
    time somebody adds a debug line. These tests read the syntax tree of
    ``src/firmware/upgrade_service.py`` and fail on the exact node.

    The tests read the syntax tree, not the text. A text search finds the word
    ``print`` inside a docstring and reports a false failure, and it misses a
    call that a line break splits. The syntax tree sees the call itself.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from src.firmware import upgrade_service

# The names that a web request can never use, because a web request has no
# terminal and no keyboard.
FORBIDDEN_CALLS = frozenset({"print", "input", "safe_input", "raw_input"})

# The module that holds four globals and two save-and-restore blocks that are
# not thread safe.
FORBIDDEN_IMPORT = "firmware_manager"

# The types that a module-level constant may hold. Every one is immutable, so
# two threads cannot change a shared value.
IMMUTABLE_TYPES = (str, int, float, bool, bytes, tuple, frozenset, type(None))


def is_immutable(value: object) -> bool:
    """Return whether one value and every value inside it is immutable.

    Why:
        A tuple is immutable, but a tuple can hold a list. A shallow test would
        pass a shared list that two threads could change.

    Args:
        value: The value to test.

    Returns:
        True when no thread can change the value.
    """
    if isinstance(value, (tuple, frozenset)):
        return all(is_immutable(item) for item in value)
    return isinstance(value, IMMUTABLE_TYPES)


@pytest.fixture(scope="module")
def source_path() -> Path:
    """Return the path of the upgrade seam module.

    Why:
        The path comes from the imported module, so a rename of the file cannot
        leave the guard reading a stale path.

    Returns:
        The path of ``src/firmware/upgrade_service.py``.
    """
    assert upgrade_service.__file__ is not None
    return Path(upgrade_service.__file__)


@pytest.fixture(scope="module")
def tree(source_path: Path) -> ast.Module:
    """Return the parsed syntax tree of the upgrade seam module.

    Args:
        source_path: The path of the module.

    Returns:
        The syntax tree.
    """
    return ast.parse(source_path.read_text(encoding="utf-8"))


def called_names(tree: ast.Module) -> list[str]:
    """Return the name of every call in the syntax tree.

    Why:
        A call reaches the name either as ``print(...)`` or as
        ``builtins.print(...)``. Both forms need the same check.

    Args:
        tree: The syntax tree of the module.

    Returns:
        Every called name, with a repeat for each call.
    """
    names: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            names.append(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            names.append(node.func.attr)
    return names


def imported_modules(tree: ast.Module) -> list[str]:
    """Return the module name of every import in the syntax tree.

    Args:
        tree: The syntax tree of the module.

    Returns:
        Every imported module name.
    """
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            modules.append(node.module or "")
            modules.extend(f"{node.module or ''}.{alias.name}" for alias in node.names)
    return modules


def module_bindings(tree: ast.Module) -> list[tuple[str, ast.expr | None]]:
    """Return every name that the module binds at module level.

    Why:
        A binding at module level is the only place where a module global can
        appear. A binding inside a class or a function is not module state, so
        the walk reads the top-level body only.

    Args:
        tree: The syntax tree of the module.

    Returns:
        Each bound name with the expression that it binds.
    """
    bindings: list[tuple[str, ast.expr | None]] = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            bindings.extend((target.id, node.value) for target in node.targets if isinstance(target, ast.Name))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            bindings.append((node.target.id, node.value))
        elif isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name):
            bindings.append((node.target.id, node.value))
    return bindings


class TestProhibitions:
    """Tests for the six prohibitions of section 3 of the contract."""

    def test_imports_no_firmware_manager(self, tree: ast.Module) -> None:
        """The seam never imports the module with the unsafe globals.

        Args:
            tree: The syntax tree of the module.
        """
        offenders = [name for name in imported_modules(tree) if FORBIDDEN_IMPORT in name]
        assert offenders == []

    def test_calls_no_print(self, tree: ast.Module) -> None:
        """A web request has no terminal.

        Args:
            tree: The syntax tree of the module.
        """
        assert "print" not in called_names(tree)

    def test_calls_no_input_reader(self, tree: ast.Module) -> None:
        """A web request has no keyboard.

        Args:
            tree: The syntax tree of the module.
        """
        offenders = sorted(set(called_names(tree)) & FORBIDDEN_CALLS)
        assert offenders == []

    def test_opens_no_file(self, tree: ast.Module) -> None:
        """Every output of the portal belongs under ``data/``, never beside the process.

        Args:
            tree: The syntax tree of the module.
        """
        offenders = sorted({name for name in called_names(tree) if name in {"open", "write_text", "write_bytes"}})
        assert offenders == []

    def test_declares_no_global_statement(self, tree: ast.Module) -> None:
        """No function rebinds a module name.

        Args:
            tree: The syntax tree of the module.
        """
        offenders = [node for node in ast.walk(tree) if isinstance(node, (ast.Global, ast.Nonlocal))]
        assert offenders == []

    def test_binds_no_mutable_module_value(self, tree: ast.Module) -> None:
        """Every module-level name binds an immutable value, so no thread can change it.

        The syntax tree names each binding, so a name inside a string cannot
        hide one. A constant that names an earlier constant defeats the literal
        reader, so the test reads the runtime value of that name instead.

        Args:
            tree: The syntax tree of the module.
        """
        offenders: list[str] = []
        for name, value in module_bindings(tree):
            try:
                literal = ast.literal_eval(value) if value is not None else None
            except (ValueError, TypeError, SyntaxError):
                literal = getattr(upgrade_service, name, [])  # WHY: A missing name counts as an offender.
            if not is_immutable(literal):
                offenders.append(name)
        assert offenders == []

    def test_holds_no_module_level_logger_object(self, tree: ast.Module) -> None:
        """The seam builds its logger inside each call, so it holds no logger object.

        Args:
            tree: The syntax tree of the module.
        """
        assert [name for name, _ in module_bindings(tree) if "logger" in name.lower()] == []

    def test_logs_no_credential(self, tree: ast.Module) -> None:
        """FR-009 forbids a token value or a password value in a log record.

        Args:
            tree: The syntax tree of the module.
        """
        secrets = ("token", "password", "apitoken", "secret", "credential")
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                assert not any(word in node.value.lower() and "%s" in node.value for word in secrets)


class TestRuntimeProhibitions:
    """Tests that read the imported module instead of its syntax tree."""

    def test_holds_no_mutable_attribute(self) -> None:
        """No public attribute of the module is a list, a dictionary, or a set."""
        offenders = [
            name
            for name in dir(upgrade_service)
            if not name.startswith("__") and isinstance(getattr(upgrade_service, name), (list, dict, set, bytearray))
        ]
        assert offenders == []

    def test_sanctions_no_broken_endpoint(self) -> None:
        """The allow list holds no ``getOrgSsrUpgrade``.

        The installed SDK builds the cancel path inside that function at
        ``mistapi/api/v1/orgs/ssr.py:167``, so a status read would post to the
        cancel path.
        """
        names = [name for name, _ in upgrade_service._ENDPOINT_MODULES]
        assert "getOrgSsrUpgrade" not in names

    def test_sanctions_every_endpoint_that_the_seam_names(self) -> None:
        """Every cancel endpoint and read endpoint sits in the allow list."""
        names = {name for name, _ in upgrade_service._ENDPOINT_MODULES}
        needed = {
            "upgradeSiteDevices",
            "upgradeOrgSsrs",
            "cancelSiteDeviceUpgrade",
            "cancelOrgDeviceUpgrade",
            "cancelOrgSsrUpgrade",
            "getSiteDeviceUpgrade",
            "getOrgDeviceUpgrade",
            "getSiteSsrUpgrade",
            "listOrgDevicesStats",
            "listSiteAvailableDeviceVersions",
        }
        assert needed <= names

    def test_every_public_record_is_frozen(self) -> None:
        """A frozen record is safe to hand to another thread."""
        records = (
            upgrade_service.DeviceTarget,
            upgrade_service.UpgradeOptions,
            upgrade_service.PlanRoute,
            upgrade_service.UpgradePlan,
            upgrade_service.UpgradeSubmission,
            upgrade_service.CancelOutcome,
        )
        assert all(record.__dataclass_params__.frozen for record in records)  # type: ignore[attr-defined]

    def test_the_gateway_family_holds_two_members(self) -> None:
        """The contract names two members, ``JUNOS`` and ``SSR``."""
        assert [member.name for member in upgrade_service.GatewayFamily] == ["JUNOS", "SSR"]
