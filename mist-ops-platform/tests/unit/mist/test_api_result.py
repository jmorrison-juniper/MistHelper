"""Tests for ApiResult .success and .error derived properties (T019).

Verify .success returns True for 2xx, False otherwise.
Verify .error returns None for 2xx, extracts detail for non-2xx.
"""

from __future__ import annotations

import logging

import pytest

from src.shared.mist.endpoints import ApiResult

LOGGER = logging.getLogger(__name__)


class TestApiResultSuccess:
    """ApiResult.success is True for 2xx status codes."""

    def test_200_is_success(self) -> None:
        result = ApiResult(status_code=200, data={})
        assert result.success is True

    def test_201_is_success(self) -> None:
        result = ApiResult(status_code=201, data={})
        assert result.success is True

    def test_299_is_success(self) -> None:
        result = ApiResult(status_code=299, data={})
        assert result.success is True

    def test_400_is_not_success(self) -> None:
        result = ApiResult(status_code=400, data={})
        assert result.success is False

    def test_500_is_not_success(self) -> None:
        result = ApiResult(status_code=500, data={})
        assert result.success is False


class TestApiResultError:
    """ApiResult.error extracts detail for non-2xx codes."""

    def test_success_returns_none(self) -> None:
        result = ApiResult(status_code=200, data={"id": "a"})
        assert result.error is None

    def test_error_with_detail_key(self) -> None:
        result = ApiResult(
            status_code=404,
            data={"detail": "Not Found"},
        )
        assert result.error == "Not Found"

    def test_error_without_detail_stringifies_data(self) -> None:
        result = ApiResult(
            status_code=500,
            data={"message": "internal"},
        )
        assert "message" in str(result.error)

    @pytest.mark.parametrize(
        ("data", "expected_error"),
        [
            pytest.param([], "[]", id="empty-list"),
            pytest.param([{"err": "bad"}], "[{'err': 'bad'}]", id="single-error"),
            pytest.param(
                [{"detail": "first"}, {"detail": "second"}],
                "[{'detail': 'first'}, {'detail': 'second'}]",
                id="multiple-errors",
            ),
            pytest.param(
                [{"err": "bad", "code": "E400"}],
                "[{'err': 'bad', 'code': 'E400'}]",
                id="all-fields",
            ),
        ],
    )
    def test_error_with_list_data(self, data: list[dict[str, str]], expected_error: str) -> None:
        """Keep every list entry and field in the error text."""
        LOGGER.info("Checking the error text for %d list entries.", len(data))
        result = ApiResult(status_code=400, data=data)
        assert result.error == expected_error
        LOGGER.debug("Checked the error text for %d list entries.", len(data))
