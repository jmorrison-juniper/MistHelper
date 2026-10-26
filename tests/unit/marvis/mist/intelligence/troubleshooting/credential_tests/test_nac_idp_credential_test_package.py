"""Package smoke tests for the NAC identity provider credential test."""


def test_nac_idp_credential_test_package_imports() -> None:
    """Import the package and expose the menu handler."""
    import src.mist.intelligence.troubleshooting.nac_idp_credential_test as package  # Import the moved dependency.

    assert package.__all__ == ["NacIdpCredentialTest"]  # Prove the public menu handler export is stable.
