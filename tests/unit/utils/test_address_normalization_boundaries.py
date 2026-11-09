"""Verify that optional address parsing catches only parser failures."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from src.foundation.support.utils import address_utils
from src.foundation.support.utils.address_utils import AddressUtils


class TestScourgifyBoundary:
    """Keep optional parser failures separate from local result-shaping defects."""

    @pytest.mark.parametrize(
        "shaping_error_type",
        [RuntimeError, TypeError, AttributeError, NameError, IndexError, ValueError],
    )
    def test_result_shaping_error_propagates(self, shaping_error_type: type[Exception]) -> None:
        """Expose result-building defects instead of hiding them with fallback parsing."""
        address = "123 Main St, Springfield, IL 62701"  # WHY: use one supported input for both boundaries
        normalized_record = {"address_line_1": "123 Main St"}  # WHY: provide a valid optional-parser result
        shaping_error = "result shaping defect"  # WHY: identify the local error that must escape

        with (
            patch.object(address_utils, "normalize_address_record", return_value=normalized_record) as normalize,
            patch.object(
                AddressUtils,
                "_build_scourgify_result",
                side_effect=shaping_error_type(shaping_error),
            ) as build_result,
            patch.object(AddressUtils, "_parse_components") as fallback,
        ):
            with pytest.raises(shaping_error_type, match=shaping_error):  # WHY: local defects must remain visible
                AddressUtils.enhanced_parse(address)  # WHY: exercise the public parser boundary

        normalize.assert_called_once_with(address)  # WHY: confirm the optional parser received the input
        build_result.assert_called_once_with(normalized_record, address)  # WHY: confirm the failing stage
        fallback.assert_not_called()  # WHY: local defects must not enter the parser fallback

    def test_optional_parser_error_keeps_heuristic_fallback(self) -> None:
        """Preserve fallback behavior when the optional parser rejects an input."""
        address = "123 Main St, Springfield, IL 62701"  # WHY: use one supported input for both boundaries
        fallback_result = {"is_parseable": True}  # WHY: mark the expected heuristic result

        with (
            patch.object(
                address_utils,
                "normalize_address_record",
                side_effect=ValueError("unsupported address"),
            ),
            patch.object(AddressUtils, "_parse_components", return_value=fallback_result) as fallback,
        ):
            result = AddressUtils.enhanced_parse(address)  # WHY: exercise fallback after parser rejection

        assert result is fallback_result  # WHY: preserve the heuristic result without reshaping it
        fallback.assert_called_once_with(address, debug=False)  # WHY: confirm fallback receives the input
