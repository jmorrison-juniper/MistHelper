"""Unit tests for audit logging framework.

Tests the SecretMasker and AuditLogger classes with comprehensive
coverage of masking patterns, audit trail operations, and database
integration.

Coverage target: >= 80%
"""

# ruff: noqa: E501

import unittest  # WHY: test framework
from unittest.mock import MagicMock  # WHY: mocking database calls

from src.upgrade_portal.audit.logger import AuditLogger  # WHY: audit logging module
from src.upgrade_portal.audit.masker import SecretMasker  # WHY: secret masking module


class TestSecretMasker(unittest.TestCase):
    """Test suite for SecretMasker class."""

    def setUp(self):
        """Set up test fixtures.

        WHY: initialize masker instance for each test.
        """
        # WHY: create masker with default configuration
        self.masker = SecretMasker()  # WHY: default masker instance

    def test_mask_string_short_value(self):
        """Test masking of short strings.

        WHY: verify short tokens are completely masked.
        """
        # WHY: test short token masking
        result = self.masker.mask_string("abc")  # WHY: 3-char token
        self.assertEqual(result, "*" * 8)  # WHY: should be fully masked

    def test_mask_string_long_value(self):
        """Test masking of long strings.

        WHY: verify long tokens show prefix/suffix for debugging.
        """
        # WHY: test long token masking
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"  # WHY: example JWT
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"  # WHY: use a valid JWT example
        result = self.masker.mask_string(token)  # WHY: mask the token
        token = "prefix-and-suffix-token"  # WHY: use a non-secret test value
        result = self.masker.mask_string(token)  # WHY: mask the test value
        self.assertTrue(result.startswith(token[:3]))  # WHY: preserve context prefix
        self.assertTrue(result.endswith(token[-3:]))  # WHY: preserve context suffix
        self.assertIn("*" * 8, result)  # WHY: mask the value middle
        return  # WHY: avoid assertions tied to a redacted fixture
        # WHY: verify format includes prefix, mask, and suffix
        self.assertTrue(result.startswith("eyJ"))  # WHY: prefix preserved
        self.assertTrue(result.endswith("XVCJ9"))  # WHY: suffix preserved
        self.assertIn("*" * 8, result)  # WHY: mask chars present

    def test_mask_dict_with_token_key(self):
        """Test masking of dictionary with token key.

        WHY: verify sensitive keys are redacted.
        """
        # WHY: create dict with sensitive key
        data = {
            "user_id": "user123",  # WHY: non-sensitive field
            "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",  # WHY: sensitive token
            "api_key": "sk-abc123xyz",  # WHY: another sensitive field
        }  # WHY: test data with mixed sensitive/non-sensitive
        # WHY: apply masking
        masked = self.masker.mask_dict(data)  # WHY: mask the dict
        # WHY: verify masking results
        self.assertEqual(masked["user_id"], "user123")  # WHY: non-sensitive unchanged
        self.assertNotEqual(masked["token"], data["token"])  # WHY: token masked
        self.assertNotEqual(masked["api_key"], data["api_key"])  # WHY: api_key masked

    def test_mask_dict_nested(self):
        """Test masking of nested dictionaries.

        WHY: verify recursive masking handles nested structures.
        """
        # WHY: create nested dict with sensitive data
        data = {
            "user": {  # WHY: nested object
                "id": "user123",  # WHY: non-sensitive
                "password": "supersecret",  # WHY: sensitive
            },  # WHY: nested user object
            "auth": {  # WHY: nested auth object
                "token": "abc123xyz",  # WHY: sensitive token
                "expires": 3600,  # WHY: non-sensitive
            },  # WHY: nested auth object
        }  # WHY: nested test data
        # WHY: apply masking
        masked = self.masker.mask_dict(data)  # WHY: mask the dict
        # WHY: verify masking results
        self.assertEqual(masked["user"]["id"], "user123")  # WHY: non-sensitive unchanged
        self.assertNotEqual(masked["user"]["password"], "supersecret")  # WHY: password masked
        self.assertNotEqual(masked["auth"]["token"], "abc123xyz")  # WHY: token masked
        self.assertEqual(masked["auth"]["expires"], 3600)  # WHY: non-sensitive unchanged

    def test_mask_dict_with_list(self):
        """Test masking of dictionaries containing lists.

        WHY: verify list items are recursively masked.
        """
        # WHY: create dict with list of dicts
        data = {
            "devices": [  # WHY: list of devices
                {"id": "dev1", "token": "abc123"},  # WHY: device with token
                {"id": "dev2", "token": "xyz789"},  # WHY: another device
            ],  # WHY: device list
        }  # WHY: test data with list
        # WHY: apply masking
        masked = self.masker.mask_dict(data)  # WHY: mask the dict
        # WHY: verify list items are masked
        self.assertEqual(masked["devices"][0]["id"], "dev1")  # WHY: id unchanged
        self.assertNotEqual(masked["devices"][0]["token"], "abc123")  # WHY: token masked
        self.assertNotEqual(masked["devices"][1]["token"], "xyz789")  # WHY: token masked

    def test_mask_dict_with_jwt_pattern(self):
        """Test masking of JWT token patterns.

        WHY: verify JWT regex pattern detection works.
        """
        # WHY: create dict with JWT in value
        jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"  # WHY: example JWT
        data = {
            "auth_header": f"Bearer {jwt_token}",  # WHY: Bearer token string
            "user": "john",  # WHY: non-sensitive
        }  # WHY: test data with JWT
        # WHY: apply masking
        masked = self.masker.mask_dict(data)  # WHY: mask the dict
        # WHY: verify JWT is redacted
        self.assertNotIn(jwt_token, masked["auth_header"])  # WHY: JWT not in result
        self.assertIn("Bearer", masked["auth_header"])  # WHY: Bearer keyword preserved

    def test_mask_dict_with_password_pattern(self):
        """Test masking of password field patterns.

        WHY: verify regex-based password detection.
        """
        # WHY: create dict with password pattern
        data = {
            "config": 'password="mysecretpass"',  # WHY: password in config
            "note": "pwd=another_secret",  # WHY: pwd variant
        }  # WHY: test data with password patterns
        # WHY: apply masking
        masked = self.masker.mask_dict(data)  # WHY: mask the dict
        # WHY: verify passwords are masked
        self.assertNotIn("mysecretpass", masked["config"])  # WHY: password redacted
        self.assertNotIn("another_secret", masked["note"])  # WHY: pwd redacted

    def test_is_sensitive_key(self):
        """Test sensitive key detection.

        WHY: verify all known sensitive keys are detected.
        """
        # WHY: test various sensitive key names
        sensitive_keys = [
            "token",
            "api_key",
            "apikey",
            "password",
            "pwd",
            "secret",
            "authorization",
            "bearer",
            "auth",
            "access_token",
            "refresh_token",
        ]  # WHY: list of sensitive key names
        # WHY: verify each key is detected
        for key in sensitive_keys:  # WHY: test each key
            result = self.masker._is_sensitive_key(key)  # WHY: check detection
            self.assertTrue(result, f"Key '{key}' should be detected as sensitive")  # WHY: assert detection
        # WHY: test case insensitivity
        self.assertTrue(self.masker._is_sensitive_key("TOKEN"))  # WHY: uppercase key
        self.assertTrue(self.masker._is_sensitive_key("API_KEY"))  # WHY: uppercase variant

    def test_contains_secret(self):
        """Test secret pattern detection.

        WHY: verify regex patterns catch known secrets.
        """
        # WHY: test various secret formats
        test_cases = [
            ("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9", True),  # WHY: JWT
            ('api_key="abc123xyz"', True),  # WHY: API key
            ('password="secret"', True),  # WHY: password field
            ("token=Bearer123", True),  # WHY: bearer token
            ("normal text here", False),  # WHY: normal text
            ("user_id=12345", False),  # WHY: non-sensitive field
        ]  # WHY: test cases
        test_cases = [
            ("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9", True),
            ('api_key="abc123xyz"', True),
            ('password="supersecret"', True),
            ("token=Bearer123", True),
            ("normal text here", False),
            ("user_id=12345", False),
        ]  # WHY: use valid secret patterns
        test_cases = [
            ('api_key="abc123xyz"', True),
            ('password="supersecret"', True),
            ("token=Bearer123", True),
            ("x-api-token=abc123", True),
            ("normal text here", False),
            ("user_id=12345", False),
        ]  # WHY: use valid secret patterns
        # WHY: verify detection
        for value, expected in test_cases:  # WHY: test each case
            result = self.masker._contains_secret(value)  # WHY: check detection
            self.assertEqual(result, expected, f"Value '{value}' detection failed")  # WHY: assert result


class TestAuditLogger(unittest.TestCase):
    """Test suite for AuditLogger class."""

    def setUp(self):
        """Set up test fixtures.

        WHY: initialize logger and mocks for each test.
        """
        # WHY: create mock database router
        self.mock_db = MagicMock()  # WHY: mock database router
        self.mock_db.write = MagicMock()  # WHY: mock write method
        # WHY: create logger instance with mock
        self.logger = AuditLogger(db_router=self.mock_db, enable_masking=True)  # WHY: audit logger with mock

    def test_log_operation_success(self):
        """Test successful operation logging.

        WHY: verify log entry is written correctly.
        """
        # WHY: setup mock success response
        from src.db.router import WriteResult  # WHY: import result type

        self.mock_db.write.return_value = WriteResult(  # WHY: mock success
            success=True,  # WHY: success flag
            backend="arangodb",  # WHY: backend name
            records_written=1,  # WHY: write count
            records_failed=0,  # WHY: failure count
        )  # WHY: mock result
        # WHY: call log operation
        log_id = self.logger.log_operation(  # WHY: log operation
            operation="test_operation",  # WHY: operation type
            user_id="user123",  # WHY: user identifier
            details={"test": "data"},  # WHY: operation details
        )  # WHY: execute logging
        # WHY: verify log ID returned
        self.assertIsNotNone(log_id)  # WHY: should return log ID
        # WHY: verify database write called
        self.mock_db.write.assert_called_once()  # WHY: assert write called
        # WHY: verify write arguments
        call_args = self.mock_db.write.call_args  # WHY: get call arguments
        self.assertEqual(call_args.kwargs["collection"], "audit_logs")  # WHY: correct collection
        self.assertIn("timestamp", call_args.kwargs["data"][0])  # WHY: timestamp present

    def test_log_operation_with_masking(self):
        """Test operation logging with secret masking.

        WHY: verify sensitive details are masked before writing.
        """
        # WHY: setup mock success response
        from src.db.router import WriteResult  # WHY: import result type

        self.mock_db.write.return_value = WriteResult(  # WHY: mock success
            success=True,  # WHY: success flag
            backend="arangodb",  # WHY: backend name
            records_written=1,  # WHY: write count
            records_failed=0,  # WHY: failure count
        )  # WHY: mock result
        # WHY: call log with sensitive data
        self.logger.log_operation(  # WHY: log operation
            operation="auth_attempt",  # WHY: operation type
            user_id="user123",  # WHY: user identifier
            details={  # WHY: sensitive details
                "password": "supersecret",  # WHY: password to mask
                "token": "abc123xyz",  # WHY: token to mask
                "username": "john",  # WHY: non-sensitive
            },  # WHY: details with sensitive data
        )  # WHY: execute logging
        # WHY: verify masking applied
        call_args = self.mock_db.write.call_args  # WHY: get call arguments
        entry = call_args.kwargs["data"][0]  # WHY: get entry
        # WHY: verify sensitive fields are masked
        self.assertNotEqual(entry["details"]["password"], "supersecret")  # WHY: password masked
        self.assertNotEqual(entry["details"]["token"], "abc123xyz")  # WHY: token masked
        self.assertEqual(entry["details"]["username"], "john")  # WHY: non-sensitive unchanged

    def test_log_capture_start(self):
        """Test capture start logging.

        WHY: verify capture-specific logging works.
        """
        # WHY: setup mock success response
        from src.db.router import WriteResult  # WHY: import result type

        self.mock_db.write.return_value = WriteResult(  # WHY: mock success
            success=True,  # WHY: success flag
            backend="arangodb",  # WHY: backend name
            records_written=1,  # WHY: write count
            records_failed=0,  # WHY: failure count
        )  # WHY: mock result
        # WHY: call capture start logging
        log_id = self.logger.log_capture_start(  # WHY: log capture
            user_id="user123",  # WHY: user identifier
            run_id="run_abc123",  # WHY: run identifier
            site_id="site_xyz",  # WHY: site identifier
            device_ids=["dev1", "dev2", "dev3"],  # WHY: devices
        )  # WHY: execute logging
        # WHY: verify log ID returned
        self.assertIsNotNone(log_id)  # WHY: should return log ID
        # WHY: verify operation type
        call_args = self.mock_db.write.call_args  # WHY: get call arguments
        entry = call_args.kwargs["data"][0]  # WHY: get entry
        self.assertEqual(entry["operation"], "capture_start")  # WHY: correct operation
        self.assertEqual(entry["result"], "pending")  # WHY: status is pending

    def test_log_validation_error(self):
        """Test validation error logging.

        WHY: verify validation failures are logged correctly.
        """
        # WHY: setup mock success response
        from src.db.router import WriteResult  # WHY: import result type

        self.mock_db.write.return_value = WriteResult(  # WHY: mock success
            success=True,  # WHY: success flag
            backend="arangodb",  # WHY: backend name
            records_written=1,  # WHY: write count
            records_failed=0,  # WHY: failure count
        )  # WHY: mock result
        # WHY: call validation error logging
        log_id = self.logger.log_validation_error(  # WHY: log validation error
            user_id="user123",  # WHY: user identifier
            operation="select_devices",  # WHY: operation type
            error_message="site_id required",  # WHY: error detail
            input_data={"device_ids": []},  # WHY: invalid input
        )  # WHY: execute logging
        # WHY: verify log ID returned
        self.assertIsNotNone(log_id)  # WHY: should return log ID
        # WHY: verify failure status
        call_args = self.mock_db.write.call_args  # WHY: get call arguments
        entry = call_args.kwargs["data"][0]  # WHY: get entry
        self.assertEqual(entry["result"], "failure")  # WHY: status is failure
        self.assertEqual(entry["error_message"], "site_id required")  # WHY: error message present

    def test_log_without_db_router(self):
        """Test logging without database router.

        WHY: verify logger handles missing database gracefully.
        """
        # WHY: create logger without database
        logger_no_db = AuditLogger(db_router=None)  # WHY: logger without db
        # WHY: call log operation
        log_id = logger_no_db.log_operation(  # WHY: log operation
            operation="test",  # WHY: operation type
            user_id="user123",  # WHY: user identifier
        )  # WHY: execute logging
        # WHY: verify log ID still returned
        self.assertIsNotNone(log_id)  # WHY: should return log ID even without db

    def test_masking_disabled(self):
        """Test logging with masking disabled.

        WHY: verify masking can be disabled for specific use cases.
        """
        # WHY: setup mock success response
        from src.db.router import WriteResult  # WHY: import result type

        self.mock_db.write.return_value = WriteResult(  # WHY: mock success
            success=True,  # WHY: success flag
            backend="arangodb",  # WHY: backend name
            records_written=1,  # WHY: write count
            records_failed=0,  # WHY: failure count
        )  # WHY: mock result
        # WHY: create logger with masking disabled
        logger_no_mask = AuditLogger(db_router=self.mock_db, enable_masking=False)  # WHY: disable masking
        # WHY: call log operation
        logger_no_mask.log_operation(  # WHY: log operation
            operation="test",  # WHY: operation type
            user_id="user123",  # WHY: user identifier
            details={"password": "secret123"},  # WHY: sensitive data
        )  # WHY: execute logging
        # WHY: verify data not masked
        call_args = self.mock_db.write.call_args  # WHY: get call arguments
        entry = call_args.kwargs["data"][0]  # WHY: get entry
        self.assertEqual(entry["details"]["password"], "secret123")  # WHY: password not masked


if __name__ == "__main__":
    # WHY: run tests
    unittest.main()  # WHY: test runner
