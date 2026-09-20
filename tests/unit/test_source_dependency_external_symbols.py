"""Guard the third-party symbols the source dependency resolver returns.

Issue #3111: the resolver returned the bare ``tqdm`` module, so every caller
that wrote ``deps.tqdm(items, ...)`` raised
``TypeError: 'module' object is not callable``. Menu 34 failed on every run,
and menu 17 and menu 24 held the same latent fault. An empty data set hid the
defect, because the progress bar never ran.

These tests state the contract for each external name the resolver publishes.
"""

from __future__ import annotations

import prettytable
import tqdm as tqdm_module

from src.config.source_dependency_resolver import SourceDependencyResolver


class TestExternalSymbolResolution:
    """Each external name must resolve to the object the caller uses."""

    def test_tqdm_resolves_to_the_callable(self):
        """The resolver must return the progress-bar callable, not its module."""
        resolved = SourceDependencyResolver.tqdm
        assert resolved is tqdm_module.tqdm  # The caller writes deps.tqdm(items, ...).
        assert callable(resolved)  # A module is not callable, which is the reported defect.

    def test_tqdm_iterates_without_raising(self):
        """A progress-bar call must iterate, because menu 34 stops here."""
        assert list(SourceDependencyResolver.tqdm([1, 2, 3], desc="Sites", unit="site")) == [1, 2, 3]

    def test_tqdm_supports_the_context_manager_form(self):
        """switch_vc_stats uses ``with deps.tqdm(total=...)``, so the value must enter a context."""
        with SourceDependencyResolver.tqdm(total=2, desc="Switches", unit="switch") as progress:
            progress.update(1)  # A bare module raises AttributeError here.
        assert progress.n == 1  # The bar must record the single step it received.

    def test_prettytable_resolves_to_the_class(self):
        """The renderer must stay a class, because the repair must not change it."""
        assert SourceDependencyResolver.PrettyTable is prettytable.PrettyTable

    def test_mistapi_resolves_to_the_module(self):
        """A package with no named attribute must still resolve to the module itself."""
        import mistapi

        assert SourceDependencyResolver.mistapi is mistapi

    def test_every_named_attribute_exists_on_its_module(self):
        """Each configured attribute must exist, so a typo cannot return a missing symbol."""
        import importlib

        configured = SourceDependencyResolver._external_attributes
        assert len(configured) >= 2, "The resolver must name the tqdm and PrettyTable attributes."
        for name, attribute in configured.items():
            module = importlib.import_module(SourceDependencyResolver._external_modules[name])
            assert hasattr(module, attribute), f"{name} names a missing attribute {attribute}"

    def test_attribute_map_only_names_known_modules(self):
        """Every attribute entry must name a module the resolver can import."""
        unknown = set(SourceDependencyResolver._external_attributes) - set(SourceDependencyResolver._external_modules)
        assert unknown == set()  # An orphan entry would never take effect.
