"""Verify that display masking preserves the existing portal parameter contract."""

from web_portal.services.operation import PARAMETER_REGISTRY, _required_text_param, _text_param


class TestVerificationMetadata:
    """Keep the verification override separate from ordinary text parameters."""

    def test_verification_retains_its_required_text_contract(self) -> None:
        """Only the display override changes the established verification metadata."""
        assert PARAMETER_REGISTRY["247"] == {
            "category": "interactive",
            "parameters": [
                {
                    "name": "email_change_token",
                    "label": "Email Change Token",
                    "param_type": "text",
                    "required": True,
                    "placeholder": "Token from the Mist email",
                    "input_type": "password",
                }
            ],
        }

    def test_only_verification_requests_password_display(self) -> None:
        """No other registered control gains the password display override."""
        masked = [
            (menu_number, parameter["name"])
            for menu_number, entry in PARAMETER_REGISTRY.items()
            for parameter in entry.get("parameters", [])
            if parameter.get("input_type") == "password"
        ]
        assert masked == [("247", "email_change_token")]

    def test_ordinary_text_builders_keep_their_metadata(self) -> None:
        """Optional and required text controls do not inherit masking."""
        optional = _text_param("probe", "Probe", placeholder="Example")
        required = _required_text_param("probe", "Probe", placeholder="Example")
        assert optional == {
            "name": "probe",
            "label": "Probe",
            "param_type": "text",
            "required": False,
            "placeholder": "Example",
        }
        assert required == {**optional, "required": True}
