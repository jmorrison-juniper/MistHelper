"""Feature-private native SDK fixtures with real temporary output."""

from __future__ import annotations

from collections.abc import Iterator
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

import mistapi
import pytest
from requests import Session

from src.export.data_exporter import DataExporter
from tests.unit.export.test_endpoint_family_exporter import (
    local_trend_context as local_trend_context,
)
from tests.unit.export.test_endpoint_family_exporter import (
    local_trend_environment as local_trend_environment,
)
from tests.unit.export.test_endpoint_family_exporter import (
    trend_sdk_absence as trend_sdk_absence,
)
from tests.unit.export.test_endpoint_family_exporter import (
    trend_sdk_logging as trend_sdk_logging,
)
from tests.unit.export.trend_object_export.documents import CANONICAL_DOCUMENTS, TrendDocument
from tests.unit.export.trend_object_export.native_transport import (
    COMMON_FAILURES,
    NativeBoundaries,
    NativeResponseFactory,
    NativeTrendTransport,
    WireScenario,
)


@pytest.fixture(params=range(2), ids=("summary", "classifier"))
def trend_document(request: pytest.FixtureRequest) -> TrendDocument:
    """Give each case independent literal document and expected-record dictionaries."""
    return deepcopy(CANONICAL_DOCUMENTS[request.param])


@pytest.fixture
def local_trend_session(local_trend_environment: Path, trend_sdk_logging: None) -> Iterator[mistapi.APISession]:
    """Use a real credential-free session without rejecting expected SDK failure logs."""
    session = mistapi.APISession(env_file=str(local_trend_environment), show_cli_notif=False)
    try:
        yield session
    finally:
        session._session.close()


@pytest.fixture
def native_trend_run(
    local_trend_session: mistapi.APISession,
    local_trend_context: None,
    trend_document: TrendDocument,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[NativeBoundaries]:
    """Control only HTTP, console input, and forbidden stores while the real writer executes."""
    monkeypatch.setenv("MISTHELPER_STANDALONE", "true")
    monkeypatch.setattr(DataExporter, "_standalone_logged", False)
    monkeypatch.setattr(DataExporter, "_standalone_probe", None)
    transport = NativeTrendTransport(trend_document)
    with (
        patch.object(local_trend_session, "mist_get", side_effect=transport.request),
        patch("builtins.input", side_effect=trend_document.target.answers),
        patch.object(
            DataExporter, "write_with_format_selection", wraps=DataExporter.write_with_format_selection
        ) as writer,
        patch.object(Session, "request", side_effect=AssertionError("A network request is forbidden.")) as network,
        patch.object(
            DataExporter, "_init_router", side_effect=AssertionError("A production store is forbidden.")
        ) as router,
    ):
        yield NativeBoundaries(trend_document, transport, writer, network, router)


@pytest.fixture(params=COMMON_FAILURES, ids=[case[0] for case in COMMON_FAILURES])
def native_failure(request: pytest.FixtureRequest, native_trend_run: NativeBoundaries) -> str:
    """Apply genuine wire or transport failures without replacing an endpoint or writer."""
    name, scenario = deepcopy(request.param)
    uri = native_trend_run.document.target.uri
    response = NativeResponseFactory.make(uri, scenario) if isinstance(scenario, WireScenario) else scenario
    native_trend_run.transport.responses[uri] = response
    return str(name)
