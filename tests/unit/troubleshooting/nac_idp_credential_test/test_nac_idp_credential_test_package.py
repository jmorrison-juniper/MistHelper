"""Package smoke tests for the NAC identity provider credential test."""


def test_nac_idp_credential_test_package_imports() -> None:
    """Import the package before the operation modules exist."""
    import src.troubleshooting.nac_idp_credential_test as package  # Ensure the package path is importable.

    assert package.__doc__  # Prove the package module loaded during the setup task group.
