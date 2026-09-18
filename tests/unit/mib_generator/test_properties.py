"""Property tests for the descriptor maker and the OID ledger.

A hand-picked example proves one case. A property test feeds many random
cases, so it finds the input that a person did not think of. Tasks T030
and T033 ask for these two properties.
"""

from __future__ import annotations

import json  # JSONDecodeError names the expected malformed ledger failure.
from pathlib import Path  # Path keeps the temporary ledger name free of a separator.

from hypothesis import HealthCheck, given, settings  # The property engine.
from hypothesis import strategies as st  # The random input builders.

from src.metrics_gateway.catalog import MetricScope  # The scope decides the descriptor prefix.
from src.mib_generator.assignment import DescriptorMaker, OidLedger  # The two units under test.

# A field path in the wild holds letters, digits, dots, and the array marker.
PATHS = st.text(
    alphabet=st.characters(min_codepoint=32, max_codepoint=0x2FFF),
    min_size=1,
    max_size=60,
)
SCOPES = st.sampled_from(list(MetricScope))  # Every scope must give a legal name.


@given(scope=SCOPES, path=PATHS)
@settings(
    max_examples=200,  # Keep the existing sample count for descriptor coverage.
    deadline=None,  # Disable the duration limit because this test checks a property.
    suppress_health_check=[HealthCheck.function_scoped_fixture],  # Keep the fixture health check rule for this file.
)
def test_every_descriptor_is_a_legal_smiv2_name(scope: MetricScope, path: str) -> None:
    """Random text must still give a legal SMIv2 descriptor."""
    name = DescriptorMaker().make(scope, path, frozenset())  # Feed the random path in.
    assert name[0].islower()  # SMIv2 wants a lower-case first letter.
    assert name.isascii()  # The MIB file carries ASCII only.
    assert name.isalnum()  # No separator and no accent may survive the clean-up.
    assert len(name) <= 64  # SMIv2 caps the descriptor length at 64 characters.


@given(scope=SCOPES, paths=st.lists(PATHS, min_size=2, max_size=12, unique=True))
@settings(
    max_examples=100,  # Keep the existing sample count for duplicate coverage.
    deadline=None,  # Disable the duration limit because this test checks a property.
    suppress_health_check=[HealthCheck.function_scoped_fixture],  # Keep the fixture health check rule for this file.
)
def test_two_paths_never_share_one_descriptor(scope: MetricScope, paths: list[str]) -> None:
    """The taken set must stop a second field from stealing a name."""
    maker = DescriptorMaker()  # One maker serves the whole batch.
    seen: set[str] = set()  # The set grows as each name is handed out.
    for path in paths:  # Walk the random batch in order.
        name = maker.make(scope, path, frozenset(seen))  # Give the maker the used names.
        assert name not in seen  # The maker must never repeat a name.
        seen.add(name)  # The new name is now taken for the next round.


@given(order=st.permutations(list(range(1, 9))))
@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_the_claim_order_never_changes_a_column(order: list[int], tmp_path: Path) -> None:
    """A field must keep its column whatever order the run claims it in."""
    first = OidLedger(tmp_path / "first.json")  # A fresh ledger for the plain order.
    for index in range(1, 9):  # Claim the eight fields in rising order.
        first.claim(f"org/f{index}", MetricScope.ORG, f"f{index}")
    baseline = {entry.key: entry.column for entry in first.entries()}  # Record the answer.
    second = OidLedger(tmp_path / "second.json")  # A second ledger for the shuffled order.
    for index in order:  # Claim the same eight fields in the random order.
        second.claim(f"org/f{index}", MetricScope.ORG, f"f{index}")
    shuffled = {entry.key: entry.column for entry in second.entries()}  # Record the answer.
    assert len(set(shuffled.values())) == len(shuffled)  # No two fields may share a column.
    assert sorted(shuffled.values()) == sorted(baseline.values())  # The same column set comes out.


def test_oid_ledger_empty_body_reports_json_parse_error(tmp_path: Path) -> None:
    """A zero-byte ledger file must report a JSON parse error."""
    path = tmp_path / "ledger.json"  # Keep the damaged ledger isolated to this test.
    path.write_text(b"".decode(), encoding="utf-8")  # Model an empty ledger body.
    try:
        OidLedger(path).load()  # Drive the product ledger parser.
    except json.JSONDecodeError as error:
        assert error.msg == "Expecting value"  # The parser must name the empty JSON body.
    else:
        raise AssertionError("OidLedger.load must reject an empty JSON body.")  # Guard false success.


def test_oid_ledger_malformed_body_reports_json_parse_error(tmp_path: Path) -> None:
    """A malformed ledger file must report a JSON parse error."""
    path = tmp_path / "ledger.json"  # Keep the damaged ledger isolated to this test.
    path.write_text("{not valid JSONDecodeError", encoding="utf-8")  # Model a damaged ledger body.
    try:
        OidLedger(path).load()  # Drive the product ledger parser.
    except json.JSONDecodeError as error:
        assert error.msg == "Expecting property name enclosed in double quotes"  # The parser must name damage.
    else:
        raise AssertionError("OidLedger.load must reject a malformed JSON body.")  # Guard false success.
