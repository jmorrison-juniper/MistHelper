"""Tests for the NAC identity provider credential test models."""

from __future__ import annotations  # WHY: keep annotation behavior the same as source modules.

import json  # WHY: parse the attributes cell from export rows.

from src.mist.intelligence.troubleshooting.nac_idp_credential_test.model import (  # Import the moved dependency.
    RESULT_FIELD_NAMES,
    CredentialTestRequest,
    CredentialTestResult,
    IdentityProviderChoice,
)


def test_nac_idp_credential_test_request_body_shape() -> None:
    """Build the exact request body required by the feature contract."""
    request = CredentialTestRequest("idp-1", "user@example.net", "hidden-value")  # WHY: representative body.

    body = request.as_body()  # WHY: this is the dictionary sent to Mist.

    assert body == {  # WHY: acceptance criteria require this exact shape.
        "idp_id": "idp-1",
        "username": "user@example.net",
        "password": "hidden-value",
    }


def test_nac_idp_credential_test_export_row_has_no_password() -> None:
    """Exclude the password from attributes and export rows."""
    provider = IdentityProviderChoice("idp-1", "Corp LDAP", "ldap")  # WHY: result needs provider context.
    result = CredentialTestResult.from_response(  # WHY: normalize a response that echoes unsafe fields.
        provider,
        "user@example.net",
        200,
        {"status": "success", "groups": ["staff"], "password": "hidden-value"},
    )

    row = result.as_row()  # WHY: export row is the file-facing safety boundary.
    attributes = json.loads(row["attributes"])  # WHY: inspect the serialized attributes cell.

    assert "password" not in row  # WHY: no password column is allowed.
    assert "password" not in attributes  # WHY: echoed secret fields must be filtered.
    assert row["verdict"] == "success"  # WHY: success verdict must reach the operator.
    assert tuple(row.keys()) == RESULT_FIELD_NAMES  # WHY: fixed CSV column order prevents drift.


def test_nac_idp_credential_test_failure_reason_is_readable() -> None:
    """Keep the API failure reason without raising an exception."""
    provider = IdentityProviderChoice("idp-1", "Corp LDAP", "ldap")  # WHY: result needs provider context.

    result = CredentialTestResult.from_response(  # WHY: failed validation returns a safe result object.
        provider,
        "user@example.net",
        200,
        {"status": "failure", "error": "Invalid Credentials", "idp_type": "ldap"},
    )

    assert result.status == "failure"  # WHY: body status controls the verdict.
    assert result.reason == "Invalid Credentials"  # WHY: operator needs the exact API reason.
    assert result.attributes == {"idp_type": "ldap"}  # WHY: safe attributes stay available.
