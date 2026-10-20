"""Regression tests for named menu 195 CSV choices."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from src.mist.resources.site.address_audit import address_corrector as corrector_module
from src.mist.resources.site.address_audit import audit_engine as audit_module
from src.mist.resources.site.address_audit.address_corrector import AddressCorrector
from src.mist.resources.site.address_audit.audit_engine import AddressAuditEngine


def test_primary_csv_prompt_accepts_an_exact_file_name(monkeypatch) -> None:
    """A browser file choice resolves only to a current CSV candidate."""
    candidates = ["data/primary.csv", "data/authority.tsv"]
    answers = iter(["file:primary.csv", ""])
    monkeypatch.setattr(
        audit_module.InputUtils,
        "safe_input",
        staticmethod(lambda *args, **kwargs: next(answers)),
    )

    selected = AddressAuditEngine()._prompt_csv_choice(candidates)

    assert selected == "data/primary.csv"


def test_authority_csv_prompt_accepts_an_exact_file_name(monkeypatch) -> None:
    """A browser authority choice resolves without changing the prompt order."""
    candidates = ["data/primary.csv", "data/Authority.TSV"]
    answers = iter(["file:Authority.TSV", "q"])
    monkeypatch.setattr(
        audit_module.InputUtils,
        "safe_input",
        staticmethod(lambda *args, **kwargs: next(answers)),
    )

    selected = AddressAuditEngine()._prompt_business_csv_choice(candidates, candidates[0])

    assert selected == "data/Authority.TSV"


def test_address_writeback_stays_off_without_explicit_selection(monkeypatch) -> None:
    """An exhausted or blank batch answer never calls the write-back collaborator."""

    class _Corrector:
        """Record whether the write path starts without contacting Mist."""

        def __init__(self) -> None:
            self.review_called = False

        def correctable(self, results: list[object]) -> list[object]:
            return [object()]

        def review_and_apply(self, results: list[object]) -> list[object]:
            self.review_called = True
            return []

    engine = AddressAuditEngine()
    corrector = _Corrector()
    monkeypatch.setattr(engine, "_make_corrector", lambda _: corrector)
    monkeypatch.setattr(audit_module.InputUtils, "safe_input", staticmethod(lambda *args, **kwargs: ""))

    engine._offer_write_back([], None)

    assert corrector.review_called is False


@pytest.mark.parametrize("status_code", [403, 503], ids=["client-error", "server-error"])
def test_address_writeback_rejects_http_errors(monkeypatch, status_code: int) -> None:
    """Mocked HTTP failures cannot report a successful address update."""
    fake_mistapi = MagicMock(name="mistapi")
    fake_mistapi.api.v1.sites.sites.getSiteInfo.return_value = SimpleNamespace(data={"address": "Old"})
    fake_mistapi.api.v1.sites.sites.updateSiteInfo.return_value = SimpleNamespace(status_code=status_code)
    monkeypatch.setattr(corrector_module, "mistapi", fake_mistapi)

    result = AddressCorrector(object())._update_site_address("site-id", "New")

    assert result is False
