"""Route-level contract tests for option number refusals."""

from __future__ import annotations

import pytest

from src.upgrade_portal.upgrade import options


@pytest.mark.parametrize("field", ["max_failure_percentage", "p2p_cluster_size"])
def test_single_site_mapper_returns_named_refusal(field: str) -> None:
    """The single-site mapper returns the existing named error boundary."""
    with pytest.raises(options.BadOptionError) as caught:
        options.build_options({field: "²"})
    assert caught.value.code == options.ERROR_BAD_OPTION
    assert caught.value.field == field


@pytest.mark.parametrize("field", ["max_failure_percentage", "p2p_cluster_size"])
def test_multi_site_mapper_uses_the_same_refusal_boundary(field: str) -> None:
    """The shared mapper keeps the same refusal for multi-site option data."""
    with pytest.raises(options.BadOptionError) as caught:
        options.build_options({field: "9" * 5000})
    assert caught.value.code == options.ERROR_BAD_OPTION
    assert caught.value.field == field
