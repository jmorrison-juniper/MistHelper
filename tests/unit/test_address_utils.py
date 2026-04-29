"""Unit tests for address utilities in src/utils/address_utils.py."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.utils.address_utils import (
    AddressBusinessNameUtils,
    AddressUtils,
    AddressValidationConfig,
    NameNormalizationUtils,
    NominatimValidator,
    _check_parse_status,
    _check_partial_skip,
    _check_single_skip,
    _compare_fields,
    _compare_single_field,
    _detect_country,
    _detect_state,
    _detect_zip,
    _parse_address_parts,
)

# ============================================================================
# AddressValidationConfig
# ============================================================================


class TestAddressValidationConfig:
    """Tests for AddressValidationConfig dataclass."""

    def test_defaults(self):
        config = AddressValidationConfig()
        assert config.timeout == 5
        assert config.debug is False
        assert config.skip_ssl_verify is False
        assert config.org_name is None
        assert config.site_name is None
        assert config.mist_duplicates is None
        assert config.ref_duplicates is None

    def test_custom_values(self):
        config = AddressValidationConfig(
            timeout=10,
            debug=True,
            skip_ssl_verify=True,
            org_name="Acme Corp",
            site_name="HQ",
            mist_duplicates={"key": True},
            ref_duplicates={"key": True},
        )
        assert config.timeout == 10
        assert config.debug is True
        assert config.org_name == "Acme Corp"
        assert config.site_name == "HQ"


# ============================================================================
# AddressUtils.normalize_zip
# ============================================================================


class TestNormalizeZip:
    """Tests for AddressUtils.normalize_zip."""

    def test_empty(self):
        assert AddressUtils.normalize_zip("") == ""
        assert AddressUtils.normalize_zip(None) == ""

    def test_five_digit(self):
        assert AddressUtils.normalize_zip("90210") == "90210"

    def test_nine_digit_dash(self):
        assert AddressUtils.normalize_zip("90210-1234") == "90210"

    def test_four_digit_pads_zero(self):
        assert AddressUtils.normalize_zip("1234") == "01234"

    def test_non_numeric_stripped(self):
        assert AddressUtils.normalize_zip("  9 0 2 1 0  ") == "90210"

    def test_long_truncated(self):
        assert AddressUtils.normalize_zip("123456789") == "12345"


# ============================================================================
# AddressUtils._normalize_state
# ============================================================================


class TestNormalizeState:
    """Tests for AddressUtils._normalize_state."""

    def test_empty(self):
        assert AddressUtils._normalize_state("") == ""
        assert AddressUtils._normalize_state(None) == ""

    def test_full_name(self):
        assert AddressUtils._normalize_state("California") == "ca"

    def test_abbreviation(self):
        assert AddressUtils._normalize_state("CA") == "ca"

    def test_dc(self):
        assert AddressUtils._normalize_state("District of Columbia") == "dc"

    def test_unknown_state(self):
        assert AddressUtils._normalize_state("Narnia") == "narnia"


# ============================================================================
# AddressUtils._normalize_address
# ============================================================================


class TestNormalizeAddress:
    """Tests for AddressUtils._normalize_address."""

    def test_empty(self):
        assert AddressUtils._normalize_address("") == ""
        assert AddressUtils._normalize_address(None) == ""

    def test_abbreviations_applied(self):
        result = AddressUtils._normalize_address("123 Main Street")
        assert "st" in result
        assert "street" not in result

    def test_case_insensitive(self):
        result = AddressUtils._normalize_address("123 MAIN AVE")
        assert "ave" in result

    def test_whitespace_collapsed(self):
        result = AddressUtils._normalize_address("  123  Main   St  ")
        assert "  " not in result

    def test_direction_abbreviated(self):
        result = AddressUtils._normalize_address("100 North Broadway")
        assert "n" in result.split()


# ============================================================================
# AddressUtils._parse_components
# ============================================================================


class TestParseComponents:
    """Tests for AddressUtils._parse_components."""

    def test_empty_string(self):
        result = AddressUtils._parse_components("")
        assert result["is_parseable"] is False
        assert result["parse_reason"] == "empty_input"

    def test_none(self):
        result = AddressUtils._parse_components(None)
        assert result["is_parseable"] is False
        assert result["parse_reason"] == "empty_input"

    def test_unknown_value(self):
        result = AddressUtils._parse_components("unknown")
        assert result["is_parseable"] is False
        assert result["parse_reason"] == "unknown_address"

    def test_na_value(self):
        result = AddressUtils._parse_components("N/A")
        assert result["is_parseable"] is False
        assert result["parse_reason"] == "unknown_address"

    def test_valid_us_address(self):
        result = AddressUtils._parse_components("123 Main St, Springfield, IL, 62701, US")
        assert result["is_parseable"] is True
        assert result["country"] == "US"
        assert result["zip"] == "62701"

    def test_address_with_debug(self):
        result = AddressUtils._parse_components("123 Main St, Springfield, IL", debug=True)
        assert result["is_parseable"] is True


# ============================================================================
# AddressUtils.enhanced_parse
# ============================================================================


class TestEnhancedParse:
    """Tests for AddressUtils.enhanced_parse."""

    def test_fallback_when_no_scourgify(self):
        with patch("src.utils.address_utils.normalize_address_record", None):
            result = AddressUtils.enhanced_parse("123 Main St, Springfield, IL")
            assert result["is_parseable"] is True

    def test_scourgify_success(self):
        mock_result = {
            "address_line_1": "123 Main St",
            "city": "Springfield",
            "state": "IL",
            "postal_code": "62701",
        }
        with patch("src.utils.address_utils.normalize_address_record", return_value=mock_result):
            result = AddressUtils.enhanced_parse("123 Main St, Springfield, IL 62701")
            assert result["is_parseable"] is True
            assert result["parse_reason"] == "usaddress_success"
            assert result["address"] == "123 Main St"

    def test_scourgify_with_line2(self):
        mock_result = {
            "address_line_1": "123 Main St",
            "address_line_2": "Suite 200",
            "city": "Springfield",
            "state": "IL",
            "postal_code": "62701",
        }
        with patch("src.utils.address_utils.normalize_address_record", return_value=mock_result):
            result = AddressUtils.enhanced_parse("123 Main St Suite 200, Springfield, IL")
            assert "Suite 200" in result["address"]

    def test_scourgify_exception_falls_back(self):
        with patch(
            "src.utils.address_utils.normalize_address_record",
            side_effect=Exception("parse error"),
        ):
            result = AddressUtils.enhanced_parse("123 Main St, Springfield, IL")
            assert result["is_parseable"] is True

    def test_debug_mode(self):
        with patch("src.utils.address_utils.normalize_address_record", None):
            result = AddressUtils.enhanced_parse("123 Main St, City, ST", debug=True)
            assert result is not None


# ============================================================================
# AddressUtils._calculate_similarity
# ============================================================================


class TestCalculateSimilarity:
    """Tests for AddressUtils._calculate_similarity."""

    def test_both_empty(self):
        assert AddressUtils._calculate_similarity("", "") == 100.0

    def test_one_empty(self):
        assert AddressUtils._calculate_similarity("hello", "") == 0.0
        assert AddressUtils._calculate_similarity("", "hello") == 0.0

    def test_identical(self):
        sim = AddressUtils._calculate_similarity("123 Main St", "123 Main St")
        assert sim >= 90.0

    def test_different(self):
        sim = AddressUtils._calculate_similarity("123 Main St", "456 Oak Ave")
        assert sim < 50.0

    def test_with_fuzz(self):
        with patch("src.utils.address_utils.fuzz") as mock_fuzz:
            mock_fuzz.token_sort_ratio.return_value = 85.0
            sim = AddressUtils._calculate_similarity("test", "test2")
            assert sim == 85.0

    def test_fuzz_exception_fallback(self):
        with patch("src.utils.address_utils.fuzz") as mock_fuzz:
            mock_fuzz.token_sort_ratio.side_effect = Exception("fuzz error")
            sim = AddressUtils._calculate_similarity("hello", "hello")
            assert sim > 0


# ============================================================================
# AddressUtils.check_should_skip
# ============================================================================


class TestCheckShouldSkip:
    """Tests for AddressUtils.check_should_skip."""

    def test_empty_skip_list(self):
        result = AddressUtils.check_should_skip({"address": "123 Main"}, [])
        assert result == (False, "")

    def test_exact_match_skips(self):
        skip_list = [
            {
                "Skip_Address": "123 MAIN",
                "Skip_City": "CITY",
                "Skip_State": "IL",
                "Skip_Zip": "62701",
                "Reason": "Test skip",
            }
        ]
        result = AddressUtils.check_should_skip(
            {"address": "123 Main", "city": "City", "state": "IL", "zip": "62701"},
            skip_list,
        )
        assert result[0] is True
        assert result[1] == "Test skip"

    def test_no_match(self):
        skip_list = [
            {
                "Skip_Address": "999 OTHER",
                "Skip_City": "TOWN",
                "Skip_State": "CA",
                "Skip_Zip": "90210",
            }
        ]
        result = AddressUtils.check_should_skip(
            {"address": "123 Main", "city": "City", "state": "IL", "zip": "62701"},
            skip_list,
        )
        assert result[0] is False


# ============================================================================
# AddressUtils.compare_with_threshold
# ============================================================================


class TestCompareWithThreshold:
    """Tests for AddressUtils.compare_with_threshold."""

    def test_unparseable_mist(self):
        result = AddressUtils.compare_with_threshold(
            {"address": "unknown", "city": "", "state": "", "zip": ""},
            {"address": "123 Main", "city": "City", "state": "IL", "zip": "62701"},
            threshold=70.0,
        )
        assert result["is_match"] is False
        assert result["overall_similarity"] == 0.0

    def test_identical_addresses(self):
        addr = {"address": "123 Main St", "city": "Springfield", "state": "IL", "zip": "62701"}
        result = AddressUtils.compare_with_threshold(addr, addr, threshold=70.0)
        assert result["is_match"] is True
        assert result["overall_similarity"] >= 70.0

    def test_debug_mode(self):
        addr = {"address": "123 Main St", "city": "Springfield", "state": "IL", "zip": "62701"}
        result = AddressUtils.compare_with_threshold(addr, addr, threshold=70.0, debug=True)
        assert result["is_match"] is True


# ============================================================================
# AddressUtils.apply_business_context_rules
# ============================================================================


class TestApplyBusinessContextRules:
    """Tests for AddressUtils.apply_business_context_rules."""

    def test_mist_commercial_comp_residential(self):
        mist = {"place_type": "commercial", "confidence": 0.5}
        comp = {"place_type": "residential", "confidence": 0.5}
        result = AddressUtils.apply_business_context_rules(mist, comp)
        assert result == "mist"

    def test_comp_commercial_mist_residential(self):
        mist = {"place_type": "house", "confidence": 0.5}
        comp = {"place_type": "office", "confidence": 0.5}
        result = AddressUtils.apply_business_context_rules(mist, comp)
        assert result == "comparison"

    def test_confidence_tiebreak(self):
        mist = {"place_type": "other", "confidence": 0.9}
        comp = {"place_type": "other", "confidence": 0.5}
        result = AddressUtils.apply_business_context_rules(mist, comp)
        assert result == "mist"

    def test_uncertain(self):
        mist = {"place_type": "other", "confidence": 0.5}
        comp = {"place_type": "other", "confidence": 0.5}
        result = AddressUtils.apply_business_context_rules(mist, comp)
        assert result == "uncertain"


# ============================================================================
# Private helper: _parse_address_parts
# ============================================================================


class TestParseAddressParts:
    """Tests for _parse_address_parts private helper."""

    def test_us_full_address(self):
        result: dict = {"is_parseable": False, "parse_reason": "unparsed", "original": ""}
        parsed = _parse_address_parts("123 Main St, Springfield, IL, 62701, US", result, False)
        assert parsed["is_parseable"] is True
        assert parsed["country"] == "US"
        assert parsed["zip"] == "62701"

    def test_no_country(self):
        result: dict = {"is_parseable": False, "parse_reason": "unparsed", "original": ""}
        parsed = _parse_address_parts("123 Main St, City, ST", result, False)
        assert parsed["is_parseable"] is True

    def test_debug_logging(self):
        result: dict = {"is_parseable": False, "parse_reason": "unparsed", "original": ""}
        parsed = _parse_address_parts("123 Main St, City", result, True)
        assert parsed["is_parseable"] is True


# ============================================================================
# Private helper: _detect_country
# ============================================================================


class TestDetectCountry:
    """Tests for _detect_country."""

    def test_empty_parts(self):
        assert _detect_country([]) is None

    def test_usa(self):
        assert _detect_country(["123 Main", "City", "USA"]) == "US"

    def test_united_states(self):
        assert _detect_country(["City", "United States"]) == "US"

    def test_us(self):
        assert _detect_country(["City", "US"]) == "US"

    def test_puerto_rico(self):
        assert _detect_country(["City", "Puerto Rico"]) == "US"

    def test_two_letter_code(self):
        assert _detect_country(["City", "DE"]) == "DE"

    def test_not_country(self):
        assert _detect_country(["Springfield"]) is None

    def test_numeric_not_country(self):
        assert _detect_country(["12345"]) is None


# ============================================================================
# Private helper: _detect_zip
# ============================================================================


class TestDetectZip:
    """Tests for _detect_zip."""

    def test_empty(self):
        assert _detect_zip([], None) == (None, None)

    def test_five_digit(self):
        z, c = _detect_zip(["62701"], None)
        assert z == "62701"
        assert c == "US"

    def test_nine_digit(self):
        z, c = _detect_zip(["62701-1234"], None)
        assert z == "62701-1234"
        assert c == "US"

    def test_existing_country_preserved(self):
        z, c = _detect_zip(["62701"], "CA")
        assert z == "62701"
        assert c == "CA"

    def test_not_zip(self):
        z, c = _detect_zip(["Springfield"], None)
        assert z is None
        assert c is None


# ============================================================================
# Private helper: _detect_state
# ============================================================================


class TestDetectState:
    """Tests for _detect_state."""

    def test_empty(self):
        assert _detect_state([]) is None

    def test_two_letter_abbrev(self):
        assert _detect_state(["IL"]) == "IL"

    def test_puerto_rico(self):
        assert _detect_state(["Puerto Rico"]) == "PR"

    def test_full_name_with_multiple_parts(self):
        assert _detect_state(["123 Main", "California"]) == "CA"

    def test_single_long_part_returns_none(self):
        # Single part that's a full state name but only 1 part - _detect_state
        # only normalizes full names when len(parts) > 1
        assert _detect_state(["California"]) is None


# ============================================================================
# Private helper: _check_single_skip
# ============================================================================


class TestCheckSingleSkip:
    """Tests for _check_single_skip."""

    def test_exact_match(self):
        skip = {
            "Skip_Address": "123 MAIN",
            "Skip_City": "CITY",
            "Skip_State": "IL",
            "Skip_Zip": "62701",
            "Reason": "exact",
        }
        result = _check_single_skip("123 MAIN", "CITY", "IL", "62701", skip, False)
        assert result == (True, "exact")

    def test_no_match(self):
        skip = {
            "Skip_Address": "999 OTHER",
            "Skip_City": "TOWN",
            "Skip_State": "CA",
            "Skip_Zip": "90210",
        }
        result = _check_single_skip("123 MAIN", "CITY", "IL", "62701", skip, False)
        assert result == (False, "")


# ============================================================================
# Private helper: _check_partial_skip
# ============================================================================


class TestCheckPartialSkip:
    """Tests for _check_partial_skip."""

    def test_no_matches(self):
        result = _check_partial_skip("A", "B", "C", "D", "X", "Y", "Z", "W", "reason", False)
        assert result == (False, "")

    def test_wildcard_match(self):
        # Only zip populated and matches
        result = _check_partial_skip("A", "B", "C", "62701", "", "", "", "62701", "wildcard", False)
        assert result == (True, "wildcard")

    def test_specific_match(self):
        # Two of four fields match
        result = _check_partial_skip("A", "B", "IL", "62701", "A", "", "IL", "62701", "specific", False)
        assert result == (True, "specific")


# ============================================================================
# Private helper: _check_parse_status
# ============================================================================


class TestCheckParseStatus:
    """Tests for _check_parse_status."""

    def test_both_valid(self):
        mist = {"address": "123 Main", "city": "City", "state": "IL", "zip": "62701"}
        comp = {"address": "456 Oak", "city": "Town", "state": "CA", "zip": "90210"}
        status = _check_parse_status(mist, comp, {"address": 0.4, "city": 0.3, "state": 0.2, "zip": 0.1})
        assert status["mist_parseable"] is True
        assert status["comparison_parseable"] is True

    def test_mist_unparseable(self):
        mist = {"address": "unknown", "city": "", "state": "", "zip": ""}
        comp = {"address": "456 Oak", "city": "Town", "state": "CA", "zip": "90210"}
        status = _check_parse_status(mist, comp, {"address": 0.4, "city": 0.3, "state": 0.2, "zip": 0.1})
        assert status["mist_parseable"] is False


# ============================================================================
# Private helper: _compare_single_field / _compare_fields
# ============================================================================


class TestCompareFields:
    """Tests for _compare_single_field and _compare_fields."""

    def test_zip_match(self):
        assert _compare_single_field("zip", "62701", "62701") == 100.0

    def test_zip_no_match(self):
        assert _compare_single_field("zip", "62701", "90210") == 0.0

    def test_state_match(self):
        assert _compare_single_field("state", "Illinois", "IL") == 100.0

    def test_state_no_match(self):
        assert _compare_single_field("state", "IL", "CA") == 0.0

    def test_address_similarity(self):
        sim = _compare_single_field("address", "123 Main St", "123 Main St")
        assert sim >= 90.0

    def test_compare_fields_all(self):
        mist = {"address": "123 Main St", "city": "Springfield", "state": "IL", "zip": "62701"}
        comp = {"address": "123 Main St", "city": "Springfield", "state": "IL", "zip": "62701"}
        weights = {"address": 0.4, "city": 0.3, "state": 0.2, "zip": 0.1}
        sims, failed = _compare_fields(mist, comp, weights, 70.0, False)
        assert all(s >= 70.0 for s in sims.values())
        assert len(failed) == 0


# ============================================================================
# NameNormalizationUtils
# ============================================================================


class TestNameNormalizationUtils:
    """Tests for NameNormalizationUtils."""

    def test_normalize_business_name_empty(self):
        assert NameNormalizationUtils.normalize_business_name("") == ""

    def test_normalize_business_name_strips_suffix(self):
        result = NameNormalizationUtils.normalize_business_name("Acme Corp")
        assert "corp" not in result

    def test_normalize_business_name_strips_inc(self):
        result = NameNormalizationUtils.normalize_business_name("Acme Inc.")
        assert "inc" not in result

    def test_normalize_business_name_strips_llc(self):
        result = NameNormalizationUtils.normalize_business_name("Widgets LLC")
        assert "llc" not in result

    def test_normalize_generic_empty(self):
        assert NameNormalizationUtils.normalize_generic("") == ""

    def test_normalize_generic(self):
        result = NameNormalizationUtils.normalize_generic("  Hello  WORLD  ")
        assert result == "hello world"

    def test_extract_tokens_empty(self):
        assert NameNormalizationUtils.extract_tokens("") == []

    def test_extract_tokens(self):
        tokens = NameNormalizationUtils.extract_tokens("Acme Corp!")
        assert "acme" in tokens
        assert "corp" in tokens

    def test_calculate_org_name_similarity_empty(self):
        assert NameNormalizationUtils.calculate_org_name_similarity("", "test") == 0.0
        assert NameNormalizationUtils.calculate_org_name_similarity("test", "") == 0.0

    def test_calculate_org_name_similarity_match(self):
        sim = NameNormalizationUtils.calculate_org_name_similarity("acme", "Acme Corporation, Springfield IL")
        assert sim > 0.0

    def test_backward_compat_alias(self):
        assert AddressBusinessNameUtils is NameNormalizationUtils


# ============================================================================
# NominatimValidator
# ============================================================================


class TestNominatimValidatorInit:
    """Tests for NominatimValidator initialization."""

    def test_default_init(self):
        validator = NominatimValidator()
        assert validator.timeout == 5
        assert validator.debug is False
        assert validator.skip_ssl_verify is False

    def test_config_init(self):
        config = AddressValidationConfig(
            timeout=10,
            debug=True,
            skip_ssl_verify=True,
            org_name="Acme",
            site_name="HQ",
        )
        validator = NominatimValidator(config)
        assert validator.timeout == 10
        assert validator.debug is True
        assert validator.org_name == "Acme"

    def test_ssl_warnings_suppressed(self):
        config = AddressValidationConfig(skip_ssl_verify=True)
        with patch("src.utils.address_utils._has_urllib3", True):
            with patch("src.utils.address_utils.urllib3") as mock_u3:
                mock_u3.exceptions.InsecureRequestWarning = Exception
                NominatimValidator(config)
                mock_u3.disable_warnings.assert_called_once()


class TestNominatimValidatorHelpers:
    """Tests for NominatimValidator helper methods."""

    def setup_method(self):
        self.validator = NominatimValidator()

    def test_build_address_string_empty(self):
        result, parts = self.validator._build_address_string({})
        assert result is None
        assert parts == []

    def test_build_address_string(self):
        result, parts = self.validator._build_address_string(
            {"address": "123 Main", "city": "Springfield", "state": "IL", "zip": "62701"}
        )
        assert "123 Main" in result
        assert len(parts) == 4

    def test_create_empty_result(self):
        result = self.validator._create_empty_result("test error")
        assert result["valid"] is False
        assert result["confidence"] == 0.0
        assert result["error"] == "test error"

    def test_create_address_key(self):
        key = self.validator._create_address_key(
            {"address": "123 Main", "city": "Springfield", "state": "IL", "zip": "62701"}
        )
        assert "123 main" in key
        assert "springfield" in key

    def test_calculate_component_match_empty(self):
        score = self.validator._calculate_component_match([], "Some Display", "test")
        assert score == 0.0

    def test_calculate_component_match_full(self):
        parts = ["123 Main St", "Springfield", "Illinois"]
        display = "123 Main St, Springfield, Illinois, USA"
        score = self.validator._calculate_component_match(parts, display, "test")
        assert score > 0.0

    def test_calculate_component_match_partial(self):
        parts = ["123 Main St", "Springfield"]
        display = "Main St, Different City, IL"
        score = self.validator._calculate_component_match(parts, display, "test")
        assert 0.0 < score < 1.0

    def test_calculate_quality_boost_high(self):
        boost = self.validator._calculate_quality_boost(
            {"type": "building", "class": "building", "address": {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5}},
            "test",
        )
        assert boost >= 0.5  # 0.3 type + 0.2 details

    def test_calculate_quality_boost_medium(self):
        boost = self.validator._calculate_quality_boost(
            {"type": "residential", "class": "other", "address": {"a": 1}},
            "test",
        )
        assert boost == 0.2

    def test_calculate_quality_boost_class(self):
        boost = self.validator._calculate_quality_boost(
            {"type": "other", "class": "place", "address": {}},
            "test",
        )
        assert boost == 0.1

    def test_calculate_quality_boost_none(self):
        boost = self.validator._calculate_quality_boost(
            {"type": "other", "class": "other"},
            "test",
        )
        assert boost == 0.0

    def test_calculate_confidence_with_importance(self):
        result = {"importance": 0.6}
        conf = self.validator._calculate_confidence(result, [], "test")
        assert conf > 0.0

    def test_calculate_confidence_no_importance(self):
        result = {"importance": 0.0, "display_name": "123 Main St", "type": "house", "class": "building", "address": {}}
        conf = self.validator._calculate_confidence(result, ["123 Main St"], "test")
        assert conf > 0.0


class TestNominatimValidatorAPI:
    """Tests for NominatimValidator API methods."""

    def setup_method(self):
        self.validator = NominatimValidator()

    def test_make_api_request_no_requests(self):
        with patch("src.utils.address_utils.requests", None):
            result = self.validator._make_api_request("123 Main", "test")
            assert result is None

    def test_make_api_request_success(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        with patch("src.utils.address_utils.requests") as mock_req:
            mock_req.get.return_value = mock_resp
            result = self.validator._make_api_request("123 Main", "test")
            assert result is not None

    def test_make_api_request_retry_then_success(self):
        mock_resp = MagicMock()
        with patch("src.utils.address_utils.requests") as mock_req:
            mock_req.get.side_effect = [Exception("timeout"), mock_resp]
            with patch("time.sleep"):
                result = self.validator._make_api_request("123 Main", "test")
                assert result is mock_resp

    def test_make_api_request_all_retries_fail(self):
        with patch("src.utils.address_utils.requests") as mock_req:
            mock_req.get.side_effect = Exception("timeout")
            with patch("time.sleep"):
                result = self.validator._make_api_request("123 Main", "test")
                assert result is None

    def test_parse_geocode_response_not_200(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        result = self.validator._parse_geocode_response(mock_resp, [], "test")
        assert result["valid"] is False
        assert "404" in result["error"]

    def test_parse_geocode_response_empty(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = []
        result = self.validator._parse_geocode_response(mock_resp, [], "test")
        assert result["valid"] is False

    def test_parse_geocode_response_success(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [
            {
                "lat": "39.78",
                "lon": "-89.65",
                "importance": 0.6,
                "display_name": "Springfield, IL, USA",
                "type": "city",
                "class": "place",
                "address": {},
            }
        ]
        result = self.validator._parse_geocode_response(mock_resp, ["Springfield"], "test")
        assert result["valid"] is True
        assert result["lat"] == 39.78

    def test_geocode_address_empty(self):
        result = self.validator._geocode_address({}, "test")
        assert result["valid"] is False
        assert "Empty" in result["error"]

    def test_geocode_address_no_response(self):
        with patch.object(self.validator, "_make_api_request", return_value=None):
            result = self.validator._geocode_address(
                {"address": "123 Main", "city": "City"},
                "test",
            )
            assert result["valid"] is False

    def test_geocode_address_exception(self):
        with patch.object(self.validator, "_build_address_string", side_effect=Exception("boom")):
            result = self.validator._geocode_address({"address": "123"}, "test")
            assert result["valid"] is False

    def test_geocode_address_exception_debug(self):
        self.validator.debug = True
        with patch.object(self.validator, "_build_address_string", side_effect=Exception("boom")):
            result = self.validator._geocode_address({"address": "123"}, "test")
            assert result["valid"] is False


class TestNominatimValidatorRecommendation:
    """Tests for NominatimValidator recommendation logic."""

    def setup_method(self):
        self.validator = NominatimValidator()

    def test_only_mist_valid(self):
        mist_r = {"valid": True, "confidence": 0.8}
        comp_r = {"valid": False, "confidence": 0.0}
        rec, reason = self.validator._determine_recommendation(mist_r, comp_r, {}, {})
        assert rec == "mist"

    def test_only_comp_valid(self):
        mist_r = {"valid": False, "confidence": 0.0}
        comp_r = {"valid": True, "confidence": 0.7}
        rec, reason = self.validator._determine_recommendation(mist_r, comp_r, {}, {})
        assert rec == "comparison"

    def test_both_invalid(self):
        mist_r = {"valid": False, "confidence": 0.0}
        comp_r = {"valid": False, "confidence": 0.0}
        rec, reason = self.validator._determine_recommendation(mist_r, comp_r, {}, {})
        assert rec == "uncertain"

    def test_both_valid_mist_higher_confidence(self):
        mist_r = {"valid": True, "confidence": 0.9, "display_name": "", "place_type": ""}
        comp_r = {"valid": True, "confidence": 0.5, "display_name": "", "place_type": ""}
        rec, reason = self.validator._determine_recommendation(
            mist_r,
            comp_r,
            {"address": "a", "city": "b", "state": "c", "zip": "d"},
            {"address": "e", "city": "f", "state": "g", "zip": "h"},
        )
        assert rec == "mist"

    def test_duplicate_mist_prefers_comparison(self):
        config = AddressValidationConfig(
            site_name="HQ",
            mist_duplicates={"a|b|c|D": True},
        )
        validator = NominatimValidator(config)
        mist_r = {"valid": True, "confidence": 0.8, "display_name": "", "place_type": ""}
        comp_r = {"valid": True, "confidence": 0.8, "display_name": "", "place_type": ""}
        mist_addr = {"address": "A", "city": "B", "state": "C", "zip": "D"}
        comp_addr = {"address": "E", "city": "F", "state": "G", "zip": "H"}
        rec, reason = validator._determine_recommendation(mist_r, comp_r, mist_addr, comp_addr)
        assert rec == "comparison"

    def test_duplicate_ref_prefers_mist(self):
        config = AddressValidationConfig(
            site_name="HQ",
            ref_duplicates={"e|f|g|H": True},
        )
        validator = NominatimValidator(config)
        mist_r = {"valid": True, "confidence": 0.8, "display_name": "", "place_type": ""}
        comp_r = {"valid": True, "confidence": 0.8, "display_name": "", "place_type": ""}
        mist_addr = {"address": "A", "city": "B", "state": "C", "zip": "D"}
        comp_addr = {"address": "E", "city": "F", "state": "G", "zip": "H"}
        rec, reason = validator._determine_recommendation(mist_r, comp_r, mist_addr, comp_addr)
        assert rec == "mist"

    def test_both_duplicates_uncertain(self):
        config = AddressValidationConfig(
            site_name="HQ",
            mist_duplicates={"a|b|c|D": True},
            ref_duplicates={"e|f|g|H": True},
        )
        validator = NominatimValidator(config)
        mist_r = {"valid": True, "confidence": 0.8, "display_name": "", "place_type": ""}
        comp_r = {"valid": True, "confidence": 0.8, "display_name": "", "place_type": ""}
        mist_addr = {"address": "A", "city": "B", "state": "C", "zip": "D"}
        comp_addr = {"address": "E", "city": "F", "state": "G", "zip": "H"}
        rec, reason = validator._determine_recommendation(mist_r, comp_r, mist_addr, comp_addr)
        assert rec == "uncertain"


class TestNominatimValidatorOrgNameTiebreaker:
    """Tests for org name tiebreaker logic."""

    def test_org_name_mist_wins(self):
        config = AddressValidationConfig(org_name="Acme Corp")
        validator = NominatimValidator(config)
        mist_r = {"valid": True, "confidence": 0.5, "display_name": "Acme Corp, Springfield", "place_type": ""}
        comp_r = {"valid": True, "confidence": 0.5, "display_name": "Random Place, Town", "place_type": ""}
        rec, reason = validator._apply_org_name_tiebreaker(mist_r, comp_r)
        assert rec == "mist"

    def test_no_org_name(self):
        validator = NominatimValidator()
        rec, reason = validator._apply_org_name_tiebreaker({}, {})
        assert rec is None


class TestNominatimValidatorValidate:
    """Tests for NominatimValidator.validate end-to-end."""

    def test_validate_mocks_geocode(self):
        validator = NominatimValidator()
        mist_result = {"valid": True, "confidence": 0.9, "display_name": "", "place_type": ""}
        comp_result = {"valid": True, "confidence": 0.4, "display_name": "", "place_type": ""}
        with patch.object(validator, "_geocode_address", side_effect=[mist_result, comp_result]):
            with patch("time.sleep"):
                result = validator.validate(
                    {"address": "123 Main", "city": "City", "state": "IL", "zip": "62701"},
                    {"address": "456 Oak", "city": "Town", "state": "CA", "zip": "90210"},
                )
                assert result["recommendation"] == "mist"
                assert result["mist_validation"]["confidence"] == 0.9

    def test_validate_both_fail(self):
        validator = NominatimValidator()
        fail_result = {"valid": False, "confidence": 0.0, "error": "fail"}
        with patch.object(validator, "_geocode_address", return_value=fail_result):
            with patch("time.sleep"):
                result = validator.validate({}, {})
                assert result["recommendation"] == "uncertain"


class TestNominatimValidatorBusinessContext:
    """Tests for business context tiebreaker."""

    def test_mist_business_type(self):
        validator = NominatimValidator()
        mist_r = {"confidence": 0.5, "place_type": "commercial"}
        comp_r = {"confidence": 0.5, "place_type": "house"}
        rec, reason = validator._apply_business_context_tiebreaker(mist_r, comp_r)
        assert rec == "mist"

    def test_comp_business_type(self):
        validator = NominatimValidator()
        mist_r = {"confidence": 0.5, "place_type": "house"}
        comp_r = {"confidence": 0.5, "place_type": "office"}
        rec, reason = validator._apply_business_context_tiebreaker(mist_r, comp_r)
        assert rec == "comparison"

    def test_uncertain_tiebreaker(self):
        validator = NominatimValidator()
        mist_r = {"confidence": 0.5, "place_type": "other"}
        comp_r = {"confidence": 0.5, "place_type": "other"}
        rec, reason = validator._apply_business_context_tiebreaker(mist_r, comp_r)
        assert rec == "uncertain"


class TestNominatimDuplicateStatus:
    """Tests for duplicate detection helpers."""

    def test_no_duplicates(self):
        validator = NominatimValidator()
        mist_dup, ref_dup = validator._check_duplicate_status(
            {"address": "a", "city": "b", "state": "c", "zip": "d"},
            {"address": "e", "city": "f", "state": "g", "zip": "h"},
        )
        assert mist_dup is False
        assert ref_dup is False

    def test_apply_duplicate_rules_both(self):
        validator = NominatimValidator()
        rec, reason = validator._apply_duplicate_rules(True, True)
        assert rec == "uncertain"

    def test_apply_duplicate_rules_mist_only(self):
        validator = NominatimValidator()
        rec, reason = validator._apply_duplicate_rules(True, False)
        assert rec == "comparison"

    def test_apply_duplicate_rules_ref_only(self):
        validator = NominatimValidator()
        rec, reason = validator._apply_duplicate_rules(False, True)
        assert rec == "mist"

    def test_apply_duplicate_rules_neither(self):
        validator = NominatimValidator()
        rec, reason = validator._apply_duplicate_rules(False, False)
        assert rec is None


class TestNominatimConfidenceComparison:
    """Tests for confidence comparison."""

    def test_mist_higher(self):
        validator = NominatimValidator()
        rec, reason = validator._apply_confidence_comparison(0.9, 0.5)
        assert rec == "mist"

    def test_comp_higher(self):
        validator = NominatimValidator()
        rec, reason = validator._apply_confidence_comparison(0.5, 0.9)
        assert rec == "comparison"

    def test_similar(self):
        validator = NominatimValidator()
        rec, reason = validator._apply_confidence_comparison(0.5, 0.5)
        assert rec is None


class TestNominatimLogEntry:
    """Tests for _log_entry method."""

    def test_log_entry_debug(self):
        config = AddressValidationConfig(debug=True)
        validator = NominatimValidator(config)
        # Should not raise
        validator._log_entry({"address": "a"}, {"address": "b"})

    def test_log_entry_no_debug(self):
        validator = NominatimValidator()
        # Should not raise
        validator._log_entry({}, {})


class TestNominatimDetermineRecommendationBothValid:
    """Tests for _determine_both_valid method."""

    def test_all_tiebreakers_uncertain(self):
        config = AddressValidationConfig(org_name="")
        validator = NominatimValidator(config)
        mist_r = {"valid": True, "confidence": 0.5, "display_name": "", "place_type": "other"}
        comp_r = {"valid": True, "confidence": 0.5, "display_name": "", "place_type": "other"}
        mist_addr = {"address": "a", "city": "b", "state": "c", "zip": "d"}
        comp_addr = {"address": "e", "city": "f", "state": "g", "zip": "h"}
        rec, reason = validator._determine_both_valid(mist_r, comp_r, mist_addr, comp_addr)
        assert rec == "uncertain"
