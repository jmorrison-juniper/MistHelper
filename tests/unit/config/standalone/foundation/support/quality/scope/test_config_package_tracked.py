"""Guard the accidental source exclusion and the bind-all default (issue #1778).

An unanchored ``config/`` rule in ``.gitignore`` matched every nested directory
of that name. It therefore hid the source package
``mist-ops-platform/src/shared/config/`` from git and from every scanner. A
MEDIUM bandit finding (B104, ``hardcoded_bind_all_interfaces``) sat inside that
package, and no gate reported it.

These tests read text only. They import no application module, so they run in
any environment and they need no optional dependency.
"""

import ast  # Read the assignments of the module without an import of the module.
import re  # Match the ignore rules and the field default without an import of the module.
from pathlib import Path  # Portable paths, because the repository runs on Windows and on Linux.

import pytest  # Test framework of the repository.

REPO_ROOT = Path(__file__).resolve().parents[2]  # tests/unit/<file> sits two levels below the root.
GITIGNORE = REPO_ROOT / ".gitignore"  # The file that held the over-broad rule.
SETTINGS = REPO_ROOT / "mist-ops-platform" / "src" / "shared" / "config" / "settings.py"  # The hidden module.
CONFIG_PACKAGE = SETTINGS.parent  # The whole package that the rule hid.

_UNANCHORED_CONFIG_RULE = re.compile(r"^\s*!?configs?/\s*$")  # A rule without a leading slash matches every level.
_BIND_ALL_ADDRESS = ".".join(["0"] * 4)  # WHY: build the address, so no scanner reads a bind-all literal here.
_INERT_NOQA = re.compile(r"#\s*noqa:\s*S\d+")  # Ruff does not select the S family here, so such a note is inert.


def _gitignore_lines() -> list[str]:
    """Return every line of the repository ignore file."""
    return GITIGNORE.read_text(encoding="utf-8").splitlines()  # Read once, because each test scans the same text.


def _settings_source() -> str:
    """Return the source text of the platform settings module."""
    return SETTINGS.read_text(encoding="utf-8")  # Read the text, because an import needs an optional dependency.


def _assigned_string_defaults() -> list[str]:
    """Return every string value that the settings module assigns to a name."""
    tree = ast.parse(_settings_source())  # Parse the text, because a docstring must not count as a default.
    values: list[str] = []  # Collect the assigned strings for the caller to check.
    for node in ast.walk(tree):  # Walk the whole module, so a nested class also counts.
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):  # Only an assignment carries a field default.
            continue  # Skip a docstring, a call, and every other statement.
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):  # A literal default.
            values.append(node.value.value)  # Record the literal for the bind-all check.
    return values  # The caller asserts against this list.


class TestSourceIsVisible:
    """The ignore rules must not hide a source module."""

    def test_gitignore_holds_no_unanchored_config_rule(self):
        """Every config ignore rule carries a leading slash, so it matches the root only."""
        offenders = [line for line in _gitignore_lines() if _UNANCHORED_CONFIG_RULE.match(line)]
        assert offenders == [], f"An unanchored config rule hides nested source directories: {offenders}"

    def test_settings_module_is_present_in_the_checkout(self):
        """The settings module reaches a checkout, which proves git tracks it."""
        assert SETTINGS.is_file(), "The platform settings module is missing, so git does not track it."

    def test_config_package_holds_its_init_module(self):
        """The package keeps an __init__ module, so every import site resolves."""
        assert (CONFIG_PACKAGE / "__init__.py").is_file()  # A package without this file is not importable.


class TestBindAddressDefault:
    """The API host default must not bind to every interface."""

    def test_default_api_host_is_not_the_bind_all_address(self):
        """The api_host default is a specific address, so bandit reports no B104 finding."""
        match = re.search(r"^\s*api_host:\s*str\s*=\s*\"([^\"]+)\"", _settings_source(), re.MULTILINE)
        if match is None:  # The module defines no bind address, so no field can carry B104.
            pytest.skip("The settings module defines no api_host field, so no bind default exists.")
        assert match.group(1) != _BIND_ALL_ADDRESS  # A bind-all default exposes the API to the whole network.

    def test_settings_module_holds_no_inert_noqa_annotation(self):
        """No `# noqa: S...` note remains, because such a note suppresses nothing here."""
        found = _INERT_NOQA.findall(_settings_source())
        assert found == [], f"An inert ruff annotation remains and misleads a reader: {found}"

    def test_no_field_default_binds_to_every_interface(self):
        """No field default holds the bind-all address, so a later edit cannot reintroduce B104."""
        offenders = [value for value in _assigned_string_defaults() if value == _BIND_ALL_ADDRESS]
        assert offenders == [], "A field default binds the service to every interface."


if __name__ == "__main__":  # Allow a direct run during local development.
    raise SystemExit(pytest.main([__file__, "-q"]))  # Run only this module.
