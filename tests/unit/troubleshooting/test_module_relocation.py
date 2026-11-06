"""Verify canonical imports and identities after the troubleshooting relocation."""

from __future__ import annotations

import importlib
from pathlib import Path
from types import ModuleType

import pytest

from src.foundation.runtime.config.source_dependency_resolver import SourceDependencyResolverService

_CANONICAL_MODULES = (
    ("src.foundation.support.menu_testing.interactive_test_runner", "InteractiveTestRunner"),
    ("src.mist.intelligence.marvis.troubleshooting.marvis_troubleshoot_utils", "MarvisTroubleshootUtils"),
    ("src.mist.intelligence.marvis.troubleshooting.troubleshoot_utils", "TroubleshootUtils"),
)
_OLD_PACKAGE = ".".join(("src", "mist", "intelligence", "troubleshooting", "core"))
_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize(("module_name", "class_name"), _CANONICAL_MODULES)
def test_canonical_class_and_logger_identity(module_name: str, class_name: str) -> None:
    """Require each canonical module to own its class and logger identities."""
    module = importlib.import_module(module_name)
    assert getattr(module, class_name).__module__ == module_name
    assert module.logger.name == module_name
    assert isinstance(module, ModuleType)


@pytest.mark.parametrize(
    "module_suffix",
    ("", ".interactive_test_runner", ".marvis_troubleshoot_utils", ".troubleshoot_utils"),
)
def test_obsolete_import_is_absent(module_suffix: str) -> None:
    """Reject the obsolete package and all three obsolete module imports."""
    with pytest.raises(ModuleNotFoundError, match=_OLD_PACKAGE):
        importlib.import_module(_OLD_PACKAGE + module_suffix)


@pytest.mark.parametrize("dependency_name", ("ExtractedMarvisTroubleshootUtils", "MarvisTroubleshootDeps"))
def test_unbound_resolver_returns_canonical_class(dependency_name: str) -> None:
    """Resolve both changed entries without a mocked host or a root CLI import."""
    resolver = SourceDependencyResolverService()
    module = importlib.import_module(_CANONICAL_MODULES[1][0])
    class_name = "MarvisTroubleshootUtils" if dependency_name.startswith("Extracted") else dependency_name
    assert resolver._resolve_source_symbol(dependency_name) is getattr(module, class_name)


def test_obsolete_package_directory_is_absent() -> None:
    """Require removal rather than an empty package or a compatibility shim."""
    package_directory = _REPOSITORY_ROOT.joinpath(*_OLD_PACKAGE.split("."))
    assert not package_directory.exists()
